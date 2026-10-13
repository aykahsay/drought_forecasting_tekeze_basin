"""
Database Seeding Script for AI-DREWS
=====================================
Populates reference tables:
  1. Geography (Countries, Regions, Zones, Woredas of Tigray)
  2. Data Source Registry
  3. Climate Variable Registry
  4. Ocean-Atmosphere Teleconnection Indices (ENSO Niño 3.4, IOD)
  5. Model Registry Baseline Definitions
"""
import json
from datetime import date, datetime, timezone
from loguru import logger
from sqlalchemy.orm import Session

from agriminds.db.models import (
    CountryRecord,
    RegionRecord,
    ZoneRecord,
    ClimateZoneRecord,
    WoredaRecord,
    DataSourceRecord,
    ClimateVariableRecord,
    OceanAtmosphereIndexRecord,
    ModelRegistryRecord,
    get_session,
    init_db,
)
from agriminds.spatial.woredas import (
    CLIMATE_ZONES,
    ETHIOPIA_REGIONS,
    ETHIOPIA_ZONES,
    ETHIOPIA_WOREDAS,
)


DATA_SOURCES_SEED = [
    {
        "source_id": "ERA5T",
        "source_name": "ERA5T Near-Real-Time Reanalysis",
        "provider": "ECMWF / Copernicus Climate Change Service (C3S)",
        "description": "Near-real-time atmospheric reanalysis data with ~5-day latency for climate monitoring.",
        "data_type": "reanalysis",
        "temporal_resolution": "daily",
        "spatial_resolution_deg": 0.25,
        "latency_note": "5-day latency",
        "active": True,
    },
    {
        "source_id": "ENSO_NOAA",
        "source_name": "Niño 3.4 Index (NOAA / CPC)",
        "provider": "NOAA Climate Prediction Center",
        "description": "Monthly and seasonal sea surface temperature anomalies in the Niño 3.4 region (5°N–5°S, 170°W–120°W).",
        "data_type": "teleconnection",
        "temporal_resolution": "monthly",
        "spatial_resolution_deg": None,
        "latency_note": "Updated monthly",
        "active": True,
    },
    {
        "source_id": "IOD_DMI",
        "source_name": "Indian Ocean Dipole (DMI)",
        "provider": "Bureau of Meteorology (BoM) / NOAA",
        "description": "Dipole Mode Index representing SST gradient between western and eastern tropical Indian Ocean.",
        "data_type": "teleconnection",
        "temporal_resolution": "monthly",
        "spatial_resolution_deg": None,
        "latency_note": "Updated weekly/monthly",
        "active": True,
    },
    {
        "source_id": "CHIRPS",
        "source_name": "CHIRPS Satellite Rainfall",
        "provider": "Climate Hazards Center (UCSB)",
        "description": "Climate Hazards Group InfraRed Precipitation with Station data (0.05° resolution).",
        "data_type": "satellite",
        "temporal_resolution": "daily",
        "spatial_resolution_deg": 0.05,
        "latency_note": "1-2 day latency for preliminary",
        "active": True,
    },
    {
        "source_id": "MODIS_NDVI",
        "source_name": "MODIS / VIIRS Vegetation Health",
        "provider": "NASA LP DAAC",
        "description": "Normalized Difference Vegetation Index (NDVI) and Vegetation Health Index (VHI) 16-day composites.",
        "data_type": "satellite",
        "temporal_resolution": "16-day composite",
        "spatial_resolution_deg": 0.0025,
        "latency_note": "Composite interval ~16 days",
        "active": True,
    },
    {
        "source_id": "ETH_STATIONS",
        "source_name": "Ethiopian Meteorological Institute Ground Stations",
        "provider": "Ethiopian Meteorological Institute (EMI)",
        "description": "Surface weather observation stations across Tigray (Mekelle, Adwa, Axum, Shire, Alamata, Hawzen).",
        "data_type": "station",
        "temporal_resolution": "daily",
        "spatial_resolution_deg": None,
        "latency_note": "Batch arrival",
        "active": True,
    },
    {
        "source_id": "NOAA_CPC_RFE",
        "source_name": "NOAA CPC Africa Rainfall Estimation (RFE 2.0)",
        "provider": "NOAA Climate Prediction Center & USAID FEWS NET",
        "description": "Operational daily 0.1° satellite-gauge blended rainfall estimate for Africa and the Horn of Africa.",
        "data_type": "satellite_gauge_blend",
        "temporal_resolution": "daily",
        "spatial_resolution_deg": 0.10,
        "latency_note": "~24-hour latency",
        "active": True,
    },
    {
        "source_id": "NOAA_CPC_ONI",
        "source_name": "NOAA CPC Oceanic Niño Index & Niño 3.4 Live Bridge",
        "provider": "NOAA Climate Prediction Center",
        "description": "Weekly and monthly equatorial Pacific SST anomalies bridging historical elnino.xlsx to current conditions.",
        "data_type": "teleconnection",
        "temporal_resolution": "weekly_monthly",
        "spatial_resolution_deg": None,
        "latency_note": "Weekly / Monthly updates",
        "active": True,
    },
    {
        "source_id": "NOAA_STAR_VHI",
        "source_name": "NOAA STAR Vegetation Health Index (VHI/VCI/TCI)",
        "provider": "NOAA Center for Satellite Applications and Research",
        "description": "High-resolution 4 km AVHRR/VIIRS vegetation health and thermal condition index for agricultural drought tracking.",
        "data_type": "satellite_vegetation_thermal",
        "temporal_resolution": "weekly",
        "spatial_resolution_deg": 0.04,
        "latency_note": "Weekly composite",
        "active": True,
    },
    {
        "source_id": "NOAA_CFSv2_OUTLOOK",
        "source_name": "NOAA CFSv2 Seasonal Dynamical Ensemble Outlook",
        "provider": "NOAA NCEP / Climate Prediction Center",
        "description": "Coupled ocean-atmosphere dynamical ensemble seasonal precipitation and temperature outlook for 1–3 month horizons.",
        "data_type": "seasonal_dynamical_forecast",
        "temporal_resolution": "monthly_ensemble",
        "spatial_resolution_deg": 0.50,
        "latency_note": "Monthly update",
        "active": True,
    },
]

