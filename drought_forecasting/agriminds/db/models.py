"""
SQLAlchemy database models for AI-DREWS / AgriMinds.

Two separate data layers:
  1. Historical ENSO / El Niño dataset  (from elnino.xlsx — never overwritten)
  2. ERA5T near-real-time atmospheric reanalysis data

Additional layers are extensible via ClimateDataSource interface.
"""
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from agriminds.config import get_settings


# ────────────────────────────────────────────────────────────────────────────
# Base
# ────────────────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ────────────────────────────────────────────────────────────────────────────
# 1. Historical ENSO / El Niño Dataset
#    Source: elnino.xlsx  —  NEVER overwritten
# ────────────────────────────────────────────────────────────────────────────
class ENSORecord(Base):
    """
    One row per year from elnino.xlsx.
    This table mirrors the historical climate/ENSO reference dataset.
    It is populated once and treated as read-only ground truth.
    """

    __tablename__ = "enso_historical"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False, unique=True, index=True)

    # Niño 3.4 index by season
    nino34_djf = Column(Float, nullable=True)  # Dec–Jan–Feb
    nino34_mam = Column(Float, nullable=True)  # Mar–Apr–May
    nino34_jja = Column(Float, nullable=True)  # Jun–Jul–Aug
    nino34_son = Column(Float, nullable=True)  # Sep–Oct–Nov
    nino34_annual = Column(Float, nullable=True)

    # Precipitation (metres per season)
    p_djf_m = Column(Float, nullable=True)  # Dec–Jan–Feb  [m]
    p_mam_m = Column(Float, nullable=True)  # Mar–Apr–May  [m]
    p_jja_m = Column(Float, nullable=True)  # Jun–Jul–Aug  [m]
    p_son_m = Column(Float, nullable=True)  # Sep–Oct–Nov  [m]
    p_c_mm_mon = Column(Float, nullable=True)  # Annual mean  [mm/month]

    # Temperature (Kelvin by season; annual in °C)
    t_djf_k = Column(Float, nullable=True)   # [K]
    t_mam_k = Column(Float, nullable=True)   # [K]
    t_jja_k = Column(Float, nullable=True)   # [K]
    t_son_k = Column(Float, nullable=True)   # [K]
    t_annual_c = Column(Float, nullable=True)  # [°C]

    # Drought indicator (historical target variable)
    sc_pdsi = Column(Float, nullable=True)  # Self-calibrated Palmer Drought Severity Index

    # Metadata
    source_file = Column(String(255), default="elnino.xlsx")
    loaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ENSORecord year={self.year} nino34_annual={self.nino34_annual}>"


# ────────────────────────────────────────────────────────────────────────────
# 2. ERA5T Raw Observations
#    Source: Copernicus CDS API
#    ERA5T is near-real-time atmospheric reanalysis with ~5-day latency
# ────────────────────────────────────────────────────────────────────────────
class ERA5TObservation(Base):
    """
    Long/narrow format: one row per (timestamp, variable, lat, lon).

    This structure keeps ERA5T separate from the existing Excel dataset.
    It is NOT merged into elnino.xlsx columns.

    Units per variable (as downloaded from CDS):
        total_precipitation              : m  (metres per hour)
        2m_temperature                  : K  (Kelvin)
        2m_dewpoint_temperature         : K  (Kelvin)
        surface_pressure                : Pa (Pascals)
        10m_u_component_of_wind         : m/s
        10m_v_component_of_wind         : m/s
        surface_solar_radiation_downwards: J/m²
        volumetric_soil_water_layer_1   : m³/m³
        volumetric_soil_water_layer_2   : m³/m³
        volumetric_soil_water_layer_3   : m³/m³
        volumetric_soil_water_layer_4   : m³/m³
    """

    __tablename__ = "era5t_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Temporal  (all UTC)
    timestamp_utc = Column(DateTime, nullable=False, index=True)
    date = Column(String(10), nullable=False)   # YYYY-MM-DD  (indexed for fast queries)

    # Spatial
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Variable
    variable = Column(String(100), nullable=False)
    value = Column(Float, nullable=True)
    unit = Column(String(30), nullable=True)

    # Quality flags
    is_valid = Column(Boolean, default=True)
    validation_note = Column(Text, nullable=True)

    # Ingestion metadata
    ingested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    source_file = Column(String(500), nullable=True)  # Path to raw NetCDF file

    __table_args__ = (
        UniqueConstraint(
            "timestamp_utc", "latitude", "longitude", "variable",
            name="uq_era5t_obs",
        ),
        Index("ix_era5t_date_var", "date", "variable"),
        Index("ix_era5t_latlon", "latitude", "longitude"),
    )

    def __repr__(self):
        return (
            f"<ERA5T {self.date} {self.variable}={self.value} "
            f"@({self.latitude},{self.longitude})>"
        )


