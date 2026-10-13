"""
Comprehensive Test Suite for AI-DREWS Data System Architecture
==============================================================
Validates:
  1. Data Quality Engine (7-Step Protocol & Missing Data Taxonomy)
  2. Source Ingestion Pipelines (Contract: extract, validate, transform, load, log)
  3. Spatial Aggregation Engine (Grid to Woreda polygon)
  4. Multi-Horizon Forecasting (1-month, 2-month, 3-month lead times)
  5. Scientific Ablation Study (Skill comparison across Models A, B, C, D)
  6. Model Explainability ("Factors contributing to the model prediction")
  7. Multi-Tier REST API Endpoints (National, Regional, Woreda, Causal Pipeline)
"""
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from agriminds.app import create_app
from agriminds.climate.quality import (
    DataQualityEngine,
    MissingDataCategory,
    QualityFlag,
)
from agriminds.climate.sources.registry import get_source_registry
from agriminds.climate.sources.teleconnections import (
    ENSOLoader,
    IODLoader,
    classify_iod_phase,
)
from agriminds.ml.ablation import get_ablation_suite
from agriminds.spatial.aggregation import SpatialAggregator
from agriminds.spatial.woredas import get_all_woredas, get_woreda_by_id


# ════════════════════════════════════════════════════════════════════════════
# 1. Data Quality Engine Tests (§5)
# ════════════════════════════════════════════════════════════════════════════
class TestDataQualityEngine:
    def test_missing_data_taxonomy_zero_rainfall(self):
        """0.0 mm rainfall must be preserved as legitimate zero, NOT missing data."""
        engine = DataQualityEngine(region="tigray")
        df = pd.DataFrame([
            {"date": "2026-05-01", "variable": "total_precipitation", "value": 0.0, "unit": "mm"},
            {"date": "2026-05-02", "variable": "total_precipitation", "value": None, "unit": "mm"},
            {"date": "2026-05-03", "variable": "total_precipitation", "value": 15.2, "unit": "mm"},
        ])
        clean_df, report = engine.process(df, source_name="TestEngine")

        # Zero rainfall check
        zero_row = clean_df[clean_df["date"] == "2026-05-01"].iloc[0]
        assert zero_row["missing_category"] == MissingDataCategory.LEGITIMATE_ZERO.value
        assert zero_row["quality_flag"] == QualityFlag.GOOD.value

        # Missing value check
        missing_row = clean_df[clean_df["date"] == "2026-05-02"].iloc[0]
        assert missing_row["missing_category"] == MissingDataCategory.MISSING_VALUE.value
        assert missing_row["quality_flag"] == QualityFlag.MISSING.value

    def test_unit_normalization(self):
        """Kelvin must be converted to Celsius, metres to mm, Pa to hPa."""
        engine = DataQualityEngine(region="tigray")
        df = pd.DataFrame([
            {"date": "2026-05-01", "variable": "2m_temperature", "value": 298.15, "unit": "K"},
            {"date": "2026-05-01", "variable": "total_precipitation", "value": 0.012, "unit": "m"},
            {"date": "2026-05-01", "variable": "surface_pressure", "value": 85000.0, "unit": "Pa"},
        ])
        clean_df, report = engine.process(df, source_name="TestEngine")

        # Temp: 298.15 K = 25.0 °C
        t_row = clean_df[clean_df["variable"] == "2m_temperature"].iloc[0]
        assert t_row["canonical_value"] == 25.0
        assert t_row["unit"] == "°C"
        assert t_row["original_unit"] == "K"

        # Precip: 0.012 m = 12.0 mm
        p_row = clean_df[clean_df["variable"] == "total_precipitation"].iloc[0]
        assert p_row["canonical_value"] == 12.0
        assert p_row["unit"] == "mm"

        # Pressure: 85000 Pa = 850.0 hPa
        sp_row = clean_df[clean_df["variable"] == "surface_pressure"].iloc[0]
        assert sp_row["canonical_value"] == 850.0
        assert sp_row["unit"] == "hPa"

    def test_duplicate_detection(self):
        """Duplicates on (date, variable, lat, lon) must be detected and deduplicated."""
        engine = DataQualityEngine(region="tigray")
        df = pd.DataFrame([
            {"date": "2026-05-01", "variable": "total_precipitation", "value": 10.0, "unit": "mm", "latitude": 13.8, "longitude": 39.5},
            {"date": "2026-05-01", "variable": "total_precipitation", "value": 10.0, "unit": "mm", "latitude": 13.8, "longitude": 39.5},
        ])
        clean_df, report = engine.process(df, source_name="TestEngine")
        assert len(clean_df) == 1
        assert report.steps[2].issues_found == 1

    def test_physical_range_bounds(self):
        """Physically impossible temperatures and negative precip must be flagged INVALID."""
        engine = DataQualityEngine(region="tigray")
        df = pd.DataFrame([
            {"date": "2026-05-01", "variable": "total_precipitation", "value": -5.0, "unit": "mm"},
            {"date": "2026-05-01", "variable": "2m_temperature", "value": 100.0, "unit": "°C"},
        ])
        clean_df, report = engine.process(df, source_name="TestEngine")
        assert (clean_df["quality_flag"] == QualityFlag.INVALID.value).all()


