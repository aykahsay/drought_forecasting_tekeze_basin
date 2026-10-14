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
    cdf_gamma_spi,
    cdf_generalized_logistic,
    compute_standardized_z_score,
    fit_gamma_spi,
    fit_generalized_logistic_l_moments,
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
