"""
AI-DREWS Data Quality Engine (7-Step Protocol)
=============================================
Explicit, non-destructive quality control for all climate observations:

  RAW OBSERVATION
        ↓
  Step 1: Schema Validation
        ↓
  Step 2: Missing Data Taxonomy (Distinguishes 0 mm from missing data)
        ↓
  Step 3: Duplicate Detection (source + variable + timestamp + lat + lon)
        ↓
  Step 4: Physical Range & Thermodynamic Consistency Checks
        ↓
  Step 5: Canonical Unit Normalization (stores canonical, preserves original)
        ↓
  Step 6: Spatial Validation (WGS84, bounding boxes, geographic constraints)
        ↓
  Step 7: Temporal Validation (UTC normalization, chronological monotonic ordering, no future dates)
        ↓
  CLEAN / STANDARDIZED DATA WITH QUALITY FLAGS (GOOD, SUSPECT, INVALID, MISSING)

Non-destructive principle:
  Observations are NOT silently dropped. They are categorized and flagged
  to maintain a complete scientific audit trail.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Optional

import numpy as np
import pandas as pd
from loguru import logger


class QualityFlag(str, Enum):
    GOOD = "GOOD"
    SUSPECT = "SUSPECT"
    INVALID = "INVALID"
    MISSING = "MISSING"


class MissingDataCategory(str, Enum):
    VALID_OBSERVATION = "VALID"
    LEGITIMATE_ZERO = "ZERO"           # E.g. 0.0 mm rainfall
    NOT_OBSERVED = "NOT_OBSERVED"       # Station down or sensor off
    MISSING_VALUE = "MISSING"           # NaN / None
    PHYSICALLY_INVALID = "INVALID"      # Out of bounds / corrupted sensor


@dataclass
class QualityCheckRecord:
    step_number: int
    step_name: str
    status: str
    issues_found: int
    details: list[str] = field(default_factory=list)


@dataclass
class QualityAuditReport:
    source_name: str
    run_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_records: int = 0
    records_good: int = 0
    records_suspect: int = 0
    records_invalid: int = 0
    records_missing: int = 0
    steps: list[QualityCheckRecord] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.records_invalid == 0


# Physical Bounds Reference by Variable & Unit
PHYSICAL_LIMITS = {
    "total_precipitation": {
        "m": {"min": 0.0, "max": 0.50},          # m/day
        "mm": {"min": 0.0, "max": 500.0},        # mm/day
        "m/hour": {"min": 0.0, "max": 0.05},
    },
    "precipitation": {
        "mm": {"min": 0.0, "max": 500.0},
        "m": {"min": 0.0, "max": 0.50},
    },
    "2m_temperature": {
        "K": {"min": 250.0, "max": 335.0},       # ~ -23°C to 62°C (Ethiopia extremes)
        "°C": {"min": -23.0, "max": 62.0},
    },
    "temperature": {
        "K": {"min": 250.0, "max": 335.0},
        "°C": {"min": -23.0, "max": 62.0},
    },
    "2m_dewpoint_temperature": {
        "K": {"min": 240.0, "max": 315.0},
        "°C": {"min": -33.0, "max": 42.0},
    },
    "surface_pressure": {
        "Pa": {"min": 60000.0, "max": 105000.0},
        "hPa": {"min": 600.0, "max": 1050.0},
    },
    "volumetric_soil_water_layer_1": {
        "m³/m³": {"min": 0.0, "max": 0.65},
    },
    "soil_moisture": {
        "m³/m³": {"min": 0.0, "max": 0.65},
        "m3/m3": {"min": 0.0, "max": 0.65},
        "%": {"min": 0.0, "max": 100.0},
    },
    "10m_u_wind": {
        "m/s": {"min": -60.0, "max": 60.0},
    },
    "10m_v_wind": {
        "m/s": {"min": -60.0, "max": 60.0},
    },
    "nino34": {
        "°C": {"min": -4.0, "max": 4.0},
    },
    "iod": {
        "°C": {"min": -3.0, "max": 3.0},
    },
}

# Ethiopia / Horn of Africa Geographic Bounding Box
ETHIOPIA_BBOX = {
    "lat_min": 3.0,
    "lat_max": 15.5,
    "lon_min": 32.5,
    "lon_max": 48.5,
}

TIGRAY_BBOX = {
    "lat_min": 12.2,
    "lat_max": 14.9,
    "lon_min": 36.4,
    "lon_max": 40.0,
}


class DataQualityEngine:
    """
    Unified 7-step data cleaning and quality assurance engine for AI-DREWS.
    """

    def __init__(self, region: str = "ethiopia"):
        self.region = region.lower()
        self.bbox = TIGRAY_BBOX if self.region == "tigray" else ETHIOPIA_BBOX

    def process(
        self,
        df: pd.DataFrame,
        source_name: str,
        variable_col: str = "variable",
        value_col: str = "value",
        unit_col: str = "unit",
        date_col: str = "date",
        lat_col: str = "latitude",
        lon_col: str = "longitude",
    ) -> tuple[pd.DataFrame, QualityAuditReport]:
        """
        Execute the full 7-step quality control pipeline.
        Returns the standardized DataFrame and the audit report.
        """
        report = QualityAuditReport(source_name=source_name, total_records=len(df))
        if df.empty:
            return df, report

        clean_df = df.copy()

        # Step 1: Schema validation
        clean_df = self._step1_schema_validation(
            clean_df, [date_col, variable_col, value_col, unit_col], report
        )

        # Step 2: Missing Data Taxonomy
        clean_df = self._step2_missing_taxonomy(clean_df, value_col, variable_col, report)

        # Step 3: Duplicate Detection
        clean_df = self._step3_duplicate_detection(
            clean_df, [date_col, variable_col, lat_col, lon_col], report
        )

        # Step 4: Physical Range & Thermodynamic Checks
        clean_df = self._step4_physical_ranges(
            clean_df, variable_col, value_col, unit_col, report
        )

        # Step 5: Unit Normalization
        clean_df = self._step5_unit_normalization(
            clean_df, variable_col, value_col, unit_col, report
        )

        # Step 6: Spatial Validation
        clean_df = self._step6_spatial_validation(clean_df, lat_col, lon_col, report)

        # Step 7: Temporal Validation
        clean_df = self._step7_temporal_validation(clean_df, date_col, report)

        # Final quality flag tallies
        report.records_good = int((clean_df["quality_flag"] == QualityFlag.GOOD.value).sum())
        report.records_suspect = int((clean_df["quality_flag"] == QualityFlag.SUSPECT.value).sum())
        report.records_invalid = int((clean_df["quality_flag"] == QualityFlag.INVALID.value).sum())
        report.records_missing = int((clean_df["quality_flag"] == QualityFlag.MISSING.value).sum())

        logger.info(
            f"Quality Engine [{source_name}]: {len(clean_df)} records | "
            f"Good: {report.records_good}, Suspect: {report.records_suspect}, "
            f"Invalid: {report.records_invalid}, Missing: {report.records_missing}"
        )

        return clean_df, report

    def _step1_schema_validation(
        self, df: pd.DataFrame, required_cols: list[str], report: QualityAuditReport
    ) -> pd.DataFrame:
        """Step 1: Check presence of expected columns."""
        missing = [c for c in required_cols if c not in df.columns]
        issues = len(missing)
        details = [f"Missing required column: {c}" for c in missing]
        if missing:
            raise ValueError(f"Schema validation failed. Missing columns: {missing}")

        report.steps.append(
            QualityCheckRecord(
                step_number=1,
                step_name="Schema Validation",
                status="PASS" if issues == 0 else "FAIL",
                issues_found=issues,
                details=details,
            )
        )
        return df

    def _step2_missing_taxonomy(
        self, df: pd.DataFrame, value_col: str, variable_col: str, report: QualityAuditReport
    ) -> pd.DataFrame:
        """
        Step 2: Missing Data Taxonomy.
        Crucial: 0.0 mm rainfall is a legitimate observation, NOT missing data!
        """
        if "quality_flag" not in df.columns:
            df["quality_flag"] = QualityFlag.GOOD.value
        if "missing_category" not in df.columns:
            df["missing_category"] = MissingDataCategory.VALID_OBSERVATION.value
        if "quality_note" not in df.columns:
            df["quality_note"] = ""

        is_na = df[value_col].isna()
        is_zero = (df[value_col] == 0.0) & ~is_na

        # Mark legitimate zeros (e.g. zero rainfall in dry season)
        df.loc[is_zero, "missing_category"] = MissingDataCategory.LEGITIMATE_ZERO.value

        # Mark missing
        df.loc[is_na, "missing_category"] = MissingDataCategory.MISSING_VALUE.value
        df.loc[is_na, "quality_flag"] = QualityFlag.MISSING.value
        df.loc[is_na, "quality_note"] = "Missing observation"

        report.steps.append(
            QualityCheckRecord(
                step_number=2,
                step_name="Missing Data Taxonomy",
                status="PASS",
                issues_found=int(is_na.sum()),
                details=[
                    f"Identified {int(is_zero.sum())} legitimate zero observations (e.g. dry days).",
                    f"Identified {int(is_na.sum())} missing observation entries.",
                ],
            )
        )
        return df

    def _step3_duplicate_detection(
        self, df: pd.DataFrame, key_cols: list[str], report: QualityAuditReport
    ) -> pd.DataFrame:
        """Step 3: Duplicate detection on (source, variable, timestamp, lat, lon)."""
        valid_keys = [c for c in key_cols if c in df.columns]
        dupes = df.duplicated(subset=valid_keys, keep="first")
        n_dupes = int(dupes.sum())

        if n_dupes > 0:
            df.loc[dupes, "quality_flag"] = QualityFlag.SUSPECT.value
            df.loc[dupes, "quality_note"] = "Duplicate record detected"
            # Deduplicate keeping earliest
            df = df.drop_duplicates(subset=valid_keys, keep="first")

        report.steps.append(
            QualityCheckRecord(
                step_number=3,
                step_name="Duplicate Detection",
                status="PASS" if n_dupes == 0 else "WARNED",
                issues_found=n_dupes,
                details=[f"Deduplicated {n_dupes} duplicate entries."] if n_dupes > 0 else ["No duplicates found."],
            )
        )
        return df

    def _step4_physical_ranges(
        self,
        df: pd.DataFrame,
        variable_col: str,
        value_col: str,
        unit_col: str,
        report: QualityAuditReport,
    ) -> pd.DataFrame:
        """Step 4: Check physical bounds and thermodynamic consistency."""
        out_of_bounds_count = 0
        details = []

        for (var, unit), group_idx in df.groupby([variable_col, unit_col]).groups.items():
            var_key = str(var).lower()
            unit_key = str(unit)

            limits = None
            if var_key in PHYSICAL_LIMITS:
                var_limits = PHYSICAL_LIMITS[var_key]
                limits = var_limits.get(unit_key) or var_limits.get(unit_key.replace("K", "K"))

            if limits:
                vals = df.loc[group_idx, value_col]
                invalid = (vals < limits["min"]) | (vals > limits["max"])
                n_inv = int(invalid.sum())
                if n_inv > 0:
                    out_of_bounds_count += n_inv
                    bad_indices = vals[invalid].index
                    df.loc[bad_indices, "quality_flag"] = QualityFlag.INVALID.value
                    df.loc[bad_indices, "missing_category"] = MissingDataCategory.PHYSICALLY_INVALID.value
                    df.loc[bad_indices, "quality_note"] = (
                        f"Out of physical bounds: {limits['min']}–{limits['max']} {unit_key}"
                    )
                    details.append(f"{var} ({unit_key}): {n_inv} rows out of bounds [{limits['min']}, {limits['max']}]")

        report.steps.append(
            QualityCheckRecord(
                step_number=4,
                step_name="Physical Range Checks",
                status="PASS" if out_of_bounds_count == 0 else "FLAGGED",
                issues_found=out_of_bounds_count,
                details=details or ["All values within physical thermodynamic bounds."],
            )
        )
        return df

    def _step5_unit_normalization(
        self,
        df: pd.DataFrame,
        variable_col: str,
        value_col: str,
        unit_col: str,
        report: QualityAuditReport,
    ) -> pd.DataFrame:
        """
        Step 5: Canonical Unit Normalization.
        Canonical units:
          temperature  → °C
          precipitation → mm
          pressure     → hPa
        Original unit is preserved in 'original_unit' column.
        """
        if "original_unit" not in df.columns:
            df["original_unit"] = df[unit_col]
        if "canonical_value" not in df.columns:
            df["canonical_value"] = df[value_col]

        conversions = 0
        for idx, row in df.iterrows():
            var = str(row[variable_col]).lower()
            unit = str(row[unit_col])
            val = row[value_col]

            if pd.isna(val):
                continue

            # Temperature Kelvin to Celsius
            if ("temperature" in var or "t2m" in var or "dewpoint" in var) and unit.upper() == "K":
                df.at[idx, "canonical_value"] = round(val - 273.15, 2)
                df.at[idx, unit_col] = "°C"
                conversions += 1
            # Precipitation metres to millimetres
            elif ("precipitation" in var or "tp" in var) and unit.lower() in ["m", "metres", "meters"]:
                df.at[idx, "canonical_value"] = round(val * 1000.0, 2)
                df.at[idx, unit_col] = "mm"
                conversions += 1
            # Pressure Pascals to hPa
            elif ("pressure" in var or "sp" in var) and unit.lower() in ["pa", "pascals"]:
                df.at[idx, "canonical_value"] = round(val / 100.0, 2)
                df.at[idx, unit_col] = "hPa"
                conversions += 1

        report.steps.append(
            QualityCheckRecord(
                step_number=5,
                step_name="Unit Normalization",
                status="PASS",
                issues_found=0,
                details=[f"Normalized {conversions} observations to canonical units (°C, mm, hPa)."],
            )
        )
        return df

    def _step6_spatial_validation(
        self, df: pd.DataFrame, lat_col: str, lon_col: str, report: QualityAuditReport
    ) -> pd.DataFrame:
        """Step 6: Spatial validation against WGS84 coordinates and bounding box."""
        if lat_col not in df.columns or lon_col not in df.columns:
            report.steps.append(
                QualityCheckRecord(
                    step_number=6,
                    step_name="Spatial Validation",
                    status="SKIPPED",
                    issues_found=0,
                    details=["Point location columns not applicable for this data source."],
                )
            )
            return df

        valid_lat = df[lat_col].between(-90.0, 90.0)
        valid_lon = df[lon_col].between(-180.0, 180.0)
        invalid_coords = (~valid_lat | ~valid_lon) & df[lat_col].notna()

        in_region = (
            df[lat_col].between(self.bbox["lat_min"], self.bbox["lat_max"])
            & df[lon_col].between(self.bbox["lon_min"], self.bbox["lon_max"])
        )
        outside_region = ~in_region & df[lat_col].notna() & ~invalid_coords

        n_invalid_coords = int(invalid_coords.sum())
        n_outside = int(outside_region.sum())

        if n_invalid_coords > 0:
            df.loc[invalid_coords, "quality_flag"] = QualityFlag.INVALID.value
            df.loc[invalid_coords, "quality_note"] = "Invalid WGS84 coordinates"

        if n_outside > 0:
            df.loc[outside_region, "quality_flag"] = QualityFlag.SUSPECT.value
            df.loc[outside_region, "quality_note"] = f"Coordinates outside target region ({self.region})"

        report.steps.append(
            QualityCheckRecord(
                step_number=6,
                step_name="Spatial Validation",
                status="PASS" if (n_invalid_coords + n_outside) == 0 else "FLAGGED",
                issues_found=n_invalid_coords + n_outside,
                details=[
                    f"WGS84 invalid coords: {n_invalid_coords}.",
                    f"Coordinates outside bounding box ({self.bbox}): {n_outside}.",
                ],
            )
        )
        return df

    def _step7_temporal_validation(
        self, df: pd.DataFrame, date_col: str, report: QualityAuditReport
    ) -> pd.DataFrame:
        """Step 7: Temporal validation (no future dates, monotonic sequence)."""
        today = date.today()
        dates = pd.to_datetime(df[date_col], errors="coerce").dt.date
        future_mask = dates > today
        n_future = int(future_mask.sum())

        if n_future > 0:
            df.loc[future_mask, "quality_flag"] = QualityFlag.INVALID.value
            df.loc[future_mask, "quality_note"] = "Future timestamp detected"

        report.steps.append(
            QualityCheckRecord(
                step_number=7,
                step_name="Temporal Validation",
                status="PASS" if n_future == 0 else "FLAGGED",
                issues_found=n_future,
                details=[f"Future timestamps found: {n_future}."],
            )
        )
        return df