# ════════════════════════════════════════════════════════════════════════════
# 2. Source Ingestion Pipeline Contract Tests (§2, §3)
# ════════════════════════════════════════════════════════════════════════════
class TestSourceIngestionPipelines:
    def test_enso_loader_contract(self):
        loader = ENSOLoader()
        dt = date.today() - timedelta(days=30)
        raw = loader.extract(dt)
        assert not raw.empty
        assert "value" in raw.columns
        assert "phase" in raw.columns

        validated = loader.validate(raw)
        assert not validated.empty

        clean = loader.transform(validated)
        count = loader.load(clean, dt)
        assert count >= 0

    def test_iod_phase_classification(self):
        assert classify_iod_phase(0.6) == "Positive IOD"
        assert classify_iod_phase(-0.5) == "Negative IOD"
        assert classify_iod_phase(0.1) == "Neutral"
        assert classify_iod_phase(None) == "Unknown"

    def test_source_registry_tracking(self):
        registry = get_source_registry()
        statuses = registry.get_all_source_statuses()
        sources = [s["source"] for s in statuses]
        assert "ERA5T" in sources
        assert "ENSO_NOAA" in sources
        assert "IOD_DMI" in sources
        assert "CHIRPS_MODIS" in sources
        assert "ETH_STATIONS" in sources

        # Every source must track last_available_date and ingestion_status
        for s in statuses:
            assert "last_available_date" in s
            assert "ingestion_status" in s
            assert "suggested_frequency" in s


# ════════════════════════════════════════════════════════════════════════════
# 3. Spatial Aggregation Tests (§7)
# ════════════════════════════════════════════════════════════════════════════
class TestSpatialAggregation:
    def test_woreda_definitions_exist(self):
        woredas = get_all_woredas()
        assert len(woredas) >= 15
        hawzen = get_woreda_by_id("hawzen")
        assert hawzen is not None
        assert hawzen["zone_id"] == "eastern_tigray"
        assert "bbox" in hawzen

    def test_aggregate_all_woredas(self):
        aggregator = SpatialAggregator()
        dummy_obs = pd.DataFrame([
            {"date": "2026-05-01", "variable": "total_precipitation", "latitude": 13.95, "longitude": 39.45, "value": 0.015},
            {"date": "2026-05-01", "variable": "total_precipitation", "latitude": 13.98, "longitude": 39.42, "value": 0.020},
            {"date": "2026-05-01", "variable": "2m_temperature", "latitude": 13.95, "longitude": 39.45, "value": 296.0},
        ])
        agg_df = aggregator.aggregate_all_woredas(dummy_obs)
        assert not agg_df.empty
        assert "woreda_name" in agg_df.columns
        assert "mean" in agg_df.columns


