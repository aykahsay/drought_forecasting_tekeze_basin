"""
Unit and Integration Tests for NOAA Climate Data Integration Suite (§17)
"""
from datetime import date
import pytest
from fastapi.testclient import TestClient

from agriminds.app import create_app
from agriminds.climate.sources.noaa import (
    NOAACFSv2SeasonalSource,
    NOAACPCRainfallSource,
    NOAAONISource,
    NOAAVegetationHealthSource,
    get_noaa_suite,
)
from agriminds.climate.sources.registry import get_source_registry


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────────────
# 1. NOAA CPC Africa Rainfall Estimation (RFE 2.0)
# ─────────────────────────────────────────────────────────────────────────────
class TestNOAACPCRainfall:
    def test_source_metadata(self):
        src = NOAACPCRainfallSource()
        assert src.source_name == "NOAA_CPC_RFE"
        assert src.source_type == "satellite_gauge_blend"
        assert src.spatial_resolution_deg == 0.10
        assert src.temporal_resolution == "daily"
        assert src.is_available() is True

    def test_extract_returns_valid_observations(self):
        src = NOAACPCRainfallSource()
        df = src.extract(date(2024, 7, 15))
        assert not df.empty
        assert "variable" in df.columns
        assert "noaa_rfe_precipitation" in df["variable"].values
        assert "noaa_rfe_dekad_total" in df["variable"].values
        assert "woreda_id" in df.columns

    def test_cross_validation_with_era5t(self):
        src = NOAACPCRainfallSource()
        comp = src.get_comparison_with_era5t("sinan")
        assert comp["woreda_id"] == "sinan"
        assert "NOAA_CPC_RFE" in comp["sources"]
        assert "ERA5T_REANALYSIS" in comp["sources"]
        assert "CHIRPS_SATELLITE" in comp["sources"]
        assert "multi_source_spread_mm" in comp["metrics"]
        assert "observational_confidence" in comp["metrics"]


# ─────────────────────────────────────────────────────────────────────────────
# 2. NOAA CPC Oceanic Niño Index (ONI) & Niño 3.4 Live Bridge
# ─────────────────────────────────────────────────────────────────────────────
class TestNOAAONI:
    def test_source_metadata(self):
        src = NOAAONISource()
        assert src.source_name == "NOAA_CPC_ONI"
        assert src.source_type == "oceanic_index"
        assert src.is_available() is True

    def test_extract_and_transform_phases(self):
        src = NOAAONISource()
        raw = src.extract(date.today())
        val = src.validate(raw)
        trans = src.transform(val)
        assert "phase" in trans.columns
        assert all(trans["oni_value"] >= -4.0)
        assert all(trans["oni_value"] <= 4.0)

    def test_live_teleconnection_state(self):
        src = NOAAONISource()
        state = src.get_live_teleconnection_state()
        assert "current_oni_value" in state
        assert "weekly_nino34_value" in state
        assert "ethiopia_teleconnection_impact" in state
        assert "historical_baseline_link" in state


# ─────────────────────────────────────────────────────────────────────────────
# 3. NOAA STAR Vegetation Health Index (VHI/VCI/TCI)
# ─────────────────────────────────────────────────────────────────────────────
class TestNOAAVegetationHealth:
    def test_source_metadata(self):
        src = NOAAVegetationHealthSource()
        assert src.source_name == "NOAA_STAR_VHI"
        assert src.source_type == "satellite_vegetation_thermal"
        assert src.spatial_resolution_deg == 0.04
        assert src.is_available() is True

    def test_extract_computes_vhi_composite(self):
        src = NOAAVegetationHealthSource()
        df = src.extract(date.today())
        assert not df.empty
        assert "vhi_index" in df.columns
        assert "vci_index" in df.columns
        assert "tci_index" in df.columns
        # VHI should equal 0.5 * VCI + 0.5 * TCI
        row = df.iloc[0]
        expected_vhi = round(0.5 * row["vci_index"] + 0.5 * row["tci_index"], 1)
        assert abs(row["vhi_index"] - expected_vhi) < 0.01

    def test_woreda_vegetation_health_lookup(self):
        src = NOAAVegetationHealthSource()
        vhi_sinan = src.get_woreda_vegetation_health("sinan")
        assert vhi_sinan["woreda_id"] == "sinan"
        assert vhi_sinan["stress_category"] == "HEALTHY_VEGETATION"

        vhi_gode = src.get_woreda_vegetation_health("gode")
        assert vhi_gode["woreda_id"] == "gode"
        assert vhi_gode["stress_category"] == "EXTREME_VEGETATIVE_DROUGHT"