# ────────────────────────────────────────────────────────────────────────────
# 3. ERA5T Ingestion Log
# ────────────────────────────────────────────────────────────────────────────
class IngestionStatus(PyEnum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    VALIDATING = "validating"
    STORING = "storing"
    COMPLETE = "complete"
    FAILED = "failed"
    SKIPPED = "skipped"  # Already ingested (idempotency)


class ERA5TIngestionLog(Base):
    """
    Tracks every ingestion attempt.
    Enables idempotency, retry, and health monitoring.
    """

    __tablename__ = "era5t_ingestion_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    variables_requested = Column(Text, nullable=True)              # JSON list
    status = Column(Enum(IngestionStatus), default=IngestionStatus.PENDING)
    records_stored = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    raw_file_path = Column(String(500), nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<IngestionLog {self.target_date} status={self.status}>"


# ────────────────────────────────────────────────────────────────────────────
# 4. Derived Climate Features
# ────────────────────────────────────────────────────────────────────────────
class ClimateFeature(Base):
    """
    Engineered features derived from ERA5T observations and/or ENSO data.

    IMPORTANT: This is a derived/processed product — NOT an observation.
    Never present these as raw ERA5T measurements.
    """

    __tablename__ = "climate_features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)
    location_id = Column(String(100), nullable=False, index=True)  # Woreda/grid cell
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Precipitation features [mm]
    rainfall_7d = Column(Float, nullable=True)
    rainfall_30d = Column(Float, nullable=True)
    rainfall_60d = Column(Float, nullable=True)
    rainfall_90d = Column(Float, nullable=True)
    rainfall_180d = Column(Float, nullable=True)
    rainfall_anomaly = Column(Float, nullable=True)    # vs climatological mean
    rainfall_percentile = Column(Float, nullable=True) # 0–100

    # Temperature features [°C]
    temperature_mean = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    temperature_min = Column(Float, nullable=True)
    temperature_anomaly = Column(Float, nullable=True)
    temperature_percentile = Column(Float, nullable=True)

    # Soil moisture (volumetric, m³/m³)
    soil_moisture_layer1 = Column(Float, nullable=True)
    soil_moisture_layer2 = Column(Float, nullable=True)
    soil_moisture_layer3 = Column(Float, nullable=True)
    soil_moisture_layer4 = Column(Float, nullable=True)
    soil_moisture_anomaly = Column(Float, nullable=True)
    soil_moisture_percentile = Column(Float, nullable=True)

    # Drought indices (derived products)
    spi_1 = Column(Float, nullable=True)
    spi_3 = Column(Float, nullable=True)
    spi_6 = Column(Float, nullable=True)
    spi_12 = Column(Float, nullable=True)
    spei_1 = Column(Float, nullable=True)
    spei_3 = Column(Float, nullable=True)
    spei_6 = Column(Float, nullable=True)
    spei_12 = Column(Float, nullable=True)
    sc_pdsi = Column(Float, nullable=True)  # From historical dataset where available

    # ENSO features (from elnino.xlsx — historical reference)
    nino34 = Column(Float, nullable=True)
    enso_phase = Column(String(20), nullable=True)  # El Niño / La Niña / Neutral

    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    data_sources = Column(Text, nullable=True)  # JSON list of contributing sources

    __table_args__ = (
        UniqueConstraint("date", "location_id", name="uq_climate_feature"),
    )


# ────────────────────────────────────────────────────────────────────────────
# 5. Drought Risk Predictions
# ────────────────────────────────────────────────────────────────────────────
class DroughtRiskPrediction(Base):
    """
    AI/ML model outputs.

    IMPORTANT SCIENTIFIC REQUIREMENT:
    These are MODEL PREDICTIONS, not observed climate measurements.
    They must NEVER be presented as observations or reanalysis data.
    """

    __tablename__ = "drought_risk_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_date = Column(String(10), nullable=False)    # Date prediction was made
    target_date = Column(String(10), nullable=False)      # Drought risk horizon
    location_id = Column(String(100), nullable=False)

    # Model output
    drought_probability = Column(Float, nullable=True)    # 0.0 – 1.0
    risk_level = Column(String(20), nullable=True)        # Normal/Moderate/Severe/Extreme
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)

    # Drought classification thresholds (DOCUMENTED — requirement §11)
    # Normal      : Sc-PDSI > -1.0
    # Moderate    : -2.0 < Sc-PDSI ≤ -1.0
    # Severe      : -3.0 < Sc-PDSI ≤ -2.0
    # Extreme     : Sc-PDSI ≤ -3.0
    classification_scheme = Column(String(100), default="SC-PDSI-Palmer")

    predicted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_drought_risk_date_loc", "forecast_date", "location_id"),
    )


# ────────────────────────────────────────────────────────────────────────────
# 6. Geography Models (Ethiopia -> Region -> Zone -> Woreda)
# ────────────────────────────────────────────────────────────────────────────
class CountryRecord(Base):
    __tablename__ = "geo_countries"
    country_id = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    iso3 = Column(String(3), nullable=False)


class RegionRecord(Base):
    __tablename__ = "geo_regions"
    region_id = Column(String(50), primary_key=True)
    country_id = Column(String(10), default="ETH")
    name = Column(String(100), nullable=False)
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)