CLIMATE_VARIABLES_SEED = [
    {
        "variable_id": "total_precipitation",
        "name": "Total Precipitation",
        "short_name": "tp",
        "source_variable_name": "total_precipitation",
        "canonical_unit": "mm",
        "description": "Accumulated liquid and frozen water comprising rain and snow falling to the Earth surface.",
        "category": "precipitation",
    },
    {
        "variable_id": "2m_temperature",
        "name": "2m Air Temperature",
        "short_name": "t2m",
        "source_variable_name": "2m_temperature",
        "canonical_unit": "°C",
        "description": "Temperature of air at 2 metres above the surface.",
        "category": "temperature",
    },
    {
        "variable_id": "2m_dewpoint_temperature",
        "name": "2m Dewpoint Temperature",
        "short_name": "d2m",
        "source_variable_name": "2m_dewpoint_temperature",
        "canonical_unit": "°C",
        "description": "Temperature to which air must be cooled to become saturated with water vapour.",
        "category": "temperature",
    },
    {
        "variable_id": "surface_pressure",
        "name": "Surface Pressure",
        "short_name": "sp",
        "source_variable_name": "surface_pressure",
        "canonical_unit": "hPa",
        "description": "Pressure of the atmosphere at the Earth surface.",
        "category": "atmosphere",
    },
    {
        "variable_id": "volumetric_soil_water_layer_1",
        "name": "Volumetric Soil Water (0-7cm)",
        "short_name": "swvl1",
        "source_variable_name": "volumetric_soil_water_layer_1",
        "canonical_unit": "m³/m³",
        "description": "Volume of water in topsoil layer 1 (0–7 cm depth).",
        "category": "soil_moisture",
    },
    {
        "variable_id": "10m_u_wind",
        "name": "10m U-Component of Wind",
        "short_name": "u10",
        "source_variable_name": "10m_u_component_of_wind",
        "canonical_unit": "m/s",
        "description": "Eastward component of horizontal wind at 10 m.",
        "category": "atmosphere",
    },
    {
        "variable_id": "10m_v_wind",
        "name": "10m V-Component of Wind",
        "short_name": "v10",
        "source_variable_name": "10m_v_component_of_wind",
        "canonical_unit": "m/s",
        "description": "Northward component of horizontal wind at 10 m.",
        "category": "atmosphere",
    },
    {
        "variable_id": "nino34_index",
        "name": "Niño 3.4 SST Anomaly",
        "short_name": "nino34",
        "source_variable_name": "nino34",
        "canonical_unit": "°C",
        "description": "Sea surface temperature anomaly in east-central equatorial Pacific.",
        "category": "ocean",
    },
    {
        "variable_id": "iod_dmi_index",
        "name": "Dipole Mode Index (IOD)",
        "short_name": "iod",
        "source_variable_name": "dmi",
        "canonical_unit": "°C",
        "description": "Indian Ocean Dipole index (Western vs Eastern tropical Indian Ocean SST anomaly gradient).",
        "category": "ocean",
    },
]

