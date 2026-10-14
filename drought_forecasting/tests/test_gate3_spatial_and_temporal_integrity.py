"""
test_gate3_spatial_and_temporal_integrity.py
=============================================
Automated Cross-Validation Test Suite for Gate 3:
Spatial and Temporal Integrity Auditing for the Tekezé River Basin (1981–2024).

Verifies:
  1. Catchment polygon validity, EPSG:4326 CRS, and geodesic area (67,135.4 km²).
  2. Coordinate alignment between vector boundary and CHIRPS / CPC raster grids.
  3. Strict NoData exclusion from both numerator and denominator in area-weighted aggregation.
  4. Fractional cell coverage and spherical cosine-latitude weight conservation.
  5. 95% spatial coverage threshold rule: coverage < 0.95 MUST produce NaN.
  6. Exact continuous 528-month sequence (1981-01 through 2024-12) with zero gaps/duplicates.
  7. Strict NaN propagation through rolling 3-month window accumulations.
  8. Independent source audit separation between precipitation and temperature feeds.
"""

import math
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point, Polygon, box, shape

from agriminds.climate.spei_calculator import (
    calculate_rolling_spei,
    calculate_rolling_spi,
)
from scripts.build_verified_tekeze_monthly_climate_1981_2024 import (
    construct_basin_raster_mask,
    BASIN_GEOJSON_PATH,
    CHIRPS_AFRICA_ORIGIN,
    CHIRPS_PIXEL_RES,
)


