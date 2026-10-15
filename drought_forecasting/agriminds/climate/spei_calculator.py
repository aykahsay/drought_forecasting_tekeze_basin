"""
spei_calculator.py
==================
Mathematically rigorous and reproducible implementation of:
  1. Standardized Precipitation-Evapotranspiration Index (SPEI)
     using Hosking's Generalized Logistic (GLO) distribution fitted via
     unbiased L-moments (Beguería et al. 2014; R SPEI package reference standard).
  2. Standardized Precipitation Index (SPI)
     using the 2-parameter Gamma distribution with Thom (1958) Maximum Likelihood
     and zero-precipitation probability adjustment (McKee et al. 1993; WMO 2012).
  3. Potential Evapotranspiration (PET)
     - Hargreaves-Samani (1985) monthly PET with FAO-56 extraterrestrial solar radiation Ra.
     - Thornthwaite (1948) monthly PET for sensitivity baseline.

Quality & Mathematical Guarantees:
  - Zero arbitrary parameter clamping (beta=5 or heuristic fallback).
  - Explicit input validation: NaN/Inf inputs MUST return NaN, never silent 0.0 PET.
  - Strict fixed calibration baseline (default WMO 1991–2020): never silently shifted or gap-bridged.
  - Standard normal conversion via scipy.special.ndtri and Abramowitz-Stegun.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import scipy.special as sp


# ---------------------------------------------------------------------------
# 1. Extraterrestrial Solar Radiation (Ra) & PET Formulations
# ---------------------------------------------------------------------------

def calculate_extraterrestrial_radiation_ra(
    latitude_deg: float,
    month: int,
    days_in_month: int
) -> float:
    """
    Computes monthly extraterrestrial radiation Ra in mm/day equivalent following FAO-56 (Allen et al. 1998).

    Args:
        latitude_deg: Latitude in decimal degrees (positive North, [-90.0, 90.0]).
        month: Calendar month (1 to 12).
        days_in_month: Number of days in the specified month (> 0).

    Returns:
        Ra in mm/day equivalent, or float("nan") if inputs are non-finite or invalid.
    """
    if not (isinstance(latitude_deg, (int, float)) and math.isfinite(latitude_deg)):
        return float("nan")
    if not (-90.0 <= latitude_deg <= 90.0) or not (1 <= month <= 12) or days_in_month <= 0:
        return float("nan")

    # Mid-month Julian day approximation
    mid_month_day = [15, 45, 74, 105, 135, 165, 196, 227, 258, 288, 319, 349][month - 1]
    phi = math.radians(latitude_deg)

    # Solar declination delta (radians)
    delta = 0.409 * math.sin((2.0 * math.pi / 365.0) * mid_month_day - 1.39)

    # Relative distance Earth-Sun dr
    dr = 1.0 + 0.033 * math.cos((2.0 * math.pi / 365.0) * mid_month_day)

    # Sunset hour angle omega_s (radians)
    x = -math.tan(phi) * math.tan(delta)
    if x < -1.0:
        omega_s = math.pi  # Polar day
    elif x > 1.0:
        omega_s = 0.0      # Polar night
    else:
        omega_s = math.acos(x)

    # Solar constant Gsc = 0.0820 MJ / (m^2 * min) -> Ra in MJ / (m^2 * day)
    ra_mj = (24.0 * 60.0 / math.pi) * 0.0820 * dr * (
        omega_s * math.sin(phi) * math.sin(delta) +
        math.cos(phi) * math.cos(delta) * math.sin(omega_s)
    )
    # Convert MJ / (m^2 * day) to mm/day equivalent (1 MJ/m^2/day = 0.408 mm/day)
    ra_mm_day = max(0.0, 0.408 * ra_mj)
    return ra_mm_day


def calculate_hargreaves_pet(
    t_max_c: float,
    t_min_c: float,
    t_mean_c: float,
    latitude_deg: float,
    month: int,
    days_in_month: int
) -> float:
    """
    Calculates monthly Hargreaves-Samani (1985) Potential Evapotranspiration in mm/month.

    Formula:
        PET (mm/day) = 0.0023 * Ra * (T_mean + 17.8) * sqrt(T_max - T_min)
        PET (mm/month) = PET (mm/day) * days_in_month

    Methodological Context:
        Hargreaves-Samani uses extraterrestrial radiation Ra and diurnal temperature range
        (T_max - T_min) as an empirical proxy for net surface radiation and vapour pressure deficit.
        It does not directly measure net radiation or atmospheric humidity.
        Evaluated alongside Thornthwaite (1948) and ERA5-Land Penman-Monteith reference data.

    Returns:
        Monthly PET in mm/month, or float("nan") if inputs are non-finite, missing, or unphysical.
    """
    values = [t_max_c, t_min_c, t_mean_c]
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        return float("nan")

    if t_max_c < t_min_c:
        return float("nan")

    if not (-60.0 <= t_min_c <= 60.0 and -60.0 <= t_max_c <= 65.0 and -60.0 <= t_mean_c <= 65.0):
        return float("nan")

    ra_mm_day = calculate_extraterrestrial_radiation_ra(latitude_deg, month, days_in_month)
    if not math.isfinite(ra_mm_day) or ra_mm_day <= 0.0:
        return float("nan")

    dtr = t_max_c - t_min_c
    t_term = max(0.0, t_mean_c + 17.8)
    pet_day = 0.0023 * ra_mm_day * t_term * math.sqrt(dtr)
    return max(0.0, pet_day * days_in_month)


def calculate_thornthwaite_monthly_pet(
    monthly_t_mean: List[float],
    latitude_deg: float
) -> List[float]:
    """
    Calculates monthly Thornthwaite (1948) PET in mm/month for a 12-month calendar year.
    Used for comparative baseline and sensitivity analysis.

    Returns:
        List of 12 monthly PET values in mm, or list of NaNs if inputs are invalid.
    """
    if len(monthly_t_mean) != 12 or not all(isinstance(t, (int, float)) and math.isfinite(t) for t in monthly_t_mean):
        return [float("nan")] * 12
    if not (isinstance(latitude_deg, (int, float)) and math.isfinite(latitude_deg) and -90.0 <= latitude_deg <= 90.0):
        return [float("nan")] * 12

    # Annual heat index I
    heat_index = 0.0
    for t in monthly_t_mean:
        if t > 0.0:
            heat_index += (t / 5.0) ** 1.514
    heat_index = max(1e-4, heat_index)

    # Exponent a
    a = (6.75e-7 * (heat_index ** 3)) - (7.71e-5 * (heat_index ** 2)) + (1.792e-2 * heat_index) + 0.49239

    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    pet_list = []

    for m_idx, t in enumerate(monthly_t_mean):
        d_count = days_per_month[m_idx]
        if t <= 0.0:
            pet_unadjusted = 0.0
        else:
            pet_unadjusted = 16.0 * ((10.0 * t / heat_index) ** a)

        mid_day = [15, 45, 74, 105, 135, 165, 196, 227, 258, 288, 319, 349][m_idx]
        phi = math.radians(latitude_deg)
        delta = 0.409 * math.sin((2.0 * math.pi / 365.0) * mid_day - 1.39)
        tan_prod = -math.tan(phi) * math.tan(delta)
        if tan_prod < -1.0:
            omega_s = math.pi
        elif tan_prod > 1.0:
            omega_s = 0.0
        else:
            omega_s = math.acos(tan_prod)
        day_length_hours = (24.0 / math.pi) * omega_s

        pet_monthly = pet_unadjusted * (day_length_hours / 12.0) * (d_count / 30.0)
        pet_list.append(max(0.0, pet_monthly))

    return pet_list


# ---------------------------------------------------------------------------
# 2. Hosking Generalized Logistic (GLO) Distribution Fitting for SPEI
# ---------------------------------------------------------------------------

def fit_generalized_logistic_l_moments(
    data: np.ndarray,
    min_samples: int = 20
) -> Tuple[float, float, float]:
    """
    Fits Hosking (1990) Generalized Logistic (GLO) distribution parameters (xi, alpha, k)
    using unbiased sample L-moments (lambda1, lambda2, tau3) as used in the official
    R SPEI package (Beguería et al. 2014; lmom::pelglo).

    Formulas:
        k = -tau3 = -(l3 / l2)
        alpha = (l2 * sin(k * pi)) / (k * pi)  [for k != 0; alpha = l2 for k == 0]
        xi = l1 - (alpha / k) * (1 - (k * pi) / sin(k * pi))

    Args:
        data: 1D array of climatic water balance values (P - PET).
        min_samples: Minimum required finite calibration observations (default 20).

    Returns:
        (xi, alpha, k) -> (location, scale, shape)

    Raises:
        ValueError: If sample size is inadequate or parameters violate mathematical bounds.
    """
    clean_data = data[np.isfinite(data)]
    n = len(clean_data)
    if n < min_samples:
        raise ValueError(
            f"Insufficient valid calibration observations ({n} < {min_samples}) "
            f"for Generalized Logistic L-moments estimation."
        )

    sorted_d = np.sort(clean_data)

    # Hosking unbiased sample PWMs b0, b1, b2
    # b_r = (1/n) * sum_{i=1}^n [ (binom(i - 1, r) / binom(n - 1, r)) * x_(i) ]
    i_idx = np.arange(1, n + 1, dtype=np.float64)
    b0 = float(np.mean(sorted_d))
    b1 = float(np.sum((i_idx - 1.0) / (n - 1.0) * sorted_d) / n)
    b2 = float(np.sum(((i_idx - 1.0) * (i_idx - 2.0)) / ((n - 1.0) * (n - 2.0)) * sorted_d) / n)

    # Unbiased sample L-moments
    l1 = b0
    l2 = 2.0 * b1 - b0
    l3 = 6.0 * b2 - 6.0 * b1 + b0

    if l2 <= 0.0:
        raise ValueError(f"Sample L-scale l2={l2:.4f} <= 0 (zero or negative variance). Fitting failed.")

    tau3 = l3 / l2
    k = -tau3

    # Shape bound: |k| < 1.0 required for finite mean in GLO
    if abs(k) >= 1.0:
        raise ValueError(
            f"Generalized Logistic shape parameter |k|={abs(k):.4f} >= 1.0 (mean does not converge). "
            f"Fitting rejected."
        )

    if abs(k) < 1e-6:
        alpha = l2
        xi = l1
    else:
        k_pi = k * math.pi
        sin_k_pi = math.sin(k_pi)
        if abs(sin_k_pi) < 1e-12:
            raise ValueError(f"Singular sin(k*pi) for k={k:.4f}.")
        alpha = (l2 * sin_k_pi) / k_pi
        xi = l1 - (alpha / k) * (1.0 - k_pi / sin_k_pi)

    if not math.isfinite(alpha) or alpha <= 0.0:
        raise ValueError(f"Generalized Logistic scale alpha={alpha:.4f} <= 0. Fitting failed.")

    return float(xi), float(alpha), float(k)


def cdf_generalized_logistic(x: float, xi: float, alpha: float, k: float) -> float:
    """
    Computes non-exceedance probability F(x) under the Generalized Logistic distribution.

    Formula (Hosking 1990; lmom::cdfglo):
        y = 1 - k * (x - xi) / alpha
        F(x) = 1 / (1 + y^(1/k))  for k != 0
        F(x) = 1 / (1 + exp(-(x - xi)/alpha)) for k == 0
    """
    if not math.isfinite(x):
        return float("nan")

    if abs(k) < 1e-6:
        arg = -(x - xi) / alpha
        arg = np.clip(arg, -50.0, 50.0)
        return float(1.0 / (1.0 + math.exp(arg)))

    y = 1.0 - (k * (x - xi)) / alpha
    if y <= 0.0:
        return 1.0 if k > 0 else 0.0

    try:
        term = y ** (1.0 / k)
        prob = 1.0 / (1.0 + term)
    except (OverflowError, ZeroDivisionError):
        prob = 0.0 if k < 0 else 1.0

    return float(prob)


# Backwards compatibility alias for Log-Logistic
def fit_log_logistic_l_moments(data: np.ndarray, min_samples: int = 20) -> Tuple[float, float, float]:
    """Alias for Hosking Generalized Logistic L-moments parameter estimation."""
    return fit_generalized_logistic_l_moments(data, min_samples=min_samples)


# ---------------------------------------------------------------------------
# 3. McKee et al. (1993) Two-Parameter Gamma SPI Formulation
# ---------------------------------------------------------------------------

def fit_gamma_spi(
    precip_data: np.ndarray,
    min_samples: int = 20
) -> Tuple[float, float, float]:
    """
    Fits 2-parameter Gamma distribution parameters (alpha, beta) via Maximum Likelihood
    with Thom (1958) approximation and computes zero-precipitation probability q
    following McKee et al. (1993) and WMO (2012) standard.

    Args:
        precip_data: 1D array of seasonal accumulated precipitation in mm.
        min_samples: Minimum required calibration observations.

    Returns:
        (alpha, beta, q_zero) -> (shape, scale, zero_fraction)
    """
    clean_p = precip_data[np.isfinite(precip_data)]
    n = len(clean_p)
    if n < min_samples:
        raise ValueError(f"Insufficient valid calibration observations ({n} < {min_samples}) for Gamma SPI.")

    m_zeros = int(np.sum(clean_p <= 0.0))
    q_zero = float(m_zeros / n)

    positive_p = clean_p[clean_p > 0.0]
    if len(positive_p) < 10:
        raise ValueError("Too few non-zero precipitation observations to fit Gamma distribution.")

    mean_p = float(np.mean(positive_p))
    log_mean = math.log(mean_p)
    mean_log = float(np.mean(np.log(positive_p)))

    A = log_mean - mean_log
    if A <= 1e-6:
        A = 1e-6

    # Thom (1958) Maximum Likelihood estimator for shape alpha
    alpha_g = (1.0 / (4.0 * A)) * (1.0 + math.sqrt(1.0 + 4.0 * A / 3.0))
    beta_g = mean_p / alpha_g

    return float(alpha_g), float(beta_g), float(q_zero)


def cdf_gamma_spi(p: float, alpha: float, beta: float, q_zero: float) -> float:
    """
    Computes cumulative probability H(p) = q + (1 - q) * G(p) for precipitation p.
    """
    if not math.isfinite(p):
        return float("nan")

    if p <= 0.0:
        return float(np.clip(q_zero, 1e-6, 1.0 - 1e-6))

    # Incomplete gamma function G(p)
    g_p = float(sp.gammainc(alpha, p / beta))
    h_p = q_zero + (1.0 - q_zero) * g_p
    return float(np.clip(h_p, 1e-6, 1.0 - 1e-6))


# ---------------------------------------------------------------------------
# 4. Standard Normal Transformation
# ---------------------------------------------------------------------------

def compute_standardized_z_score(prob: float) -> float:
    """
    Converts non-exceedance probability P to standard normal z-score
    using scipy.special.ndtri with Abramowitz & Stegun rational fallback.
    Bounded to [1e-6, 1.0 - 1e-6].
    """
    if not math.isfinite(prob):
        return float("nan")

    p = np.clip(prob, 1e-6, 1.0 - 1e-6)

    try:
        z = float(sp.ndtri(p))
        if math.isfinite(z):
            return z
    except Exception:
        pass

    # Abramowitz & Stegun (1965) fallback
    c0 = 2.515517
    c1 = 0.802853
    c2 = 0.010328
    d1 = 1.432788
    d2 = 0.189269
    d3 = 0.001308

    if p <= 0.5:
        w = math.sqrt(-2.0 * math.log(p))
        z = -(w - ((c0 + c1 * w + c2 * (w ** 2)) / (1.0 + d1 * w + d2 * (w ** 2) + d3 * (w ** 3))))
    else:
        w = math.sqrt(-2.0 * math.log(1.0 - p))
        z = (w - ((c0 + c1 * w + c2 * (w ** 2)) / (1.0 + d1 * w + d2 * (w ** 2) + d3 * (w ** 3))))

    return float(z)


# ---------------------------------------------------------------------------
# 5. Seasonal SPEI and SPI Standardization Engines
# ---------------------------------------------------------------------------

def calculate_spei_seasonal(
    d_seasonal_series: np.ndarray,
    years: np.ndarray,
    calibration_period: Tuple[int, int] = (1991, 2020),
    min_calibration_years: int = 20
) -> Dict[str, Any]:
    """
    Computes standardized seasonal SPEI series (e.g. September-ending SPEI-3)
    fitted strictly on the fixed calibration reference interval.

    Args:
        d_seasonal_series: 1D array of 3-month accumulated water balance (P - PET) in mm.
        years: 1D array of corresponding calendar years.
        calibration_period: Fixed (start_year, end_year) interval (default 1991–2020).
        min_calibration_years: Minimum required valid years in calibration period (default 20).

    Returns:
        Dictionary with standardized SPEI series, parameters, and metadata.
    """
    if len(d_seasonal_series) != len(years):
        raise ValueError("Lengths of d_seasonal_series and years must match exactly.")

    calib_start, calib_end = calibration_period
    calib_mask = (years >= calib_start) & (years <= calib_end) & np.isfinite(d_seasonal_series)
    calib_data = d_seasonal_series[calib_mask]

    n_calib_valid = int(len(calib_data))
    if n_calib_valid < min_calibration_years:
        raise ValueError(
            f"Insufficient valid calibration observations ({n_calib_valid} < {min_calibration_years}) "
            f"in fixed reference window {calibration_period}. Pipeline will not silently substitute full record."
        )

    xi, alpha, k = fit_generalized_logistic_l_moments(calib_data, min_samples=min_calibration_years)

    spei_out = np.full(len(d_seasonal_series), np.nan, dtype=np.float64)
    for i, d_val in enumerate(d_seasonal_series):
        if not math.isfinite(d_val):
            continue
        prob = cdf_generalized_logistic(d_val, xi, alpha, k)
        spei_out[i] = compute_standardized_z_score(prob)

    moderate_droughts = years[(spei_out <= -1.0) & np.isfinite(spei_out)].tolist()
    severe_droughts = years[(spei_out <= -2.0) & np.isfinite(spei_out)].tolist()

    return {
        "spei": spei_out,
        "distribution": "Generalized_Logistic_Hosking",
        "params": {"xi": xi, "alpha": alpha, "k": k},
        "calibration_period": list(calibration_period),
        "n_total": len(years),
        "n_calib_valid": n_calib_valid,
        "status": "SUCCESS",
        "drought_years_moderate": [int(y) for y in moderate_droughts],
        "drought_years_severe": [int(y) for y in severe_droughts]
    }


def calculate_spi_seasonal(
    p_seasonal_series: np.ndarray,
    years: np.ndarray,
    calibration_period: Tuple[int, int] = (1991, 2020),
    min_calibration_years: int = 20
) -> Dict[str, Any]:
    """
    Computes Standardized Precipitation Index (SPI-3) using 2-parameter Gamma distribution
    fitted strictly on the fixed calibration reference interval with zero adjustment.

    Args:
        p_seasonal_series: 1D array of 3-month accumulated precipitation in mm.
        years: 1D array of corresponding calendar years.
        calibration_period: Fixed (start_year, end_year) interval (default 1991–2020).
        min_calibration_years: Minimum required valid years in calibration period (default 20).
    """
    if len(p_seasonal_series) != len(years):
        raise ValueError("Lengths of p_seasonal_series and years must match exactly.")

    calib_start, calib_end = calibration_period
    calib_mask = (years >= calib_start) & (years <= calib_end) & np.isfinite(p_seasonal_series)
    calib_data = p_seasonal_series[calib_mask]

    n_calib_valid = int(len(calib_data))
    if n_calib_valid < min_calibration_years:
        raise ValueError(
            f"Insufficient valid calibration observations ({n_calib_valid} < {min_calibration_years}) "
            f"for SPI Gamma fitting in reference window {calibration_period}."
        )

    alpha_g, beta_g, q_zero = fit_gamma_spi(calib_data, min_samples=min_calibration_years)

    spi_out = np.full(len(p_seasonal_series), np.nan, dtype=np.float64)
    for i, p_val in enumerate(p_seasonal_series):
        if not math.isfinite(p_val):
            continue
        prob = cdf_gamma_spi(p_val, alpha_g, beta_g, q_zero)
        spi_out[i] = compute_standardized_z_score(prob)

    return {
        "spi": spi_out,
        "distribution": "Gamma_2Param_Thom_MLE",
        "params": {"alpha": alpha_g, "beta": beta_g, "q_zero": q_zero},
        "calibration_period": list(calibration_period),
        "n_total": len(years),
        "n_calib_valid": n_calib_valid,
        "status": "SUCCESS"
    }


def calculate_rolling_spei(
    d_monthly: np.ndarray,
    years: np.ndarray,
    months: np.ndarray,
    scale: int = 3,
    calibration_period: Tuple[int, int] = (1991, 2020),
    min_calibration_years: int = 20
) -> Dict[str, Any]:
    """
    Computes continuous multi-scalar rolling SPEI time series (e.g. SPEI-3) across all months.
    Follows Beguería et al. (2014) and the R 'SPEI' package:
      1. Computes rolling sums of water balance D over 'scale' months.
      2. Groups observations by calendar month m in {1, ..., 12}.
      3. For each calendar month m, fits Hosking Generalized Logistic parameters on fixed calibration baseline.
      4. Standardizes each month using its month-specific distribution parameters.

    Args:
        d_monthly: 1D array of monthly water balance D = P - PET (length T).
        years: 1D array of calendar years for each month (length T).
        months: 1D array of calendar months (1 to 12) for each month (length T).
        scale: Rolling accumulation window in months (default 3 for SPEI-3).
        calibration_period: Fixed (start_year, end_year) baseline interval (default 1991–2020).
        min_calibration_years: Minimum required valid calibration years for each calendar month.

    Returns:
        Dictionary with:
          - 'spei': 1D array of rolling standardized SPEI values (length T, first scale-1 values are NaN).
          - 'd_rolling': 1D array of rolling accumulated water balance.
          - 'params_by_month': Dict mapping calendar month (1..12) to fitted (xi, alpha, k) parameters.
          - 'scale': rolling window size in months.
          - 'calibration_period': [start, end].
    """
    n_total = len(d_monthly)
    if len(years) != n_total or len(months) != n_total:
        raise ValueError("d_monthly, years, and months must have identical lengths.")

    # 1. Rolling accumulation
    d_rolling = np.full(n_total, np.nan, dtype=np.float64)
    for i in range(scale - 1, n_total):
        window = d_monthly[i - scale + 1 : i + 1]
        if np.all(np.isfinite(window)):
            d_rolling[i] = float(np.sum(window))

    # 2. Fit and standardize month-by-month
    spei_out = np.full(n_total, np.nan, dtype=np.float64)
    params_by_month = {}
    calib_start, calib_end = calibration_period

    for m in range(1, 13):
        m_mask = (months == m)
        calib_mask = m_mask & (years >= calib_start) & (years <= calib_end) & np.isfinite(d_rolling)
        calib_vals = d_rolling[calib_mask]

        if len(calib_vals) < min_calibration_years:
            raise ValueError(
                f"Insufficient valid calibration observations for calendar month {m} "
                f"({len(calib_vals)} < {min_calibration_years}) in fixed reference period {calibration_period}."
            )

        xi, alpha, k = fit_generalized_logistic_l_moments(calib_vals, min_samples=min_calibration_years)
        params_by_month[m] = {"xi": xi, "alpha": alpha, "k": k, "n_calib": len(calib_vals)}

        # Standardize all timesteps corresponding to calendar month m
        for idx in np.where(m_mask)[0]:
            val = d_rolling[idx]
            if math.isfinite(val):
                prob = cdf_generalized_logistic(val, xi, alpha, k)
                spei_out[idx] = compute_standardized_z_score(prob)

    return {
        "spei": spei_out,
        "d_rolling": d_rolling,
        "params_by_month": params_by_month,
        "scale": scale,
        "calibration_period": list(calibration_period),
        "status": "SUCCESS"
    }


def calculate_rolling_spi(
    p_monthly: np.ndarray,
    years: np.ndarray,
    months: np.ndarray,
    scale: int = 3,
    calibration_period: Tuple[int, int] = (1991, 2020),
    min_calibration_years: int = 20
) -> Dict[str, Any]:
    """
    Computes continuous multi-scalar rolling SPI time series (e.g. SPI-3) across all months
    using month-specific 2-parameter Gamma distributions with zero-precipitation adjustments.
    """
    n_total = len(p_monthly)
    if len(years) != n_total or len(months) != n_total:
        raise ValueError("p_monthly, years, and months must have identical lengths.")

    p_rolling = np.full(n_total, np.nan, dtype=np.float64)
    for i in range(scale - 1, n_total):
        window = p_monthly[i - scale + 1 : i + 1]
        if np.all(np.isfinite(window)):
            p_rolling[i] = float(np.sum(window))

    spi_out = np.full(n_total, np.nan, dtype=np.float64)
    params_by_month = {}
    calib_start, calib_end = calibration_period

    for m in range(1, 13):
        m_mask = (months == m)
        calib_mask = m_mask & (years >= calib_start) & (years <= calib_end) & np.isfinite(p_rolling)
        calib_vals = p_rolling[calib_mask]

        if len(calib_vals) < min_calibration_years:
            raise ValueError(
                f"Insufficient valid calibration observations for calendar month {m} "
                f"({len(calib_vals)} < {min_calibration_years}) in fixed reference period {calibration_period}."
            )

        alpha_g, beta_g, q_zero = fit_gamma_spi(calib_vals, min_samples=min_calibration_years)
        params_by_month[m] = {"alpha": alpha_g, "beta": beta_g, "q_zero": q_zero, "n_calib": len(calib_vals)}

        for idx in np.where(m_mask)[0]:
            val = p_rolling[idx]
            if math.isfinite(val):
                prob = cdf_gamma_spi(val, alpha_g, beta_g, q_zero)
                spi_out[idx] = compute_standardized_z_score(prob)

    return {
        "spi": spi_out,
        "p_rolling": p_rolling,
        "params_by_month": params_by_month,
        "scale": scale,
        "calibration_period": list(calibration_period),
        "status": "SUCCESS"
    }
