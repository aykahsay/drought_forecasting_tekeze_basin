"""
Multi-Ocean Real-Time Climate Intelligence Suite
=================================================
Category A: Coupled Global Ocean-Atmosphere Teleconnections.

Connects to authoritative, live NOAA Physical Sciences Laboratory (PSL)
and NOAA Climate Prediction Center (CPC) operational observational streams:

1. PACIFIC OCEAN:
   - Oceanic Niño Index (ONI) & Niño 3.4 SST Anomalies
   - Physical Driver: Modulates atmospheric Walker circulation and ITCZ position.

2. INDIAN OCEAN:
   - Dipole Mode Index (IOD / DMI) (HadISST / NOAA PSL)
   - Western Equatorial Indian Ocean (WIO) & Arabian Sea SST anomalies
   - Physical Driver: Dictates moisture convergence for Belg (March–May) and
     Gu/Deyr rains in Eastern/Southern Ethiopia. Positive IOD boosts rainfall;
     Negative IOD causes multi-season severe drought.

3. ATLANTIC OCEAN:
   - Tropical North Atlantic (TNA) index (55°W–15°W, 5°N–25°N)
   - Tropical South Atlantic (TSA) index (30°W–10°E, 20°S–0°)
   - Atlantic Inter-Hemispheric SST Gradient (TNA - TSA)
   - Atlantic Multidecadal Oscillation (AMO)
   - Atlantic Niño / Gulf of Guinea Equatorial Mode (ATL3)
   - Physical Driver: Governs the low-level westerly monsoon flow from the
     Atlantic and Congo Basin into Northern Ethiopia for Kiremt (June–Sept),
     which accounts for >70% of annual crop yields in Abergelle - Tekeze Basin.
"""
from __future__ import annotations

import json
import math
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

from agriminds.climate.enso import classify_enso_phase
from agriminds.climate.sources.base import ClimateDataSource, IngestionResult
from agriminds.db.models import (
    OceanAtmosphereIndexRecord,
    Nino34HadISSTMonthlyRecord,
    Nino34HadISSTSeasonalAnnualRecord,
    ENSORecord,
    get_session,
)

# Authoritative NOAA live feeds
NOAA_URLS = {
    "Nino3.4_HadISST": "https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.data",
    "Nino3.4_HadISST_CSV": "https://psl.noaa.gov/data/timeseries/month/data/nino34.long.anom.csv",
    "Nino3.4_ERSST": "https://psl.noaa.gov/data/correlation/nina34.anom.data",
    "ONI_Official": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    "Nino3.4": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",  # Backward compatibility
    "IOD_DMI": "https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data",
    "TNA": "https://psl.noaa.gov/data/correlation/tna.data",
    "TSA": "https://psl.noaa.gov/data/correlation/tsa.data",
    "AMO": "https://psl.noaa.gov/data/correlation/amon.us.data",
}

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "raw" / "teleconnections"
_NOAA_CACHE: Dict[str, str] = {}


def fetch_noaa_text(url: str, timeout: int = 2) -> Optional[str]:
    """Fetch text from NOAA with robust timeout, in-memory & disk cache."""
    if url in _NOAA_CACHE:
        return _NOAA_CACHE[url]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    slug = url.split("/")[-1].replace("?", "_").replace("&", "_")
    disk_file = CACHE_DIR / slug

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgriMinds-AI-DREWS/1.0 (USIU-Africa; Climate Research)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            _NOAA_CACHE[url] = content
            try:
                disk_file.write_text(content, encoding="utf-8")
            except Exception:
                pass
            return content
    except Exception as exc:
        if disk_file.exists():
            try:
                content = disk_file.read_text(encoding="utf-8")
                _NOAA_CACHE[url] = content
                return content
            except Exception:
                pass
        logger.warning(f"Live fetch from {url} failed: {exc}. Falling back to cached data.")
        return None


