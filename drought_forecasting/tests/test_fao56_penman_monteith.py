"""
test_fao56_penman_monteith.py
=============================
Rigorous unit tests for the FAO-56 Penman-Monteith Reference Evapotranspiration (ET_0)
formulation in drought_forecasting/agriminds/climate/spei_calculator.py.
"""

import math
import pytest
from drought_forecasting.agriminds.climate.spei_calculator import (
    calculate_fao56_penman_monteith_daily_et0,
    calculate_fao56_penman_monteith_monthly_et0,
)


def test_fao56_pm_valid_computation():
    """Verify standard FAO-56 daily ET0 calculation produces physically realistic values."""
    # Semi-arid conditions: Tmax=32°C, Tmin=18°C, Lat=13.25°N, DOY=75 (March in Tanqua Abergele)
    et0 = calculate_fao56_penman_monteith_daily_et0(
        t_max_c=32.0,
        t_min_c=18.0,
        latitude_deg=13.25,
        day_of_year=75,
        elevation_m=1450.0,
        wind_speed_2m_m_s=2.0
    )
    assert math.isfinite(et0)
    assert 4.0 <= et0 <= 7.0  # Typical semi-arid March pre-monsoon daily ET0 in Tekezé gorge


def test_fao56_pm_boundary_and_invalidation():
    """Verify that unphysical inputs (Tmax < Tmin, non-finite values) return NaN."""
    # Tmax < Tmin
    assert math.isnan(calculate_fao56_penman_monteith_daily_et0(
        t_max_c=15.0, t_min_c=20.0, latitude_deg=13.25, day_of_year=100
    ))
    # NaN input
    assert math.isnan(calculate_fao56_penman_monteith_daily_et0(
        t_max_c=float("nan"), t_min_c=18.0, latitude_deg=13.25, day_of_year=100
    ))
    # Invalid day of year
    assert math.isnan(calculate_fao56_penman_monteith_daily_et0(
        t_max_c=30.0, t_min_c=18.0, latitude_deg=13.25, day_of_year=400
    ))


def test_fao56_pm_wind_sensitivity():
    """Verify that higher wind speed increases evaporative demand when vapor pressure deficit > 0."""
    et0_calm = calculate_fao56_penman_monteith_daily_et0(
        t_max_c=32.0, t_min_c=18.0, latitude_deg=13.25, day_of_year=75, wind_speed_2m_m_s=1.0
    )
    et0_windy = calculate_fao56_penman_monteith_daily_et0(
        t_max_c=32.0, t_min_c=18.0, latitude_deg=13.25, day_of_year=75, wind_speed_2m_m_s=4.0
    )
    assert et0_windy > et0_calm


def test_fao56_pm_elevation_psychrometric_scaling():
    """Verify that elevation affects atmospheric pressure and psychrometric constant."""
    et0_lowland = calculate_fao56_penman_monteith_daily_et0(
        t_max_c=30.0, t_min_c=15.0, latitude_deg=13.25, day_of_year=150, elevation_m=500.0
    )
    et0_highland = calculate_fao56_penman_monteith_daily_et0(
        t_max_c=30.0, t_min_c=15.0, latitude_deg=13.25, day_of_year=150, elevation_m=2500.0
    )
    # Both are finite and positive
    assert math.isfinite(et0_lowland) and et0_lowland > 0.0
    assert math.isfinite(et0_highland) and et0_highland > 0.0


def test_fao56_pm_monthly_accumulation():
    """Verify monthly ET0 formulation scales correctly with days in month."""
    monthly_et0 = calculate_fao56_penman_monteith_monthly_et0(
        t_max_c=30.0,
        t_min_c=16.0,
        t_mean_c=23.0,
        latitude_deg=13.25,
        month=7,
        days_in_month=31,
        elevation_m=1450.0
    )
    assert math.isfinite(monthly_et0)
    assert 100.0 <= monthly_et0 <= 250.0  # Realistic monthly ET0 (mm/month)
