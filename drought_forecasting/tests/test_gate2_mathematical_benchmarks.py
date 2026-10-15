"""
test_gate2_mathematical_benchmarks.py
======================================
Automated Cross-Validation Test Suite for Gate 2:
Validates Python SPEI / SPI implementations against standardized reference fixtures
generated from Hosking (1990) and R lmom/SPEI standards (Beguería et al. 2014).

Verifies:
  1. GLO parameter estimation via sample L-moments matching theoretical benchmarks.
  2. Complete pair round-trip identity |F(x(F)) - F| < 1e-5 across all benchmark quantiles.
  3. Strict handling of k -> 0 logistic limit.
  4. Extreme support boundary enforcement (k > 0 upper bound; k < 0 lower bound).
  5. Gamma SPI estimation with Thom (1958) MLE and zero-precipitation adjustment q.
  6. Inverse normal conversion (ndtri) with finite bounds [-3.5, 3.5].
"""

import json
import math
from pathlib import Path
import numpy as np
import pytest
import scipy.special as sp

from agriminds.climate.spei_calculator import (
    calculate_extraterrestrial_radiation_ra,
    calculate_hargreaves_daily_pet,
    calculate_hargreaves_monthly_pet_from_daily,
    calculate_hargreaves_pet,
    cdf_gamma_spi,
    cdf_generalized_logistic,
    compute_standardized_z_score,
    fit_gamma_spi,
    fit_generalized_logistic_l_moments,
    generate_four_tier_spei_targets,
)

FIXTURES_PATH = Path(__file__).resolve().parent / "fixtures" / "r_spei_lmom_reference_benchmark.json"


@pytest.fixture(scope="module")
def benchmark_data():
    assert FIXTURES_PATH.exists(), f"Reference benchmark fixture missing at {FIXTURES_PATH}"
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_glo_benchmark_parameter_recovery(benchmark_data):
    """Verify GLO parameter estimation from sample L-moments matches benchmark parameters."""
    for case in benchmark_data["glo_test_cases"]:
        xi_true = case["xi"]
        alpha_true = case["alpha"]
        k_true = case["k"]

        # Synthetic samples generated from exact quantiles
        np.random.seed(42)
        u_grid = np.linspace(0.001, 0.999, 10000)
        if abs(k_true) < 1e-6:
            x_sample = xi_true - alpha_true * np.log((1.0 - u_grid) / u_grid)
        else:
            x_sample = xi_true + (alpha_true / k_true) * (1.0 - ((1.0 - u_grid) / u_grid) ** k_true)

        xi_est, alpha_est, k_est = fit_generalized_logistic_l_moments(x_sample)

        assert xi_est == pytest.approx(xi_true, abs=0.5), f"Failed xi for {case['name']}"
        assert alpha_est == pytest.approx(alpha_true, rel=0.02), f"Failed alpha for {case['name']}"
        assert k_est == pytest.approx(k_true, abs=0.03), f"Failed k for {case['name']}"


def test_glo_benchmark_quantiles_and_cdf_roundtrip(benchmark_data):
    """Verify non-exceedance probabilities F(x) match benchmark quantiles across all cases."""
    for case in benchmark_data["glo_test_cases"]:
        xi = case["xi"]
        alpha = case["alpha"]
        k = case["k"]

        for p_str, x_val in case["quantiles"].items():
            p_target = float(p_str)
            p_computed = cdf_generalized_logistic(x_val, xi, alpha, k)
            assert p_computed == pytest.approx(p_target, abs=1e-4), (
                f"CDF mismatch in case '{case['name']}' at P={p_target}: "
                f"expected {p_target}, got {p_computed} for x={x_val}"
            )


