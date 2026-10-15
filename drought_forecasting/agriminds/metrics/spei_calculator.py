"""
spei_calculator.py
==================
Metrics module for calculating Standardized Precipitation Evapotranspiration Index (SPEI-3)
and Potential Evapotranspiration (PET / ET0) under Gate 1 & Gate 2 Scientific Standards.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import scipy.special as sp
from scipy import stats

from drought_forecasting.agriminds.climate.spei_calculator import (
    calculate_extraterrestrial_radiation_ra,
    calculate_hargreaves_pet,
    calculate_hargreaves_daily_pet,
    calculate_fao56_penman_monteith_daily_et0,
    calculate_fao56_penman_monteith_monthly_et0,
    fit_generalized_logistic_l_moments,
    cdf_generalized_logistic,
    quantile_generalized_logistic,
    fit_gamma_spi,
    cdf_gamma_spi,
    calculate_spei_seasonal,
)

__all__ = [
    "calculate_extraterrestrial_radiation_ra",
    "calculate_hargreaves_pet",
    "calculate_hargreaves_daily_pet",
    "calculate_fao56_penman_monteith_daily_et0",
    "calculate_fao56_penman_monteith_monthly_et0",
    "fit_generalized_logistic_l_moments",
    "cdf_generalized_logistic",
    "quantile_generalized_logistic",
    "fit_gamma_spi",
    "cdf_gamma_spi",
    "calculate_spei_seasonal",
    "compute_spei_series",
]


def compute_spei_series(
    precip: np.ndarray,
    pet: np.ndarray,
    scale: int = 3,
    calib_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Computes rolling SPEI at given scale using 3-parameter log-logistic (GLO) distribution
    fitted via unbiased L-moments strictly on the calibration baseline (calib_mask).
    """
    n = len(precip)
    spei_out = np.full(n, np.nan, dtype=np.float64)
    if calib_mask is None:
        calib_mask = np.ones(n, dtype=bool)

    d_series = precip - pet
    d_acc = np.full(n, np.nan, dtype=np.float64)

    for i in range(scale - 1, n):
        w = d_series[i - scale + 1 : i + 1]
        if not np.any(np.isnan(w)):
            d_acc[i] = np.sum(w)

    for mo in range(12):
        mo_indices = np.arange(mo, n, 12)
        valid_mo = [idx for idx in mo_indices if not np.isnan(d_acc[idx])]
        train_mo = [idx for idx in valid_mo if calib_mask[idx]]

        if len(train_mo) >= 20:
            sample_d = d_acc[train_mo]
            try:
                xi, alpha, k = fit_generalized_logistic_l_moments(sample_d)
                for idx in valid_mo:
                    val = d_acc[idx]
                    p_cum = cdf_generalized_logistic(val, xi, alpha, k)
                    p_cum = np.clip(p_cum, 1e-6, 1.0 - 1e-6)
                    spei_out[idx] = stats.norm.ppf(p_cum)
            except Exception:
                pass

    return spei_out