class ClimateZoneRecord(Base):
    """
    Agro-Ecological Climate Zones (AEZs) of Ethiopia:
      - Bereha (Hot Arid Lowlands, < 500-800m)
      - Kolla (Warm Semi-Arid Lowlands, 500-1500m)
      - Weyna Dega (Temperate Mid-Highlands, 1500-2300m)
      - Dega (Cool Highlands, 2300-3200m)
      - Wurch / Kur (Afro-Alpine, > 3200m)
    """
    __tablename__ = "geo_climate_zones"
    climate_zone_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    local_name = Column(String(100), nullable=False)
    elevation_range = Column(String(100), nullable=False)
    annual_rainfall_mm = Column(String(100), nullable=False)
    temperature_range_c = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    vulnerability_profile = Column(Text, nullable=True)


class ZoneRecord(Base):
    __tablename__ = "geo_zones"
    zone_id = Column(String(50), primary_key=True)
    region_id = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)


class WoredaRecord(Base):
    __tablename__ = "geo_woredas"
    woreda_id = Column(String(50), primary_key=True)
    zone_id = Column(String(50), nullable=False)
    region_id = Column(String(50), nullable=False)
    climate_zone_id = Column(String(50), nullable=True, index=True)  # Climate-based zone on top of woreda
    rainfall_regime = Column(String(50), nullable=True)             # Regime A, B, or C
    name = Column(String(100), nullable=False)
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    area_km2 = Column(Float, nullable=True)
    elevation_mean_m = Column(Float, nullable=True)
    vulnerability_index = Column(Float, nullable=True)
    bbox_json = Column(Text, nullable=True)



# ────────────────────────────────────────────────────────────────────────────
# 7. Data Source & Ingestion Registry
# ────────────────────────────────────────────────────────────────────────────
class DataSourceRecord(Base):
    __tablename__ = "data_sources"
    source_id = Column(String(50), primary_key=True)
    source_name = Column(String(100), nullable=False)
    provider = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    data_type = Column(String(50), nullable=False)
    temporal_resolution = Column(String(50), nullable=False)
    spatial_resolution_deg = Column(Float, nullable=True)
    latency_note = Column(String(255), nullable=True)
    active = Column(Boolean, default=True)


class IngestionRunRecord(Base):
    __tablename__ = "ingestion_runs"
    run_id = Column(String(64), primary_key=True)
    source_id = Column(String(50), nullable=False, index=True)
    target_date = Column(String(10), nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)
    records_downloaded = Column(Integer, default=0)
    records_valid = Column(Integer, default=0)
    records_invalid = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    raw_storage_uri = Column(String(500), nullable=True)


# ────────────────────────────────────────────────────────────────────────────
# 8. Variable Registry & Ocean-Atmosphere Indices
# ────────────────────────────────────────────────────────────────────────────
class ClimateVariableRecord(Base):
    __tablename__ = "climate_variables"
    variable_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(30), nullable=False)
    source_variable_name = Column(String(100), nullable=True)
    canonical_unit = Column(String(30), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)


class OceanAtmosphereIndexRecord(Base):
    __tablename__ = "ocean_atmosphere_indices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False, index=True)
    index_name = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(30), default="°C")
    phase = Column(String(30), nullable=True)
    source_id = Column(String(50), default="NOAA_CPC")


# ────────────────────────────────────────────────────────────────────────────
# 9. Clean Standardized Observations (Long format)
# ────────────────────────────────────────────────────────────────────────────
class ClimateObservationRecord(Base):
    __tablename__ = "climate_observations_clean"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), nullable=False, index=True)
    variable_id = Column(String(50), nullable=False, index=True)
    timestamp_utc = Column(DateTime, nullable=False)
    date = Column(String(10), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    value = Column(Float, nullable=True)
    unit = Column(String(30), nullable=False)
    quality_flag = Column(String(20), default="GOOD")
    quality_note = Column(Text, nullable=True)
    ingestion_run_id = Column(String(64), nullable=True)


# ────────────────────────────────────────────────────────────────────────────
# 10. Model Registry
# ────────────────────────────────────────────────────────────────────────────
class ModelRegistryRecord(Base):
    __tablename__ = "model_registry"
    model_id = Column(String(64), primary_key=True)
    model_name = Column(String(100), nullable=False)
    version = Column(String(30), nullable=False)
    algorithm = Column(String(50), nullable=False)
    features_tier = Column(String(50), nullable=False)
    training_start = Column(String(10), nullable=True)
    training_end = Column(String(10), nullable=True)
    target_variable = Column(String(50), default="sc_pdsi")
    metrics_json = Column(Text, nullable=True)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))



# ────────────────────────────────────────────────────────────────────────────
# Database engine and session factory
# ────────────────────────────────────────────────────────────────────────────
def create_db_engine(database_url: Optional[str] = None):
    settings = get_settings()
    url = database_url or settings.database_url
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, echo=False)


def init_db(engine=None):
    """Create all tables. Safe to call multiple times (idempotent)."""
    if engine is None:
        engine = create_db_engine()
    Base.metadata.create_all(bind=engine)
    return engine


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_db_engine()
        init_db(_engine)
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal()


def get_db():
    """FastAPI dependency that provides a DB session."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