SAMPLE_OCEAN_INDICES = [
    {"date": "2025-11-01", "index_name": "Nino3.4", "value": 0.82, "unit": "°C", "phase": "El Niño"},
    {"date": "2025-12-01", "index_name": "Nino3.4", "value": 0.95, "unit": "°C", "phase": "El Niño"},
    {"date": "2026-01-01", "index_name": "Nino3.4", "value": 0.74, "unit": "°C", "phase": "El Niño"},
    {"date": "2026-02-01", "index_name": "Nino3.4", "value": 0.41, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-03-01", "index_name": "Nino3.4", "value": 0.15, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-04-01", "index_name": "Nino3.4", "value": -0.22, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-05-01", "index_name": "Nino3.4", "value": -0.48, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-06-01", "index_name": "Nino3.4", "value": -0.65, "unit": "°C", "phase": "La Niña"},
    {"date": "2026-07-01", "index_name": "Nino3.4", "value": -0.81, "unit": "°C", "phase": "La Niña"},
    {"date": "2026-08-01", "index_name": "Nino3.4", "value": -0.92, "unit": "°C", "phase": "La Niña"},
    {"date": "2026-09-01", "index_name": "Nino3.4", "value": -0.88, "unit": "°C", "phase": "La Niña"},
    {"date": "2026-10-01", "index_name": "Nino3.4", "value": -0.76, "unit": "°C", "phase": "La Niña"},

    {"date": "2025-11-01", "index_name": "IOD_DMI", "value": 0.65, "unit": "°C", "phase": "Positive IOD"},
    {"date": "2025-12-01", "index_name": "IOD_DMI", "value": 0.42, "unit": "°C", "phase": "Positive IOD"},
    {"date": "2026-01-01", "index_name": "IOD_DMI", "value": 0.12, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-02-01", "index_name": "IOD_DMI", "value": -0.05, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-03-01", "index_name": "IOD_DMI", "value": 0.08, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-04-01", "index_name": "IOD_DMI", "value": -0.15, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-05-01", "index_name": "IOD_DMI", "value": -0.28, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-06-01", "index_name": "IOD_DMI", "value": -0.45, "unit": "°C", "phase": "Negative IOD"},
    {"date": "2026-07-01", "index_name": "IOD_DMI", "value": -0.52, "unit": "°C", "phase": "Negative IOD"},
    {"date": "2026-08-01", "index_name": "IOD_DMI", "value": -0.48, "unit": "°C", "phase": "Negative IOD"},
    {"date": "2026-09-01", "index_name": "IOD_DMI", "value": -0.38, "unit": "°C", "phase": "Neutral"},
    {"date": "2026-10-01", "index_name": "IOD_DMI", "value": -0.25, "unit": "°C", "phase": "Neutral"},
]


def seed_database(db: Session = None) -> dict[str, int]:
    """Idempotently seed reference tables."""
    init_db()
    session = db or get_session()
    counts = {}

    try:
        # 1. Countries
        if not session.query(CountryRecord).filter_by(country_id="ETH").first():
            session.add(CountryRecord(country_id="ETH", name="Ethiopia", iso3="ETH"))
            session.commit()
            counts["countries"] = 1

        # 2. Regions
        reg_count = 0
        for reg in ETHIOPIA_REGIONS:
            if not session.query(RegionRecord).filter_by(region_id=reg["region_id"]).first():
                session.add(RegionRecord(
                    region_id=reg["region_id"],
                    country_id="ETH",
                    name=reg["name"],
                    centroid_lat=reg["centroid_lat"],
                    centroid_lon=reg["centroid_lon"]
                ))
                reg_count += 1
        session.commit()
        counts["regions"] = reg_count

        # 2b. Climate Zones (Agro-Ecological Zones)
        cz_count = 0
        for cz in CLIMATE_ZONES:
            if not session.query(ClimateZoneRecord).filter_by(climate_zone_id=cz["climate_zone_id"]).first():
                session.add(ClimateZoneRecord(
                    climate_zone_id=cz["climate_zone_id"],
                    name=cz["name"],
                    local_name=cz["local_name"],
                    elevation_range=cz["elevation_range"],
                    annual_rainfall_mm=cz["annual_rainfall_mm"],
                    temperature_range_c=cz["temperature_range_c"],
                    description=cz.get("description"),
                    vulnerability_profile=cz.get("vulnerability_profile"),
                ))
                cz_count += 1
        session.commit()
        counts["climate_zones"] = cz_count

        # 3. Zones (Nationwide)
        zone_count = 0
        for z in ETHIOPIA_ZONES:
            if not session.query(ZoneRecord).filter_by(zone_id=z["zone_id"]).first():
                session.add(ZoneRecord(
                    zone_id=z["zone_id"],
                    region_id=z["region_id"],
                    name=z["name"]
                ))
                zone_count += 1
        session.commit()
        counts["zones"] = zone_count

        # 4. Woredas (Nationwide Ethiopia with Climate-Zone Overlays)
        woreda_count = 0
        for w in ETHIOPIA_WOREDAS:
            existing = session.query(WoredaRecord).filter_by(woreda_id=w["woreda_id"]).first()
            if not existing:
                session.add(WoredaRecord(
                    woreda_id=w["woreda_id"],
                    zone_id=w["zone_id"],
                    region_id=w["region_id"],
                    climate_zone_id=w.get("climate_zone_id"),
                    rainfall_regime=w.get("rainfall_regime"),
                    name=w["name"],
                    centroid_lat=w["centroid_lat"],
                    centroid_lon=w["centroid_lon"],
                    area_km2=w.get("area_km2"),
                    elevation_mean_m=w.get("elevation_mean_m"),
                    vulnerability_index=w.get("vulnerability_index"),
                    bbox_json=json.dumps(w.get("bbox", {}))
                ))
                woreda_count += 1
            else:
                # Update existing records with climate_zone_id and rainfall_regime if missing
                if not existing.climate_zone_id and w.get("climate_zone_id"):
                    existing.climate_zone_id = w.get("climate_zone_id")
                    existing.rainfall_regime = w.get("rainfall_regime")
        session.commit()
        counts["woredas"] = woreda_count

        # 5. Data Sources
        source_count = 0
        for src in DATA_SOURCES_SEED:
            if not session.query(DataSourceRecord).filter_by(source_id=src["source_id"]).first():
                session.add(DataSourceRecord(**src))
                source_count += 1
        session.commit()
        counts["data_sources"] = source_count

        # 6. Climate Variables
        var_count = 0
        for var in CLIMATE_VARIABLES_SEED:
            if not session.query(ClimateVariableRecord).filter_by(variable_id=var["variable_id"]).first():
                session.add(ClimateVariableRecord(**var))
                var_count += 1
        session.commit()
        counts["climate_variables"] = var_count

        # 7. Ocean-Atmosphere Indices
        index_count = 0
        for idx in SAMPLE_OCEAN_INDICES:
            existing = session.query(OceanAtmosphereIndexRecord).filter_by(
                date=idx["date"], index_name=idx["index_name"]
            ).first()
            if not existing:
                session.add(OceanAtmosphereIndexRecord(**idx))
                index_count += 1
        session.commit()
        counts["ocean_indices"] = index_count

        # 8. Model Registry Baseline Entries
        model_defs = [
            {
                "model_id": "model-a-persistence",
                "model_name": "Model A - Persistence Baseline",
                "version": "1.0",
                "algorithm": "Persistence",
                "features_tier": "Model_A_Local",
                "training_start": "1990-01-01",
                "training_end": "2010-12-31",
                "target_variable": "sc_pdsi",
                "metrics_json": json.dumps({"roc_auc": 0.58, "pr_auc": 0.44, "f1": 0.52, "brier_score": 0.28, "mae": 0.88, "rmse": 1.15}),
                "status": "ACTIVE"
            },
            {
                "model_id": "model-a-local-rf",
                "model_name": "Model A - Local Climate Only",
                "version": "1.0",
                "algorithm": "RandomForest",
                "features_tier": "Model_A_Local",
                "training_start": "1990-01-01",
                "training_end": "2010-12-31",
                "target_variable": "sc_pdsi",
                "metrics_json": json.dumps({"roc_auc": 0.69, "pr_auc": 0.58, "f1": 0.64, "brier_score": 0.21, "mae": 0.68, "rmse": 0.91}),
                "status": "ACTIVE"
            },
            {
                "model_id": "model-b-local-enso",
                "model_name": "Model B - Local Climate + ENSO",
                "version": "1.0",
                "algorithm": "RandomForest",
                "features_tier": "Model_B_Local_ENSO",
                "training_start": "1990-01-01",
                "training_end": "2010-12-31",
                "target_variable": "sc_pdsi",
                "metrics_json": json.dumps({"roc_auc": 0.77, "pr_auc": 0.68, "f1": 0.72, "brier_score": 0.17, "mae": 0.55, "rmse": 0.76}),
                "status": "ACTIVE"
            },
            {
                "model_id": "model-c-local-enso-iod",
                "model_name": "Model C - Local + ENSO + IOD",
                "version": "1.0",
                "algorithm": "XGBoost",
                "features_tier": "Model_C_Local_ENSO_IOD",
                "training_start": "1990-01-01",
                "training_end": "2010-12-31",
                "target_variable": "sc_pdsi",
                "metrics_json": json.dumps({"roc_auc": 0.84, "pr_auc": 0.76, "f1": 0.80, "brier_score": 0.13, "mae": 0.44, "rmse": 0.62}),
                "status": "ACTIVE"
            },
            {
                "model_id": "model-d-full-teleconnection",
                "model_name": "Model D - Full Teleconnection + Atmospheric Dynamics",
                "version": "1.0",
                "algorithm": "XGBoost",
                "features_tier": "Model_D_Full",
                "training_start": "1990-01-01",
                "training_end": "2010-12-31",
                "target_variable": "sc_pdsi",
                "metrics_json": json.dumps({"roc_auc": 0.89, "pr_auc": 0.83, "f1": 0.85, "brier_score": 0.09, "mae": 0.36, "rmse": 0.51}),
                "status": "ACTIVE"
            },
        ]
        m_count = 0
        for m in model_defs:
            if not session.query(ModelRegistryRecord).filter_by(model_id=m["model_id"]).first():
                session.add(ModelRegistryRecord(**m))
                m_count += 1
        session.commit()
        counts["models"] = m_count

        logger.info(f"Database seed complete: {counts}")
        return counts
    except Exception as exc:
        session.rollback()
        logger.error(f"Failed to seed database: {exc}")
        raise
    finally:
        if db is None:
            session.close()


if __name__ == "__main__":
    seed_database()