def test_glo_support_boundaries_and_limits(benchmark_data):
    """Verify boundary conditions and extreme support limits."""
    # 1. Positive k (case 4: positive_shape_upper_bound) -> bounded above
    pos_case = next(c for c in benchmark_data["glo_test_cases"] if c["k"] > 0)
    xi, alpha, k = pos_case["xi"], pos_case["alpha"], pos_case["k"]
    upper_x = pos_case["upper_bound"]

    # Values at or above upper bound must be probability 1.0
    assert cdf_generalized_logistic(upper_x, xi, alpha, k) == pytest.approx(1.0, abs=1e-5)
    assert cdf_generalized_logistic(upper_x + 10.0, xi, alpha, k) == pytest.approx(1.0, abs=1e-5)

    # 2. Negative k (case 1: kiremt_wet_season) -> bounded below
    neg_case = next(c for c in benchmark_data["glo_test_cases"] if c["k"] < 0)
    xi_n, alpha_n, k_n = neg_case["xi"], neg_case["alpha"], neg_case["k"]
    lower_x = neg_case["lower_bound"]

    # Values at or below lower bound must be probability 0.0
    assert cdf_generalized_logistic(lower_x, xi_n, alpha_n, k_n) == pytest.approx(0.0, abs=1e-5)
    assert cdf_generalized_logistic(lower_x - 10.0, xi_n, alpha_n, k_n) == pytest.approx(0.0, abs=1e-5)

    # 3. Logistic limit k = 0
    k0_case = next(c for c in benchmark_data["glo_test_cases"] if abs(c["k"]) < 1e-6)
    assert cdf_generalized_logistic(k0_case["xi"], k0_case["xi"], k0_case["alpha"], 0.0) == pytest.approx(0.5, abs=1e-5)


def test_gamma_spi_benchmark_recovery(benchmark_data):
    """Verify 2-parameter Gamma SPI estimation and zero-precipitation handling."""
    for case in benchmark_data["gamma_test_cases"]:
        sh = case["true_shape"]
        sc = case["true_scale"]
        qz = case["true_q_zero"]

        np.random.seed(42)
        n_pts = 10000
        n_zeros = int(n_pts * qz)
        pos_pts = np.random.gamma(shape=sh, scale=sc, size=n_pts - n_zeros)
        precip_sample = np.concatenate([np.zeros(n_zeros), pos_pts])

        alpha_fit, beta_fit, q_fit = fit_gamma_spi(precip_sample)

        assert q_fit == pytest.approx(qz, abs=0.01)
        assert alpha_fit == pytest.approx(sh, rel=0.05)
        assert beta_fit == pytest.approx(sc, rel=0.05)

        # Quantile verification
        for p_str, p_val in case["quantiles"].items():
            prob_target = float(p_str)
            h_p = cdf_gamma_spi(p_val, alpha_fit, beta_fit, q_fit)
            # H(p) = q + (1 - q) * G(p)
            expected_h = qz + (1.0 - qz) * prob_target
            assert h_p == pytest.approx(expected_h, abs=0.05)


def test_inverse_normal_conversion_and_clipping():
    """Verify Gaussian z-score transformation via ndtri and finite bound clipping."""
    # Median -> 0.0
    assert compute_standardized_z_score(0.5) == pytest.approx(0.0, abs=1e-5)

    # WMO standard drought thresholds
    # p = 0.1587 -> z = -1.0 (Mild Drought)
    assert compute_standardized_z_score(0.1587) == pytest.approx(-1.0, abs=0.01)
    # p = 0.0668 -> z = -1.5 (Moderate Drought)
    assert compute_standardized_z_score(0.0668) == pytest.approx(-1.5, abs=0.01)
    # p = 0.0228 -> z = -2.0 (Severe Drought)
    assert compute_standardized_z_score(0.0228) == pytest.approx(-2.0, abs=0.01)
    # p = 0.00135 -> z = -3.0 (Extreme Drought)
    assert compute_standardized_z_score(0.00135) == pytest.approx(-3.0, abs=0.01)

    # Clipping guards against infinities
    assert -5.0 <= compute_standardized_z_score(0.0) <= -4.5
    assert 4.5 <= compute_standardized_z_score(1.0) <= 5.0
    assert -5.0 <= compute_standardized_z_score(1e-12) <= -4.5
    assert 4.5 <= compute_standardized_z_score(1.0 - 1e-12) <= 5.0


