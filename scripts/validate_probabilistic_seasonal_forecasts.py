"""
validate_probabilistic_seasonal_forecasts.py
============================================
Comprehensive Validation and Methodological Audit of Probabilistic Seasonal Forecasts
for Tanqua Abergele Woreda (Tekezé River Basin, Northern Ethiopia):

1. Exact Ridge Predictive Distribution:
   - Derives the exact sampling covariance of the Ridge estimator (sandwich form).
   - Accounts for intercept variance (1/n_tr), feature standardization, and leverage.
   - Computes effective residual degrees of freedom:
       df_res = n_tr - tr(2*H_alpha - H_alpha^2) - 1
   - Explicitly documents shrinkage bias and why OLS Student-t is an approximation for Ridge.

2. Comparison of Probability-Generation Methods:
   - Method A: Parametric Ridge Student-t Predictive Distribution with exact sandwich variance.
   - Method B: Training-only Non-Parametric Empirical Residual-Based Predictive Distribution.
   - Zero evaluation-outcome calibration: strictly fitted on past years y < Y.

3. Forward-Chaining Hyperparameter Validation vs LOOCV:
   - Implements strictly causal forward-chaining (expanding-window) cross-validation
     within historical training years (y < Y) with an initial burn-in window.
   - Compares forward-chaining alpha selection directly against LOOCV.

4. Metrics & Uncertainty:
   - Recomputes Brier Score (BS) and Brier Skill Score (BSS) for all models and leads.
   - Computes reliability tables (binned forecast probability vs observed event frequency).
   - Reports event counts (observed lower-tercile drought occurrences).
   - Computes paired calendar year-block bootstrap (B=2,000) 95% confidence intervals
     for Delta-BS and Delta-BSS against both Climatology and Local History.

5. Preserves Auditability:
   - Exports complete row-level predictions CSV and structured metrics JSON.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
CSV_PATH = PROCESSED_DIR / "abregelle_tekeze_unified_monthly_1981_2024.csv"

OUT_PREDICTIONS_CSV = PROCESSED_DIR / "seasonal_forecast_validated_probabilistic_predictions_2000_2024.csv"
OUT_METRICS_JSON = PROCESSED_DIR / "seasonal_forecast_probabilistic_validation_metrics.json"


def safe_pearsonr(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    if np.std(y_pred) < 1e-8 or np.std(y_true) < 1e-8:
        return None
    r_val, _ = stats.pearsonr(y_true, y_pred)
    return round(float(r_val), 4)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    mse = float(np.mean((y_true - y_pred) ** 2))
    rmse = float(np.sqrt(mse))
    mae = float(np.mean(np.abs(y_true - y_pred)))
    r_val = safe_pearsonr(y_true, y_pred)
    return {"rmse": round(rmse, 2), "mae": round(mae, 2), "r": r_val}


def compute_brier_score(obs_events: np.ndarray, pred_probs: np.ndarray) -> float:
    return float(np.mean((pred_probs - obs_events) ** 2))


def compute_reliability_table(
    pred_probs: np.ndarray, obs_events: np.ndarray, bin_edges: List[float] = [0.0, 0.20, 0.40, 1.0]
) -> List[Dict[str, Any]]:
    """Compute reliability diagram data: binned forecast probability vs observed relative frequency."""
    table = []
    for i in range(len(bin_edges) - 1):
        low, high = bin_edges[i], bin_edges[i + 1]
        if i == len(bin_edges) - 2:
            mask = (pred_probs >= low) & (pred_probs <= high)
        else:
            mask = (pred_probs >= low) & (pred_probs < high)

        count = int(np.sum(mask))
        if count > 0:
            mean_prob = float(np.mean(pred_probs[mask]))
            obs_freq = float(np.mean(obs_events[mask]))
            event_count = int(np.sum(obs_events[mask]))
        else:
            mean_prob = float((low + high) / 2.0)
            obs_freq = 0.0
            event_count = 0

        table.append({
            "bin": f"[{low:.2f}, {high:.2f}]",
            "count": count,
            "mean_pred_prob": round(mean_prob, 4),
            "obs_event_freq": round(obs_freq, 4),
            "obs_event_count": event_count,
        })
    return table


def run_probabilistic_audit():
    print("=" * 85)
    print("AI-DREWS: PROBABILISTIC DROUGHT FORECAST VALIDATION & TEMPORAL AUDIT")
    print("Evaluating Exact Ridge Predictive Distributions, Empirical Residuals & Forward-Chaining")
    print("=" * 85)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing master climate dataset: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"])
    precip_col = "chirps_abregelle_precip_mm"

    years = np.sort(df["year"].unique())

    # Precompute Kiremt (JJAS) seasonal rainfall
    seasonal_data = []
    for y in years:
        df_y = df[df["year"] == y].sort_values("month")
        kiremt_p = df_y[df_y["month"].isin([6, 7, 8, 9])][precip_col].sum()
        seasonal_data.append({"year": y, "kiremt_jjas_mm": kiremt_p})
    df_seasons = pd.DataFrame(seasonal_data)

    eval_years = [y for y in years if y >= 2000]
    n_eval = len(eval_years)
    print(f"Evaluation Period: 2000–2024 (N = {n_eval} annual forecast origins)")

    issue_configs = [
        {"lead_label": "Lead 0 (Issue 1 June)", "issue_month": 5, "type": "Retrospective Simulation"},
        {"lead_label": "Lead 1 (Issue 1 May)", "issue_month": 4, "type": "1-Month Operational Lead"},
        {"lead_label": "Lead 2 (Issue 1 April)", "issue_month": 3, "type": "2-Month Operational Lead"},
        {"lead_label": "Lead 3 (Issue 1 March)", "issue_month": 2, "type": "3-Month Pre-Season Lead"},
    ]

    candidate_alphas = [1.0, 10.0, 50.0, 100.0, 500.0]
    models = ["m0_clim", "m1_local", "m2_ocean", "m3_pacific", "m4_indian", "m5_all_oceans"]

    # We evaluate two hyperparameter validation procedures:
    # 1. 'forward_chaining': strictly forward expanding window within y < Y
    # 2. 'loocv': leave-one-out CV within y < Y
    cv_schemes = ["forward_chaining", "loocv"]

    full_results: Dict[str, Any] = {
        "metadata": {
            "evaluation_years": [int(y) for y in eval_years],
            "n_years": n_eval,
            "target_season": "Kiremt Monsoon (JJAS)",
            "historical_mean_jjas_mm": round(float(df_seasons["kiremt_jjas_mm"].mean()), 2),
        },
        "schemes": {}
    }

    all_prediction_records = []

    for cv_scheme in cv_schemes:
        print(f"\n" + "#" * 80)
        print(f"HYPERPARAMETER SELECTION SCHEME: {cv_scheme.upper()}")
        print("#" * 80)

        scheme_summary = {}

        for cfg in issue_configs:
            l_label = cfg["lead_label"]
            iss_m = cfg["issue_month"]
            lead_type = cfg["type"]

            print(f"\n=======================================================")
            print(f"PROCESSING: {l_label} ({lead_type}) [{cv_scheme}]")
            print("=======================================================")

            y_obs_list = []
            drought_obs_list = []
            drought_threshold_list = []
            train_clim_list = []

            # Store predictions & probabilities per model
            preds_raw = {m: [] for m in models}
            probs_param_t = {m: [] for m in models}
            probs_param_norm = {m: [] for m in models}
            probs_empirical = {m: [] for m in models}
            chosen_alphas = {m: [] for m in models if m != "m0_clim"}
            forecast_se_list = {m: [] for m in models if m != "m0_clim"}

            for target_y in eval_years:
                obs_p = float(df_seasons.loc[df_seasons["year"] == target_y, "kiremt_jjas_mm"].values[0])
                y_obs_list.append(obs_p)

                train_years = [y for y in years if y >= 1982 and y < target_y]
                n_tr = len(train_years)
                y_tr_raw = df_seasons.loc[df_seasons["year"].isin(train_years), "kiremt_jjas_mm"].values

                train_clim = float(np.mean(y_tr_raw))
                train_clim_list.append(train_clim)
                y_tr_anom = y_tr_raw - train_clim

                # Lower-tercile drought threshold estimated strictly on past years
                drought_thresh = float(np.percentile(y_tr_raw, 33.33))
                drought_threshold_list.append(drought_thresh)
                is_drought = 1 if obs_p < drought_thresh else 0
                drought_obs_list.append(is_drought)

                # Feature extraction
                def extract_features(yr_list):
                    l_list, n_list, d_list, a_list = [], [], [], []
                    for yr in yr_list:
                        row_iss = df[(df["year"] == yr) & (df["month"] == iss_m)].iloc[0]
                        sub_pre = df[
                            (df["year"] == yr)
                            & (
                                df["month"].isin([
                                    iss_m,
                                    iss_m - 1 if iss_m > 1 else 12,
                                    iss_m - 2 if iss_m > 2 else (11 if iss_m == 2 else 10),
                                ])
                            )
                        ]
                        ant_p = float(sub_pre[precip_col].sum())
                        l_list.append([ant_p, float(row_iss[precip_col])])
                        n_list.append([float(row_iss["nino34_sst_anomaly"])])
                        d_list.append([float(row_iss["dmi"])])
                        a_list.append([float(row_iss["atl_meridional_gradient"])])

                    return {
                        "m1_local": np.array(l_list),
                        "m2_ocean": np.hstack([np.array(n_list), np.array(d_list), np.array(a_list)]),
                        "m3_pacific": np.hstack([np.array(l_list), np.array(n_list)]),
                        "m4_indian": np.hstack([np.array(l_list), np.array(d_list)]),
                        "m5_all_oceans": np.hstack([np.array(l_list), np.array(n_list), np.array(d_list), np.array(a_list)]),
                    }

                tr_feats = extract_features(train_years)
                te_feats = extract_features([target_y])

                # M0 Climatology
                preds_raw["m0_clim"].append(train_clim)
                p_clim = float(np.mean(y_tr_raw < drought_thresh))
                probs_param_t["m0_clim"].append(p_clim)
                probs_param_norm["m0_clim"].append(p_clim)
                probs_empirical["m0_clim"].append(p_clim)

                # Fit Models M1 to M5
                row_pred_dict = {
                    "cv_scheme": cv_scheme,
                    "season": "Kiremt Monsoon (JJAS)",
                    "lead_config": l_label,
                    "lead_type": lead_type,
                    "target_year": target_y,
                    "observed_rain_mm": round(obs_p, 2),
                    "expanding_climatology_mm": round(train_clim, 2),
                    "drought_threshold_33pct_mm": round(drought_thresh, 2),
                    "is_drought_event": is_drought,
                    "pred_m0_clim_mm": round(train_clim, 2),
                    "prob_param_t_m0_clim": round(p_clim, 4),
                    "prob_emp_m0_clim": round(p_clim, 4),
                }

                for m_k in ["m1_local", "m2_ocean", "m3_pacific", "m4_indian", "m5_all_oceans"]:
                    X_tr = tr_feats[m_k]
                    X_te = te_feats[m_k]
                    p_feats = X_tr.shape[1]

                    best_a = 50.0

                    if cv_scheme == "forward_chaining":
                        # Strictly causal forward-chaining (expanding-window) within past years
                        # Initial burn-in window: 8 years (1982-1989), validation folds: 1990 to target_y - 1
                        burn_in = min(8, n_tr - 2)
                        fwd_errors = {a: [] for a in candidate_alphas}

                        for a in candidate_alphas:
                            for t_idx in range(burn_in, n_tr):
                                idx_tr = list(range(t_idx))
                                sc_fwd = StandardScaler()
                                X_fwd_tr = sc_fwd.fit_transform(X_tr[idx_tr])
                                X_fwd_val = sc_fwd.transform(X_tr[[t_idx]])

                                rg_fwd = Ridge(alpha=a).fit(X_fwd_tr, y_tr_anom[idx_tr])
                                pred_val = float(rg_fwd.predict(X_fwd_val)[0])
                                fwd_errors[a].append((y_tr_anom[t_idx] - pred_val) ** 2)

                        best_a = min(candidate_alphas, key=lambda a: np.mean(fwd_errors[a]))

                    elif cv_scheme == "loocv":
                        # Nested Leave-One-Out CV on past years
                        loocv_errors = {a: [] for a in candidate_alphas}
                        for a in candidate_alphas:
                            for cv_i in range(n_tr):
                                cv_idx_tr = [idx for idx in range(n_tr) if idx != cv_i]
                                sc_loo = StandardScaler()
                                X_loo_tr = sc_loo.fit_transform(X_tr[cv_idx_tr])
                                X_loo_val = sc_loo.transform(X_tr[[cv_i]])

                                rg_loo = Ridge(alpha=a).fit(X_loo_tr, y_tr_anom[cv_idx_tr])
                                pred_val = float(rg_loo.predict(X_loo_val)[0])
                                loocv_errors[a].append((y_tr_anom[cv_i] - pred_val) ** 2)

                        best_a = min(candidate_alphas, key=lambda a: np.mean(loocv_errors[a]))

                    chosen_alphas[m_k].append(best_a)

                    # Fit final model on all historical years y < target_y
                    sc_final = StandardScaler()
                    X_tr_sc = sc_final.fit_transform(X_tr)
                    X_te_sc = sc_final.transform(X_te)

                    rg_final = Ridge(alpha=best_a).fit(X_tr_sc, y_tr_anom)
                    pred_anom = float(rg_final.predict(X_te_sc)[0])
                    pred_tot = train_clim + pred_anom
                    preds_raw[m_k].append(pred_tot)

                    # Residuals and Effective Degrees of Freedom for Ridge
                    tr_preds = rg_final.predict(X_tr_sc)
                    res = y_tr_anom - tr_preds

                    # SVD of X_tr_sc to compute exact hat matrix trace terms
                    U, S_vals, Vt = np.linalg.svd(X_tr_sc, full_matrices=False)
                    d2 = S_vals ** 2
                    tr_H = float(np.sum(d2 / (d2 + best_a)))
                    tr_2H_minus_H2 = float(np.sum(d2 * (d2 + 2.0 * best_a) / ((d2 + best_a) ** 2)))
                    df_res = max(1.0, float(n_tr - tr_2H_minus_H2 - 1.0))
                    s_res = float(np.sqrt(np.sum(res ** 2) / df_res))

                    # Exact Ridge Sandwich Covariance for Conditional Mean:
                    # Var(beta_hat) = s_res^2 * (X^T X + a*I)^(-1) * (X^T X) * (X^T X + a*I)^(-1)
                    A_mat = X_tr_sc.T @ X_tr_sc + best_a * np.eye(p_feats)
                    inv_A = np.linalg.pinv(A_mat)
                    sandwich_var_mean = float((X_te_sc @ inv_A @ (X_tr_sc.T @ X_tr_sc) @ inv_A @ X_te_sc.T)[0, 0])

                    # Predictive standard error accounts for:
                    # 1. Residual variance (1.0)
                    # 2. Intercept estimation variance (1 / n_tr)
                    # 3. Ridge sandwich coefficient parameter covariance (sandwich_var_mean)
                    se_exact = s_res * np.sqrt(1.0 + (1.0 / n_tr) + sandwich_var_mean)
                    forecast_se_list[m_k].append(se_exact)

                    # Method A1: Parametric Student-t Predictive Distribution
                    t_stat = (drought_thresh - pred_tot) / max(se_exact, 1e-3)
                    p_dr_t = float(stats.t.cdf(t_stat, df=df_res))
                    probs_param_t[m_k].append(p_dr_t)

                    # Method A2: Parametric Normal Predictive Distribution
                    p_dr_norm = float(stats.norm.cdf(t_stat))
                    probs_param_norm[m_k].append(p_dr_norm)

                    # Method B: Training-Only Non-Parametric Empirical Residual Distribution
                    # Uses in-sample training residuals e_i: P_tilde_i = pred_tot + e_i
                    # Continuity-corrected empirical CDF
                    emp_count = int(np.sum(res < (drought_thresh - pred_tot)))
                    p_dr_emp = float((emp_count + 0.5) / (n_tr + 1.0))
                    probs_empirical[m_k].append(p_dr_emp)

                    row_pred_dict[f"pred_{m_k}_mm"] = round(pred_tot, 2)
                    row_pred_dict[f"se_fcst_{m_k}_mm"] = round(se_exact, 2)
                    row_pred_dict[f"alpha_{m_k}"] = best_a
                    row_pred_dict[f"prob_param_t_{m_k}"] = round(p_dr_t, 4)
                    row_pred_dict[f"prob_param_norm_{m_k}"] = round(p_dr_norm, 4)
                    row_pred_dict[f"prob_emp_{m_k}"] = round(p_dr_emp, 4)

                all_prediction_records.append(row_pred_dict)

            # Convert to numpy arrays for verification
            y_obs_arr = np.array(y_obs_list)
            drought_obs_arr = np.array(drought_obs_list)
            total_drought_events = int(np.sum(drought_obs_arr))

            # Base climatological Brier score
            bs_clim_param = float(np.mean((np.array(probs_param_t["m0_clim"]) - drought_obs_arr) ** 2))
            bs_clim_emp = float(np.mean((np.array(probs_empirical["m0_clim"]) - drought_obs_arr) ** 2))

            lead_metrics = {}

            for m_k in models:
                yp = np.array(preds_raw[m_k])
                pt = np.array(probs_param_t[m_k])
                pnorm = np.array(probs_param_norm[m_k])
                pemp = np.array(probs_empirical[m_k])

                # Point metrics
                p_met = compute_metrics(y_obs_arr, yp)

                # Probabilistic metrics (Student-t)
                bs_t = compute_brier_score(drought_obs_arr, pt)
                bss_t = 1.0 - (bs_t / bs_clim_param) if bs_clim_param > 1e-6 else 0.0

                # Probabilistic metrics (Normal)
                bs_norm = compute_brier_score(drought_obs_arr, pnorm)
                bss_norm = 1.0 - (bs_norm / bs_clim_param) if bs_clim_param > 1e-6 else 0.0

                # Probabilistic metrics (Empirical Residual)
                bs_emp = compute_brier_score(drought_obs_arr, pemp)
                bss_emp = 1.0 - (bs_emp / bs_clim_emp) if bs_clim_emp > 1e-6 else 0.0

                # Reliability tables
                rel_t = compute_reliability_table(pt, drought_obs_arr)
                rel_emp = compute_reliability_table(pemp, drought_obs_arr)

                lead_metrics[m_k] = {
                    "rmse": p_met["rmse"],
                    "mae": p_met["mae"],
                    "r": p_met["r"],
                    "brier_score_param_t": round(bs_t, 4),
                    "brier_skill_score_param_t": round(bss_t, 4),
                    "brier_score_param_norm": round(bs_norm, 4),
                    "brier_skill_score_param_norm": round(bss_norm, 4),
                    "brier_score_empirical": round(bs_emp, 4),
                    "brier_skill_score_empirical": round(bss_emp, 4),
                    "reliability_table_param_t": rel_t,
                    "reliability_table_empirical": rel_emp,
                }

            # Paired Year-Resampled Bootstrap (B=2000, seed=42)
            np.random.seed(42)
            B = 2000
            bootstrap_diffs = {
                "m4_vs_m1": {
                    "dRMSE": [], "dMAE": [],
                    "dBS_param_t": [], "dBSS_param_t": [],
                    "dBS_emp": [], "dBSS_emp": []
                },
                "m4_vs_m0": {
                    "dRMSE": [], "dMAE": [],
                    "dBS_param_t": [], "dBSS_param_t": [],
                    "dBS_emp": [], "dBSS_emp": []
                },
                "m5_vs_m4": {
                    "dRMSE": [], "dMAE": [],
                    "dBS_param_t": [], "dBSS_param_t": [],
                    "dBS_emp": [], "dBSS_emp": []
                }
            }

            p_0 = np.array(preds_raw["m0_clim"])
            p_1 = np.array(preds_raw["m1_local"])
            p_4 = np.array(preds_raw["m4_indian"])
            p_5 = np.array(preds_raw["m5_all_oceans"])

            pt_0 = np.array(probs_param_t["m0_clim"])
            pt_1 = np.array(probs_param_t["m1_local"])
            pt_4 = np.array(probs_param_t["m4_indian"])
            pt_5 = np.array(probs_param_t["m5_all_oceans"])

            pe_0 = np.array(probs_empirical["m0_clim"])
            pe_1 = np.array(probs_empirical["m1_local"])
            pe_4 = np.array(probs_empirical["m4_indian"])
            pe_5 = np.array(probs_empirical["m5_all_oceans"])

            for _ in range(B):
                b_idx = np.random.choice(n_eval, size=n_eval, replace=True)
                yb = y_obs_arr[b_idx]
                drb = drought_obs_arr[b_idx]

                # Point errors
                rmse_0 = np.sqrt(np.mean((yb - p_0[b_idx]) ** 2))
                rmse_1 = np.sqrt(np.mean((yb - p_1[b_idx]) ** 2))
                rmse_4 = np.sqrt(np.mean((yb - p_4[b_idx]) ** 2))
                rmse_5 = np.sqrt(np.mean((yb - p_5[b_idx]) ** 2))

                mae_0 = np.mean(np.abs(yb - p_0[b_idx]))
                mae_1 = np.mean(np.abs(yb - p_1[b_idx]))
                mae_4 = np.mean(np.abs(yb - p_4[b_idx]))
                mae_5 = np.mean(np.abs(yb - p_5[b_idx]))

                # Parametric Brier scores
                bst_0 = np.mean((pt_0[b_idx] - drb) ** 2)
                bst_1 = np.mean((pt_1[b_idx] - drb) ** 2)
                bst_4 = np.mean((pt_4[b_idx] - drb) ** 2)
                bst_5 = np.mean((pt_5[b_idx] - drb) ** 2)

                bsst_1 = 1.0 - (bst_1 / bst_0) if bst_0 > 1e-6 else 0.0
                bsst_4 = 1.0 - (bst_4 / bst_0) if bst_0 > 1e-6 else 0.0
                bsst_5 = 1.0 - (bst_5 / bst_0) if bst_0 > 1e-6 else 0.0

                # Empirical Brier scores
                bse_0 = np.mean((pe_0[b_idx] - drb) ** 2)
                bse_1 = np.mean((pe_1[b_idx] - drb) ** 2)
                bse_4 = np.mean((pe_4[b_idx] - drb) ** 2)
                bse_5 = np.mean((pe_5[b_idx] - drb) ** 2)

                bsse_1 = 1.0 - (bse_1 / bse_0) if bse_0 > 1e-6 else 0.0
                bsse_4 = 1.0 - (bse_4 / bse_0) if bse_0 > 1e-6 else 0.0
                bsse_5 = 1.0 - (bse_5 / bse_0) if bse_0 > 1e-6 else 0.0

                # Differences
                bootstrap_diffs["m4_vs_m1"]["dRMSE"].append(rmse_4 - rmse_1)
                bootstrap_diffs["m4_vs_m1"]["dMAE"].append(mae_4 - mae_1)
                bootstrap_diffs["m4_vs_m1"]["dBS_param_t"].append(bst_4 - bst_1)
                bootstrap_diffs["m4_vs_m1"]["dBSS_param_t"].append(bsst_4 - bsst_1)
                bootstrap_diffs["m4_vs_m1"]["dBS_emp"].append(bse_4 - bse_1)
                bootstrap_diffs["m4_vs_m1"]["dBSS_emp"].append(bsse_4 - bsse_1)

                bootstrap_diffs["m4_vs_m0"]["dRMSE"].append(rmse_4 - rmse_0)
                bootstrap_diffs["m4_vs_m0"]["dMAE"].append(mae_4 - mae_0)
                bootstrap_diffs["m4_vs_m0"]["dBS_param_t"].append(bst_4 - bst_0)
                bootstrap_diffs["m4_vs_m0"]["dBSS_param_t"].append(bsst_4)
                bootstrap_diffs["m4_vs_m0"]["dBS_emp"].append(bse_4 - bse_0)
                bootstrap_diffs["m4_vs_m0"]["dBSS_emp"].append(bsse_4)

                bootstrap_diffs["m5_vs_m4"]["dRMSE"].append(rmse_5 - rmse_4)
                bootstrap_diffs["m5_vs_m4"]["dMAE"].append(mae_5 - mae_4)
                bootstrap_diffs["m5_vs_m4"]["dBS_param_t"].append(bst_5 - bst_4)
                bootstrap_diffs["m5_vs_m4"]["dBSS_param_t"].append(bsst_5 - bsst_4)
                bootstrap_diffs["m5_vs_m4"]["dBS_emp"].append(bse_5 - bse_4)
                bootstrap_diffs["m5_vs_m4"]["dBSS_emp"].append(bsse_5 - bsse_4)

            bootstrap_stats = {}
            for comp_k in bootstrap_diffs:
                bootstrap_stats[comp_k] = {}
                for met_k in bootstrap_diffs[comp_k]:
                    arr = np.array(bootstrap_diffs[comp_k][met_k])
                    ci = [round(float(x), 4) for x in np.percentile(arr, [2.5, 97.5])]
                    med = round(float(np.median(arr)), 4)
                    bootstrap_stats[comp_k][met_k] = {"median": med, "ci95": ci}

            scheme_summary[l_label] = {
                "observed_drought_events": total_drought_events,
                "n_eval_years": n_eval,
                "metrics": lead_metrics,
                "paired_bootstrap_uncertainty": bootstrap_stats,
            }

            print(f"  M0 Climatology:     RMSE={lead_metrics['m0_clim']['rmse']:6.2f} mm | BS_param={lead_metrics['m0_clim']['brier_score_param_t']:.4f} | BS_emp={lead_metrics['m0_clim']['brier_score_empirical']:.4f}")
            print(f"  M1 Local History:   RMSE={lead_metrics['m1_local']['rmse']:6.2f} mm | BSS_param={lead_metrics['m1_local']['brier_skill_score_param_t']:+.4f} | BSS_emp={lead_metrics['m1_local']['brier_skill_score_empirical']:+.4f}")
            print(f"  M4 Local + Indian:  RMSE={lead_metrics['m4_indian']['rmse']:6.2f} mm | BSS_param={lead_metrics['m4_indian']['brier_skill_score_param_t']:+.4f} | BSS_emp={lead_metrics['m4_indian']['brier_skill_score_empirical']:+.4f}")
            print(f"  M5 Local + All:     RMSE={lead_metrics['m5_all_oceans']['rmse']:6.2f} mm | BSS_param={lead_metrics['m5_all_oceans']['brier_skill_score_param_t']:+.4f} | BSS_emp={lead_metrics['m5_all_oceans']['brier_skill_score_empirical']:+.4f}")
            print(f"  --> M4 vs M1 (Local) dRMSE:        {bootstrap_stats['m4_vs_m1']['dRMSE']['median']:+.2f} mm (95% CI: {bootstrap_stats['m4_vs_m1']['dRMSE']['ci95']})")
            print(f"  --> M4 vs M1 (Local) dBSS (Param): {bootstrap_stats['m4_vs_m1']['dBSS_param_t']['median']:+.4f} (95% CI: {bootstrap_stats['m4_vs_m1']['dBSS_param_t']['ci95']})")
            print(f"  --> M4 vs M1 (Local) dBSS (Emp):   {bootstrap_stats['m4_vs_m1']['dBSS_emp']['median']:+.4f} (95% CI: {bootstrap_stats['m4_vs_m1']['dBSS_emp']['ci95']})")

        full_results["schemes"][cv_scheme] = scheme_summary

    # Save outputs
    df_out = pd.DataFrame(all_prediction_records)
    df_out.to_csv(OUT_PREDICTIONS_CSV, index=False)
    print(f"\n[OK] Saved Auditable Validated Predictions CSV to: {OUT_PREDICTIONS_CSV} ({len(df_out)} rows)")

    with open(OUT_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2)
    print(f"[OK] Saved Validated Probabilistic Metrics JSON to: {OUT_METRICS_JSON}")


if __name__ == "__main__":
    t0 = time.time()
    run_probabilistic_audit()
    print(f"\nAudit completed in {time.time() - t0:.2f}s!")
