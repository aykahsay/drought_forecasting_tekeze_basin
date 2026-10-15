"""
run_fao56_penman_monteith_spei_pipeline.py
==========================================
End-to-end implementation of the FAO-56 Penman-Monteith Reference Evapotranspiration (ET_0)
and SPEI-3 pipeline for Tanqua Abergele Woreda (Tekezé River Basin, Northern Ethiopia):

1. Calculates monthly FAO-56 Penman-Monteith ET_0 across all 528 months (1981–2024).
2. Derives atmospheric water deficit: D_t = P_t - ET_{0, t}.
3. Computes rolling 3-month water balance deficits: D_{3, t}.
4. Standardizes via Hosking's Generalized Logistic (GLO) distribution using unbiased L-moments
   fitted strictly on the pre-2016 historical baseline (1981 <= year < 2016) per Gate 1 & 2 zero-leakage standards.
5. Performs comparative analysis between SPI-3, SPEI-3 (Hargreaves), and SPEI-3 (Penman-Monteith).
6. Identifies severe and extreme drought events and exports structured metrics and unified dataset.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from drought_forecasting.agriminds.climate.spei_calculator import (
    calculate_fao56_penman_monteith_monthly_et0,
    fit_generalized_logistic_l_moments,
    cdf_generalized_logistic,
)

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MASTER_CSV = PROCESSED_DIR / "abregelle_tekeze_unified_monthly_1981_2024.csv"
OUT_COMPARISON_JSON = PROCESSED_DIR / "fao56_spei3_comparative_audit.json"

# Geographical constants for Tanqua Abergele Woreda
LATITUDE_ABREGELLE = 13.25       # degrees North
ELEVATION_ABREGELLE = 1450.0     # meters above sea level
WIND_SPEED_2M = 2.0             # m/s (FAO-56 standard semi-arid default)


def run_fao56_spei_pipeline():
    print("=" * 88)
    print("AI-DREWS: FAO-56 PENMAN-MONTEITH SPEI-3 PIPELINE (TANQUA ABERGELE, 1981–2024)")
    print("=" * 88)

    if not MASTER_CSV.exists():
        raise FileNotFoundError(f"Missing master climate dataset: {MASTER_CSV}")

    df = pd.read_csv(MASTER_CSV)
    df["date"] = pd.to_datetime(df["date"])
    n = len(df)
    print(f"Loaded master climate dataset: {n} monthly observations ({df['date'].min().date()} to {df['date'].max().date()})")

    # 1. Compute monthly FAO-56 Penman-Monteith ET0
    print("\n[1/4] Calculating FAO-56 Penman-Monteith Reference Evapotranspiration (ET_0)...")
    et0_pm_list = []
    days_per_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

    for idx, row in df.iterrows():
        y = int(row["year"])
        m = int(row["month"])
        # Check leap year for Feb
        days = 29 if (m == 2 and (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0))) else days_per_month[m]

        t_max = float(row["t_max_c"])
        t_min = float(row["t_min_c"])
        t_mean = float(row["t_mean_c"])

        et0 = calculate_fao56_penman_monteith_monthly_et0(
            t_max_c=t_max,
            t_min_c=t_min,
            t_mean_c=t_mean,
            latitude_deg=LATITUDE_ABREGELLE,
            month=m,
            days_in_month=days,
            elevation_m=ELEVATION_ABREGELLE,
            wind_speed_2m_m_s=WIND_SPEED_2M,
        )
        et0_pm_list.append(round(et0, 3) if math.isfinite(et0) else np.nan)

    df["et0_fao56_pm_mm"] = et0_pm_list

    # 2. Compute Atmospheric Water Deficit (D_t = P_t - ET_{0, t})
    print("\n[2/4] Deriving Atmospheric Water Balance Deficit (D_t = P_t - ET_0)...")
    df["climatic_water_balance_pm_mm"] = df["chirps_abregelle_precip_mm"] - df["et0_fao56_pm_mm"]

    # 3. Rolling 3-month water balance deficit D_{3, t}
    print("\n[3/4] Standardizing rolling 3-month deficits via Hosking Generalized Logistic L-moments...")
    d_series = df["climatic_water_balance_pm_mm"].values
    d3_acc = np.full(n, np.nan, dtype=np.float64)
    for i in range(2, n):
        w = d_series[i - 2 : i + 1]
        if not np.any(np.isnan(w)):
            d3_acc[i] = np.sum(w)
    df["d3_pm_mm"] = d3_acc

    # Standardize per calendar month strictly on pre-2016 calibration window
    calib_mask = (df["year"] < 2016).values
    spei3_pm = np.full(n, np.nan, dtype=np.float64)
    glo_params_by_month = {}

    for mo in range(12):
        mo_indices = np.arange(mo, n, 12)
        valid_mo = [idx for idx in mo_indices if not np.isnan(d3_acc[idx])]
        train_mo = [idx for idx in valid_mo if calib_mask[idx]]

        if len(train_mo) >= 20:
            sample_d = d3_acc[train_mo]
            try:
                xi, alpha, k = fit_generalized_logistic_l_moments(sample_d)
                glo_params_by_month[f"Month_{mo + 1:02d}"] = {
                    "xi_location": round(xi, 4),
                    "alpha_scale": round(alpha, 4),
                    "k_shape": round(k, 4),
                    "n_calib_years": len(sample_d)
                }
                for idx in valid_mo:
                    val = d3_acc[idx]
                    p_cum = cdf_generalized_logistic(val, xi, alpha, k)
                    p_cum = np.clip(p_cum, 1e-6, 1.0 - 1e-6)
                    spei3_pm[idx] = stats.norm.ppf(p_cum)
            except Exception as e:
                print(f"  [!] Warning: Month {mo + 1} GLO fitting error: {e}")

    df["spei3_fao56_pm"] = np.round(spei3_pm, 4)

    # 4. Save updated master dataset
    df.to_csv(MASTER_CSV, index=False)
    print(f"\n[OK] Updated Master Dataset with FAO-56 SPEI-3: {MASTER_CSV}")

    # 5. Comparative Audit Statistics
    valid_idx = df["spei3_fao56_pm"].notna() & df["spei3"].notna() & df["spi3"].notna()
    sub = df[valid_idx]

    r_spi_spei_pm = float(np.corrcoef(sub["spi3"], sub["spei3_fao56_pm"])[0, 1])
    r_harg_spei_pm = float(np.corrcoef(sub["spei3"], sub["spei3_fao56_pm"])[0, 1])
    mean_et0_pm = float(sub["et0_fao56_pm_mm"].mean())
    mean_pet_harg = float(sub["pet_hargreaves_mm"].mean())

    # Identify severe drought events (Index < -1.5)
    severe_spi3 = set(sub[sub["spi3"] < -1.5]["year"].unique())
    severe_spei3_harg = set(sub[sub["spei3"] < -1.5]["year"].unique())
    severe_spei3_pm = set(sub[sub["spei3_fao56_pm"] < -1.5]["year"].unique())

    print("\n" + "=" * 88)
    print("COMPARATIVE DROUGHT METRIC AUDIT: SPI-3 vs SPEI-3 (Hargreaves) vs SPEI-3 (FAO-56 PM)")
    print("=" * 88)
    print(f"Mean Annual ET0 (FAO-56 PM):           {mean_et0_pm * 12:.1f} mm/yr ({mean_et0_pm:.2f} mm/mo)")
    print(f"Mean Annual PET (Hargreaves-Samani):  {mean_pet_harg * 12:.1f} mm/yr ({mean_pet_harg:.2f} mm/mo)")
    print(f"Correlation: SPI-3 vs SPEI-3 (FAO-56 PM):         r = {r_spi_spei_pm:.4f}")
    print(f"Correlation: SPEI-3 (Harg) vs SPEI-3 (FAO-56 PM): r = {r_harg_spei_pm:.4f}")
    print(f"\nSevere Drought Years (Index < -1.5, Kiremt/Belg):")
    print(f"  • SPI-3 (< -1.5):           {sorted(list(severe_spi3))}")
    print(f"  • SPEI-3 Hargreaves (< -1.5):{sorted(list(severe_spei3_harg))}")
    print(f"  • SPEI-3 FAO-56 PM (< -1.5):  {sorted(list(severe_spei3_pm))}")

    # Notable catastrophic drought years check
    key_droughts = [1984, 1989, 2002, 2009, 2015]
    print(f"\nTarget Diagnostic for Catastrophic Drought Years (September SPEI-3):")
    for yr in key_droughts:
        row_sep = df[(df["year"] == yr) & (df["month"] == 9)]
        if not row_sep.empty:
            p_val = float(row_sep["chirps_abregelle_precip_mm"].values[0])
            spi_val = float(row_sep["spi3"].values[0])
            spei_harg = float(row_sep["spei3"].values[0])
            spei_pm = float(row_sep["spei3_fao56_pm"].values[0])
            print(f"  Year {yr}: Rain={p_val:5.1f}mm | SPI-3={spi_val:+.2f} | SPEI-3(Harg)={spei_harg:+.2f} | SPEI-3(FAO-56 PM)={spei_pm:+.2f}")

    audit_summary = {
        "metadata": {
            "period": "1981-2024",
            "total_months": n,
            "latitude_deg": LATITUDE_ABREGELLE,
            "elevation_m": ELEVATION_ABREGELLE,
            "wind_speed_2m_m_s": WIND_SPEED_2M,
        },
        "mean_monthly_et0_fao56_pm_mm": round(mean_et0_pm, 2),
        "mean_monthly_pet_hargreaves_mm": round(mean_pet_harg, 2),
        "correlation_spi3_vs_spei3_pm": round(r_spi_spei_pm, 4),
        "correlation_spei3_harg_vs_spei3_pm": round(r_harg_spei_pm, 4),
        "severe_drought_years_fao56_pm": sorted([int(y) for y in severe_spei3_pm]),
        "glo_calibration_parameters": glo_params_by_month
    }

    with open(OUT_COMPARISON_JSON, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"\n[OK] Saved FAO-56 SPEI-3 Comparative Audit JSON to: {OUT_COMPARISON_JSON}")


if __name__ == "__main__":
    run_fao56_spei_pipeline()