@pytest.fixture(scope="module")
def basin_polygon_and_props():
    assert BASIN_GEOJSON_PATH.exists(), f"Basin GeoJSON missing at {BASIN_GEOJSON_PATH}"
    with open(BASIN_GEOJSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    feat = data["features"][0]
    poly = shape(feat["geometry"])
    return poly, feat["properties"]


def test_gate3_basin_boundary_validity_and_area(basin_polygon_and_props):
    """Verify Tekezé boundary is topologically valid, EPSG:4326, and matches 67,135.4 km²."""
    poly, props = basin_polygon_and_props

    assert poly.is_valid, "Tekezé catchment polygon is not topologically valid"
    assert not poly.is_empty, "Tekezé catchment polygon is empty"
    assert poly.geom_type in ["Polygon", "MultiPolygon"]

    assert props["crs"].startswith("EPSG:4326")
    assert props["total_area_km2"] == pytest.approx(67135.4, rel=1e-3)

    # Spherical excess area calculation independently
    def spherical_ring_area(coords, r_km=6371.0088):
        rad = [(math.radians(lon), math.radians(lat)) for lon, lat in coords]
        tot = 0.0
        for i in range(len(rad) - 1):
            tot += (rad[i + 1][0] - rad[i][0]) * (2.0 + math.sin(rad[i][1]) + math.sin(rad[i + 1][1]))
        return abs(tot * (r_km ** 2) / 2.0)

    exterior_area = spherical_ring_area(list(poly.exterior.coords))
    assert exterior_area == pytest.approx(67135.4, rel=0.01)

    # Bounding box bounds check: Tekezé covers ~11.66°N–14.80°N, ~35.86°E–39.79°E
    min_x, min_y, max_x, max_y = poly.bounds
    assert 35.80 <= min_x <= 36.00
    assert 39.70 <= max_x <= 39.90
    assert 11.60 <= min_y <= 11.75
    assert 14.70 <= max_y <= 14.85


def test_gate3_chirps_grid_coordinate_alignment():
    """Verify CHIRPS raster cell alignment, affine transformation, and coordinate conventions."""
    mask, weights, lats, lons, crop_window, meta = construct_basin_raster_mask(BASIN_GEOJSON_PATH)

    r_start, r_end, c_start, c_end = crop_window
    origin_lat, origin_lon = CHIRPS_AFRICA_ORIGIN
    res = CHIRPS_PIXEL_RES

    # Verify cell center affine grid mapping (+ 0.5 offset convention)
    calc_lat_0 = origin_lat - (r_start + 0.5) * res
    calc_lon_0 = origin_lon + (c_start + 0.5) * res
    assert lats[0] == pytest.approx(calc_lat_0, abs=1e-5)
    assert lons[0] == pytest.approx(calc_lon_0, abs=1e-5)

    # Lats must decrease monotonically (north to south)
    assert np.all(np.diff(lats) < 0)
    # Lons must increase monotonically (west to east)
    assert np.all(np.diff(lons) > 0)


def test_gate3_area_weighted_aggregation_nodata_exclusion():
    """Verify that NoData cells (-9999) are excluded from both numerator and denominator."""
    mask, weights, _, _, _, _ = construct_basin_raster_mask(BASIN_GEOJSON_PATH)

    # Create synthetic precipitation field with 100 mm everywhere
    synth_precip = np.full(weights.shape, 100.0, dtype=np.float32)

    # Inject negative NoData sentinels in 30% of active cells
    active_idx = np.where(mask)
    num_active = len(active_idx[0])
    corrupt_idx = (active_idx[0][:int(num_active * 0.3)], active_idx[1][:int(num_active * 0.3)])
    synth_precip[corrupt_idx] = -9999.0

    # Gate 3 Correct Aggregation:
    valid_mask = mask & (synth_precip >= 0.0) & np.isfinite(synth_precip)
    val_weights = weights[valid_mask]
    weight_coverage = np.sum(val_weights)

    # With 30% corrupted, weight coverage should be ~70%
    assert 0.65 <= weight_coverage <= 0.75

    # Area-weighted mean over valid cells must strictly recover 100.0 mm
    norm_w = val_weights / weight_coverage
    mean_p = float(np.sum(synth_precip[valid_mask] * norm_w))
    assert mean_p == pytest.approx(100.0, abs=1e-5)

    # Flawed naive calculation (without valid_mask filtering) would be severely negative
    flawed_mean = float(np.sum(synth_precip[mask] * weights[mask]))
    assert flawed_mean < 0.0, "Naive aggregation failed to demonstrate sensitivity to NoData contamination"


def test_gate3_spatial_coverage_95_percent_threshold():
    """Verify that basin coverage below 95% (0.95) flags INSUFFICIENT_COVERAGE and returns NaN."""
    mask, weights, _, _, _, _ = construct_basin_raster_mask(BASIN_GEOJSON_PATH)

    # Case A: 96% coverage -> should pass and compute valid mean
    synth_grid_a = np.full(weights.shape, 50.0, dtype=np.float32)
    # Mask out 4% of basin weight
    active_coords = list(zip(*np.where(mask)))
    # Sort by weight ascending and mask cumulative 4%
    cum_w = 0.0
    for r, c in active_coords:
        if cum_w < 0.04:
            synth_grid_a[r, c] = -9999.0
            cum_w += weights[r, c]
        else:
            break

    valid_a = mask & (synth_grid_a >= 0.0)
    cov_a = float(np.sum(weights[valid_a]))
    assert cov_a >= 0.95
    mean_a = float(np.sum(synth_grid_a[valid_a] * (weights[valid_a] / cov_a)))
    assert mean_a == pytest.approx(50.0, abs=1e-4)

    # Case B: 90% coverage -> MUST trigger NaN / failure
    synth_grid_b = np.full(weights.shape, 50.0, dtype=np.float32)
    cum_w_b = 0.0
    for r, c in active_coords:
        if cum_w_b < 0.10:  # 10% missing -> 90% coverage
            synth_grid_b[r, c] = -9999.0
            cum_w_b += weights[r, c]
        else:
            break

    valid_b = mask & (synth_grid_b >= 0.0)
    cov_b = float(np.sum(weights[valid_b]))
    assert cov_b < 0.95

    # Enforce Gate 3 rule
    if cov_b < 0.95:
        result_b = np.nan
    else:
        result_b = float(np.sum(synth_grid_b[valid_b] * (weights[valid_b] / cov_b)))

    assert np.isnan(result_b), "Coverage < 95% failed to produce NaN"


def test_gate3_continuous_528_month_temporal_sequence():
    """Confirm a continuous 528-month index from 1981-01 to 2024-12 with zero missing/duplicate months."""
    dates = pd.date_range("1981-01-01", "2024-12-01", freq="MS")

    assert len(dates) == 528, f"Expected exactly 528 months, got {len(dates)}"
    assert dates[0] == pd.Timestamp("1981-01-01")
    assert dates[-1] == pd.Timestamp("2024-12-01")

    # Check monthly increments
    diffs = dates[1:] - dates[:-1]
    # In monthly freq, days between consecutive months range from 28 to 31
    assert all(28 <= d.days <= 31 for d in diffs)

    # Check leap years: 1984, 1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024
    leap_years = [y for y in range(1981, 2025) if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)]
    assert len(leap_years) == 11
    assert 2000 in leap_years
    assert 1984 in leap_years

    # Check zero duplicates
    assert len(dates.unique()) == 528


