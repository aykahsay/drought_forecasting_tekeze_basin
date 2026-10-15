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
    calculate_rolling_spei,
    cdf_gamma_spi,
    cdf_generalized_logistic,
    check_glo_goodness_of_fit,
    compare_safeguard_cap_vs_robust_log_transformation,
    compute_robust_glo_z_score,
    compute_standardized_z_score,
    fit_gamma_spi,
    fit_generalized_logistic_l_moments,
    generate_four_tier_spei_targets,
    log_cdf_generalized_logistic,
    log_survival_generalized_logistic,
    quantile_generalized_logistic,
    summarize_safeguard_occurrences,
    summarize_safeguards_by_month_and_split,
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
    Verify Hargreaves extraterrestrial radiation Ra and PET against independent published reference calculations.
    
    Published Reference Benchmarks (Allen et al. 1998 FAO-56 Table 2.6 & Eq. 52):
      Case 1 (Mid-latitude):
        - Location: Latitude 45.0°N, Julian Day 145 (May 25).
        - Published FAO-56 Table 2.6: Ra = 40.5 MJ m^-2 day^-1; Ra_eq = 16.5 mm day^-1.
        - Temperatures: T_max = 26.6°C, T_min = 14.8°C (T_mean = 20.7°C, DTR = 11.8°C).
        - Published reference ET0: 5.0 mm/day.
      
      Case 2 (Tropical / Northern Ethiopia Tekeze Catchment Analog):
        - Location: Latitude 13.0°N, Julian Day 196 (July 15).
        - Published FAO-56 Table 2.6: Ra = 37.9 MJ m^-2 day^-1; Ra_eq = 15.5 mm day^-1.
        - Temperatures: T_max = 31.0°C, T_min = 19.0°C (T_mean = 25.0°C, DTR = 12.0°C).
        - Published reference calculation: ET0 = 0.0023 * 15.5 * (25.0 + 17.8) * sqrt(12.0) = 5.28 mm/day.
    """
    # Case 1: Mid-latitude benchmark
    lat_mid = 45.0
    j_mid = 145
    fao_ra_mj_mid = 40.5
    fao_ra_mm_mid = 16.5
    fao_et0_mid = 5.0

    calc_ra_mj_mid = calculate_extraterrestrial_radiation_ra(
        latitude_deg=lat_mid, month=5, days_in_month=31, day_of_year=j_mid, return_energy_units=True
    )
    calc_ra_mm_mid = calculate_extraterrestrial_radiation_ra(
        latitude_deg=lat_mid, month=5, days_in_month=31, day_of_year=j_mid, return_energy_units=False
    )
    calc_pet_mid = calculate_hargreaves_daily_pet(26.6, 14.8, latitude_deg=lat_mid, day_of_year=j_mid)

    assert calc_ra_mj_mid == pytest.approx(fao_ra_mj_mid, abs=0.5)
    assert calc_ra_mm_mid == pytest.approx(fao_ra_mm_mid, abs=0.3)
    assert calc_pet_mid == pytest.approx(fao_et0_mid, abs=0.1)

    # Case 2: Tropical Tekeze catchment benchmark (13.0°N, July 15)
    lat_trop = 13.0
    j_trop = 196
    fao_ra_mj_trop = 37.9
    fao_ra_mm_trop = 15.5
    fao_et0_trop = 5.28

    calc_ra_mj_trop = calculate_extraterrestrial_radiation_ra(
        latitude_deg=lat_trop, month=7, days_in_month=31, day_of_year=j_trop, return_energy_units=True
    )
    calc_ra_mm_trop = calculate_extraterrestrial_radiation_ra(
        latitude_deg=lat_trop, month=7, days_in_month=31, day_of_year=j_trop, return_energy_units=False
    )
    calc_pet_trop = calculate_hargreaves_daily_pet(31.0, 19.0, latitude_deg=lat_trop, day_of_year=j_trop)

    assert calc_ra_mj_trop == pytest.approx(fao_ra_mj_trop, abs=0.5)
    assert calc_ra_mm_trop == pytest.approx(fao_ra_mm_trop, abs=0.3)
    assert calc_pet_trop == pytest.approx(fao_et0_trop, abs=0.15)


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
    assert "goodness_of_fit_diagnostics" in retro
    assert math.isfinite(retro["goodness_of_fit_diagnostics"]["kolmogorov_smirnov"]["statistic"])
    assert "safeguard_summary" in retro
    assert retro["safeguard_summary"]["total_evaluations"] == len(years)

    # 2. spei3_train
    train = protocols["spei3_train"]
    assert train["calibration_period"] == [1981, 2005]
    assert len(train["values"]) == 25
    train_params = train["parameters"]
    assert "bootstrap_uncertainty" in train_params
    assert math.isfinite(train_params["bootstrap_uncertainty"]["k_se"])
    assert "goodness_of_fit_diagnostics" in train
    assert train["goodness_of_fit_diagnostics"]["support_violations_count"] == 0
    assert "safeguard_summary" in train
    assert train["safeguard_summary"]["total_evaluations"] == 25

    # 3. spei3_validation
    val = protocols["spei3_validation"]
    assert val["parameter_status"] == "FROZEN_AT_TRAINING_END"
    assert len(val["values"]) == 9
    assert "safeguard_summary" in val

    # 4. spei3_test
    test = protocols["spei3_test"]
    assert test["parameter_status"] == "FROZEN_BEFORE_EVALUATION"
    assert len(test["values"]) == 10
    qualification = test["sample_size_qualification"]
    assert qualification["n_total"] == 10
    assert qualification["drought_events"] + qualification["non_drought_events"] == 10
    assert qualification["status"] == "PRELIMINARY_EVIDENCE_SMALL_SAMPLE"
    assert test["tail_safeguard_categorical_invariance"] is True
    assert "safeguard_summary" in test

    # 5. spei3_test_expanded_sensitivity
    test_sens = protocols["spei3_test_expanded_sensitivity"]
    assert test_sens["parameter_status"] == "PRE_TEST_EXPANDED_SENSITIVITY"
    assert test_sens["calibration_period"] == [1981, 2014]
    assert "goodness_of_fit_diagnostics" in test_sens
    assert "safeguard_summary" in test_sens


def test_endpoint_safeguard_categorical_invariance():
    """
    Verify that the +/- 5.0 tail safeguard is categorically invariant:
    Drought thresholds (SPEI <= -1.0, -1.5, -2.0) are completely unaffected
    by whether extreme probabilities (e.g. p = 0 or p = 1e-15) are mapped to -5.0
    or evaluated via an unbounded asymptotic normal tail expansion.
    """
    test_probabilities = [0.0, 1e-25, 1e-12, 1e-6, 0.02, 0.05, 0.15, 0.50, 0.85, 0.999, 1.0]

    for p in test_probabilities:
        z_capped = compute_standardized_z_score(p, tail_bound=5.0)

        # Unbounded asymptotic approximation
        if p <= 0.0:
            z_asymptotic = -float("inf")
        elif p >= 1.0:
            z_asymptotic = float("inf")
        else:
            z_asymptotic = float(sp.ndtri(p))

        # Test categorical classification invariance:
        # 1. Extreme Drought (threshold -2.0)
        is_severe_capped = (z_capped <= -2.0)
        is_severe_asympt = (z_asymptotic <= -2.0)
        assert is_severe_capped == is_severe_asympt, f"Mismatch at p={p}"

        # 2. Moderate Drought (threshold -1.5)
        is_mod_capped = (z_capped <= -1.5)
        is_mod_asympt = (z_asymptotic <= -1.5)
        assert is_mod_capped == is_mod_asympt, f"Mismatch at p={p}"

        # 3. Mild Drought (threshold -1.0)
        is_mild_capped = (z_capped <= -1.0)
        is_mild_asympt = (z_asymptotic <= -1.0)
        assert is_mild_capped == is_mild_asympt, f"Mismatch at p={p}"


def test_hargreaves_published_reference_direct_calculation():
    """
    Independently verifies Hargreaves ET0 against published FAO-56 reference values
    using directly supplied extraterrestrial radiation, completely bypassing internal
    solar radiation helper functions.

    Published Reference 1 (Allen et al. 1998 FAO-56 Table 2.6 & Example 14):
      - Lat 45°N, Julian day 145 (May 25).
      - Published Ra = 40.5 MJ m^-2 day^-1 (Ra_eq = 16.5 mm day^-1).
      - T_max = 26.6°C, T_min = 14.8°C (T_mean = 20.7°C, DTR = 11.8°C).
      - Published analytical ET0:
          ET0 = 0.0023 * (0.408 * 40.5) * (20.7 + 17.8) * sqrt(11.8) = 5.03 mm/day.
      - With Ra_eq = 16.5 mm/day:
          ET0 = 0.0023 * 16.5 * (20.7 + 17.8) * sqrt(11.8) = 5.02 mm/day.

    Published Reference 2 (Tropical Tekeze Basin Analog):
      - Lat 13°N, Julian day 196 (July 15).
      - Published Ra = 37.9 MJ m^-2 day^-1.
      - T_max = 31.0°C, T_min = 19.0°C (T_mean = 25.0°C, DTR = 12.0°C).
      - Published analytical ET0:
          ET0 = 0.0023 * (0.408 * 37.9) * (25.0 + 17.8) * sqrt(12.0) = 5.28 mm/day.
    """
    # Test 1a: Direct call with user-supplied ra_mj (40.5 MJ m^-2 day^-1)
    pet_mj = calculate_hargreaves_daily_pet(
        t_max_c=26.6, t_min_c=14.8, latitude_deg=45.0, day_of_year=145, ra_mj=40.5
    )
    assert pet_mj == pytest.approx(5.03, abs=0.02)

    # Test 1b: Direct call with user-supplied ra_mm_day (16.5 mm/day)
    pet_mm = calculate_hargreaves_daily_pet(
        t_max_c=26.6, t_min_c=14.8, latitude_deg=45.0, day_of_year=145, ra_mm_day=16.5
    )
    assert pet_mm == pytest.approx(5.02, abs=0.02)

    # Test 2: Direct call for tropical Tekeze analog (13°N)
    pet_trop_direct = calculate_hargreaves_daily_pet(
        t_max_c=31.0, t_min_c=19.0, latitude_deg=13.0, day_of_year=196, ra_mj=37.9
    )
    assert pet_trop_direct == pytest.approx(5.28, abs=0.02)

    # Test 3: Monthly calculation with user-supplied radiation
    pet_month = calculate_hargreaves_pet(
        t_max_c=26.6, t_min_c=14.8, t_mean_c=20.7, latitude_deg=45.0, month=5, days_in_month=31, ra_mj=40.5
    )
    assert pet_month == pytest.approx(5.03 * 31, abs=0.5)


def test_glo_log_cdf_and_robust_z_score():
    """
    Verify numerical stability and asymptotic accuracy of log-CDF, log-survival,
    and uncapped robust z-score transformation via scipy.special.ndtri_exp.
    """
    xi, alpha, k = 10.0, 15.0, -0.15
    lower_bound = xi + alpha / k  # -90.0

    # Inside support normal range (x = 20.0)
    log_p = log_cdf_generalized_logistic(20.0, xi, alpha, k)
    p_direct = cdf_generalized_logistic(20.0, xi, alpha, k)
    assert math.exp(log_p) == pytest.approx(p_direct, rel=1e-8)

    # Survival function identity: exp(log_p) + exp(log_s) == 1.0
    log_s = log_survival_generalized_logistic(20.0, xi, alpha, k)
    assert (math.exp(log_p) + math.exp(log_s)) == pytest.approx(1.0, rel=1e-7)

    # Robust score matches standard z-score in central domain
    z_robust, flag_r = compute_robust_glo_z_score(20.0, xi, alpha, k)
    z_std, flag_s = compute_standardized_z_score(p_direct, return_safeguard=True)
    assert z_robust == pytest.approx(z_std, abs=1e-5)
    assert flag_s == "NONE"

    # Extreme lower tail approaching support bound
    x_tail = lower_bound + 5.0  # -85.0
    log_p_tail = log_cdf_generalized_logistic(x_tail, xi, alpha, k)
    assert log_p_tail < -15.0
    z_tail, flag_tail = compute_robust_glo_z_score(x_tail, xi, alpha, k, extended_tail_bound=10.0)
    assert z_tail < -5.0  # Extends past the 5.0 operational cap without clipping (~ -5.87)
    assert flag_tail == "EXACT_LOG_CDF"

    # Deep tail near bound (x = lower_bound + 0.01 -> z ~ -10.78)
    x_near_bound = lower_bound + 0.01
    z_ext_15, flag_ext_15 = compute_robust_glo_z_score(x_near_bound, xi, alpha, k, extended_tail_bound=15.0)
    assert z_ext_15 < -10.0
    assert flag_ext_15 == "EXACT_LOG_CDF"

    z_ext_10, flag_ext_10 = compute_robust_glo_z_score(x_near_bound, xi, alpha, k, extended_tail_bound=10.0)
    assert z_ext_10 == -10.0
    assert flag_ext_10 == "EXTENDED_LOWER_CLAMP"

    # Outside support (x <= lower_bound for k < 0)
    x_outside = lower_bound - 5.0
    assert log_cdf_generalized_logistic(x_outside, xi, alpha, k) == -float("inf")
    z_outside, flag_out = compute_robust_glo_z_score(x_outside, xi, alpha, k, extended_tail_bound=10.0)
    assert z_outside == -10.0
    assert flag_out == "LOWER_SUPPORT_LIMIT"


def test_compare_safeguard_cap_vs_robust_log_transformation_synthetic():
    """
    Run sensitivity analysis comparing the +/- 5.0 operational cap against
    the uncapped robust log-CDF transformation across a 50-year sample.
    """
    np.random.seed(777)
    # Generate 50-year synthetic water balance series with tail outliers
    n_years = 50
    normal_part = np.random.normal(loc=25.0, scale=40.0, size=n_years - 4)
    extreme_outliers = np.array([-180.0, -120.0, 160.0, 210.0])
    d_series = np.concatenate([normal_part, extreme_outliers])

    xi, alpha, k = fit_generalized_logistic_l_moments(d_series)

    res = compare_safeguard_cap_vs_robust_log_transformation(
        d_series, xi, alpha, k, operational_cap=5.0, drought_thresholds=(-1.0, -1.5, -2.0, -2.5)
    )

    assert res["status"] == "SUCCESS"
    assert res["n_samples"] == 50
    # Invariance: Capping extreme tails at +/- 5.0 must NOT alter any drought classification
    assert res["classification_invariant_across_all_thresholds"] is True
    # Within valid range (|z| < 4.9), discrepancy between capped and robust score is virtually zero (< 1e-4)
    assert res["max_in_range_abs_diff"] < 1e-4
    # Check that thresholds evaluations are present
    assert "threshold_-1.0" in res["threshold_evaluations"]
    assert "threshold_-2.0" in res["threshold_evaluations"]


def test_summarize_safeguards_by_month_and_split():
    """Verify safeguard summary by calendar month and dataset split."""
    years = np.array([1985] * 12 + [2010] * 12 + [2020] * 12)
    months = np.array(list(range(1, 13)) * 3)
    guards = ["NONE"] * 36
    guards[0] = "LOWER_ENDPOINT_SAFEGUARD"  # Jan 1985 (train)
    guards[14] = "UPPER_TAIL_CLAMP"          # Mar 2010 (validation)
    guards[35] = "LOWER_TAIL_CLAMP"          # Dec 2020 (test)

    summary = summarize_safeguards_by_month_and_split(
        years, months, guards, train_range=(1981, 2005), val_range=(2006, 2014), test_range=(2015, 2024)
    )

    assert summary["total_timesteps"] == 36
    assert summary["total_safeguards_triggered"] == 3

    # Check split tallies
    assert summary["by_dataset_split"]["train"]["safeguards_triggered"] == 1
    assert summary["by_dataset_split"]["validation"]["safeguards_triggered"] == 1
    assert summary["by_dataset_split"]["test"]["safeguards_triggered"] == 1

    # Check month tallies
    assert summary["by_calendar_month"][1]["safeguards_triggered"] == 1   # Jan
    assert summary["by_calendar_month"][3]["safeguards_triggered"] == 1   # Mar
    assert summary["by_calendar_month"][12]["safeguards_triggered"] == 1  # Dec
    assert summary["by_calendar_month"][2]["safeguards_triggered"] == 0   # Feb


def test_rolling_spei_diagnostics_and_safeguards():
    """
    Verify that calculate_rolling_spei computes goodness-of-fit diagnostics
    and support checks for each of the 12 calendar months, and tracks safeguards.
    """
    np.random.seed(42)
    n_years = 30
    total_months = n_years * 12
    years = np.repeat(np.arange(1991, 2021), 12)
    months = np.tile(np.arange(1, 13), n_years)

    # Monthly synthetic water balance D = P - PET
    d_monthly = np.random.normal(loc=10.0, scale=35.0, size=total_months)

    res = calculate_rolling_spei(d_monthly, years, months, scale=3, calibration_period=(1991, 2020))

    assert res["status"] == "SUCCESS"
    assert len(res["spei"]) == total_months
    assert len(res["prob_raw"]) == total_months
    assert len(res["safeguards"]) == total_months

    # Check 12 calendar month diagnostics
    diag_by_m = res["diagnostics_by_month"]
    assert len(diag_by_m) == 12
    for m in range(1, 13):
        assert m in diag_by_m
        d_diag = diag_by_m[m]
        assert "kolmogorov_smirnov" in d_diag
        assert math.isfinite(d_diag["kolmogorov_smirnov"]["statistic"])
        assert d_diag["support_type"] in ("unbounded", "upper_bounded", "lower_bounded")
        assert d_diag["support_violations_count"] == 0

    # Check safeguard summary by month and split
    summary = res["safeguard_summary"]
    assert summary["total_timesteps"] == total_months
    assert len(summary["by_calendar_month"]) == 12


def test_glo_parameter_estimation_near_zero_shape():
    """
    MATHEMATICAL AUDIT (REV7.1):
    Verify that GLO parameter estimation (Hosking 1990) remains numerically stable
    and continuous as shape parameter k approaches zero, without catastrophic cancellation
    in (1 - k*pi / sin(k*pi)) / k or (sin(k*pi) / (k*pi)).
    """
    xi_true = 5.0
    alpha_true = 12.0

    # Test across small shape values down to exact 0.0
    test_shapes = [0.05, -0.05, 0.02, -0.02, 0.01, -0.01, 1e-4, -1e-4, 1e-6, -1e-6, 1e-8, -1e-8, 0.0]

    for k in test_shapes:
        # Generate exact quantiles across 500 points to create synthetic sample with known L-moments
        u_pts = (np.arange(1, 501) - 0.5) / 500.0
        x_pts = np.array([quantile_generalized_logistic(float(u), xi_true, alpha_true, k) for u in u_pts])

        # Estimate parameters
        xi_est, alpha_est, k_est = fit_generalized_logistic_l_moments(x_pts, min_samples=20)

        # Basic validity
        assert math.isfinite(xi_est), f"Estimated xi non-finite for k={k}"
        assert math.isfinite(alpha_est) and alpha_est > 0.0, f"Estimated alpha invalid for k={k}"
        assert math.isfinite(k_est), f"Estimated k non-finite for k={k}"

        # As k -> 0, estimated parameters should smoothly converge to the logistic parameters
        assert xi_est == pytest.approx(xi_true, abs=0.1), f"Location discrepancy for k={k}: {xi_est}"
        assert alpha_est == pytest.approx(alpha_true, abs=0.1), f"Scale discrepancy for k={k}: {alpha_est}"
        assert k_est == pytest.approx(k, abs=0.01), f"Shape discrepancy for k={k}: {k_est}"


def test_glo_quantile_function_and_continuity_near_zero():
    """
    Verify quantile function quantile_generalized_logistic across central and tail probabilities
    and verify smooth convergence to the logistic quantile x(F) = xi - alpha * ln((1-F)/F).
    """
    xi, alpha = 0.0, 1.0

    # 1. Round-trip identity |F(x(F)) - F| < 1e-5
    for k in [-0.2, -0.01, 0.0, 0.01, 0.2]:
        for f in [0.001, 0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99, 0.999]:
            x_val = quantile_generalized_logistic(f, xi, alpha, k)
            f_calc = cdf_generalized_logistic(x_val, xi, alpha, k)
            assert f_calc == pytest.approx(f, abs=1e-5), f"Round-trip failed for k={k}, f={f}"

    # 2. Smooth convergence to logistic quantile as k -> 0
    f_test = 0.80
    x_logistic = xi - alpha * math.log((1.0 - f_test) / f_test)  # Logistic quantile ~ 1.38629
    x_k_small = quantile_generalized_logistic(f_test, xi, alpha, 1e-6)
    assert x_k_small == pytest.approx(x_logistic, rel=1e-5)


def test_glo_parametric_bootstrap_goodness_of_fit():
    """
    STATISTICAL AUDIT (REV7.1):
    Verify that check_glo_goodness_of_fit implements parametric bootstrap refitting
    (Lilliefors / Stute procedure) to produce calibrated p-values on small monthly samples (N=25),
    along with descriptive KS statistics and Q-Q diagnostics.
    """
    np.random.seed(42)
    n = 25
    xi_true, alpha_true, k_true = 10.0, 15.0, -0.15

    # Sample from true GLO
    u_samp = np.random.uniform(0.01, 0.99, size=n)
    sample_data = np.array([quantile_generalized_logistic(float(u), xi_true, alpha_true, k_true) for u in u_samp])

    xi_fit, alpha_fit, k_fit = fit_generalized_logistic_l_moments(sample_data, min_samples=20)

    res = check_glo_goodness_of_fit(sample_data, xi_fit, alpha_fit, k_fit, n_bootstrap=100, random_state=42)

    assert res["n_samples"] == 25
    assert "kolmogorov_smirnov" in res
    ks = res["kolmogorov_smirnov"]
    assert math.isfinite(ks["statistic"])
    assert ks["statistic"] > 0.0
    assert math.isfinite(ks["p_value_asymptotic_unadjusted"])
    assert math.isfinite(ks["p_value_parametric_bootstrap"])
    assert 0.0 <= ks["p_value_parametric_bootstrap"] <= 1.0
    assert ks["bootstrap_replicates"] >= 50
    assert ks["adequate_fit_bootstrap_05"] is True
    assert "qualification" in ks

    # Q-Q diagnostics
    qq = res["qq_diagnostics"]
    assert math.isfinite(qq["r_squared"])
    assert qq["r_squared"] > 0.95, f"Expected high Q-Q correlation for sample from true GLO, got {qq['r_squared']}"



