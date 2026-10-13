"""
Historical ENSO Dataset Integration
=====================================
Loads elnino.xlsx into the ENSORecord table.

IMPORTANT:
  - elnino.xlsx is NEVER overwritten.
  - It is treated as the historical climate/ENSO reference dataset.
  - This loader is idempotent: re-running does not duplicate records.
  - The Excel structure is preserved exactly in the database schema.
"""
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from agriminds.config import get_settings
from agriminds.db.models import ENSORecord, get_session


# ---------------------------------------------------------------------------
# Column mapping: Excel header → ENSORecord attribute
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    "Year": "year",
    "Nino3.4-DJF": "nino34_djf",
    "Nino3.4-MAM": "nino34_mam",
    "Nino3.4-JJA": "nino34_jja",
    "Nino3.4-SON": "nino34_son",
    "Nino3.4-annual": "nino34_annual",
    "P-DJF (m)": "p_djf_m",
    "P-MAM (m)": "p_mam_m",
    "P-JJA (m)": "p_jja_m",
    "P-SON (m)": "p_son_m",
    "P-c (mm/mon)": "p_c_mm_mon",
    "T-DJF (K)": "t_djf_k",
    "T-MAM (K)": "t_mam_k",
    "T-JJA (K)": "t_jja_k",
    "T-SON (K)": "t_son_k",
    "T-annual (0C)": "t_annual_c",
    "Sc-PDSI": "sc_pdsi",
}


def load_elnino_dataset(
    file_path: Optional[Path] = None,
    force_reload: bool = False,
) -> int:
    """
    Load elnino.xlsx into the database as ENSORecord rows.

    Args:
        file_path:    Path to elnino.xlsx. Defaults to settings.elnino_dataset_path.
        force_reload: If True, update existing records even if already loaded.

    Returns:
        Number of records inserted or updated.
    """
    settings = get_settings()
    path = file_path or settings.elnino_dataset_path

    if not Path(path).exists():
        logger.error(f"El Niño dataset not found: {path}")
        return 0

    logger.info(f"Loading historical ENSO dataset from: {path}")
    df = _read_excel(path)

    db = get_session()
    count = 0
    try:
        for _, row in df.iterrows():
            year = int(row["year"])
            existing = (
                db.query(ENSORecord).filter(ENSORecord.year == year).first()
            )

            if existing and not force_reload:
                continue  # Idempotent: skip already-loaded years

            record_data = {k: _safe_float(row.get(k)) for k in COLUMN_MAP.values() if k != "year"}
            record_data["year"] = year
            record_data["source_file"] = str(path)

            if existing:
                for attr, val in record_data.items():
                    setattr(existing, attr, val)
            else:
                db.add(ENSORecord(**record_data))
            count += 1

        db.commit()
        logger.info(f"ENSO dataset: {count} records loaded/updated.")
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to load ENSO dataset: {exc}")
        raise
    finally:
        db.close()

    return count


def _read_excel(path: Path) -> pd.DataFrame:
    """
    Read elnino.xlsx and clean the data.
    Handles Excel formula values (e.g. '=AVERAGE(B2:E2)') gracefully.
    """
    df = pd.read_excel(path, engine="openpyxl")

    # Rename columns using our mapping (only rename columns that exist)
    rename = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename)

    # Replace Excel formula strings with NaN
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: None if isinstance(x, str) and x.strip().startswith("=") else x
        )

    # Keep only rows with valid year values
    df = df[df["year"].notna() & df["year"].apply(lambda x: str(x).isdigit() if isinstance(x, (int, float)) else False)]
    df["year"] = df["year"].astype(int)

    return df


def _safe_float(val) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def get_enso_dataframe() -> pd.DataFrame:
    """
    Return all ENSO records as a pandas DataFrame.
    Useful for feature engineering and model training.
    """
    db = get_session()
    try:
        records = db.query(ENSORecord).order_by(ENSORecord.year).all()
        if not records:
            return pd.DataFrame()

        return pd.DataFrame(
            [
                {
                    "year": r.year,
                    "nino34_djf": r.nino34_djf,
                    "nino34_mam": r.nino34_mam,
                    "nino34_jja": r.nino34_jja,
                    "nino34_son": r.nino34_son,
                    "nino34_annual": r.nino34_annual,
                    "p_djf_m": r.p_djf_m,
                    "p_mam_m": r.p_mam_m,
                    "p_jja_m": r.p_jja_m,
                    "p_son_m": r.p_son_m,
                    "p_c_mm_mon": r.p_c_mm_mon,
                    "t_djf_k": r.t_djf_k,
                    "t_mam_k": r.t_mam_k,
                    "t_jja_k": r.t_jja_k,
                    "t_son_k": r.t_son_k,
                    "t_annual_c": r.t_annual_c,
                    "sc_pdsi": r.sc_pdsi,
                }
                for r in records
            ]
        )
    finally:
        db.close()


def classify_enso_phase(nino34_value: Optional[float]) -> str:
    """
    Classify ENSO phase from Niño 3.4 index.

    Thresholds (documented):
        El Niño  : Niño 3.4 ≥ +0.5 °C for ≥5 consecutive months
        La Niña  : Niño 3.4 ≤ −0.5 °C for ≥5 consecutive months
        Neutral  : −0.5 < Niño 3.4 < +0.5 °C

    For single-value classification (used in feature tables):
        El Niño  : nino34 ≥ 0.5
        La Niña  : nino34 ≤ −0.5
        Neutral  : otherwise
    """
    if nino34_value is None or pd.isna(nino34_value):
        return "Unknown"
    if nino34_value >= 0.5:
        return "El Niño"
    if nino34_value <= -0.5:
        return "La Niña"
    return "Neutral"