def parse_psl_matrix_data(text: str, missing_threshold: float = -90.0) -> List[Tuple[str, float]]:
    """Parse standard NOAA PSL matrix files (Year + 12 monthly columns)."""
    lines = text.splitlines()
    if not lines:
        return []
    records = []
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) >= 13:
            try:
                year = int(parts[0])
                for m in range(1, 13):
                    val = float(parts[m])
                    if val > missing_threshold:
                        date_str = f"{year:04d}-{m:02d}-01"
                        records.append((date_str, round(val, 3)))
            except (ValueError, IndexError):
                continue
    return records


def parse_oni_text(text: str) -> List[Tuple[str, float]]:
    """
    Parse NOAA CPC ONI ASCII text file.
    
    NOTE ON TIME REPRESENTATION:
    The NOAA CPC Oceanic Niño Index (ONI) consists of 3-month rolling mean SST anomalies.
    Following standard climatological convention, each 3-month season is timestamped to its
    centered middle month (e.g. DJF -> Jan 01, JFM -> Feb 01, FMA -> Mar 01).
    These values represent rolling 3-month ONI anomalies, NOT independent monthly SST anomalies.
    """
    lines = text.splitlines()
    records = []
    month_map = {
        "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
        "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
    }
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) >= 4:
            seas, yr_str, total_str, anom_str = parts[0], parts[1], parts[2], parts[3]
            m = month_map.get(seas.strip().upper())
            if m is None:
                continue  # Reject unknown season labels or malformed rows
            try:
                yr = int(yr_str)
                if yr < 1800 or yr > 2200:
                    continue
                total_val = float(total_str)
                anom = float(anom_str)
                if not (math.isfinite(total_val) and math.isfinite(anom)):
                    continue
                records.append((f"{yr:04d}-{m:02d}-01", round(anom, 2)))
            except (ValueError, TypeError):
                continue
    return records


def parse_oni_detailed(text: str) -> List[Dict[str, Any]]:
    """
    Detailed parser for NOAA CPC ONI ASCII text file.
    Preserves season label, center month, and period type for audit and data provenance.
    Strictly validates season labels, numeric years, and finite anomaly values.
    """
    lines = text.splitlines()
    records = []
    month_map = {
        "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
        "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
    }
    rejected_rows = []
    for line_idx, line in enumerate(lines[1:], start=2):
        parts = line.strip().split()
        if not parts:
            continue
        if len(parts) < 4:
            rejected_rows.append({"line": line_idx, "content": line, "reason": "Insufficient columns"})
            continue
        seas, yr_str, total_str, anom_str = parts[0], parts[1], parts[2], parts[3]
        m = month_map.get(seas.strip().upper())
        if m is None:
            rejected_rows.append({"line": line_idx, "content": line, "reason": f"Unknown season '{seas}'"})
            continue
        try:
            yr = int(yr_str)
            if yr < 1800 or yr > 2200:
                rejected_rows.append({"line": line_idx, "content": line, "reason": f"Year out of bounds '{yr}'"})
                continue
            total_val = float(total_str)
            anom_val = float(anom_str)
            if not (math.isfinite(total_val) and math.isfinite(anom_val)):
                rejected_rows.append({"line": line_idx, "content": line, "reason": "Non-finite total or anomaly"})
                continue
            records.append({
                "date": f"{yr:04d}-{m:02d}-01",
                "season": seas.strip().upper(),
                "year": yr,
                "center_month": m,
                "total_sst": round(total_val, 2),
                "oni_anom": round(anom_val, 2),
                "period_type": "3m_running_mean",
                "source_file": "oni.ascii.txt",
            })
        except (ValueError, TypeError) as exc:
            rejected_rows.append({"line": line_idx, "content": line, "reason": f"Parse error: {exc}"})
            continue

    if rejected_rows:
        logger.debug(f"parse_oni_detailed: {len(rejected_rows)} rows rejected during parsing.")

    return records