# ════════════════════════════════════════════════════════════════════════════
# 4. Multi-Horizon Forecasting & Ablation Tests (§9, §11, §14)
# ════════════════════════════════════════════════════════════════════════════
class TestMultiHorizonAndAblation:
    def test_ablation_skill_gain_matrix(self):
        suite = get_ablation_suite()
        summary = suite.get_ablation_summary()
        assert len(summary) >= 4

        # Model A: Local only
        m_a = summary[0]
        # Model D: Full teleconnection
        m_d = summary[3]

        assert m_a["roc_auc"] < m_d["roc_auc"]
        assert m_d["skill_gain_vs_local_pct"] > 20.0
        assert m_d["brier_score"] < m_a["brier_score"]

    def test_multi_horizon_probabilities(self):
        suite = get_ablation_suite()
        features = {"spi_3": -1.4, "nino34": -0.8, "iod": -0.35, "soil_moisture_percentile": 20.0}
        forecast = suite.predict_multi_horizon(features, woreda_id="hawzen")

        assert len(forecast.horizons) == 3
        h1, h2, h3 = forecast.horizons

        assert h1.horizon_months == 1
        assert h2.horizon_months == 2
        assert h3.horizon_months == 3

        # Probabilities between 0 and 1
        assert 0.0 <= h1.drought_probability <= 1.0
        assert 0.0 <= h2.drought_probability <= 1.0
        assert 0.0 <= h3.drought_probability <= 1.0

        # Top contributing factors explainability phrasing
        factors = forecast.top_contributing_factors
        assert len(factors) >= 4
        assert any("SPI-3" in f["feature"] for f in factors)
        assert any("Moisture" in f["feature"] for f in factors)


# ════════════════════════════════════════════════════════════════════════════
# 5. REST API Multi-Tier Endpoints Tests (§17, §18)
# ════════════════════════════════════════════════════════════════════════════
class TestNewAPIEndpoints:
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app, raise_server_exceptions=False)

    def test_national_overview_endpoint(self, client):
        r = client.get("/api/overview/ethiopia")
        assert r.status_code == 200
        data = r.json()
        assert "regional_risk_distribution" in data
        assert "global_teleconnections" in data

    def test_tigray_overview_endpoint(self, client):
        r = client.get("/api/regions/tigray")
        assert r.status_code == 200
        data = r.json()
        assert data["region"] == "Tigray"
        assert "woreda_risk_ranking" in data
        assert len(data["woreda_risk_ranking"]) > 0

    def test_woredas_endpoints(self, client):
        r = client.get("/api/woredas")
        assert r.status_code == 200
        assert r.json()["count"] >= 15

        r_detail = client.get("/api/woredas/hawzen")
        assert r_detail.status_code == 200
        data = r_detail.json()
        assert data["woreda"]["name"] == "Hawzen"
        assert "probabilistic_forecast" in data
        assert "1_month" in data["probabilistic_forecast"]

    def test_causal_story_endpoint(self, client):
        r = client.get("/api/teleconnections/story")
        assert r.status_code == 200
        data = r.json()
        assert "pipeline" in data
        assert len(data["pipeline"]) == 6
        assert data["pipeline"][0]["stage"] == "Global Ocean-Atmosphere Trigger"

    def test_ablation_experiment_endpoint(self, client):
        r = client.get("/api/experiments/ablation")
        assert r.status_code == 200
        data = r.json()
        assert "models_evaluated" in data
        assert len(data["models_evaluated"]) >= 4

    def test_sources_registry_endpoint(self, client):
        r = client.get("/api/sources/registry")
        assert r.status_code == 200
        data = r.json()
        assert data["sources_tracked"] >= 5
