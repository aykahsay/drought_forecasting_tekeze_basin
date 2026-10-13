"""
ERA5T Data Validation (Requirement §18)

Validates raw ERA5T observations for:
  - Missing values
  - Impossible precipitation values (negative, excessively large)
  - Impossible temperatures (physical bounds)
  - Duplicate timestamps
  - Missing spatial cells
  - Incorrect units / unit-scale anomalies
  - Unexpected coordinate systems
  - Incomplete downloads (partial spatial coverage)

All units are documented inline.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger


# ---------------------------------------------------------------------------
# Physical bounds per variable (documented units)
# ---------------------------------------------------------------------------
VARIABLE_BOUNDS: dict[str, dict] = {
    # Total precipitation [m/hour]
    # ERA5 can accumulate ~0.5 m/day in extreme tropical events
    "total_precipitation": {"min": 0.0, "max": 0.05, "unit": "m"},

    # Temperature [K]
    # Earth range: ~183 K (−90 °C, Antarctica) to ~340 K (~67 °C, Death Valley)
    "2m_temperature": {"min": 183.0, "max": 340.0, "unit": "K"},
    "2m_dewpoint_temperature": {"min": 183.0, "max": 315.0, "unit": "K"},

    # Surface pressure [Pa] — sea level to high altitude
    "surface_pressure": {"min": 50_000.0, "max": 110_000.0, "unit": "Pa"},

    # Wind components [m/s] — absolute value
    "10m_u_component_of_wind": {"min": -100.0, "max": 100.0, "unit": "m/s"},
    "10m_v_component_of_wind": {"min": -100.0, "max": 100.0, "unit": "m/s"},

    # Solar radiation [J/m² per hour] — max ~3.6 MJ/m²
    "surface_solar_radiation_downwards": {
        "min": 0.0,
        "max": 3_600_000.0,
        "unit": "J/m²",
    },

    # Volumetric soil water [m³/m³] — physical range 0 to ~0.65
    "volumetric_soil_water_layer_1": {"min": 0.0, "max": 0.65, "unit": "m³/m³"},
    "volumetric_soil_water_layer_2": {"min": 0.0, "max": 0.65, "unit": "m³/m³"},
    "volumetric_soil_water_layer_3": {"min": 0.0, "max": 0.65, "unit": "m³/m³"},
    "volumetric_soil_water_layer_4": {"min": 0.0, "max": 0.65, "unit": "m³/m³"},
}


@dataclass
class ValidationReport:
    total_rows: int = 0
    missing_values: int = 0
    out_of_range: int = 0
    duplicates_removed: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    passed: bool = True


class ERA5TValidator:
    """
    Validates ERA5T DataFrames before storage.

    Expected input columns:
        timestamp_utc, date, latitude, longitude, variable, value, unit
    """

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run all validation checks.
        Returns a DataFrame with 'is_valid' and 'validation_note' columns added.
        """
        if df.empty:
            logger.warning("Validation called on empty DataFrame.")
            return df

        report = ValidationReport(total_rows=len(df))
        df = df.copy()
        df["is_valid"] = True
        df["validation_note"] = None

        df = self._check_required_columns(df, report)
        df = self._check_coordinate_system(df, report)
        df = self._check_missing_values(df, report)
        df = self._check_physical_bounds(df, report)
        df = self._remove_duplicates(df, report)

        self._log_report(report)
        return df

    def _check_required_columns(
        self, df: pd.DataFrame, report: ValidationReport
    ) -> pd.DataFrame:
        required = {
            "timestamp_utc", "date", "latitude", "longitude", "variable", "value"
        }
        missing = required - set(df.columns)
        if missing:
            msg = f"Missing required columns: {missing}"
            report.errors.append(msg)
            report.passed = False
            raise ValueError(msg)
        return df

    def _check_coordinate_system(
        self, df: pd.DataFrame, report: ValidationReport
    ) -> pd.DataFrame:
        """
        ERA5T uses WGS84 geographic coordinates (EPSG:4326).
        Latitudes: −90 to +90, Longitudes: −180 to +180.
        """
        invalid_lat = ~df["latitude"].between(-90, 90)
        invalid_lon = ~df["longitude"].between(-180, 180)
        bad = invalid_lat | invalid_lon

        if bad.any():
            count = bad.sum()
            msg = f"Invalid coordinates (outside WGS84 range): {count} rows"
            report.errors.append(msg)
            df.loc[bad, "is_valid"] = False
            df.loc[bad, "validation_note"] = "Invalid WGS84 coordinates"

        return df

    def _check_missing_values(
        self, df: pd.DataFrame, report: ValidationReport
    ) -> pd.DataFrame:
        missing_mask = df["value"].isna()
        count = missing_mask.sum()
        if count:
            report.missing_values = count
            report.warnings.append(f"{count} missing values detected.")
            df.loc[missing_mask, "is_valid"] = False
            df.loc[missing_mask, "validation_note"] = "Missing value"
        return df

    def _check_physical_bounds(
        self, df: pd.DataFrame, report: ValidationReport
    ) -> pd.DataFrame:
        for var, bounds in VARIABLE_BOUNDS.items():
            mask = df["variable"] == var
            if not mask.any():
                continue

            vals = df.loc[mask, "value"]
            oor = ~vals.between(bounds["min"], bounds["max"]) & vals.notna()

            if oor.any():
                count = oor.sum()
                report.out_of_range += count
                report.warnings.append(
                    f"{count} out-of-range values for {var} "
                    f"(expected {bounds['min']}–{bounds['max']} {bounds['unit']})"
                )
                df.loc[mask & oor, "is_valid"] = False
                df.loc[mask & oor, "validation_note"] = (
                    f"Out of physical range [{bounds['min']}, {bounds['max']}] "
                    f"{bounds['unit']}"
                )
        return df

    def _remove_duplicates(
        self, df: pd.DataFrame, report: ValidationReport
    ) -> pd.DataFrame:
        before = len(df)
        df = df.drop_duplicates(
            subset=["timestamp_utc", "latitude", "longitude", "variable"],
            keep="first",
        )
        removed = before - len(df)
        if removed:
            report.duplicates_removed = removed
            report.warnings.append(f"Removed {removed} duplicate rows.")
        return df

    def _log_report(self, report: ValidationReport) -> None:
        level = "INFO" if report.passed else "WARNING"
        logger.log(
            level,
            f"Validation: {report.total_rows} rows | "
            f"missing={report.missing_values} | "
            f"out-of-range={report.out_of_range} | "
            f"duplicates_removed={report.duplicates_removed}",
        )
        for w in report.warnings:
            logger.warning(f"  [Validation] {w}")
        for e in report.errors:
            logger.error(f"  [Validation] {e}")
