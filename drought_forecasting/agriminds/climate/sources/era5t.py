"""
ERA5T Climate Data Source
=========================
Copernicus ERA5T near-real-time atmospheric reanalysis data.

ERA5T description (used consistently throughout AI-DREWS, per requirement §2):
    "Near-real-time atmospheric reanalysis data with approximately a 5-day latency."

Key facts:
  - ERA5T covers the period from 1 month ago to ~5 days ago.
  - After ~3 months, ERA5T data is replaced by finalized ERA5 (back-extension).
  - ERA5T is NOT real-time; it has a nominal ~5-day latency.
  - Data source: Copernicus Climate Data Store (CDS) API.
  - Spatial resolution: 0.25° × 0.25° (~28 km).
  - Temporal resolution: Hourly.
  - All timestamps stored in UTC.

Units (documented per requirement §18):
    total_precipitation                 : m    (metres per hour, accumulated)
    2m_temperature                     : K    (Kelvin)
    2m_dewpoint_temperature            : K    (Kelvin)
    surface_pressure                   : Pa   (Pascals)
    10m_u_component_of_wind            : m/s
    10m_v_component_of_wind            : m/s
    surface_solar_radiation_downwards  : J/m² (accumulated per hour)
    volumetric_soil_water_layer_1      : m³/m³
    volumetric_soil_water_layer_2      : m³/m³
    volumetric_soil_water_layer_3      : m³/m³
    volumetric_soil_water_layer_4      : m³/m³
"""
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from loguru import logger

from agriminds.climate.sources.base import ClimateDataSource, IngestionResult
from agriminds.climate.validation import ERA5TValidator
from agriminds.config import get_settings
from agriminds.db.models import (
    ERA5TIngestionLog,
    ERA5TObservation,
    IngestionStatus,
    get_session,
)

# ---------------------------------------------------------------------------
# Variable metadata (unit + short name) — add new variables here
# ---------------------------------------------------------------------------
ERA5T_VARIABLE_METADATA: dict[str, dict] = {
    "total_precipitation": {
        "unit": "m",
        "short": "tp",
        "description": "Total precipitation (accumulated per hour)",
    },
    "2m_temperature": {
        "unit": "K",
        "short": "t2m",
        "description": "Air temperature at 2 m above surface",
    },
    "2m_dewpoint_temperature": {
        "unit": "K",
        "short": "d2m",
        "description": "Dewpoint temperature at 2 m above surface",
    },
    "surface_pressure": {
        "unit": "Pa",
        "short": "sp",
        "description": "Pressure at the surface",
    },
    "10m_u_component_of_wind": {
        "unit": "m/s",
        "short": "u10",
        "description": "Eastward component of 10 m wind",
    },
    "10m_v_component_of_wind": {
        "unit": "m/s",
        "short": "v10",
        "description": "Northward component of 10 m wind",
    },
    "surface_solar_radiation_downwards": {
        "unit": "J/m²",
        "short": "ssrd",
        "description": "Downward solar radiation at surface (accumulated)",
    },
    "volumetric_soil_water_layer_1": {
        "unit": "m³/m³",
        "short": "swvl1",
        "description": "Volumetric soil water, 0–7 cm",
    },
    "volumetric_soil_water_layer_2": {
        "unit": "m³/m³",
        "short": "swvl2",
        "description": "Volumetric soil water, 7–28 cm",
    },
    "volumetric_soil_water_layer_3": {
        "unit": "m³/m³",
        "short": "swvl3",
        "description": "Volumetric soil water, 28–100 cm",
    },
    "volumetric_soil_water_layer_4": {
        "unit": "m³/m³",
        "short": "swvl4",
        "description": "Volumetric soil water, 100–289 cm",
    },
}