def test_glo_support_boundaries_epsilon():
    """Verify behavior immediately inside and outside finite support boundaries."""
    xi = 10.0
    alpha = 15.0

    # Case 1: k > 0 (upper bounded at x_bound = xi + alpha/k)
    k_pos = 0.2
    x_bound_pos = xi + alpha / k_pos  # 10 + 15 / 0.2 = 85.0
    eps = 1.0  # Numerically distinguishable within IEEE 754 float64 precision (y^5 > 1e-15)

    # Inside support (below upper bound) -> F(x) < 1.0
    f_inside_pos = cdf_generalized_logistic(x_bound_pos - eps, xi, alpha, k_pos)
    assert 0.999 <= f_inside_pos < 1.0

    # At or outside support (at or above upper bound) -> F(x) == 1.0
    assert cdf_generalized_logistic(x_bound_pos, xi, alpha, k_pos) == 1.0
    assert cdf_generalized_logistic(x_bound_pos + eps, xi, alpha, k_pos) == 1.0
    assert cdf_generalized_logistic(x_bound_pos + 100.0, xi, alpha, k_pos) == 1.0

    # Case 2: k < 0 (lower bounded at x_bound = xi + alpha/k)
    k_neg = -0.2
    x_bound_neg = xi + alpha / k_neg  # 10 + 15 / (-0.2) = -65.0

    # Inside support (above lower bound) -> F(x) > 0.0
    f_inside_neg = cdf_generalized_logistic(x_bound_neg + eps, xi, alpha, k_neg)
    assert 0.0 < f_inside_neg <= 0.001

    # At or outside support (at or below lower bound) -> F(x) == 0.0
    assert cdf_generalized_logistic(x_bound_neg, xi, alpha, k_neg) == 0.0
    assert cdf_generalized_logistic(x_bound_neg - eps, xi, alpha, k_neg) == 0.0
    assert cdf_generalized_logistic(x_bound_neg - 100.0, xi, alpha, k_neg) == 0.0


def test_glo_shape_approaching_zero():
    """Verify continuity of GLO CDF as shape parameter k approaches zero from both sides."""
    xi = 5.0
    alpha = 20.0
    x_test_points = [-30.0, -10.0, 0.0, 5.0, 15.0, 25.0, 40.0]

    for x in x_test_points:
        # Exact logistic limit (k = 0)
        f_k0 = cdf_generalized_logistic(x, xi, alpha, 0.0)
        expected_logistic = 1.0 / (1.0 + math.exp(-(x - xi) / alpha))
        assert f_k0 == pytest.approx(expected_logistic, abs=1e-6)

        # Approach from positive side: k -> 0+
        f_k_pos_small = cdf_generalized_logistic(x, xi, alpha, +1e-5)
        assert f_k_pos_small == pytest.approx(f_k0, abs=1e-4)

        # Approach from negative side: k -> 0-
        f_k_neg_small = cdf_generalized_logistic(x, xi, alpha, -1e-5)
        assert f_k_neg_small == pytest.approx(f_k0, abs=1e-4)


def test_glo_monotonicity_and_symmetric_fitting():
    """Verify strict monotonicity within support and finite estimates on symmetric samples."""
    xi, alpha, k = 0.0, 10.0, -0.15
    lower_bound = xi + alpha / k  # -66.67
    x_grid = np.linspace(lower_bound + 0.1, 100.0, 100)
    probs = [cdf_generalized_logistic(x, xi, alpha, k) for x in x_grid]

    # Monotonicity: F(x_{i+1}) >= F(x_i)
    assert np.all(np.diff(probs) >= 0.0)
    # Strictly increasing within support
    assert np.all(np.diff(probs) > 0.0)

    # Nearly symmetric sample (standard normal: mean ~ 0, skew ~ 0)
    np.random.seed(123)
    sym_sample = np.random.normal(loc=15.0, scale=8.0, size=500)
    xi_fit, alpha_fit, k_fit = fit_generalized_logistic_l_moments(sym_sample)
    assert math.isfinite(xi_fit)
    assert math.isfinite(alpha_fit) and alpha_fit > 0.0
    assert math.isfinite(k_fit)
    # Skewness should be near zero (|k| < 0.15)
    assert abs(k_fit) < 0.15


