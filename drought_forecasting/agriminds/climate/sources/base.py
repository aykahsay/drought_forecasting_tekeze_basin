"""
Climate data source abstraction layer.

Architecture (requirement §16):

    ClimateDataSource  (abstract base)
        │
        ├── ERA5TSource         — near-real-time reanalysis (~5-day latency)
        ├── SatelliteRainfallSource
        ├── SoilMoistureSource
        ├── WeatherForecastSource
        ├── StationObservationSource
        └── SeasonalForecastSource

New sources can be added without touching the rest of AI-DREWS.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

import pandas as pd


@dataclass
class IngestionResult:
    """Returned by every source after an ingestion attempt."""
    source_name: str
    target_date: date
    records_stored: int
    success: bool
    error: Optional[str] = None
    raw_file_path: Optional[str] = None
    duration_seconds: Optional[float] = None


class ClimateDataSource(ABC):
    """
    Abstract base for all climate data sources.

    Implement this interface to add new data sources to AI-DREWS
    without modifying existing pipelines.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name for this data source."""
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """
        One of: observation | reanalysis | satellite | forecast | station.
        Used to correctly label data provenance in the dashboard.
        """
        ...

    @property
    @abstractmethod
    def temporal_resolution(self) -> str:
        """E.g. 'hourly', 'daily', 'monthly'."""
        ...

    @property
    @abstractmethod
    def spatial_resolution_deg(self) -> float:
        """Approximate grid spacing in degrees."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when credentials/connection are configured."""
        ...

    @abstractmethod
    def get_latest_available_date(self) -> Optional[date]:
        """
        Query the upstream source for the most recent available date.
        Returns None if the source cannot be reached.
        """
        ...

    # ── Source-Specific Ingestion Pipeline Contract (§2) ─────────────────────
    @abstractmethod
    def extract(self, target_date: date, **kwargs) -> Any:
        """Download or read raw data directly from the source without alteration."""
        ...

    @abstractmethod
    def validate(self, raw_data: Any) -> Any:
        """Apply DataQualityEngine checks without discarding raw audit records."""
        ...

    @abstractmethod
    def transform(self, validated_data: Any) -> pd.DataFrame:
        """Convert into standardized, unit-normalized clean schema."""
        ...

    @abstractmethod
    def load(self, clean_df: pd.DataFrame, target_date: date) -> int:
        """Load standardized records into the database."""
        ...

    @abstractmethod
    def log(
        self,
        run_id: str,
        status: str,
        records_stored: int,
        error: Optional[str] = None,
        target_date: Optional[date] = None,
    ):
        """Record the ingestion execution into ingestion_runs."""
        ...

    @abstractmethod
    def ingest(
        self,
        target_date: date,
        variables: Optional[list[str]] = None,
        bbox: Optional[list[float]] = None,
    ) -> IngestionResult:
        """
        Execute the full pipeline:
        extract() -> validate() -> transform() -> load() -> log()
        """
        ...

    @abstractmethod
    def get_data(
        self,
        start_date: date,
        end_date: date,
        variables: Optional[list[str]] = None,
        location_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Retrieve stored data as a DataFrame with columns:
            timestamp_utc, date, latitude, longitude, variable, value, unit
        """
        ...

    def get_status(self) -> dict[str, Any]:
        """
        Return a status dict suitable for the dashboard ERA5T panel.
        Subclasses may override to add source-specific fields.
        """
        try:
            latest = self.get_latest_available_date()
        except Exception as exc:
            latest = None
            error = str(exc)
        else:
            error = None

        return {
            "source_name": self.source_name,
            "source_type": self.source_type,
            "available": self.is_available(),
            "latest_available_date": latest.isoformat() if latest else None,
            "temporal_resolution": self.temporal_resolution,
            "spatial_resolution_deg": self.spatial_resolution_deg,
            "error": error,
        }