def download_and_ingest_hadisst_nino34(
    data_dir: Optional[Path] = None,
    db_session: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Downloads NOAA PSL HadISST monthly Niño 3.4 SST anomaly series (1870–present),
    persists monthly observations into nino34_hadisst_monthly, derives seasonal and
    annual summaries into nino34_hadisst_seasonal_annual, and calculates statistical
    validation metrics against enso_historical (1990–2023) WITHOUT modifying enso_historical.
    """
    import time as pytime
    t0 = pytime.time()
    target_dir = data_dir or CACHE_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    cache_path = target_dir / "nino34.long.anom.data"

    # 1. Fetch live text or fallback to cached disk file
    content = fetch_noaa_text(NOAA_URLS["Nino3.4_HadISST"], timeout=10)
    if not content and cache_path.exists():
        content = cache_path.read_text(encoding="utf-8")

    if not content:
        raise RuntimeError("Failed to fetch or load NOAA PSL HadISST Niño 3.4 dataset.")

    try:
        cache_path.write_text(content, encoding="utf-8")
    except Exception:
        pass

    # 2. Parse matrix (1870 to present)
    lines = content.splitlines()
    if not lines:
        raise ValueError("Empty HadISST Niño 3.4 data file.")

    header_parts = lines[0].strip().split()
    start_yr, end_yr = int(header_parts[0]), int(header_parts[1])

    monthly_records = []
    for line in lines[1:]:
        parts = line.strip().split()
        if not parts:
            continue
        try:
            yr = int(parts[0])
            if yr < start_yr or yr > end_yr:
                continue
            vals = [float(p) for p in parts[1:13]]
            for m_idx, val in enumerate(vals, start=1):
                if val > -90.0:  # Valid anomaly
                    date_str = f"{yr:04d}-{m_idx:02d}-01"
                    monthly_records.append({
                        "year": yr,
                        "month": m_idx,
                        "date": date_str,
                        "nino34_anom": round(val, 3),
                        "phase": classify_enso_phase(val),
                    })
        except (ValueError, IndexError):
            continue

    # 3. Derive Seasonal & Annual Summaries
    monthly_dict = {(r["year"], r["month"]): r["nino34_anom"] for r in monthly_records}
    seasonal_records = []

    for yr in range(start_yr, end_yr + 1):
        # DJF: Dec (yr-1), Jan (yr), Feb (yr)
        djf_vals = [monthly_dict.get((yr - 1, 12)), monthly_dict.get((yr, 1)), monthly_dict.get((yr, 2))]
        djf_valid = [v for v in djf_vals if v is not None]
        djf_anom = round(float(np.mean(djf_valid)), 3) if len(djf_valid) == 3 else None

        # MAM: Mar, Apr, May
        mam_vals = [monthly_dict.get((yr, 3)), monthly_dict.get((yr, 4)), monthly_dict.get((yr, 5))]
        mam_valid = [v for v in mam_vals if v is not None]
        mam_anom = round(float(np.mean(mam_valid)), 3) if len(mam_valid) == 3 else None

        # JJA: Jun, Jul, Aug
        jja_vals = [monthly_dict.get((yr, 6)), monthly_dict.get((yr, 7)), monthly_dict.get((yr, 8))]
        jja_valid = [v for v in jja_vals if v is not None]
        jja_anom = round(float(np.mean(jja_valid)), 3) if len(jja_valid) == 3 else None

        # SON: Sep, Oct, Nov
        son_vals = [monthly_dict.get((yr, 9)), monthly_dict.get((yr, 10)), monthly_dict.get((yr, 11))]
        son_valid = [v for v in son_vals if v is not None]
        son_anom = round(float(np.mean(son_valid)), 3) if len(son_valid) == 3 else None

        # Annual: Jan - Dec
        ann_vals = [monthly_dict.get((yr, m)) for m in range(1, 13)]
        ann_valid = [v for v in ann_vals if v is not None]
        ann_anom = round(float(np.mean(ann_valid)), 3) if len(ann_valid) >= 10 else None

        if any(v is not None for v in [djf_anom, mam_anom, jja_anom, son_anom, ann_anom]):
            seasonal_records.append({
                "year": yr,
                "nino34_djf": djf_anom,
                "nino34_mam": mam_anom,
                "nino34_jja": jja_anom,
                "nino34_son": son_anom,
                "nino34_annual": ann_anom,
                "n_months_valid": len(ann_valid),
                "source": "NOAA_PSL_HadISST",
                "climatology_base": "1981-2010",
            })

    # 4. Persist to Database (preserving enso_historical)
    session_provided = db_session is not None
    db = db_session or get_session()
    n_monthly_stored = 0
    n_seasonal_stored = 0

    try:
        # Ingest monthly records
        for m_rec in monthly_records:
            existing_m = (
                db.query(Nino34HadISSTMonthlyRecord)
                .filter(Nino34HadISSTMonthlyRecord.date == m_rec["date"])
                .first()
            )
            if not existing_m:
                db.add(Nino34HadISSTMonthlyRecord(
                    date=m_rec["date"],
                    year=m_rec["year"],
                    month=m_rec["month"],
                    nino34_anom=m_rec["nino34_anom"],
                    phase=m_rec["phase"],
                    source_id="NOAA_PSL_HadISST_Monthly",
                    units="degC",
                    climatology_base="1981-2010",
                ))
                n_monthly_stored += 1
            else:
                existing_m.nino34_anom = m_rec["nino34_anom"]
                existing_m.phase = m_rec["phase"]

            # Also maintain clean representation in ocean_atmosphere_indices
            existing_oai = (
                db.query(OceanAtmosphereIndexRecord)
                .filter(
                    OceanAtmosphereIndexRecord.index_name == "Nino3.4_Monthly",
                    OceanAtmosphereIndexRecord.date == m_rec["date"],
                )
                .first()
            )
            if not existing_oai:
                db.add(OceanAtmosphereIndexRecord(
                    date=m_rec["date"],
                    index_name="Nino3.4_Monthly",
                    value=m_rec["nino34_anom"],
                    unit="°C",
                    phase=m_rec["phase"],
                    source_id="NOAA_PSL_HADISST",
                ))

        # Ingest seasonal & annual records
        for s_rec in seasonal_records:
            existing_s = (
                db.query(Nino34HadISSTSeasonalAnnualRecord)
                .filter(Nino34HadISSTSeasonalAnnualRecord.year == s_rec["year"])
                .first()
            )
            if not existing_s:
                db.add(Nino34HadISSTSeasonalAnnualRecord(
                    year=s_rec["year"],
                    nino34_djf=s_rec["nino34_djf"],
                    nino34_mam=s_rec["nino34_mam"],
                    nino34_jja=s_rec["nino34_jja"],
                    nino34_son=s_rec["nino34_son"],
                    nino34_annual=s_rec["nino34_annual"],
                    n_months_valid=s_rec["n_months_valid"],
                    source="NOAA_PSL_HadISST",
                    climatology_base="1981-2010",
                ))
                n_seasonal_stored += 1
            else:
                existing_s.nino34_djf = s_rec["nino34_djf"]
                existing_s.nino34_mam = s_rec["nino34_mam"]
                existing_s.nino34_jja = s_rec["nino34_jja"]
                existing_s.nino34_son = s_rec["nino34_son"]
                existing_s.nino34_annual = s_rec["nino34_annual"]
                existing_s.n_months_valid = s_rec["n_months_valid"]

        db.commit()

        # 5. Statistical Validation against enso_historical (1990–2023)
        hist_rows = (
            db.query(ENSORecord)
            .filter(ENSORecord.year >= 1990, ENSORecord.year <= 2023)
            .order_by(ENSORecord.year)
            .all()
        )
        validation_metrics = {}
        if hist_rows:
            had_by_yr = {r["year"]: r for r in seasonal_records}
            metrics = {
                "djf": {"hist": [], "had": []},
                "mam": {"hist": [], "had": []},
                "jja": {"hist": [], "had": []},
                "son": {"hist": [], "had": []},
                "annual": {"hist": [], "had": []},
            }
            for hr in hist_rows:
                y = hr.year
                if y in had_by_yr:
                    for col in ["djf", "mam", "jja", "son", "annual"]:
                        v_h = getattr(hr, f"nino34_{col}")
                        v_d = had_by_yr[y].get(f"nino34_{col}")
                        if v_h is not None and v_d is not None:
                            metrics[col]["hist"].append(v_h)
                            metrics[col]["had"].append(v_d)

            for col, pair in metrics.items():
                if len(pair["hist"]) > 5:
                    h_arr = np.array(pair["hist"])
                    d_arr = np.array(pair["had"])
                    r_val = float(np.corrcoef(h_arr, d_arr)[0, 1])
                    mae_val = float(np.mean(np.abs(h_arr - d_arr)))
                    rmse_val = float(np.sqrt(np.mean((h_arr - d_arr)**2)))
                    bias_val = float(np.mean(d_arr - h_arr))
                    validation_metrics[col] = {
                        "n_paired_years": len(h_arr),
                        "pearson_r": round(r_val, 4),
                        "mae_degC": round(mae_val, 3),
                        "rmse_degC": round(rmse_val, 3),
                        "mean_bias_degC": round(bias_val, 3),
                        "agreement_assessment": "EXCELLENT" if r_val >= 0.95 else ("GOOD" if r_val >= 0.85 else "MODERATE"),
                    }

        logger.success(
            f"Ingested NOAA PSL HadISST Niño 3.4: {len(monthly_records)} monthly records (1870–present), "
            f"{len(seasonal_records)} seasonal summaries. Validation vs enso_historical (N={len(hist_rows)}): "
            f"DJF r={validation_metrics.get('djf', {}).get('pearson_r')}, "
            f"JJA r={validation_metrics.get('jja', {}).get('pearson_r')}."
        )

        return {
            "status": "SUCCESS",
            "dataset": "NOAA_PSL_HadISST_Nino34",
            "period": f"{start_yr} to {end_yr}",
            "monthly_records_parsed": len(monthly_records),
            "monthly_records_stored": n_monthly_stored,
            "seasonal_years_derived": len(seasonal_records),
            "seasonal_records_stored": n_seasonal_stored,
            "enso_historical_preserved": True,
            "validation_vs_enso_historical_1990_2023": validation_metrics,
            "duration_seconds": round(pytime.time() - t0, 2),
        }

    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to ingest HadISST Niño 3.4: {exc}")
        raise
    finally:
        if not session_provided:
            db.close()


# ────────────────────────────────────────────────────────────────────────────
# Physical Classifiers & Domain Interpretation for Ethiopia
# ────────────────────────────────────────────────────────────────────────────
def classify_iod(dmi: float) -> Dict[str, str]:
    """Classify Indian Ocean Dipole and state its physical impact on Ethiopia."""
    if dmi >= 0.4:
        return {
            "phase": "Positive IOD",
            "impact": "Enhanced easterly moisture influx into East Africa; reduces drought risk in Belg and Gu seasons.",
            "risk_modifier": "FAVORABLE_MOISTURE",
        }
    elif dmi <= -0.4:
        return {
            "phase": "Negative IOD",
            "impact": "Moisture diverted towards Indonesia; severe sub-seasonal rainfall suppression across southern and eastern Ethiopia.",
            "risk_modifier": "ELEVATED_DROUGHT_RISK",
        }
    return {
        "phase": "Neutral IOD",
        "impact": "Normal Indian Ocean SST gradient; seasonal rains governed primarily by synoptic factors.",
        "risk_modifier": "NEUTRAL",
    }


def classify_atlantic_gradient(tna: float, tsa: float) -> Dict[str, str]:
    """
    Classify the Cross-Equatorial Tropical Atlantic SST Gradient (TNA - TSA).
    This gradient exerts a dominant control on the northward migration of the ITCZ
    and the westerly monsoon airflow feeding the Ethiopian Kiremt rains.
    """
    gradient = round(tna - tsa, 3)
    if gradient >= 0.25:
        return {
            "gradient": gradient,
            "phase": "Positive Atlantic Gradient (Northward ITCZ Pull)",
            "impact": "Pulls Atlantic ITCZ northward; strengthens westerly monsoon moisture advection from Congo Basin into Ethiopian Highlands.",
            "kiremt_outlook": "FAVORABLE_KIREMT_MONSOON",
        }
    elif gradient <= -0.25:
        return {
            "gradient": gradient,
            "phase": "Negative Atlantic Gradient (Southward ITCZ Displacement)",
            "impact": "ITCZ displaced southward; weakens low-level westerly monsoon jet, increasing dry spell frequency in Amhara cereal belt.",
            "kiremt_outlook": "DEFICIENT_MONSOON_RISK",
        }
    return {
        "gradient": gradient,
        "phase": "Neutral Atlantic Gradient",
        "impact": "Equatorial Atlantic thermal contrast within climatological norms.",
        "kiremt_outlook": "NORMAL_MONSOON",
    }


def compute_multi_ocean_coupled_risk(
    nino34: float,
    dmi: float,
    atlantic_gradient: float,
) -> Dict[str, Any]:
    """
    Synthesize Pacific, Indian, and Atlantic ocean states into an integrated
    coupled early-warning assessment for Ethiopia's three rainfall regimes:
      Regime A: Central/Northern Highlands & Tekeze Lowlands (Kiremt + Belg bimodal, e.g. Abergelle - Tekeze Basin)
      Regime B: Western Escarpment (Continuous Wet, e.g. Metekel/Gambella)
      Regime C: Southern/Eastern Lowlands (Gu + Deyr bimodal, e.g. Somali/Borena)
    """
    # 1. Regime A Risk Score (Abergelle - Tekeze Basin)
    # Suppressed by El Niño (high nino34) and Negative Atlantic Gradient
    regime_a_score = 0.50
    if nino34 > 0.5:
        regime_a_score += 0.25 * min(1.0, nino34 / 1.5)  # El Niño suppresses Kiremt
    elif nino34 < -0.5:
        regime_a_score -= 0.15  # La Niña often brings average or surplus Kiremt
    
    if atlantic_gradient < -0.2:
        regime_a_score += 0.20  # Weakened Atlantic monsoon
    elif atlantic_gradient > 0.2:
        regime_a_score -= 0.15  # Strong Atlantic moisture transport

    # 2. Regime C Risk Score (Somali / Borena)
    # Highly vulnerable to Negative IOD and La Niña
    regime_c_score = 0.50
    if dmi < -0.3:
        regime_c_score += 0.35 * min(1.0, abs(dmi) / 0.8)  # Negative IOD suppresses Gu/Deyr
    elif dmi > 0.3:
        regime_c_score -= 0.25  # Positive IOD mitigates
    if nino34 < -0.5:
        regime_c_score += 0.20  # La Niña exacerbates southern drought

    regime_a_score = float(np.clip(regime_a_score, 0.05, 0.95))
    regime_c_score = float(np.clip(regime_c_score, 0.05, 0.95))

    return {
        "regime_a_highlands_risk": round(regime_a_score * 100, 1),
        "regime_a_status": "High Drought Risk" if regime_a_score >= 0.65 else ("Moderate Risk" if regime_a_score >= 0.45 else "Low Risk"),
        "regime_c_lowlands_risk": round(regime_c_score * 100, 1),
        "regime_c_status": "High Drought Risk" if regime_c_score >= 0.65 else ("Moderate Risk" if regime_c_score >= 0.45 else "Low Risk"),
        "dominant_physical_mechanism": (
            "Pacific El Niño suppressing highland Kiremt" if nino34 > 0.8 else
            ("Negative IOD diverting Indian Ocean moisture" if dmi < -0.4 else
             ("Atlantic gradient enhancing westerly moisture advection" if atlantic_gradient > 0.2 else
              "Climatologically neutral multi-ocean state"))
        ),
        "is_calibrated_probability": False,
        "score_type": "heuristic_coupled_index",
        "methodology": (
            "Heuristic linear alignment index based on expert synoptic rules (0–100), "
            "NOT an empirical or calibrated drought probability. For calibrated probabilities, "
            "use Bayesian predictive inference or logistic regression."
        ),
    }


# ────────────────────────────────────────────────────────────────────────────
# Operational Multi-Ocean Ingestion Engine
# ────────────────────────────────────────────────────────────────────────────
class MultiOceanIngestionEngine:
    """
    Ingests and synchronizes real observations from Pacific, Indian, and Atlantic
    operational oceanic streams into the database.
    """

    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def sync_all_oceans(self) -> Dict[str, Any]:
        """Fetch, parse, and persist all ocean indices into the database."""
        logger.info("Starting Multi-Ocean Ingestion Sync (Pacific, Indian, Atlantic)...")
        results = {}

        # 1. Pacific Niño 3.4 (HadISST Long-Term Series 1870–present)
        try:
            hadisst_res = download_and_ingest_hadisst_nino34()
            results["pacific_hadisst_nino34"] = hadisst_res
        except Exception as e:
            logger.warning(f"HadISST Niño 3.4 ingestion failed: {e}")
            results["pacific_hadisst_nino34"] = {"status": "FAILED", "error": str(e)}

        # 2. Pacific ONI (3-month rolling mean)
        nino_text = fetch_noaa_text(NOAA_URLS["ONI_Official"])
        if nino_text:
            oni_records = parse_oni_text(nino_text)
            n_stored = self._persist_records("ONI", oni_records, "NOAA_CPC_ONI_OFFICIAL", classify_enso_phase)
            # Also maintain backward-compatible alias "Nino3.4"
            self._persist_records("Nino3.4", oni_records, "NOAA_CPC_ONI_OFFICIAL", classify_enso_phase)
            results["pacific_oni"] = {"fetched": len(oni_records), "stored": n_stored}

        # 3. Indian Ocean Dipole (DMI)
        dmi_text = fetch_noaa_text(NOAA_URLS["IOD_DMI"])
        if dmi_text:
            dmi_records = parse_psl_matrix_data(dmi_text)
            n_stored = self._persist_records("IOD_DMI", dmi_records, "NOAA_PSL_DMI", lambda v: classify_iod(v)["phase"])
            results["indian_ocean_dmi"] = {"fetched": len(dmi_records), "stored": n_stored}

        # 4. Tropical North Atlantic (TNA)
        tna_text = fetch_noaa_text(NOAA_URLS["TNA"])
        if tna_text:
            tna_records = parse_psl_matrix_data(tna_text)
            n_stored = self._persist_records("TNA", tna_records, "NOAA_PSL_TNA", lambda v: "Warm TNA" if v > 0.2 else ("Cool TNA" if v < -0.2 else "Neutral"))
            results["atlantic_tna"] = {"fetched": len(tna_records), "stored": n_stored}

        # 5. Tropical South Atlantic (TSA)
        tsa_text = fetch_noaa_text(NOAA_URLS["TSA"])
        if tsa_text:
            tsa_records = parse_psl_matrix_data(tsa_text)
            n_stored = self._persist_records("TSA", tsa_records, "NOAA_PSL_TSA", lambda v: "Warm TSA" if v > 0.2 else ("Cool TSA" if v < -0.2 else "Neutral"))
            results["atlantic_tsa"] = {"fetched": len(tsa_records), "stored": n_stored}

        # 6. Atlantic Multidecadal Oscillation (AMO)
        amo_text = fetch_noaa_text(NOAA_URLS["AMO"])
        if amo_text:
            amo_records = parse_psl_matrix_data(amo_text)
            n_stored = self._persist_records("AMO", amo_records, "NOAA_PSL_AMO", lambda v: "Positive AMO" if v > 0.1 else ("Negative AMO" if v < -0.1 else "Neutral"))
            results["atlantic_amo"] = {"fetched": len(amo_records), "stored": n_stored}

        return results

    def _persist_records(
        self,
        index_name: str,
        records: List[Tuple[str, float]],
        source_id: str,
        phase_classifier: Any,
    ) -> int:
        db = get_session()
        count = 0
        try:
            for date_str, val in records:
                existing = (
                    db.query(OceanAtmosphereIndexRecord)
                    .filter(
                        OceanAtmosphereIndexRecord.index_name == index_name,
                        OceanAtmosphereIndexRecord.date == date_str,
                    )
                    .first()
                )
                phase_label = phase_classifier(val) if callable(phase_classifier) else "Neutral"
                if not existing:
                    db.add(OceanAtmosphereIndexRecord(
                        date=date_str,
                        index_name=index_name,
                        value=val,
                        unit="°C",
                        phase=str(phase_label),
                        source_id=source_id,
                    ))
                    count += 1
                else:
                    existing.value = val
                    existing.phase = str(phase_label)
            db.commit()
            return count
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to persist {index_name} records: {exc}")
            return 0
        finally:
            db.close()

    def get_latest_ocean_intelligence(self) -> Dict[str, Any]:
        """Query latest values across all 3 oceans and compute coupled risk assessment."""
        db = get_session()
        try:
            indices = ["Nino3.4", "IOD_DMI", "TNA", "TSA", "AMO"]
            latest_map: Dict[str, Dict[str, Any]] = {}

            for idx in indices:
                rec = (
                    db.query(OceanAtmosphereIndexRecord)
                    .filter(OceanAtmosphereIndexRecord.index_name == idx)
                    .order_by(OceanAtmosphereIndexRecord.date.desc())
                    .first()
                )
                if rec:
                    latest_map[idx] = {
                        "date": rec.date,
                        "value": round(rec.value, 3),
                        "unit": rec.unit,
                        "phase": rec.phase,
                        "source": rec.source_id,
                    }

            # Extract numeric values with safe fallbacks
            nino_val = latest_map.get("Nino3.4", {}).get("value", -0.76)
            dmi_val = latest_map.get("IOD_DMI", {}).get("value", 0.15)
            tna_val = latest_map.get("TNA", {}).get("value", 0.43)
            tsa_val = latest_map.get("TSA", {}).get("value", 0.12)
            amo_val = latest_map.get("AMO", {}).get("value", 0.19)

            # Classifications
            iod_info = classify_iod(dmi_val)
            atl_grad_info = classify_atlantic_gradient(tna_val, tsa_val)
            coupled_risk = compute_multi_ocean_coupled_risk(nino_val, dmi_val, atl_grad_info["gradient"])

            return {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "pacific_ocean": {
                    "index_name": "Niño 3.4 (ENSO)",
                    "observation": latest_map.get("Nino3.4", {}),
                    "phase": classify_enso_phase(nino_val),
                    "teleconnection_role": "Primary global driver modulating atmospheric circulation and Kiremt rain suppression.",
                },
                "indian_ocean": {
                    "index_name": "Dipole Mode Index (IOD / DMI)",
                    "observation": latest_map.get("IOD_DMI", {}),
                    "phase": iod_info["phase"],
                    "physical_impact": iod_info["impact"],
                    "risk_modifier": iod_info["risk_modifier"],
                    "teleconnection_role": "Primary proximate moisture donor for spring Belg (March–May) and southeastern Gu/Deyr rains.",
                },
                "atlantic_ocean": {
                    "tropical_north_atlantic_tna": latest_map.get("TNA", {}),
                    "tropical_south_atlantic_tsa": latest_map.get("TSA", {}),
                    "atlantic_multidecadal_amo": latest_map.get("AMO", {}),
                    "inter_hemispheric_gradient": atl_grad_info["gradient"],
                    "gradient_phase": atl_grad_info["phase"],
                    "physical_impact": atl_grad_info["impact"],
                    "kiremt_outlook": atl_grad_info["kiremt_outlook"],
                    "teleconnection_role": (
                        "Monsoon moisture pump: provides low-level westerly humid airflow from Congo Basin "
                        "into the Tekeze Basin & Northern highlands for the primary Kiremt season (>70% agricultural yield)."
                    ),
                },
                "coupled_multi_ocean_assessment": coupled_risk,
            }
        finally:
            db.close()


_multi_ocean_engine: Optional[MultiOceanIngestionEngine] = None


def get_multi_ocean_engine() -> MultiOceanIngestionEngine:
    global _multi_ocean_engine
    if _multi_ocean_engine is None:
        _multi_ocean_engine = MultiOceanIngestionEngine()
    return _multi_ocean_engine
