import os
import pytest
import numpy as np
from drought_forecasting.agriminds.spatial.tekeze_basin_boundary import (
    get_tekeze_geojson_path,
    load_tekeze_basin_geojson,
    load_tekeze_basin_geometry,
    get_tekeze_metadata,
    compute_geojson_sha256,
    is_coordinate_in_tekeze_basin,
    create_spatial_grid_mask,
    compute_area_weighted_basin_mean
)


def test_tekeze_geojson_exists_and_sha256():
    path = get_tekeze_geojson_path()
    assert os.path.exists(path), f"GeoJSON does not exist at {path}"
    sha = compute_geojson_sha256()
    assert len(sha) == 64
    assert sha == "0f93d4b2ac3110a7e0e0564519c9c7424b18e0b5f0b0f3bc0848b8bf34b1a3f6"


def test_tekeze_metadata_attributes():
    meta = get_tekeze_metadata()
    assert meta["crs"] == "EPSG:4326 (WGS 84)"
    assert meta["total_area_km2"] == pytest.approx(67135.4, rel=1e-3)
    assert meta["constituent_hybas_ids"] == [1050648030, 1050692800, 1050692900]
    assert meta["constituent_pfaf_ids"] == [17227, 17228, 17229]
    bounds = meta["bounds_wsen"]
    assert bounds[0] == pytest.approx(35.8583, abs=0.01)  # West
    assert bounds[1] == pytest.approx(11.6619, abs=0.01)  # South
    assert bounds[2] == pytest.approx(39.7917, abs=0.01)  # East
    assert bounds[3] == pytest.approx(14.7958, abs=0.01)  # North


def test_geometry_properties():
    geom = load_tekeze_basin_geometry()
    assert geom.is_valid
    assert not geom.is_empty
    minx, miny, maxx, maxy = geom.bounds
    assert miny < 12.0, "Southern boundary must encompass the Upper Tekeze headwaters below 12°N"
    assert maxy > 14.5, "Northern boundary must reach the Tigray/Eritrea border above 14.5°N"


def test_focal_point_containment():
    # Inside points (including Mekelle in the Geva tributary catchment)
    assert is_coordinate_in_tekeze_basin(38.980, 13.250), "Yechila should be inside Tekeze basin"
    assert is_coordinate_in_tekeze_basin(39.040, 12.030), "Lalibela should be inside Upper Tekeze basin"
    assert is_coordinate_in_tekeze_basin(38.370, 13.230), "Simien Mountains should be inside Tekeze basin"
    assert is_coordinate_in_tekeze_basin(38.720, 13.350), "Tekeze Reservoir should be inside Tekeze basin"
    assert is_coordinate_in_tekeze_basin(39.470, 13.500), "Mekelle (Geva River tributary) should be inside Tekeze basin"

    # Outside points
    assert not is_coordinate_in_tekeze_basin(38.7578, 8.9806), "Addis Ababa should be outside Tekeze basin"
    assert not is_coordinate_in_tekeze_basin(37.470, 12.600), "Gondar (Angereb basin) should be outside Tekeze proper"
    assert not is_coordinate_in_tekeze_basin(37.300, 12.000), "Lake Tana (Blue Nile / Abay Basin) should be outside Tekeze basin"
    assert not is_coordinate_in_tekeze_basin(40.300, 14.200), "Dallol (Danakil Depression) should be outside Tekeze basin"
    assert not is_coordinate_in_tekeze_basin(41.000, 11.800), "Semera (Awash Basin) should be outside Tekeze basin"


def test_spatial_grid_mask_and_weighted_mean():
    # Create synthetic regular grid
    lats = np.linspace(11.0, 15.5, 91)
    lons = np.linspace(35.0, 40.5, 111)

    mask, weights, lat_idx, lon_idx = create_spatial_grid_mask(lats, lons)
    assert mask.shape == (len(lat_idx), len(lon_idx))
    assert mask.sum() > 0, "Mask must contain active grid cells inside the basin"
    assert weights.sum() == pytest.approx(1.0, abs=1e-5), "Weights inside basin must sum to 1.0"

    # Uniform field test
    uniform_precip = 50.0 * np.ones((len(lats), len(lons)))
    basin_mean = compute_area_weighted_basin_mean(uniform_precip, lats, lons)
    assert basin_mean == pytest.approx(50.0, abs=1e-4)