# ─────────────────────────────────────────────────────────────────────────────
# 4. NOAA CFSv2 Seasonal Dynamical Ensemble Outlook
# ─────────────────────────────────────────────────────────────────────────────
class TestNOAACFSv2Seasonal:
    def test_source_metadata(self):
        src = NOAACFSv2SeasonalSource()
        assert src.source_name == "NOAA_CFSv2_OUTLOOK"
        assert src.source_type == "seasonal_dynamical_forecast"
        assert src.is_available() is True

    def test_multi_horizon_guidance(self):
        src = NOAACFSv2SeasonalSource()
        guidance = src.get_multi_horizon_guidance()
        assert "horizons" in guidance
        assert "1_month" in guidance["horizons"]
        assert "2_months" in guidance["horizons"]
        assert "3_months" in guidance["horizons"]
        assert guidance["horizons"]["3_months"]["rainfall_anomaly_mm_mon"] < 0


# ─────────────────────────────────────────────────────────────────────────────
# 5. Registry Integration
# ─────────────────────────────────────────────────────────────────────────────
class TestNOAAInSourceRegistry:
    def test_noaa_sources_registered(self):
        reg = get_source_registry()
        sources = reg.list_sources()
        assert "NOAA_CPC_RFE" in sources
        assert "NOAA_CPC_ONI" in sources
        assert "NOAA_STAR_VHI" in sources
        assert "NOAA_CFSv2_OUTLOOK" in sources

    def test_noaa_statuses_reported(self):
        reg = get_source_registry()
        statuses = reg.get_all_source_statuses()
        s_names = [s["source"] for s in statuses]
        assert "NOAA_CPC_RFE" in s_names
        assert "NOAA_STAR_VHI" in s_names


# ─────────────────────────────────────────────────────────────────────────────
# 6. REST API Endpoints
# ─────────────────────────────────────────────────────────────────────────────
class TestNOAARoutes:
    def test_noaa_overview_endpoint(self, client):
        res = client.get("/api/noaa/overview")
        assert res.status_code == 200
        d = res.json()
        assert d["feeds_active"] == 4
        assert "teleconnection_oni" in d
        assert "cfs_seasonal_outlook" in d

    def test_noaa_rfe_latest_endpoint(self, client):
        res = client.get("/api/noaa/rfe/latest")
        assert res.status_code == 200
        d = res.json()
        assert d["source"] == "NOAA_CPC_RFE"
        assert d["records_count"] > 0

    def test_noaa_rfe_cross_validation_endpoint(self, client):
        res = client.get("/api/noaa/rfe/cross-validation/sinan")
        assert res.status_code == 200
        d = res.json()
        assert d["woreda_id"] == "sinan"
        assert "sources" in d

    def test_noaa_oni_stream_endpoint(self, client):
        res = client.get("/api/noaa/oni/stream")
        assert res.status_code == 200
        d = res.json()
        assert "current_oni_value" in d
        assert "weekly_nino34_value" in d

    def test_noaa_vhi_woreda_endpoint(self, client):
        res = client.get("/api/noaa/vhi/woreda/hawzen")
        assert res.status_code == 200
        d = res.json()
        assert d["woreda_id"] == "hawzen"
        assert "vhi_composite" in d

    def test_noaa_cfsv2_outlook_endpoint(self, client):
        res = client.get("/api/noaa/cfsv2/outlook")
        assert res.status_code == 200
        d = res.json()
        assert "horizons" in d

    def test_noaa_ingest_endpoint(self, client):
        res = client.post("/api/noaa/ingest/NOAA_CPC_RFE")
        assert res.status_code == 200
        d = res.json()
        assert d["status"] == "SUCCESS"
        assert d["source_name"] == "NOAA_CPC_RFE"