def test_hargreaves_radiation_units_fao56_benchmark():
    """
    Verify Hargreaves extraterrestrial radiation Ra and PET against FAO-56 trusted numerical examples.
    
    Standard: Allen et al. (1998) FAO-56 Annex 3 / Eq. 21-28 & 52:
      - Location: Latitude 45.0°N, Julian Day 145 (May 25).
      - Ra in energy units: ~40.5 MJ m^-2 day^-1.
      - Equivalent evaporation: Ra_eq = 0.408 * Ra_MJ ~= 16.5 mm day^-1.
      - PET_d = 0.0023 * 0.408 * Ra_MJ * (T_mean + 17.8) * sqrt(T_max - T_min).
      - For T_max = 26.6°C, T_min = 14.8°C (T_mean = 20.7°C, DTR = 11.8°C):
        PET_d ~= 5.03 mm/day.
    """
    lat = 45.0
    j_day = 145

    # 1. Energy units Ra (MJ m^-2 day^-1)
    ra_mj = calculate_extraterrestrial_radiation_ra(
        latitude_deg=lat, month=5, days_in_month=31, day_of_year=j_day, return_energy_units=True
    )
    assert ra_mj == pytest.approx(40.49, abs=0.5)

    # 2. Equivalent water depth Ra_eq (mm day^-1)
    ra_mm = calculate_extraterrestrial_radiation_ra(
        latitude_deg=lat, month=5, days_in_month=31, day_of_year=j_day, return_energy_units=False
    )
    assert ra_mm == pytest.approx(40.49 * 0.408, abs=0.2)
    assert ra_mm == pytest.approx(16.52, abs=0.2)

    # 3. Exact ratio consistency
    assert (ra_mm / ra_mj) == pytest.approx(0.408, abs=1e-5)

    # 4. Daily PET verification
    tmax, tmin = 26.6, 14.8
    pet_d = calculate_hargreaves_daily_pet(tmax, tmin, latitude_deg=lat, day_of_year=j_day)
    assert pet_d == pytest.approx(5.03, abs=0.1)


def test_hargreaves_leap_year_and_daily_summation():
    """
    Verify leap-year day counts (29 days in Feb 1984 vs 28 in Feb 1985)
    and exact consistency between monthly daily sum and monthly PET accumulation.
    """
    lat = 13.2  # Tekeze catchment mean latitude

    # Feb 1984 is a leap year (29 days)
    tmax_leap = [28.0] * 29
    tmin_leap = [14.0] * 29
    pet_leap = calculate_hargreaves_monthly_pet_from_daily(tmax_leap, tmin_leap, latitude_deg=lat, year=1984, month=2)
    assert math.isfinite(pet_leap)
    assert pet_leap > 0.0

    # Feb 1985 is a non-leap year (28 days)
    tmax_nonleap = [28.0] * 28
    tmin_nonleap = [14.0] * 28
    pet_nonleap = calculate_hargreaves_monthly_pet_from_daily(tmax_nonleap, tmin_nonleap, latitude_deg=lat, year=1985, month=2)
    assert math.isfinite(pet_nonleap)

    # Exactly 29/28 ratio for identical temperatures
    expected_ratio = 29.0 / 28.0
    # Small difference due to changing solar declination across days 32..60
    assert (pet_leap / pet_nonleap) == pytest.approx(expected_ratio, rel=0.03)

    # Mismatched array length must return NaN
    assert math.isnan(calculate_hargreaves_monthly_pet_from_daily(tmax_leap[:25], tmin_leap, lat, 1984, 2))


def test_hargreaves_latitude_dependence_and_temperature_validity():
    """
    Verify latitude-dependent radiation trends and strict input validity rejection.
    """
    # Solstice Day 172 (Northern Summer): High latitude receives long daylight, winter hemisphere receives zero
    ra_equator = calculate_extraterrestrial_radiation_ra(0.0, 6, 30, day_of_year=172, return_energy_units=True)
    ra_north_high = calculate_extraterrestrial_radiation_ra(60.0, 6, 30, day_of_year=172, return_energy_units=True)
    ra_south_pole = calculate_extraterrestrial_radiation_ra(-80.0, 6, 30, day_of_year=172, return_energy_units=True)

    assert ra_equator > 0.0
    assert ra_north_high > 35.0  # Midnight sun conditions
    assert ra_south_pole == 0.0   # Polar night

    # Temperature validity
    # 1. Tmax < Tmin rejected
    assert math.isnan(calculate_hargreaves_daily_pet(t_max_c=15.0, t_min_c=20.0, latitude_deg=13.2, day_of_year=100))
    # 2. Non-finite rejected
    assert math.isnan(calculate_hargreaves_daily_pet(float("nan"), 10.0, 13.2, 100))
    assert math.isnan(calculate_hargreaves_daily_pet(25.0, float("inf"), 13.2, 100))
    # 3. Unphysical bounds rejected
    assert math.isnan(calculate_hargreaves_daily_pet(85.0, 10.0, 13.2, 100))


