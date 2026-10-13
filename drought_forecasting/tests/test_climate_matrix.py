"""
Unit and integration tests for the Interactive Regional Climate Matrix API.
Verifies Amhara 17 sub-basins, Lake Tana polygon, color ramps, and dual-axis monthly series.
"""

import pytest
from starlette.testclient import TestClient
from agriminds.app import create_app
from agriminds.spatial.amhara_basins import AMHARA_BASINS, LAKE_TANA_GEOMETRY, AMHARA_MONTHLY_AGGREGATE


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


class TestAmharaClimateMatrix:

    def test_basins_count_and_lake_tana(self):
        assert len(AMHARA_BASINS) == 17
        basin_ids = [b["basin_id"] for b in AMHARA_BASINS]
        assert "tana_basin" in basin_ids
        assert "north_gojam" in basin_ids
        assert "south_gojam" in basin_ids
        assert "dinder" in basin_ids
        assert "welka" in basin_ids
        assert "jemma" in basin_ids

        assert LAKE_TANA_GEOMETRY["feature_id"] == "lake_tana"
        assert "ጣና ሐይቅ" in LAKE_TANA_GEOMETRY["local_name"]
        assert LAKE_TANA_GEOMETRY["surface_area_km2"] > 3000

    def test_aggregate_monthly_series(self):
        agg = AMHARA_MONTHLY_AGGREGATE
        assert agg["region"] == "Amhara Region"
        assert len(agg["months"]) == 7
        assert len(agg["series"]["precipitation_2026"]) == 7
        assert len(agg["series"]["precipitation_2025"]) == 7
        assert len(agg["series"]["rain_days_2026"]) == 7
        assert len(agg["series"]["rain_days_2025"]) == 7

    def test_api_matrix_amhara_endpoint(self, client):
        res = client.get("/api/matrix/amhara")
        assert res.status_code == 200
        data = res.json()
        assert data["region_id"] == "amhara"
        assert data["target_year"] == 2026
        assert data["baseline_year"] == 2025
        assert data["basins_count"] == 17
        assert len(data["basins"]) == 17

        # Check color ramps exist
        assert "el_nino" in data["color_ramps"]
        assert "drought" in data["color_ramps"]
        assert "precipitation" in data["color_ramps"]

        # Check Lake Tana is included
        assert data["lake_tana"]["name"] == "Lake Tana"

    def test_api_matrix_month_filter(self, client):
        res = client.get("/api/matrix/amhara?month=aug")
        assert res.status_code == 200
        data = res.json()
        assert data["selected_month"] == "aug"
        tana = next(b for b in data["basins"] if b["basin_id"] == "tana_basin")
        assert "active_el_nino" in tana
        assert tana["active_drought"] < 0  # Severe August drought

    def test_api_matrix_basin_detail(self, client):
        res = client.get("/api/matrix/amhara/basin/north_gojam")
        assert res.status_code == 200
        data = res.json()
        assert data["basin"]["name"] == "North Gojam"
        assert "Mount Choke" in data["basin"]["description"]

    def test_api_matrix_invalid_basin(self, client):
        res = client.get("/api/matrix/amhara/basin/nonexistent_basin")
        assert res.status_code == 404
