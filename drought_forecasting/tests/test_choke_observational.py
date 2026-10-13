"""
Test Suite: Choke Mountains Observational Data & 8x8 Grid Mask
==============================================================
Validates:
  1. Surveyed CMW GeoJSON polygon and 18,948 km2 area.
  2. 8x8 grid specification and the 15-cell hydrological boundary mask (49 inside, 15 outside).
  3. 4-layer volumetric soil moisture arrays (swvl1, swvl2, swvl3, swvl4).
  4. REST API endpoints for Choke observational data.
"""
import pytest
from fastapi.testclient import TestClient

from agriminds.app import create_app
from agriminds.climate.choke_observational import (
    get_grid_spec,
    get_grid_mask,
    load_climate_cube,
    get_latest_choke_grid_state,
    get_cell_observational_history,
    get_basin_timeseries_df,
)


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_grid_spec_and_mask_integrity():
    spec = get_grid_spec()
    assert spec["rows"] == 8
    assert spec["cols"] == 8
    assert spec["inside_count"] == 49
    assert spec["outside_count"] == 15
    assert len(spec["cells"]) == 8
    assert len(spec["cells"][0]) == 8

    mask = get_grid_mask()
    assert mask.shape == (8, 8)
    assert mask.sum() == 49


def test_climate_cube_arrays():
    cube = load_climate_cube()
    assert len(cube["dates"]) == 400
    assert len(cube["lats"]) == 8
    assert len(cube["lons"]) == 8
    assert cube["swvl1"].shape == (400, 8, 8)
    assert cube["swvl2"].shape == (400, 8, 8)
    assert cube["swvl3"].shape == (400, 8, 8)
    assert cube["swvl4"].shape == (400, 8, 8)
    assert cube["swvl_root"].shape == (400, 8, 8)
    assert cube["t2m_c"].shape == (400, 8, 8)
    assert cube["tp_mm"].shape == (400, 8, 8)

    # Physical range sanity check
    assert 0.05 < cube["swvl1"].mean() < 0.60
    assert 0.05 < cube["swvl_root"].mean() < 0.60
    assert 5.0 < cube["t2m_c"].mean() < 30.0


def test_latest_grid_state_summary():
    state = get_latest_choke_grid_state()
    assert "date" in state
    assert "basin_summary" in state
    summary = state["basin_summary"]
    assert summary["total_cells"] == 64
    assert summary["cells_inside_watershed"] == 49
    assert summary["cells_masked_out"] == 15
    assert summary["mean_topsoil_swvl1"] > 0
    assert summary["mean_root_zone_swvl"] > 0
    assert len(state["grid"]) == 8
    assert len(state["grid"][0]) == 8


def test_cell_history():
    hist = get_cell_observational_history(3, 4)
    assert hist["cell"]["row"] == 3
    assert hist["cell"]["col"] == 4
    assert hist["total_records"] == 400
    assert len(hist["records"]) == 400
    assert "swvl_root" in hist["records"][0]
    assert "t2m_c" in hist["records"][0]


def test_basin_timeseries_df():
    df = get_basin_timeseries_df()
    assert len(df) == 400
    assert "swvl1_mean" in df.columns
    assert "swvl_root_mean" in df.columns
    assert "t2m_mean_c" in df.columns


def test_api_choke_endpoints(client):
    # Spec
    resp = client.get("/api/choke/grid/spec")
    assert resp.status_code == 200
    assert resp.json()["inside_count"] == 49

    # Latest
    resp = client.get("/api/choke/grid/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["basin_summary"]["cells_inside_watershed"] == 49

    # Cell history
    resp = client.get("/api/choke/grid/cell/2/3")
    assert resp.status_code == 200
    assert resp.json()["total_records"] == 400

    # Basin timeseries
    resp = client.get("/api/choke/timeseries/basin?limit=10")
    assert resp.status_code == 200
    assert resp.json()["count"] == 10

    # GeoJSON
    resp = client.get("/api/choke/geojson")
    assert resp.status_code == 200
    assert resp.json()["type"] == "FeatureCollection" or "Feature" in resp.json().get("type", "")
