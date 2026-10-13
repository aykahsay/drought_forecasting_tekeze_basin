"""
Tests for the 4-Tier National Hierarchy API (National -> Region -> Zone -> Woreda -> Kebele).
"""

import pytest
from fastapi.testclient import TestClient

from agriminds.app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_hierarchy_overview(client):
    """Overview returns complete federal hierarchy summary."""
    r = client.get("/api/hierarchy/overview")
    assert r.status_code == 200
    data = r.json()
    assert data["country"] == "Ethiopia"
    assert data["tiers"]["tier_1_national"]["count"] == 13
    assert data["tiers"]["tier_2_zones"]["count"] >= 20
    assert data["tiers"]["tier_3_woredas"]["count"] >= 9
    assert data["tiers"]["tier_4_kebeles"]["count"] >= 6


def test_hierarchy_national_tier(client):
    """Level 1 National: returns all 13 regions with SVG polygons and timeseries."""
    r = client.get("/api/hierarchy/national")
    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == "national"
    assert data["items_count"] == 13
    region_ids = [item["region_id"] for item in data["items"]]
    assert "amhara" in region_ids
    assert "tigray" in region_ids
    assert "oromia" in region_ids
    assert "somali" in region_ids
    assert "afar" in region_ids
    assert "sidama" in region_ids
    # Verify SVG path present
    assert data["items"][0]["svg_path"].startswith("M ")
    # Verify aggregate timeseries
    assert len(data["aggregate_timeseries"]["months"]) == 7


def test_hierarchy_regional_tier_amhara(client):
    """Level 2 Zonal Tier: returns administrative zones for Amhara."""
    r = client.get("/api/hierarchy/region/amhara")
    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == "zone"
    assert data["parent_id"] == "amhara"
    assert data["items_count"] >= 10
    zone_ids = [z["zone_id"] for z in data["items"]]
    assert "east_gojjam" in zone_ids
    assert "west_gojjam" in zone_ids
    assert "north_wollo" in zone_ids


def test_hierarchy_regional_tier_tigray(client):
    """Level 2 Zonal Tier: returns administrative zones for Tigray."""
    r = client.get("/api/hierarchy/region/tigray")
    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == "zone"
    assert data["parent_id"] == "tigray"
    zone_ids = [z["zone_id"] for z in data["items"]]
    assert "eastern_tigray" in zone_ids
    assert "central_tigray" in zone_ids


def test_hierarchy_zonal_tier_east_gojjam(client):
    """Level 3 Woreda Tier: returns woredas for East Gojjam zone."""
    r = client.get("/api/hierarchy/zone/east_gojjam")
    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == "woreda"
    assert data["parent_id"] == "east_gojjam"
    woreda_ids = [w["woreda_id"] for w in data["items"]]
    assert "sinan" in woreda_ids
    assert "machakel" in woreda_ids
    assert "gozamin" in woreda_ids


def test_hierarchy_woreda_tier_sinan(client):
    """Level 4 Kebele Tier: returns local kebeles, water points, and crop wilting."""
    r = client.get("/api/hierarchy/woreda/sinan")
    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == "kebele"
    assert data["parent_id"] == "sinan"
    assert data["items_count"] >= 3
    robit = next((k for k in data["items"] if k["kebele_id"] == "sinan_robit"), None)
    assert robit is not None
    assert robit["soil_cracking_depth_cm"] > 0
    assert "nearest_water_point" in robit
    assert robit["nearest_water_point"]["distance_m"] > 0
    assert "da_field_report" in robit
    assert robit["da_field_report"]["verification_status"] == "VERIFIED_ON_GROUND"


def test_hierarchy_woreda_tier_hawzen(client):
    """Level 4 Kebele Tier: returns local kebeles for Hawzen woreda."""
    r = client.get("/api/hierarchy/woreda/hawzen")
    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == "kebele"
    assert data["parent_id"] == "hawzen"
    megab = next((k for k in data["items"] if k["kebele_id"] == "hawzen_megab"), None)
    assert megab is not None
    assert megab["crop_stage"] != ""
    assert megab["nearest_water_point"]["type"] == "motorized_borehole"


def test_hierarchy_temporal_filter(client):
    """Temporal filter queries return month-specific anomalies."""
    r = client.get("/api/hierarchy/national?month=sep")
    assert r.status_code == 200
    data = r.json()
    assert data["active_month"] == "sep"
    amhara = next(item for item in data["items"] if item["region_id"] == "amhara")
    assert amhara["active_el_nino"] == 1.8
