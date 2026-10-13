"""
Tests for Nationwide Ethiopia Woredas & Agro-Ecological Climate Zones Architecture
===================================================================================
Verifies:
  1. The 5 top-level Agro-Ecological Climate Zones (Bereha, Kolla, Weyna Dega, Dega, Wurch)
  2. Climatological Rainfall Regimes (Regime A, Regime B, Regime C)
  3. Nationwide Woreda coverage across Tigray, Afar, Amhara, Oromia, Somali, Sidama, etc.
  4. Top-level Climate Zone spatial aggregation on top of administrative woredas
  5. Multi-tier REST API endpoints for climate zones, regions, and filtered woredas
"""
import pytest
from fastapi.testclient import TestClient
import pandas as pd

from agriminds.app import create_app
from agriminds.spatial.aggregation import SpatialAggregator
from agriminds.spatial.woredas import (
    CLIMATE_ZONES,
    ETHIOPIA_REGIONS,
    ETHIOPIA_WOREDAS,
    RAINFALL_REGIMES,
    get_all_regions,
    get_all_woredas,
    get_all_zones,
    get_climate_zone_by_id,
    get_climate_zones,
    get_woreda_by_id,
)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestClimateZonesDefinition:

    def test_five_agro_ecological_zones_exist(self):
        zones = get_climate_zones()
        assert len(zones) == 5
        zone_ids = {z["climate_zone_id"] for z in zones}
        assert zone_ids == {"bereha", "kolla", "weyna_dega", "dega", "wurch"}

        # Verify attributes
        bereha = get_climate_zone_by_id("bereha")
        assert bereha is not None
        assert "በረሃ" in bereha["local_name"]
        assert "< 500" in bereha["elevation_range"]
        assert "Pastoralist" in bereha["primary_livelihood"]

        weyna_dega = get_climate_zone_by_id("weyna_dega")
        assert weyna_dega is not None
        assert "ወይና ደጋ" in weyna_dega["local_name"]
        assert "1,500 – 2,300m" in weyna_dega["elevation_range"]

    def test_rainfall_regimes_exist(self):
        assert "regime_a" in RAINFALL_REGIMES
        assert "regime_b" in RAINFALL_REGIMES
        assert "regime_c" in RAINFALL_REGIMES
        assert "Bimodal" in RAINFALL_REGIMES["regime_a"]["name"]
        assert "Monomodal" in RAINFALL_REGIMES["regime_b"]["name"]
        assert "Gu" in RAINFALL_REGIMES["regime_c"]["description"]


class TestNationwideWoredas:

    def test_woredas_span_multiple_regions(self):
        all_woredas = get_all_woredas()
        assert len(all_woredas) >= 40  # Comprehensive Ethiopia catalog

        regions_represented = {w["region_id"] for w in all_woredas}
        expected_regions = {"tigray", "afar", "amhara", "oromia", "somali", "sidama"}
        assert expected_regions.issubset(regions_represented)

    def test_all_woredas_have_climate_zone_and_regime(self):
        all_woredas = get_all_woredas()
        valid_cz_ids = {"bereha", "kolla", "weyna_dega", "dega", "wurch"}
        valid_regimes = {"regime_a", "regime_b", "regime_c"}

        for w in all_woredas:
            assert "climate_zone_id" in w, f"Woreda {w['woreda_id']} missing climate_zone_id"
            assert w["climate_zone_id"] in valid_cz_ids, f"Invalid CZ in {w['woreda_id']}"
            assert "rainfall_regime" in w, f"Woreda {w['woreda_id']} missing rainfall_regime"
            assert w["rainfall_regime"] in valid_regimes, f"Invalid regime in {w['woreda_id']}"
            assert "centroid_lat" in w
            assert "centroid_lon" in w
            assert "bbox" in w

    def test_filter_woredas_by_region(self):
        afar_woredas = get_all_woredas(region_id="afar")
        assert len(afar_woredas) >= 5
        assert all(w["region_id"] == "afar" for w in afar_woredas)
        woreda_ids = {w["woreda_id"] for w in afar_woredas}
        assert "dubti" in woreda_ids
        assert "berhale" in woreda_ids

    def test_filter_woredas_by_climate_zone(self):
        bereha_woredas = get_all_woredas(climate_zone_id="bereha")
        assert len(bereha_woredas) >= 6
        assert all(w["climate_zone_id"] == "bereha" for w in bereha_woredas)
        # Should include lowlands from both Afar and Somali and Borana
        cz_regions = {w["region_id"] for w in bereha_woredas}
        assert "afar" in cz_regions
        assert "somali" in cz_regions

    def test_lookup_specific_woredas_across_ethiopia(self):
        # Somali
        gode = get_woreda_by_id("gode")
        assert gode is not None
        assert gode["region_id"] == "somali"
        assert gode["climate_zone_id"] == "bereha"
        assert gode["rainfall_regime"] == "regime_c"

        # Oromia Borana
        yabelo = get_woreda_by_id("yabelo")
        assert yabelo is not None
        assert yabelo["region_id"] == "oromia"
        assert yabelo["climate_zone_id"] == "kolla"

        # Amhara North Wollo
        delanta = get_woreda_by_id("delanta")
        assert delanta is not None
        assert delanta["region_id"] == "amhara"
        assert delanta["climate_zone_id"] == "dega"