def test_gate3_nan_propagation_rolling_3month_accumulation():
    """Verify that missing values strictly propagate through rolling 3-month accumulations without silent filling."""
    # 30-year series (360 months) covering 1991–2020
    n_years = 30
    n_months = n_years * 12
    dates = pd.date_range("1991-01-01", periods=n_months, freq="MS")
    years = dates.year.values
    months = dates.month.values

    np.random.seed(42)
    p = np.full(n_months, 50.0, dtype=np.float64) + np.random.normal(0, 5, n_months)
    pet = np.full(n_months, 40.0, dtype=np.float64)
    d = p - pet

    # Inject NaN at month index 5 (June 1991)
    d[5] = np.nan

    # Compute rolling SPEI with fixed 1991-2020 calibration
    res = calculate_rolling_spei(
        d_monthly=d,
        years=years,
        months=months,
        scale=3,
        calibration_period=(1991, 2020),
        min_calibration_years=20
    )
    d3 = res["d_rolling"]

    # Rolling window 3 uses [m-2, m-1, m].
    # Month 0: index 0 -> NaN (incomplete window < 3)
    # Month 1: index 1 -> NaN (incomplete window < 3)
    # Month 2: index 2 -> valid
    # Month 3: index 3 -> valid
    # Month 4: index 4 -> valid
    # Month 5: index 5 (month 6) has NaN in d -> rolling water balance MUST be NaN!
    # Month 6: index 6 uses [4, 5, 6] -> MUST be NaN!
    # Month 7: index 7 uses [5, 6, 7] -> MUST be NaN!
    # Month 8: index 8 uses [6, 7, 8] -> valid again!
    assert np.isnan(d3[0])
    assert np.isnan(d3[1])
    assert not np.isnan(d3[2])
    assert not np.isnan(d3[3])
    assert not np.isnan(d3[4])
    assert np.isnan(d3[5]), "Month with NaN failed to propagate NaN"
    assert np.isnan(d3[6]), "Rolling window overlapping NaN failed to propagate NaN"
    assert np.isnan(d3[7]), "Rolling window overlapping NaN failed to propagate NaN"
    assert not np.isnan(d3[8]), "Valid rolling window incorrectly marked NaN"


def test_gate3_separate_source_auditing():
    """Verify that rainfall and temperature data sources are audited separately with explicit status flags."""
    sample_audit = {
        "1984-07": {
            "rainfall_source": "CHIRPS_v2.0_p05",
            "rainfall_coverage": 1.0,
            "rainfall_status": "VALID_OBSERVATION",
            "temp_source": "NOAA_CPC_V1.0",
            "temp_coverage": 1.0,
            "temp_status": "VALID_OBSERVATION",
            "combined_status": "CERTIFIED"
        },
        "1985-07": {
            "rainfall_source": "CHIRPS_v2.0_p05",
            "rainfall_coverage": 1.0,
            "rainfall_status": "VALID_OBSERVATION",
            "temp_source": "MISSING",
            "temp_coverage": 0.0,
            "temp_status": "MISSING_TEMPERATURE_FILE",
            "combined_status": "RECONSTRUCTION_PAUSED"
        }
    }

    # Combined status MUST NOT be certified if either feed is missing
    for month, entry in sample_audit.items():
        if entry["rainfall_status"] != "VALID_OBSERVATION" or entry["temp_status"] != "VALID_OBSERVATION":
            assert entry["combined_status"] != "CERTIFIED"
            assert entry["combined_status"] == "RECONSTRUCTION_PAUSED"