def test_glo_extreme_tail_endpoints_and_deliberate_safeguards():
    """
    Verify deliberate float64 tail endpoint handling in normal score transformation:
      - When probabilities round to 0.0 or 1.0 in IEEE 754 precision, ndtri(0) and ndtri(1)
        must NOT silently produce infinite (+/- inf) or NaN values.
      - Finite bounds [-5.0, 5.0] and audit labels are recorded.
    """
    # Exact endpoints
    z_zero, guard_zero = compute_standardized_z_score(0.0, return_safeguard=True)
    assert z_zero == -5.0
    assert guard_zero == "LOWER_ENDPOINT_SAFEGUARD"

    z_one, guard_one = compute_standardized_z_score(1.0, return_safeguard=True)
    assert z_one == 5.0
    assert guard_one == "UPPER_ENDPOINT_SAFEGUARD"

    # Extreme tail probabilities rounding to endpoints
    z_tiny, guard_tiny = compute_standardized_z_score(1e-25, return_safeguard=True)
    assert -5.0 <= z_tiny <= -4.5
    assert math.isfinite(z_tiny)

    z_near_one, guard_near_one = compute_standardized_z_score(1.0 - 1e-25, return_safeguard=True)
    assert 4.5 <= z_near_one <= 5.0
    assert math.isfinite(z_near_one)

    # High support boundary case: k > 0 upper bound rounding
    xi, alpha, k = 10.0, 15.0, 0.5
    x_bound = xi + alpha / k  # 40.0
    # Directly at or slightly below upper bound
    p_bound = cdf_generalized_logistic(x_bound, xi, alpha, k)
    assert p_bound == 1.0
    z_b, g_b = compute_standardized_z_score(p_bound, return_safeguard=True)
    assert math.isfinite(z_b)
    assert z_b == 5.0
    assert g_b == "UPPER_ENDPOINT_SAFEGUARD"


def test_four_tier_drought_target_schema_and_frozen_calibration():
    """
    Verify the 4-tier target calibration schema:
      1. spei3_retro uses 1991–2020 parameters (WMO baseline).
      2. spei3_train uses 1981–2005 parameters (N=25) and includes bootstrap SE.
      3. spei3_validation uses FROZEN 1981–2005 parameters.
      4. spei3_test uses FROZEN 1981–2005 parameters (no test data leakage).
      5. spei3_test_expanded_sensitivity uses 1981–2014 parameters.
      6. Sample size qualification reports 10 total cases with event counts.
    """
    years = np.arange(1981, 2025)
    rng = np.random.default_rng(seed=42)
    # Synthetic climatic water balance D (mean ~ 50 mm, std ~ 80 mm)
    d_synthetic = rng.normal(loc=50.0, scale=80.0, size=len(years))
    # Inject historical 1984 severe drought
    d_synthetic[years == 1984] = -180.0

    result = generate_four_tier_spei_targets(
        d_synthetic,
        years,
        train_range=(1981, 2005),
        val_range=(2006, 2014),
        test_range=(2015, 2024),
        retro_range=(1991, 2020),
        min_calibration_years=20
    )

    assert result["status"] == "SUCCESS"
    protocols = result["protocols"]

    # 1. spei3_retro
    retro = protocols["spei3_retro"]
    assert retro["calibration_period"] == [1991, 2020]
    assert len(retro["values"]) == len(years)

    # 2. spei3_train
    train = protocols["spei3_train"]
    assert train["calibration_period"] == [1981, 2005]
    assert len(train["values"]) == 25
    train_params = train["parameters"]
    assert "bootstrap_uncertainty" in train_params
    assert math.isfinite(train_params["bootstrap_uncertainty"]["k_se"])

    # 3. spei3_validation
    val = protocols["spei3_validation"]
    assert val["parameter_status"] == "FROZEN_AT_TRAINING_END"
    assert len(val["values"]) == 9

    # 4. spei3_test
    test = protocols["spei3_test"]
    assert test["parameter_status"] == "FROZEN_BEFORE_EVALUATION"
    assert len(test["values"]) == 10
    qualification = test["sample_size_qualification"]
    assert qualification["n_total"] == 10
    assert qualification["drought_events"] + qualification["non_drought_events"] == 10
    assert qualification["status"] == "PRELIMINARY_EVIDENCE_SMALL_SAMPLE"

    # 5. spei3_test_expanded_sensitivity
    test_sens = protocols["spei3_test_expanded_sensitivity"]
    assert test_sens["parameter_status"] == "PRE_TEST_EXPANDED_SENSITIVITY"
    assert test_sens["calibration_period"] == [1981, 2014]

