-- ============================================================================
-- AI-DREWS: Ethiopian Climate & Drought Early Warning System
-- PostgreSQL + PostGIS Production Schema DDL
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Create Schemas
CREATE SCHEMA IF NOT EXISTS geography;
CREATE SCHEMA IF NOT EXISTS sources;
CREATE SCHEMA IF NOT EXISTS climate_raw;
CREATE SCHEMA IF NOT EXISTS climate_clean;
CREATE SCHEMA IF NOT EXISTS climate_features;
CREATE SCHEMA IF NOT EXISTS observations;
CREATE SCHEMA IF NOT EXISTS models;
CREATE SCHEMA IF NOT EXISTS system;

-- ============================================================================
-- 2. GEOGRAPHY SCHEMA
-- ============================================================================

CREATE TABLE IF NOT EXISTS geography.countries (
    country_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    iso3 VARCHAR(3) NOT NULL,
    geometry GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS geography.regions (
    region_id VARCHAR(50) PRIMARY KEY,
    country_id VARCHAR(10) REFERENCES geography.countries(country_id),
    name VARCHAR(100) NOT NULL,
    geometry GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS geography.zones (
    zone_id VARCHAR(50) PRIMARY KEY,
    region_id VARCHAR(50) REFERENCES geography.regions(region_id),
    name VARCHAR(100) NOT NULL,
    geometry GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agro-Ecological Climate Zones (AEZs) on top of administrative units
CREATE TABLE IF NOT EXISTS geography.climate_zones (
    climate_zone_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    local_name VARCHAR(100) NOT NULL,
    elevation_range VARCHAR(100) NOT NULL,
    annual_rainfall_mm VARCHAR(100) NOT NULL,
    temperature_range_c VARCHAR(100) NOT NULL,
    rainfall_regime VARCHAR(100),
    description TEXT,
    vulnerability_profile TEXT,
    geometry GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS geography.woredas (
    woreda_id VARCHAR(50) PRIMARY KEY,
    zone_id VARCHAR(50) REFERENCES geography.zones(zone_id),
    region_id VARCHAR(50) REFERENCES geography.regions(region_id),
    climate_zone_id VARCHAR(50) REFERENCES geography.climate_zones(climate_zone_id),
    rainfall_regime VARCHAR(100), -- Regime A (Bimodal Belg/Kiremt), Regime B (Monomodal), Regime C (Bimodal Gu/Deyr)
    name VARCHAR(100) NOT NULL,
    centroid_lat DOUBLE PRECISION NOT NULL,
    centroid_lon DOUBLE PRECISION NOT NULL,
    area_km2 DOUBLE PRECISION,
    elevation_mean_m DOUBLE PRECISION,
    vulnerability_index DOUBLE PRECISION,
    geometry GEOMETRY(MultiPolygon, 4326),
    bbox JSONB, -- {north, south, east, west}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS geography.kebeles (
    kebele_id VARCHAR(50) PRIMARY KEY,
    woreda_id VARCHAR(50) REFERENCES geography.woredas(woreda_id),
    name VARCHAR(100) NOT NULL,
    geometry GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_woredas_geom ON geography.woredas USING GIST(geometry);
CREATE INDEX IF NOT EXISTS ix_woredas_region ON geography.woredas(region_id);
CREATE INDEX IF NOT EXISTS ix_woredas_zone ON geography.woredas(zone_id);

-- ============================================================================
-- 3. SOURCES SCHEMA
-- ============================================================================

CREATE TABLE IF NOT EXISTS sources.data_sources (
    source_id VARCHAR(50) PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    description TEXT,
    url VARCHAR(500),
    data_type VARCHAR(50) NOT NULL, -- reanalysis, satellite, teleconnection, station
    temporal_resolution VARCHAR(50) NOT NULL, -- hourly, daily, monthly
    spatial_resolution_deg DOUBLE PRECISION,
    latency_note VARCHAR(255),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sources.ingestion_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(50) REFERENCES sources.data_sources(source_id),
    target_date DATE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL, -- RUNNING, SUCCESS, PARTIAL, FAILED, SKIPPED
    records_downloaded INTEGER DEFAULT 0,
    records_valid INTEGER DEFAULT 0,
    records_invalid INTEGER DEFAULT 0,
    error_message TEXT,
    raw_storage_uri VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_ingestion_runs_source_date ON sources.ingestion_runs(source_id, target_date);
CREATE INDEX IF NOT EXISTS ix_ingestion_runs_status ON sources.ingestion_runs(status);

-- ============================================================================
-- 4. CLIMATE CLEAN SCHEMA
-- ============================================================================

CREATE TABLE IF NOT EXISTS climate_clean.variables (
    variable_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    short_name VARCHAR(30) NOT NULL,
    source_variable_name VARCHAR(100),
    canonical_unit VARCHAR(30) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL -- precipitation, temperature, soil_moisture, atmosphere, ocean
);

CREATE TABLE IF NOT EXISTS climate_clean.observations (
    observation_id BIGSERIAL PRIMARY KEY,
    source_id VARCHAR(50) REFERENCES sources.data_sources(source_id),
    variable_id VARCHAR(50) REFERENCES climate_clean.variables(variable_id),
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    date DATE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    value DOUBLE PRECISION,
    unit VARCHAR(30) NOT NULL,
    quality_flag VARCHAR(20) NOT NULL DEFAULT 'GOOD', -- GOOD, SUSPECT, INVALID, MISSING
    quality_note TEXT,
    ingestion_run_id VARCHAR(64) REFERENCES sources.ingestion_runs(run_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_clean_obs_date_var ON climate_clean.observations(date, variable_id);
CREATE INDEX IF NOT EXISTS ix_clean_obs_latlon ON climate_clean.observations(latitude, longitude);
CREATE UNIQUE INDEX IF NOT EXISTS uq_clean_obs ON climate_clean.observations(source_id, variable_id, timestamp_utc, latitude, longitude);

CREATE TABLE IF NOT EXISTS climate_clean.ocean_atmosphere_indices (
    index_id BIGSERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    date DATE NOT NULL,
    index_name VARCHAR(50) NOT NULL, -- Nino3.4, IOD_DMI, Indian_Ocean_SST, Arabian_Sea_SST
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(30) DEFAULT '°C',
    phase VARCHAR(30), -- El Niño, La Niña, Neutral, Positive IOD, Negative IOD
    source_id VARCHAR(50) REFERENCES sources.data_sources(source_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_oai_name_date ON climate_clean.ocean_atmosphere_indices(index_name, date);

-- Historical ENSO Dataset (elnino.xlsx mirror — read-only reference)
CREATE TABLE IF NOT EXISTS climate_clean.historical_climate (
    year INTEGER PRIMARY KEY,
    nino34_djf DOUBLE PRECISION,
    nino34_mam DOUBLE PRECISION,
    nino34_jja DOUBLE PRECISION,
    nino34_son DOUBLE PRECISION,
    nino34_annual DOUBLE PRECISION,
    p_djf_m DOUBLE PRECISION,
    p_mam_m DOUBLE PRECISION,
    p_jja_m DOUBLE PRECISION,
    p_son_m DOUBLE PRECISION,
    p_c_mm_mon DOUBLE PRECISION,
    t_djf_k DOUBLE PRECISION,
    t_mam_k DOUBLE PRECISION,
    t_jja_k DOUBLE PRECISION,
    t_son_k DOUBLE PRECISION,
    t_annual_c DOUBLE PRECISION,
    sc_pdsi DOUBLE PRECISION,
    source VARCHAR(100) DEFAULT 'elnino.xlsx',
    loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 5. CLIMATE FEATURES SCHEMA
-- ============================================================================

CREATE TABLE IF NOT EXISTS climate_features.woreda_climate (
    feature_id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    woreda_id VARCHAR(50) REFERENCES geography.woredas(woreda_id),
    
    -- Climate State (Precipitation)
    rainfall_7d DOUBLE PRECISION,
    rainfall_30d DOUBLE PRECISION,
    rainfall_60d DOUBLE PRECISION,
    rainfall_90d DOUBLE PRECISION,
    rainfall_180d DOUBLE PRECISION,
    rainfall_anomaly_30d DOUBLE PRECISION,
    rainfall_anomaly_90d DOUBLE PRECISION,
    rainfall_percentile DOUBLE PRECISION,
    
    -- Climate State (Temperature)
    temperature_mean DOUBLE PRECISION,
    temperature_max DOUBLE PRECISION,
    temperature_min DOUBLE PRECISION,
    temperature_anomaly DOUBLE PRECISION,
    temperature_percentile DOUBLE PRECISION,
    
    -- Climate State (Soil Moisture)
    soil_moisture_mean DOUBLE PRECISION,
    soil_moisture_percentile DOUBLE PRECISION,
    soil_moisture_layer1 DOUBLE PRECISION,
    soil_moisture_layer2 DOUBLE PRECISION,
    soil_moisture_anomaly DOUBLE PRECISION,
    
    -- Drought Indices (Derived)
    spi_1 DOUBLE PRECISION,
    spi_3 DOUBLE PRECISION,
    spi_6 DOUBLE PRECISION,
    spi_12 DOUBLE PRECISION,
    spei_1 DOUBLE PRECISION,
    spei_3 DOUBLE PRECISION,
    spei_6 DOUBLE PRECISION,
    spei_12 DOUBLE PRECISION,
    sc_pdsi DOUBLE PRECISION,
    
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_woreda_climate_date UNIQUE(date, woreda_id)
);

CREATE INDEX IF NOT EXISTS ix_woreda_clim_date ON climate_features.woreda_climate(date);
CREATE INDEX IF NOT EXISTS ix_woreda_clim_woreda ON climate_features.woreda_climate(woreda_id);

CREATE TABLE IF NOT EXISTS climate_features.teleconnections (
    teleconnection_id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    
    -- Current Index
    nino34 DOUBLE PRECISION,
    iod DOUBLE PRECISION,
    indian_ocean_sst DOUBLE PRECISION,
    arabian_sea_sst DOUBLE PRECISION,
    red_sea_sst DOUBLE PRECISION,
    atlantic_sst DOUBLE PRECISION,
    
    -- Lagged features (predictive early warning)
    nino34_lag_1 DOUBLE PRECISION,
    nino34_lag_2 DOUBLE PRECISION,
    nino34_lag_3 DOUBLE PRECISION,
    nino34_lag_6 DOUBLE PRECISION,
    nino34_lag_9 DOUBLE PRECISION,
    nino34_lag_12 DOUBLE PRECISION,
    
    iod_lag_1 DOUBLE PRECISION,
    iod_lag_2 DOUBLE PRECISION,
    iod_lag_3 DOUBLE PRECISION,
    iod_lag_6 DOUBLE PRECISION,
    iod_lag_9 DOUBLE PRECISION,
    iod_lag_12 DOUBLE PRECISION,
    
    -- Atmospheric dynamics
    u850 DOUBLE PRECISION,
    v850 DOUBLE PRECISION,
    humidity_850 DOUBLE PRECISION,
    surface_pressure DOUBLE PRECISION,
    geopotential_500hpa DOUBLE PRECISION,
    moisture_flux DOUBLE PRECISION,
    
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS climate_features.model_dataset (
    dataset_id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    woreda_id VARCHAR(50) REFERENCES geography.woredas(woreda_id),
    
    -- Teleconnection predictors
    nino34 DOUBLE PRECISION,
    iod DOUBLE PRECISION,
    nino34_lag_1 DOUBLE PRECISION,
    nino34_lag_3 DOUBLE PRECISION,
    iod_lag_1 DOUBLE PRECISION,
    iod_lag_3 DOUBLE PRECISION,
    
    -- Local climate predictors
    rainfall_30d DOUBLE PRECISION,
    rainfall_90d DOUBLE PRECISION,
    rainfall_anomaly DOUBLE PRECISION,
    temperature_anomaly DOUBLE PRECISION,
    soil_moisture_percentile DOUBLE PRECISION,
    spi_3 DOUBLE PRECISION,
    spi_6 DOUBLE PRECISION,
    spei_3 DOUBLE PRECISION,
    spei_6 DOUBLE PRECISION,
    sc_pdsi DOUBLE PRECISION,
    
    -- Multi-Horizon Targets
    target_drought_1m DOUBLE PRECISION, -- Probability or binary flag 1 month ahead
    target_drought_2m DOUBLE PRECISION, -- 2 months ahead
    target_drought_3m DOUBLE PRECISION, -- 3 months ahead
    future_spi_3 DOUBLE PRECISION,      -- Continuous target (regression)
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_model_dataset_date_woreda UNIQUE(date, woreda_id)
);

-- ============================================================================
-- 6. OBSERVATIONS SCHEMA (Ground Stations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS observations.station_metadata (
    station_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    region_id VARCHAR(50) REFERENCES geography.regions(region_id),
    woreda_id VARCHAR(50) REFERENCES geography.woredas(woreda_id),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    elevation_m DOUBLE PRECISION,
    station_type VARCHAR(50), -- synoptic, agrometeorological, rainfall
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS observations.station_observations (
    record_id BIGSERIAL PRIMARY KEY,
    station_id VARCHAR(50) REFERENCES observations.station_metadata(station_id),
    date DATE NOT NULL,
    precipitation_mm DOUBLE PRECISION,
    temp_max_c DOUBLE PRECISION,
    temp_min_c DOUBLE PRECISION,
    temp_mean_c DOUBLE PRECISION,
    quality_flag VARCHAR(20) DEFAULT 'GOOD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_station_obs_date ON observations.station_observations(station_id, date);

-- ============================================================================
-- 7. MODELS SCHEMA
-- ============================================================================

CREATE TABLE IF NOT EXISTS models.model_registry (
    model_id VARCHAR(64) PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    version VARCHAR(30) NOT NULL,
    algorithm VARCHAR(50) NOT NULL, -- Persistence, LogisticRegression, RandomForest, XGBoost, LSTM
    features_tier VARCHAR(50) NOT NULL, -- Model_A_Local, Model_B_Local_ENSO, Model_C_Local_ENSO_IOD, Model_D_Full
    training_start DATE,
    training_end DATE,
    target_variable VARCHAR(50) NOT NULL,
    metrics JSONB, -- {roc_auc, pr_auc, f1, brier_score, mae, rmse}
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, RETIRED, CANDIDATE
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS models.predictions (
    prediction_id BIGSERIAL PRIMARY KEY,
    model_id VARCHAR(64) REFERENCES models.model_registry(model_id),
    forecast_date DATE NOT NULL, -- Date model ran
    target_date DATE NOT NULL,   -- Target horizon date
    horizon_months INTEGER NOT NULL, -- 1, 2, or 3
    woreda_id VARCHAR(50) REFERENCES geography.woredas(woreda_id),
    
    probability_drought DOUBLE PRECISION NOT NULL,
    predicted_spi DOUBLE PRECISION,
    risk_level VARCHAR(30) NOT NULL, -- Normal, Moderate, Severe, Extreme
    confidence_score DOUBLE PRECISION,
    
    contributing_factors JSONB, -- [{feature: "spi_3", weight: 0.35, direction: "deteriorating"}, ...]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_pred_date_woreda ON models.predictions(forecast_date, woreda_id);
CREATE INDEX IF NOT EXISTS ix_pred_risk ON models.predictions(risk_level);