class TestClimateZoneSpatialAggregation:

    def test_aggregate_by_climate_zone(self):
        aggregator = SpatialAggregator()
        cz_summaries = aggregator.aggregate_by_climate_zone(pd.DataFrame())
        assert len(cz_summaries) == 5

        bereha_sum = next(s for s in cz_summaries if s["climate_zone_id"] == "bereha")
        assert bereha_sum["member_woreda_count"] > 0
        assert "afar" in bereha_sum["member_regions"]
        assert "somali" in bereha_sum["member_regions"]
        assert bereha_sum["current_indicators"]["risk_level"] == "Extreme Risk"

        dega_sum = next(s for s in cz_summaries if s["climate_zone_id"] == "dega")
        assert dega_sum["member_woreda_count"] > 0
        assert "amhara" in dega_sum["member_regions"]


class TestClimateZoneAndNationwideEndpoints:

    def test_list_climate_zones_endpoint(self, client):
        r = client.get("/api/climate-zones")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 5
        assert len(data["climate_zones"]) == 5

    def test_climate_zone_detail_endpoint(self, client):
        r = client.get("/api/climate-zones/bereha")
        assert r.status_code == 200
        data = r.json()
        assert data["climate_zone_id"] == "bereha"
        assert len(data["member_woredas"]) > 0

    def test_list_regions_endpoint(self, client):
        r = client.get("/api/regions")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 8
        region_ids = [reg["region_id"] for reg in data["regions"]]
        assert "tigray" in region_ids
        assert "afar" in region_ids
        assert "oromia" in region_ids
        assert "somali" in region_ids

    def test_regional_overview_endpoint_afar(self, client):
        r = client.get("/api/regions/afar")
        assert r.status_code == 200
        data = r.json()
        assert data["region_name"] == "Afar"
        assert len(data["woreda_risk_ranking"]) >= 5

    def test_regional_overview_endpoint_somali(self, client):
        r = client.get("/api/regions/somali")
        assert r.status_code == 200
        data = r.json()
        assert data["region_name"] == "Somali"
        assert len(data["woreda_risk_ranking"]) >= 5

    def test_woredas_filter_by_climate_zone_endpoint(self, client):
        r = client.get("/api/woredas?climate_zone_id=kolla")
        assert r.status_code == 200
        data = r.json()
        assert data["filter_climate_zone"] == "kolla"
        assert all(w["climate_zone_id"] == "kolla" for w in data["woredas"])

    def test_woreda_detail_contains_climate_zone(self, client):
        r = client.get("/api/woredas/yabelo")
        assert r.status_code == 200
        data = r.json()
        assert data["woreda"]["name"] == "Yabelo"
        assert "climate_zone" in data
        assert data["climate_zone"]["climate_zone_id"] == "kolla"