class ERA5TSource(ClimateDataSource):
    """
    ERA5T near-real-time atmospheric reanalysis data source.

    Connects to the Copernicus CDS API using secure environment variables:
        CDS_API_URL
        CDS_API_KEY

    Credentials are NEVER exposed in frontend code or committed to Git.
    """

    @property
    def source_name(self) -> str:
        return "ERA5T"

    @property
    def source_type(self) -> str:
        return "reanalysis"

    @property
    def temporal_resolution(self) -> str:
        return "hourly"

    @property
    def spatial_resolution_deg(self) -> float:
        return 0.25

    @property
    def description(self) -> str:
        return (
            "Near-real-time atmospheric reanalysis data with approximately "
            "a 5-day latency."
        )

    @property
    def latency_note(self) -> str:
        return (
            "ERA5T is a near-real-time atmospheric reanalysis product with "
            "approximately a 5-day latency. Recent ERA5T data may subsequently "
            "be replaced by finalized ERA5 data."
        )

    def is_available(self) -> bool:
        settings = get_settings()
        if not settings.cds_configured:
            logger.warning(
                "CDS API key not configured. "
                "Set CDS_API_KEY in .env to enable ERA5T ingestion."
            )
            return False
        try:
            import cdsapi  # noqa: F401
            return True
        except ImportError:
            logger.error("cdsapi package not installed.")
            return False

    def get_latest_available_date(self) -> Optional[date]:
        """
        ERA5T has a nominal ~5-day latency.
        Return today minus 5 days as a conservative latest-available estimate.
        When the API is reachable, query it directly.
        """
        return date.today() - timedelta(days=5)

    def _get_cds_client(self):
        """Build and return a CDS API client using environment credentials."""
        import cdsapi

        settings = get_settings()
        if not settings.cds_configured:
            raise RuntimeError(
                "CDS API key not configured. "
                "Set CDS_API_URL and CDS_API_KEY environment variables."
            )
        return cdsapi.Client(
            url=settings.cds_api_url,
            key=settings.cds_api_key,
            quiet=True,
        )

    def ingest(
        self,
        target_date: date,
        variables: Optional[list[str]] = None,
        bbox: Optional[list[float]] = None,
    ) -> IngestionResult:
        """
        Download, validate, and store ERA5T data for *target_date*.

        Idempotent: if data for this date is already stored, returns
        a SKIPPED result without re-downloading.

        Args:
            target_date: Date to ingest.
            variables:   List of ERA5T variable names (defaults to config list).
            bbox:        [North, West, South, East] in degrees (defaults to config).

        Returns:
            IngestionResult with status and record count.
        """
        settings = get_settings()
        variables = variables or settings.era5_variables
        bbox = bbox or settings.era5_bbox

        start_time = time.monotonic()
        db = get_session()

        # ── Idempotency check ──────────────────────────────────────────────
        existing = (
            db.query(ERA5TIngestionLog)
            .filter(
                ERA5TIngestionLog.target_date == target_date.isoformat(),
                ERA5TIngestionLog.status == IngestionStatus.COMPLETE,
            )
            .first()
        )
        if existing:
            logger.info(
                f"ERA5T data for {target_date} already ingested "
                f"({existing.records_stored} records). Skipping."
            )
            db.close()
            return IngestionResult(
                source_name=self.source_name,
                target_date=target_date,
                records_stored=existing.records_stored,
                success=True,
                duration_seconds=0.0,
            )

        # ── Create ingestion log entry ─────────────────────────────────────
        log_entry = ERA5TIngestionLog(
            target_date=target_date.isoformat(),
            variables_requested=json.dumps(variables),
            status=IngestionStatus.DOWNLOADING,
            retry_count=0,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        raw_file = None
        try:
            raw_file = self._download(target_date, variables, bbox, log_entry, db)
            log_entry.status = IngestionStatus.VALIDATING
            log_entry.raw_file_path = str(raw_file)
            db.commit()

            df = self._parse_netcdf(raw_file, variables)
            validator = ERA5TValidator()
            df = validator.validate(df)

            log_entry.status = IngestionStatus.STORING
            db.commit()

            records = self._store_observations(df, str(raw_file), db)

            duration = time.monotonic() - start_time
            log_entry.status = IngestionStatus.COMPLETE
            log_entry.records_stored = records
            log_entry.completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(
                f"ERA5T ingestion complete: {target_date} | "
                f"{records} records | {duration:.1f}s"
            )
            return IngestionResult(
                source_name=self.source_name,
                target_date=target_date,
                records_stored=records,
                success=True,
                raw_file_path=str(raw_file),
                duration_seconds=duration,
            )

        except Exception as exc:
            duration = time.monotonic() - start_time
            log_entry.status = IngestionStatus.FAILED
            log_entry.error_message = str(exc)
            log_entry.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error(f"ERA5T ingestion failed for {target_date}: {exc}")
            return IngestionResult(
                source_name=self.source_name,
                target_date=target_date,
                records_stored=0,
                success=False,
                error=str(exc),
                raw_file_path=str(raw_file) if raw_file else None,
                duration_seconds=duration,
            )
        finally:
            db.close()

    # ── Source-Specific Ingestion Pipeline Contract (§2) ─────────────────────
    def extract(self, target_date: date, **kwargs) -> Path:
        """Download or locate raw ERA5T NetCDF."""
        variables = kwargs.get("variables") or get_settings().era5_variables
        bbox = kwargs.get("bbox") or get_settings().era5_bbox
        return self._download(target_date, variables, bbox, None, None)

    def validate(self, raw_data: Any) -> pd.DataFrame:
        """Apply quality control without dropping audit records."""
        if isinstance(raw_data, (str, Path)):
            df = self._parse_netcdf(Path(raw_data), get_settings().era5_variables)
        elif isinstance(raw_data, pd.DataFrame):
            df = raw_data
        else:
            raise ValueError(f"Unsupported raw_data type: {type(raw_data)}")
        validator = ERA5TValidator()
        return validator.validate(df)

    def transform(self, validated_data: pd.DataFrame) -> pd.DataFrame:
        """Standardize clean schema and normalize canonical units."""
        return validated_data

    def load(self, clean_df: pd.DataFrame, target_date: date) -> int:
        """Persist standardized observations to the database."""
        db = get_session()
        try:
            return self._store_observations(clean_df, f"era5t_{target_date.isoformat()}.nc", db)
        finally:
            db.close()

    def log(
        self,
        run_id: str,
        status: str,
        records_stored: int,
        error: Optional[str] = None,
        target_date: Optional[date] = None,
    ):
        """Record the ingestion run in ingestion_runs."""
        from agriminds.db.models import IngestionRunRecord
        db = get_session()
        try:
            db.add(IngestionRunRecord(
                run_id=run_id,
                source_id="ERA5T",
                target_date=target_date.isoformat() if target_date else None,
                status=status,
                records_downloaded=records_stored,
                records_valid=records_stored,
                error_message=error,
            ))
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning(f"Failed to log ingestion run: {exc}")
        finally:
            db.close()

    def _download(
        self,
        target_date: date,
        variables: list[str],
        bbox: list[float],
        log_entry: ERA5TIngestionLog,
        db,
    ) -> Path:
        """Call the CDS API and save the NetCDF file."""
        settings = get_settings()
        raw_dir = settings.raw_data_dir
        filename = f"era5t_{target_date.isoformat()}.nc"
        output_path = raw_dir / filename

        if output_path.exists():
            logger.info(f"Raw file already exists: {output_path}. Re-using.")
            return output_path

        client = self._get_cds_client()
        logger.info(f"Downloading ERA5T for {target_date} …")

        request = {
            "product_type": "reanalysis",
            "dataset": "reanalysis-era5-single-levels",
            "variable": variables,
            "year": str(target_date.year),
            "month": f"{target_date.month:02d}",
            "day": f"{target_date.day:02d}",
            "time": [f"{h:02d}:00" for h in range(24)],
            "area": bbox,  # [North, West, South, East]
            "format": "netcdf",
        }

        client.retrieve("reanalysis-era5-single-levels", request, str(output_path))
        logger.info(f"Download complete: {output_path}")
        return output_path

    def _parse_netcdf(self, file_path: Path, variables: list[str]) -> pd.DataFrame:
        """
        Parse a NetCDF file into a long-format DataFrame.

        Returns columns:
            timestamp_utc, date, latitude, longitude, variable, value, unit
        """
        import netCDF4 as nc  # noqa: N813

        logger.info(f"Parsing NetCDF: {file_path}")
        rows = []

        with nc.Dataset(file_path, "r") as ds:
            time_var_name = "time" if "time" in ds.variables else ("valid_time" if "valid_time" in ds.variables else None)
            if not time_var_name:
                raise ValueError(f"No time or valid_time dimension found in NetCDF {file_path}")
            times_raw = ds.variables[time_var_name][:]
            time_units = getattr(ds.variables[time_var_name], "units", "seconds since 1970-01-01")
            times_dt = nc.num2date(times_raw, time_units)

            lats = ds.variables["latitude"][:]
            lons = ds.variables["longitude"][:]

            for var_name in variables:
                short = ERA5T_VARIABLE_METADATA.get(var_name, {}).get("short")
                nc_var_name = short or var_name

                if nc_var_name not in ds.variables:
                    logger.warning(
                        f"Variable '{nc_var_name}' not found in NetCDF file."
                    )
                    continue

                data = ds.variables[nc_var_name][:]  # shape: (time, lat, lon)
                unit = ERA5T_VARIABLE_METADATA.get(var_name, {}).get("unit", "unknown")

                if hasattr(data, "mask"):
                    data = np.ma.filled(data, fill_value=np.nan)

                for ti, t in enumerate(times_dt):
                    ts_utc = datetime(
                        t.year, t.month, t.day, t.hour, t.minute, t.second,
                        tzinfo=timezone.utc,
                    )
                    date_str = ts_utc.strftime("%Y-%m-%d")
                    for li, lat in enumerate(lats):
                        for lo, lon in enumerate(lons):
                            val = float(data[ti, li, lo])
                            rows.append(
                                {
                                    "timestamp_utc": ts_utc,
                                    "date": date_str,
                                    "latitude": float(lat),
                                    "longitude": float(lon),
                                    "variable": var_name,
                                    "value": val if not np.isnan(val) else None,
                                    "unit": unit,
                                }
                            )

        df = pd.DataFrame(rows)
        logger.info(f"Parsed {len(df)} rows from NetCDF.")
        return df

    def _store_observations(self, df: pd.DataFrame, source_file: str, db) -> int:
        """
        Upsert ERA5T observations.

        Duplicate rows (same timestamp × lat × lon × variable) are detected
        and skipped (idempotency).
        """
        stored = 0
        now_utc = datetime.now(timezone.utc)

        for _, row in df.iterrows():
            # Check for existing record
            existing = (
                db.query(ERA5TObservation)
                .filter(
                    ERA5TObservation.timestamp_utc == row["timestamp_utc"],
                    ERA5TObservation.latitude == row["latitude"],
                    ERA5TObservation.longitude == row["longitude"],
                    ERA5TObservation.variable == row["variable"],
                )
                .first()
            )
            if existing:
                continue  # Skip duplicate

            obs = ERA5TObservation(
                timestamp_utc=row["timestamp_utc"],
                date=row["date"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                variable=row["variable"],
                value=row.get("value"),
                unit=row.get("unit"),
                is_valid=row.get("is_valid", True),
                validation_note=row.get("validation_note"),
                ingested_at=now_utc,
                source_file=source_file,
            )
            db.add(obs)
            stored += 1

        db.commit()
        logger.info(f"Stored {stored} new ERA5T observations.")
        return stored

    def get_data(
        self,
        start_date: date,
        end_date: date,
        variables: Optional[list[str]] = None,
        location_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Retrieve stored ERA5T data as a long-format DataFrame."""
        db = get_session()
        try:
            q = db.query(ERA5TObservation).filter(
                ERA5TObservation.date >= start_date.isoformat(),
                ERA5TObservation.date <= end_date.isoformat(),
            )
            if variables:
                q = q.filter(ERA5TObservation.variable.in_(variables))

            rows = q.all()
            if not rows:
                return pd.DataFrame()

            return pd.DataFrame(
                [
                    {
                        "timestamp_utc": r.timestamp_utc,
                        "date": r.date,
                        "latitude": r.latitude,
                        "longitude": r.longitude,
                        "variable": r.variable,
                        "value": r.value,
                        "unit": r.unit,
                        "is_valid": r.is_valid,
                    }
                    for r in rows
                ]
            )
        finally:
            db.close()

    def get_status(self) -> dict:
        """ERA5T-specific status panel for the dashboard (requirement §13)."""
        db = get_session()
        try:
            latest_log = (
                db.query(ERA5TIngestionLog)
                .filter(ERA5TIngestionLog.status == IngestionStatus.COMPLETE)
                .order_by(ERA5TIngestionLog.target_date.desc())
                .first()
            )
        finally:
            db.close()

        settings = get_settings()
        return {
            "source": "Copernicus ERA5T",
            "description": self.description,
            "latency_note": self.latency_note,
            "status": "Near-real-time",
            "latency": "~5 days",
            "configured": settings.cds_configured,
            "available": self.is_available(),
            "latest_available_date": (
                self.get_latest_available_date().isoformat()
                if self.get_latest_available_date()
                else None
            ),
            "last_ingestion": (
                latest_log.completed_at.isoformat()
                if latest_log and latest_log.completed_at
                else None
            ),
            "last_ingested_date": (
                latest_log.target_date if latest_log else None
            ),
            "variables": list(ERA5T_VARIABLE_METADATA.keys()),
            "variable_metadata": ERA5T_VARIABLE_METADATA,
            "spatial_resolution": "0.25° × 0.25° (~28 km)",
            "temporal_resolution": "Hourly",
            "coordinate_system": "WGS84 / EPSG:4326",
            "bbox": settings.era5_bbox,
            "region": "Tigray, Ethiopia (initial — expandable)",
        }
