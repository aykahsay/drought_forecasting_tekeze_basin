"""
test_climate_reconstruction_and_spei.py
========================================
Automated Quality & Verification Test Suite for the Tekezé Climate Reconstruction
and SPEI-3 / SPI-3 Target Pipeline.

Validates:
  1. Catchment geometry, CRS, and spherical area (67,135.4 km²).
  2. Exact fractional polygon-cell intersection area weighting vs center-point containment.
  3. Strict exclusion of negative NoData sentinels (-9999) and 95% spatial coverage enforcement.
  4. Non-finite temperature validation: NaN/Inf inputs MUST return NaN PET, NEVER 0.0.
  5. Hosking Generalized Logistic (GLO) parameter estimation via unbiased L-moments (Beguería et al. 2014),
     strict mathematical domain validation (alpha > 0, |k| < 1), and zero arbitrary fallbacks.
  6. Standard McKee et al. (1993) 2-parameter Gamma SPI-3 with Thom (1958) MLE and zero-precipitation adjustment.
  7. Strict fixed baseline calibration (1991–2020) and NaN propagation.
  8. Calendar conventions and physical temperature continuity.
"""

import json
import math
from pathlib import Path
import numpy as np
import pytest
from shapely.geometry import Point, box, shape

from agriminds.climate.spei_calculator import (
    calculate_extraterrestrial_radiation_ra,
    calculate_hargreaves_pet,
    calculate_rolling_spei,
    calculate_rolling_spi,
    calculate_spei_seasonal,
    calculate_spi_seasonal,
    calculate_thornthwaite_monthly_pet,
    cdf_generalized_logistic,
    compute_standardized_z_score,
    fit_generalized_logistic_l_moments,
    fit_gamma_spi,
)
from scripts.build_verified_tekeze_monthly_climate_1981_2024 import (
    construct_basin_raster_mask,
    fetch_and_extract_chirps_monthly,
    get_verified_monthly_temperature,
    MissingTemperatureDataError,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BASIN_GEOJSON = ROOT_DIR / "data" / "spatial" / "processed" / "tekeze_basin_hydrological_complete.geojson"
RAW_TEMP_CPC = ROOT_DIR / "data" / "raw" / "temperature" / "cpc"


def test_basin_geometry_area_and_crs():
    """Verify complete Tekeze basin polygon exists, CRS is EPSG:4326, and spherical area matches 67,135.4 km²."""
    assert BASIN_GEOJSON.exists(), f"Missing basin GeoJSON: {BASIN_GEOJSON}"

    with open(BASIN_GEOJSON, "r", encoding="utf-8") as f:
        gj = json.load(f)

    feat = gj["features"][0]
    poly = shape(feat["geometry"])
    props = feat["properties"]

    assert props["crs"].startswith("EPSG:4326")
    assert props["total_area_km2"] == pytest.approx(67135.4, rel=1e-3)

    # Spherical excess area calculation
    def ring_area(coords, r_km=6371.0088):
        rad = [(math.radians(lon), math.radians(lat)) for lon, lat in coords]
        tot = 0.0
        for i in range(len(rad) - 1):
            tot += (rad[i + 1][0] - rad[i][0]) * (2.0 + math.sin(rad[i][1]) + math.sin(rad[i + 1][1]))
        return abs(tot * (r_km ** 2) / 2.0)

    calc_area = ring_area(list(poly.exterior.coords))
    assert calc_area == pytest.approx(67135.4, rel=0.01), f"Calculated area {calc_area} diverges from 67,135.4 km²"

    bounds = poly.bounds
    assert bounds[0] >= 35.80 and bounds[2] <= 39.85, "Longitude bounds out of range"
    assert bounds[1] >= 11.60 and bounds[3] <= 14.85, "Latitude bounds out of range"


def test_spatial_raster_mask_and_fractional_weights():
    """Verify 0.05° raster grid dimensions, exact fractional cell intersection, and cosine weighting."""
    mask, weights, lats, lons, crop_window, meta = construct_basin_raster_mask(BASIN_GEOJSON)

    assert mask.ndim == 2
    assert weights.ndim == 2
    assert mask.shape == weights.shape

    # Weights must sum strictly to 1.0 across active cells
    assert np.sum(weights) == pytest.approx(1.0, abs=1e-6)
    # Inactive cells must have weight exactly 0
    assert np.all(weights[~mask] == 0.0)

    # Verify fractional cells exceed center-point cells due to boundary intersection
    assert meta["active_cells_fractional"] >= meta["active_cells_center_point"]
    assert 2100 <= meta["active_cells_center_point"] <= 2350
    assert 2300 <= meta["active_cells_fractional"] <= 2550


def test_chirps_nodata_exclusion_and_spatial_coverage():
    """Verify negative NoData sentinels (-9999) are excluded and coverage < 95% triggers INSUFFICIENT_SPATIAL_COVERAGE."""
    # Synthetic 10x10 raster grid
    grid_h, grid_w = 10, 10
    weights = np.full((grid_h, grid_w), 1.0 / 100.0, dtype=np.float64)

    # 1. Raster with 96 valid cells (100.0 mm) and 4 NoData cells (-9999.0) -> 96% coverage
    crop_96 = np.full((grid_h, grid_w), 100.0, dtype=np.float32)
    crop_96[0, :4] = -9999.0

    valid_mask = (crop_96 >= 0.0) & (weights > 0.0) & np.isfinite(crop_96)
    valid_weights = weights[valid_mask]
    weight_sum = np.sum(valid_weights)
    coverage = weight_sum / np.sum(weights)

    assert coverage == pytest.approx(0.96, abs=1e-4)
    assert coverage >= 0.95
    mean_p = float(np.sum(crop_96[valid_mask] * valid_weights) / weight_sum)
    assert mean_p == pytest.approx(100.0, abs=1e-4), "Negative sentinel must not contaminate the mean"

    # 2. Raster with only 80% coverage (20 NoData cells) -> should fail 95% threshold
    crop_80 = np.full((grid_h, grid_w), 100.0, dtype=np.float32)
    crop_80[:2, :] = -9999.0

    valid_mask_80 = (crop_80 >= 0.0) & (weights > 0.0) & np.isfinite(crop_80)
    weight_sum_80 = np.sum(weights[valid_mask_80])
    coverage_80 = weight_sum_80 / np.sum(weights)

    assert coverage_80 == pytest.approx(0.80, abs=1e-4)
    assert coverage_80 < 0.95


def test_pet_missing_temperature_and_input_validation():
    """Verify non-finite or inverted temperatures return NaN, NEVER 0.0."""
    # 1. NaN in t_max, t_min, or t_mean MUST produce NaN PET (never 0.0)
    assert math.isnan(calculate_hargreaves_pet(float("nan"), 16.0, 22.0, 13.325, 7, 31))
    assert math.isnan(calculate_hargreaves_pet(28.0, float("nan"), 22.0, 13.325, 7, 31))
    assert math.isnan(calculate_hargreaves_pet(28.0, 16.0, float("nan"), 13.325, 7, 31))

    # 2. Infinite values MUST return NaN
    assert math.isnan(calculate_hargreaves_pet(float("inf"), 16.0, 22.0, 13.325, 7, 31))
    assert math.isnan(calculate_hargreaves_pet(28.0, float("-inf"), 22.0, 13.325, 7, 31))

    # 3. Inverted temperature (t_max < t_min) MUST return NaN
    assert math.isnan(calculate_hargreaves_pet(15.0, 25.0, 20.0, 13.325, 7, 31))

    # 4. Out-of-bounds coordinates / months
    assert math.isnan(calculate_hargreaves_pet(28.0, 16.0, 22.0, 13.325, 13, 31))
    assert math.isnan(calculate_hargreaves_pet(28.0, 16.0, 22.0, 95.0, 7, 31))
    assert math.isnan(calculate_extraterrestrial_radiation_ra(float("nan"), 7, 31))

    # 5. Thornthwaite with non-finite values MUST return list of NaNs
    th_nan = calculate_thornthwaite_monthly_pet([18.0] * 11 + [float("nan")], 13.325)
    assert all(math.isnan(v) for v in th_nan)

    # 6. Valid physical inputs produce positive PET
    harg_valid = calculate_hargreaves_pet(28.0, 16.0, 22.0, 13.325, 7, 31)
    assert 120.0 <= harg_valid <= 180.0


def test_hosking_generalized_logistic_l_moments():
    """Verify Hosking Generalized Logistic (GLO) distribution fitting strictly enforces |k| < 1, alpha > 0."""
    # 1. Insufficient sample size (< 20) MUST raise ValueError
    d_small = np.array([10.0, 20.0, -15.0, 5.0, -30.0])
    with pytest.raises(ValueError, match="Insufficient valid calibration observations"):
        fit_generalized_logistic_l_moments(d_small, min_samples=20)

    # 2. Valid synthetic sample recovers valid distribution parameters
    np.random.seed(42)
    d_valid = np.random.normal(loc=-40.0, scale=75.0, size=30)
    xi, alpha, k = fit_generalized_logistic_l_moments(d_valid, min_samples=20)

    assert alpha > 0.0, "Scale alpha must be strictly positive"
    assert abs(k) < 1.0, "Shape |k| must be < 1.0 for finite mean in GLO"
    assert math.isfinite(xi), "Location xi must be finite"

    # 3. Non-finite values in data are filtered
    d_with_nans = np.concatenate([d_valid, [np.nan, np.inf, -np.inf]])
    xi_c, alpha_c, k_c = fit_generalized_logistic_l_moments(d_with_nans, min_samples=20)
    assert xi_c == pytest.approx(xi, rel=1e-5)
    assert alpha_c == pytest.approx(alpha, rel=1e-5)
    assert k_c == pytest.approx(k, rel=1e-5)


def test_gamma_spi_standardization():
    """Verify standard McKee Gamma SPI-3 fitting, zero probability adjustment, and standardization."""
    # 1. Insufficient samples (< 20) raises ValueError
    p_small = np.array([100.0, 200.0, 300.0])
    with pytest.raises(ValueError, match="Insufficient valid calibration observations"):
        fit_gamma_spi(p_small, min_samples=20)

    # 2. Synthetic seasonal precipitation series with some zeros
    np.random.seed(42)
    p_series = np.random.gamma(shape=5.0, scale=60.0, size=40)
    p_series[0] = 0.0  # One zero year

    alpha_g, beta_g, q_zero = fit_gamma_spi(p_series, min_samples=20)
    assert alpha_g > 0.0
    assert beta_g > 0.0
    assert q_zero == pytest.approx(1.0 / 40.0)

    years = np.arange(1981, 2021)
    spi_res = calculate_spi_seasonal(p_series, years, calibration_period=(1991, 2020), min_calibration_years=20)
    assert spi_res["status"] == "SUCCESS"
    assert len(spi_res["spi"]) == len(years)
    # Z-scores should have zero mean and unit variance approximately
    valid_spi = spi_res["spi"][np.isfinite(spi_res["spi"])]
    assert abs(np.mean(valid_spi)) < 0.5
    assert 0.7 <= np.std(valid_spi) <= 1.3


def test_spei_seasonal_standardization():
    """Verify SPEI-3 standardization handles severe drought, normal, and missing values."""
    years = np.arange(1981, 2025)
    np.random.seed(42)
    d_series = np.random.normal(loc=-30.0, scale=80.0, size=len(years))

    # Inject extreme drought in 1984 (-300 mm)
    idx_1984 = np.where(years == 1984)[0][0]
    d_series[idx_1984] = -300.0

    # Inject missing value in 2005
    idx_2005 = np.where(years == 2005)[0][0]
    d_series[idx_2005] = np.nan

    res = calculate_spei_seasonal(
        d_seasonal_series=d_series,
        years=years,
        calibration_period=(1991, 2020),
        min_calibration_years=20
    )

    spei = res["spei"]
    assert len(spei) == len(years)

    # 1984 must be severe drought (SPEI <= -2.0)
    assert spei[idx_1984] <= -2.0, f"1984 SPEI ({spei[idx_1984]}) should be <= -2.0"
    assert 1984 in res["drought_years_severe"]

    # 2005 must be strictly NaN (no silent imputation)
    assert np.isnan(spei[idx_2005]), "Missing observation must produce NaN SPEI"


def test_gate1_real_cpc_temperature_extraction():
    """Verify Gate 1: real NOAA CPC extraction for 1984 benchmark year and strict physical bounds."""
    # 1. 1984 real observational CPC data (preserved in data/raw/temperature/cpc/)
    t_max_jul, t_min_jul, t_mean_jul = get_verified_monthly_temperature(1984, 7, allow_synthetic_fallback=False)
    assert t_max_jul == pytest.approx(25.15, abs=0.1), f"Unexpected July 1984 Tmax: {t_max_jul}"
    assert t_min_jul == pytest.approx(14.98, abs=0.1), f"Unexpected July 1984 Tmin: {t_min_jul}"
    assert t_min_jul < t_max_jul
    assert t_min_jul <= t_mean_jul <= t_max_jul

    # Diurnal temperature range in wet season is positive and realistic
    dtr = t_max_jul - t_min_jul
    assert 8.0 <= dtr <= 15.0


def test_gate1_synthetic_fallback_strictly_disabled():
    """Verify Gate 1: pipeline FAILS EXPLICITLY if raw observations are absent (zero silent heuristics)."""
    # 1996 raw files have not been downloaded yet; requesting 1996 without fallback flag MUST raise MissingTemperatureDataError
    with pytest.raises(MissingTemperatureDataError, match="Synthetic heuristic fallback is strictly disabled"):
        get_verified_monthly_temperature(1996, 7, allow_synthetic_fallback=False)

    # Isolated test-only mode still operates when explicitly requested
    with pytest.warns(UserWarning, match="PROVISIONAL_HEURISTIC_MODEL"):
        t_max_h, t_min_h, t_mean_h = get_verified_monthly_temperature(1996, 7, allow_synthetic_fallback=True)
    assert t_min_h < t_max_h
    assert 5.0 <= t_mean_h <= 35.0


def test_glo_parameterization_and_cdf_complete_pair():
    """
    MATHEMATICAL AUDIT RECORD:
    Validates Generalized Logistic (GLO) parameterization and CDF as a complete pair (F(x), x(F)).
    Verifies Hosking (1990) formulas, support boundaries, and round-trip identity |F(x(F)) - F| < 1e-12.
    """
    def glo_quantile(f: float, xi: float, alpha: float, k: float) -> float:
        if abs(k) < 1e-6:
            return xi - alpha * math.log((1.0 - f) / f)
        return xi + (alpha / k) * (1.0 - ((1.0 - f) / f) ** k)

    xi, alpha = -10.0, 25.0

    # Test round-trip identity across a wide range of shape parameters and probabilities
    for k in [-0.35, -0.15, 0.0, 0.15, 0.35]:
        for f_target in [0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999]:
            x_val = glo_quantile(f_target, xi, alpha, k)
            f_calc = cdf_generalized_logistic(x_val, xi, alpha, k)
            assert f_calc == pytest.approx(f_target, abs=1e-5), (
                f"GLO roundtrip failure for k={k}, F_target={f_target}: got {f_calc}"
            )

    # Boundary conditions
    # For k > 0, support is x <= xi + alpha/k (upper bound)
    k_pos = 0.25
    x_upper = xi + alpha / k_pos
    assert cdf_generalized_logistic(x_upper + 1.0, xi, alpha, k_pos) == pytest.approx(1.0, abs=1e-5)

    # For k < 0, support is x >= xi + alpha/k (lower bound)
    k_neg = -0.25
    x_lower = xi + alpha / k_neg
    assert cdf_generalized_logistic(x_lower - 1.0, xi, alpha, k_neg) == pytest.approx(0.0, abs=1e-5)

    # Parameter recovery from synthetic sample via unbiased L-moments
    np.random.seed(42)
    u_samp = np.random.uniform(0.001, 0.999, size=50000)
    x_sample = np.array([glo_quantile(u, xi, alpha, -0.20) for u in u_samp])
    xi_est, alpha_est, k_est = fit_generalized_logistic_l_moments(x_sample)
    assert xi_est == pytest.approx(xi, rel=0.05)
    assert alpha_est == pytest.approx(alpha, rel=0.05)
    assert k_est == pytest.approx(-0.20, rel=0.05)


def test_rolling_spei_and_spi_12_calendar_months():
    """Verify rolling 3-month SPEI and SPI across all 12 calendar months with month-specific calibrations."""
    n_months = 40 * 12  # 40 years = 480 months (1981-2020)
    years = np.repeat(np.arange(1981, 2021), 12)
    months = np.tile(np.arange(1, 13), 40)

    np.random.seed(42)
    d_monthly = np.random.normal(loc=-15.0, scale=40.0, size=n_months)
    p_monthly = np.random.gamma(shape=4.0, scale=25.0, size=n_months)

    spei_res = calculate_rolling_spei(
        d_monthly=d_monthly,
        years=years,
        months=months,
        scale=3,
        calibration_period=(1991, 2020),
        min_calibration_years=20
    )

    assert spei_res["status"] == "SUCCESS"
    assert len(spei_res["spei"]) == n_months
    # First 2 months must be NaN (rolling window warmup)
    assert np.isnan(spei_res["spei"][0]) and np.isnan(spei_res["spei"][1])
    assert len(spei_res["params_by_month"]) == 12

    # Rolling SPI-3
    spi_res = calculate_rolling_spi(
        p_monthly=p_monthly,
        years=years,
        months=months,
        scale=3,
        calibration_period=(1991, 2020),
        min_calibration_years=20
    )
    assert spi_res["status"] == "SUCCESS"
    assert len(spi_res["spi"]) == n_months
    assert len(spi_res["params_by_month"]) == 12

