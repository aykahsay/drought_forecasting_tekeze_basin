"""
Climate Data Source Registry & Ingestion Orchestrator (§2, §3)
===============================================================
Central orchestrator managing multi-source ingestion:
  - Tracks frequency per source (daily, monthly, composite, event-based)
  - Tracks status: last_available_date, last_ingested_date, ingestion_status
  - Coordinates dual storage: NetCDF/Zarr object storage + relational PostGIS/SQLite
"""
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from loguru import logger

from agriminds.climate.sources.base import ClimateDataSource, IngestionResult
from agriminds.climate.sources.era5t import ERA5TSource
from agriminds.climate.sources.noaa import (
    NOAACFSv2SeasonalSource,
    NOAACPCRainfallSource,
    NOAAONISource,
    NOAAVegetationHealthSource,
)
from agriminds.climate.sources.realtime import SatelliteQuickLookIngestor
from agriminds.climate.sources.satellite import SatelliteSource
from agriminds.climate.sources.station import StationObservationSource
from agriminds.climate.sources.teleconnections import ENSOLoader, IODLoader
from agriminds.db.models import (
    DataSourceRecord,
    IngestionRunRecord,
    get_session,
)


class SourceRegistryOrchestrator:
    """
    Manages all registered climate data sources in AI-DREWS.
    """

    def __init__(self):
        self._sources: dict[str, ClimateDataSource] = {
            "ERA5T": ERA5TSource(),
            "GPM_IMERG_EARLY": SatelliteQuickLookIngestor(),
            "ENSO_NOAA": ENSOLoader(),
            "IOD_DMI": IODLoader(),
            "CHIRPS_MODIS": SatelliteSource(),
            "ETH_STATIONS": StationObservationSource(),
            "NOAA_CPC_RFE": NOAACPCRainfallSource(),
            "NOAA_CPC_ONI": NOAAONISource(),
            "NOAA_STAR_VHI": NOAAVegetationHealthSource(),
            "NOAA_CFSv2_OUTLOOK": NOAACFSv2SeasonalSource(),
        }

    def get_source(self, source_id: str) -> Optional[ClimateDataSource]:
        return self._sources.get(source_id)

    def list_sources(self) -> list[str]:
        return list(self._sources.keys())

    def get_all_source_statuses(self) -> list[dict[str, Any]]:
        """
        Return the health, frequency, and latest date status of all sources.
        As specified in §3:
          source, last_available_date, last_ingested_date, ingestion_status
        """
        db = get_session()
        statuses = []
        try:
            for s_id, source in self._sources.items():
                # Query last ingestion run from DB
                last_run = (
                    db.query(IngestionRunRecord)
                    .filter(IngestionRunRecord.source_id == s_id)
                    .order_by(IngestionRunRecord.started_at.desc())
                    .first()
                )

                try:
                    last_avail = source.get_latest_available_date()
                    avail_str = last_avail.isoformat() if last_avail else None
                except Exception:
                    avail_str = None

                status_info = {
                    "source": s_id,
                    "source_name": source.source_name,
                    "source_type": source.source_type,
                    "temporal_resolution": source.temporal_resolution,
                    "suggested_frequency": self._get_suggested_frequency(s_id),
                    "last_available_date": avail_str,
                    "last_ingested_date": last_run.target_date if last_run and last_run.target_date else (
                        last_run.started_at.strftime("%Y-%m-%d") if last_run else None
                    ),
                    "ingestion_status": last_run.status if last_run else "PENDING",
                    "records_stored": last_run.records_downloaded if last_run else 0,
                    "last_run_time": last_run.started_at.isoformat() if last_run else None,
                }
                statuses.append(status_info)
            return statuses
        finally:
            db.close()

    def run_ingestion(self, source_id: str, target_date: Optional[date] = None) -> IngestionResult:
        """Trigger ingestion for a specific source."""
        source = self.get_source(source_id)
        if not source:
            raise ValueError(f"Unknown data source: {source_id}")

        dt = target_date or (date.today() - timedelta(days=5 if source_id == "ERA5T" else 1))
        return source.ingest(target_date=dt)

    def _get_suggested_frequency(self, source_id: str) -> str:
        freq_map = {
            "ERA5T": "Daily ingestion (~5-day latency)",
            "GPM_IMERG_EARLY": "Sub-daily quick-look (~4-hour latency)",
            "ENSO_NOAA": "Monthly index update (elnino.xlsx baseline)",
            "IOD_DMI": "Monthly / weekly update",
            "CHIRPS_MODIS": "Daily precipitation / 16-day composite NDVI",
            "ETH_STATIONS": "Batch arrival whenever ground observations arrive",
            "NOAA_CPC_RFE": "Daily blended satellite-gauge estimate (~24h latency)",
            "NOAA_CPC_ONI": "Weekly & monthly SST anomaly live bridge",
            "NOAA_STAR_VHI": "Weekly 4-km vegetation & thermal stress composite",
            "NOAA_CFSv2_OUTLOOK": "Monthly sub-seasonal to seasonal ensemble outlook",
        }
        return freq_map.get(source_id, "Daily")


_registry = None


def get_source_registry() -> SourceRegistryOrchestrator:
    global _registry
    if _registry is None:
        _registry = SourceRegistryOrchestrator()
    return _registry
