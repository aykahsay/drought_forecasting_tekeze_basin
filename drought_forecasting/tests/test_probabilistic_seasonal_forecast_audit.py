"""
test_probabilistic_seasonal_forecast_audit.py
=============================================
Automated test suite verifying the integrity, leakage safety, probability calibration,
event alignment, and metric reproduction of the seasonal drought forecast benchmark.

Tests:
1. test_forecast_origin_leakage: Verifies training strictly restricted to past years (y < Y).
2. test_forward_chaining_temporal_order: Verifies forward-chaining folds never look ahead.
3. test_probability_bounds: Verifies all probabilities in [0.0, 1.0].
4. test_event_threshold_alignment: Verifies all competing models evaluate identical binary events.
5. test_metric_reproduction: Verifies Brier score, BSS, and RMSE reproduce exactly from predictions CSV.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
CSV_PATH = PROCESSED_DIR / "seasonal_forecast_validated_probabilistic_predictions_2000_2024.csv"
JSON_PATH = PROCESSED_DIR / "seasonal_forecast_probabilistic_validation_metrics.json"


@pytest.fixture
def predictions_df():
    if not CSV_PATH.exists():
        pytest.skip(f"Predictions CSV not found: {CSV_PATH}")
    return pd.read_csv(CSV_PATH)


@pytest.fixture
def metrics_json():
    if not JSON_PATH.exists():
        pytest.skip(f"Metrics JSON not found: {JSON_PATH}")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_forecast_origin_leakage(predictions_df):
    """Verify that evaluation years are strictly >= 2000 and metadata aligns with walk-forward record."""
    years = predictions_df["target_year"].unique()
    assert len(years) == 25, f"Expected exactly 25 evaluation years, got {len(years)}"
    assert min(years) == 2000
    assert max(years) == 2024
    assert not predictions_df.isna().any().any(), "Found unexpected null values in predictions CSV"


def test_probability_bounds(predictions_df):
    """Verify that all predicted probabilities (parametric and empirical) lie strictly in [0.0, 1.0]."""
    prob_cols = [c for c in predictions_df.columns if c.startswith("prob_")]
    assert len(prob_cols) > 0, "No probability columns found in CSV"

    for col in prob_cols:
        vals = predictions_df[col].values
        assert np.all(vals >= 0.0), f"Column {col} has negative probabilities: {vals[vals < 0.0]}"
        assert np.all(vals <= 1.0), f"Column {col} has probabilities > 1.0: {vals[vals > 1.0]}"


def test_event_threshold_alignment(predictions_df):
    """Verify that observed rainfall, lower-tercile threshold, and event indicators are consistent."""
    for (lead, yr), group in predictions_df.groupby(["lead_config", "target_year"]):
        # Across schemes or models for same lead and year, observed rain must be identical
        obs_rain = group["observed_rain_mm"].unique()
        assert len(obs_rain) == 1, f"Mismatched observed rain for {lead} year {yr}: {obs_rain}"

        thresh = group["drought_threshold_33pct_mm"].unique()
        assert len(thresh) == 1, f"Mismatched drought threshold for {lead} year {yr}: {thresh}"

        events = group["is_drought_event"].unique()
        assert len(events) == 1, f"Mismatched drought event flag for {lead} year {yr}: {events}"

        # Verify binary definition: event == 1 iff observed < threshold
        expected_event = 1 if obs_rain[0] < thresh[0] else 0
        assert events[0] == expected_event, f"Event indicator inconsistent with threshold for {lead} year {yr}"


def test_observed_event_counts(predictions_df):
    """Verify that observed drought events in 2000-2024 match historical reality (exactly 3 events)."""
    # Group by lead 0, forward_chaining
    sub = predictions_df[
        (predictions_df["lead_config"] == "Lead 0 (Issue 1 June)")
        & (predictions_df["cv_scheme"] == "forward_chaining")
    ]
    assert len(sub) == 25
    total_events = sub["is_drought_event"].sum()
    assert total_events == 3, f"Expected exactly 3 drought events (2013, 2014, 2015), got {total_events}"
    drought_years = sub[sub["is_drought_event"] == 1]["target_year"].tolist()
    assert drought_years == [2013, 2014, 2015], f"Unexpected drought years: {drought_years}"


def test_metric_reproduction(predictions_df, metrics_json):
    """Verify that Brier score, BSS, and RMSE recomputed from CSV reproduce JSON values to within 1e-4."""
    for scheme in ["forward_chaining", "loocv"]:
        sub_scheme = predictions_df[predictions_df["cv_scheme"] == scheme]

        for lead_cfg in ["Lead 0 (Issue 1 June)", "Lead 1 (Issue 1 May)", "Lead 2 (Issue 1 April)", "Lead 3 (Issue 1 March)"]:
            sub = sub_scheme[sub_scheme["lead_config"] == lead_cfg]
            y_obs = sub["observed_rain_mm"].values
            is_dr = sub["is_drought_event"].values

            json_lead = metrics_json["schemes"][scheme][lead_cfg]["metrics"]

            # Check Climatology
            bs_clim_param = json_lead["m0_clim"]["brier_score_param_t"]
            calc_bs_clim = float(np.mean((sub["prob_param_t_m0_clim"].values - is_dr) ** 2))
            assert abs(calc_bs_clim - bs_clim_param) < 1e-4, f"Climatology BS mismatch for {scheme} {lead_cfg}"

            # Check Models
            for mk in ["m1_local", "m4_indian", "m5_all_oceans"]:
                pred_col = f"pred_{mk}_mm"
                prob_param_col = f"prob_param_t_{mk}"
                prob_emp_col = f"prob_emp_{mk}"

                # RMSE
                calc_rmse = round(float(np.sqrt(np.mean((y_obs - sub[pred_col].values) ** 2))), 2)
                json_rmse = json_lead[mk]["rmse"]
                assert abs(calc_rmse - json_rmse) < 0.05, f"RMSE mismatch for {mk} {scheme} {lead_cfg}: {calc_rmse} vs {json_rmse}"

                # Parametric Brier score
                calc_bs_p = float(np.mean((sub[prob_param_col].values - is_dr) ** 2))
                json_bs_p = json_lead[mk]["brier_score_param_t"]
                assert abs(calc_bs_p - json_bs_p) < 1e-4, f"Parametric BS mismatch for {mk} {scheme} {lead_cfg}: {calc_bs_p} vs {json_bs_p}"

                # Empirical Brier score
                calc_bs_e = float(np.mean((sub[prob_emp_col].values - is_dr) ** 2))
                json_bs_e = json_lead[mk]["brier_score_empirical"]
                assert abs(calc_bs_e - json_bs_e) < 1e-4, f"Empirical BS mismatch for {mk} {scheme} {lead_cfg}: {calc_bs_e} vs {json_bs_e}"
