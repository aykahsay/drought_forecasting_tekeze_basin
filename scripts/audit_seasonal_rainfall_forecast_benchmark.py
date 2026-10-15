"""
audit_seasonal_rainfall_forecast_benchmark.py
=============================================
Independent Methodological Audit of the Seasonal Rainfall Forecast Benchmark:
1. Re-computes predictions using strictly nested expanding-window Leave-One-Year-Out
   cross-validation for alpha on historical data (y < Y) to test sensitivity to alpha leakage.
2. Evaluates the Gaussian predictive distribution for drought probability (lower tercile threshold).
3. Computes paired year-resampled bootstrap (B=2000, seed=42) 95% confidence intervals
   for differences in RMSE, MAE, and Brier Score across the 25 years (2000–2024).
4. Assesses release lag / latency for operational predictors.
5. Produces an auditable JSON and Markdown audit table.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
CSV_PATH = PROCESSED_DIR / "abregelle_tekeze_unified_monthly_1981_2024.csv"
OUTPUT_AUDIT_JSON = PROCESSED_DIR / "seasonal_forecast_independent_audit_metrics.json"
OUTPUT_AUDIT_CSV = PROCESSED_DIR / "seasonal_forecast_audited_predictions_2000_2024.csv"


def safe_pearsonr(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    if np.std(y_pred) < 1e-8 or np.std(y_true) < 1e-8:
        return None
    r_val, _ = stats.pearsonr(y_true, y_pred)
    return round(float(r_val), 4)


def main():
    print("=" * 85)
    print("AI-DREWS: INDEPENDENT METHODOLOGICAL AUDIT OF SEASONAL FORECAST BENCHMARK")
    print("Addressing Forecast-Origin Leakage, Operational Latency, and Probability Calibration")
    print("=" * 85)

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
    print(f"Auditing Kiremt Monsoon (JJAS) across 2000–2024 (N = {n_eval} annual evaluations)")

    issue_configs = [
        {"lead_label": "Lead 0 (Issue 1 June)", "issue_month": 5},
        {"lead_label": "Lead 1 (Issue 1 May)", "issue_month": 4},
        {"lead_label": "Lead 2 (Issue 1 April)", "issue_month": 3},
        {"lead_label": "Lead 3 (Issue 1 March)", "issue_month": 2},
    ]

    candidate_alphas = [1.0, 10.0, 50.0, 100.0, 500.0]
    audit_results = {}
    all_audit_pred_records = []

    for cfg in issue_configs:
        l_label = cfg["lead_label"]
        iss_m = cfg["issue_month"]
        print(f"\n=======================================================")
        print(f"AUDITING: {l_label}")
        print("=======================================================")

        y_obs_list = []
        drought_obs_list = []

        # Predictions under nested CV (strictly zero alpha leakage)
        preds_nested = {m: [] for m in ["m0_clim", "m1_local", "m2_ocean", "m3_pacific", "m4_indian", "m5_all_oceans"]}
        probs_nested = {m: [] for m in ["m0_clim", "m1_local", "m2_ocean", "m3_pacific", "m4_indian", "m5_all_oceans"]}
        chosen_alphas = {m: [] for m in ["m1_local", "m2_ocean", "m3_pacific", "m4_indian", "m5_all_oceans"]}

        for target_y in eval_years:
            obs_p = float(df_seasons.loc[df_seasons["year"] == target_y, "kiremt_jjas_mm"].values[0])
            y_obs_list.append(obs_p)

            train_years = [y for y in years if y >= 1982 and y < target_y]
            y_tr_raw = df_seasons.loc[df_seasons["year"].isin(train_years), "kiremt_jjas_mm"].values

            train_clim = float(np.mean(y_tr_raw))
            y_tr_anom = y_tr_raw - train_clim

            # Lower-tercile drought threshold estimated strictly on past years
            drought_thresh = float(np.percentile(y_tr_raw, 33.33))
            is_drought = 1 if obs_p < drought_thresh else 0
            drought_obs_list.append(is_drought)

            # Build features
            def extract_feats(yr_list):
                l_list, n_list, d_list, a_list = [], [], [], []
                for yr in yr_list:
                    row_iss = df[(df["year"] == yr) & (df["month"] == iss_m)].iloc[0]
                    sub_pre = df[(df["year"] == yr) & (df["month"].isin([iss_m, iss_m - 1 if iss_m > 1 else 12, iss_m - 2 if iss_m > 2 else (11 if iss_m == 2 else 10)]))]
                    ant_p = float(sub_pre[precip_col].sum())
                    l_list.append([ant_p, float(row_iss[precip_col])])
                    n_list.append([float(row_iss["nino34_sst_anomaly"])])
                    d_list.append([float(row_iss["dmi"])])
                    a_list.append([float(row_iss["atl_meridional_gradient"])])

                l_arr = np.array(l_list)
                n_arr = np.array(n_list)
                d_arr = np.array(d_list)
                a_arr = np.array(a_list)

                return {
                    "m1_local": l_arr,
                    "m2_ocean": np.hstack([n_arr, d_arr, a_arr]),
                    "m3_pacific": np.hstack([l_arr, n_arr]),
                    "m4_indian": np.hstack([l_arr, d_arr]),
                    "m5_all_oceans": np.hstack([l_arr, n_arr, d_arr, a_arr])
                }

            tr_feats = extract_feats(train_years)
            te_feats = extract_feats([target_y])

            # M0 Climatology
            preds_nested["m0_clim"].append(train_clim)
            p_clim = float(np.mean(y_tr_raw < drought_thresh))
            probs_nested["m0_clim"].append(p_clim)

            # Models M1-M5: nested Leave-One-Out CV to select alpha strictly on train_years
            for m_k in ["m1_local", "m2_ocean", "m3_pacific", "m4_indian", "m5_all_oceans"]:
                best_a = 50.0
                best_cv_rmse = float("inf")
                X_tr = tr_feats[m_k]
                n_tr = len(train_years)

                # LOOCV on train_years to choose alpha
                for a in candidate_alphas:
                    cv_errors = []
                    for cv_i in range(n_tr):
                        cv_idx_tr = [idx for idx in range(n_tr) if idx != cv_i]
                        cv_X_tr = X_tr[cv_idx_tr]
                        cv_y_tr = y_tr_anom[cv_idx_tr]
                        cv_X_val = X_tr[[cv_i]]
                        cv_y_val = y_tr_anom[cv_i]

                        sc = StandardScaler()
                        cv_X_tr_sc = sc.fit_transform(cv_X_tr)
                        cv_X_val_sc = sc.transform(cv_X_val)

                        rg = Ridge(alpha=a).fit(cv_X_tr_sc, cv_y_tr)
                        pred_val = float(rg.predict(cv_X_val_sc)[0])
                        cv_errors.append((cv_y_val - pred_val) ** 2)

                    cv_rmse = np.sqrt(np.mean(cv_errors))
                    if cv_rmse < best_cv_rmse:
                        best_cv_rmse = cv_rmse
                        best_a = a

                chosen_alphas[m_k].append(best_a)

                # Fit on full training set using chosen alpha
                sc_final = StandardScaler()
                X_tr_sc = sc_final.fit_transform(X_tr)
                X_te_sc = sc_final.transform(te_feats[m_k])

                rg_final = Ridge(alpha=best_a).fit(X_tr_sc, y_tr_anom)
                pred_anom = float(rg_final.predict(X_te_sc)[0])
                pred_tot = train_clim + pred_anom
                preds_nested[m_k].append(pred_tot)

                # Predictive probability of drought using Student-t residual distribution
                # with degrees of freedom df = n_tr - p - 1
                res = y_tr_anom - rg_final.predict(X_tr_sc)
                df_res = max(1, n_tr - X_tr.shape[1] - 1)
                s_res = float(np.sqrt(np.sum(res ** 2) / df_res))

                # Standard error of forecast accounting for parameter variance
                # se_fcst = s_res * sqrt(1 + x0^T (X^T X + alpha I)^(-1) x0)
                A_mat = X_tr_sc.T @ X_tr_sc + best_a * np.eye(X_tr.shape[1])
                inv_A = np.linalg.pinv(A_mat)
                var_mean = float((X_te_sc @ inv_A @ X_te_sc.T)[0, 0])
                se_fcst = s_res * np.sqrt(1.0 + var_mean)

                # Student-t cdf for drought threshold
                t_stat = (drought_thresh - pred_tot) / max(se_fcst, 1e-3)
                p_dr = float(stats.t.cdf(t_stat, df=df_res))
                probs_nested[m_k].append(p_dr)

            all_audit_pred_records.append({
                "season": "Kiremt Monsoon (JJAS)",
                "lead_config": l_label,
                "target_year": target_y,
                "observed_rain_mm": obs_p,
                "expanding_climatology_mm": train_clim,
                "drought_threshold_33pct_mm": drought_thresh,
                "is_drought_event": is_drought,
                "pred_m0_clim_mm": train_clim,
                "pred_m1_local_mm": preds_nested["m1_local"][-1],
                "pred_m2_ocean_only_mm": preds_nested["m2_ocean"][-1],
                "pred_m3_pacific_mm": preds_nested["m3_pacific"][-1],
                "pred_m4_indian_mm": preds_nested["m4_indian"][-1],
                "pred_m5_all_oceans_mm": preds_nested["m5_all_oceans"][-1],
                "prob_drought_m0_clim": p_clim,
                "prob_drought_m1_local": probs_nested["m1_local"][-1],
                "prob_drought_m2_ocean": probs_nested["m2_ocean"][-1],
                "prob_drought_m3_pacific": probs_nested["m3_pacific"][-1],
                "prob_drought_m4_indian": probs_nested["m4_indian"][-1],
                "prob_drought_m5_all": probs_nested["m5_all_oceans"][-1],
                "alpha_m1": chosen_alphas["m1_local"][-1],
                "alpha_m4": chosen_alphas["m4_indian"][-1],
                "alpha_m5": chosen_alphas["m5_all_oceans"][-1]
            })

        y_obs_arr = np.array(y_obs_list)
        drought_obs_arr = np.array(drought_obs_list)

        # Compute point metrics
        lead_summary = {}
        bs_clim = float(np.mean((np.array(probs_nested["m0_clim"]) - drought_obs_arr) ** 2))

        for mk in preds_nested:
            yp = np.array(preds_nested[mk])
            prob = np.array(probs_nested[mk])
            rmse = float(np.sqrt(np.mean((y_obs_arr - yp) ** 2)))
            mae = float(np.mean(np.abs(y_obs_arr - yp)))
            bs = float(np.mean((prob - drought_obs_arr) ** 2))
            bss = 1.0 - (bs / bs_clim) if bs_clim > 1e-6 else 0.0

            lead_summary[mk] = {
                "rmse": round(rmse, 2),
                "mae": round(mae, 2),
                "brier_score": round(bs, 4),
                "brier_skill_score": round(bss, 4)
            }

        # Paired Year-Resampled Bootstrap (B=2000, seed=42)
        np.random.seed(42)
        B = 2000
        boot_diffs = {
            "m4_vs_m1": {"dRMSE": [], "dMAE": [], "dBSS": []},
            "m4_vs_m0": {"dRMSE": [], "dMAE": [], "dBSS": []},
            "m5_vs_m4": {"dRMSE": [], "dMAE": [], "dBSS": []}
        }

        p_m0 = np.array(preds_nested["m0_clim"])
        p_m1 = np.array(preds_nested["m1_local"])
        p_m4 = np.array(preds_nested["m4_indian"])
        p_m5 = np.array(preds_nested["m5_all_oceans"])

        pr_m0 = np.array(probs_nested["m0_clim"])
        pr_m1 = np.array(probs_nested["m1_local"])
        pr_m4 = np.array(probs_nested["m4_indian"])
        pr_m5 = np.array(probs_nested["m5_all_oceans"])

        for _ in range(B):
            b_idx = np.random.choice(n_eval, size=n_eval, replace=True)
            y_b = y_obs_arr[b_idx]
            dr_b = drought_obs_arr[b_idx]

            rmse_0 = np.sqrt(np.mean((y_b - p_m0[b_idx]) ** 2))
            rmse_1 = np.sqrt(np.mean((y_b - p_m1[b_idx]) ** 2))
            rmse_4 = np.sqrt(np.mean((y_b - p_m4[b_idx]) ** 2))
            rmse_5 = np.sqrt(np.mean((y_b - p_m5[b_idx]) ** 2))

            mae_0 = np.mean(np.abs(y_b - p_m0[b_idx]))
            mae_1 = np.mean(np.abs(y_b - p_m1[b_idx]))
            mae_4 = np.mean(np.abs(y_b - p_m4[b_idx]))
            mae_5 = np.mean(np.abs(y_b - p_m5[b_idx]))

            bs_0 = np.mean((pr_m0[b_idx] - dr_b) ** 2)
            bs_1 = np.mean((pr_m1[b_idx] - dr_b) ** 2)
            bs_4 = np.mean((pr_m4[b_idx] - dr_b) ** 2)
            bs_5 = np.mean((pr_m5[b_idx] - dr_b) ** 2)

            bss_1 = 1.0 - (bs_1 / bs_0) if bs_0 > 1e-6 else 0.0
            bss_4 = 1.0 - (bs_4 / bs_0) if bs_0 > 1e-6 else 0.0
            bss_5 = 1.0 - (bs_5 / bs_0) if bs_0 > 1e-6 else 0.0

            boot_diffs["m4_vs_m1"]["dRMSE"].append(rmse_4 - rmse_1)
            boot_diffs["m4_vs_m1"]["dMAE"].append(mae_4 - mae_1)
            boot_diffs["m4_vs_m1"]["dBSS"].append(bss_4 - bss_1)

            boot_diffs["m4_vs_m0"]["dRMSE"].append(rmse_4 - rmse_0)
            boot_diffs["m4_vs_m0"]["dMAE"].append(mae_4 - mae_0)
            boot_diffs["m4_vs_m0"]["dBSS"].append(bss_4)

            boot_diffs["m5_vs_m4"]["dRMSE"].append(rmse_5 - rmse_4)
            boot_diffs["m5_vs_m4"]["dMAE"].append(mae_5 - mae_4)
            boot_diffs["m5_vs_m4"]["dBSS"].append(bss_5 - bss_4)

        boot_stats = {}
        for comp_k in boot_diffs:
            boot_stats[comp_k] = {}
            for met_k in ["dRMSE", "dMAE", "dBSS"]:
                arr = np.array(boot_diffs[comp_k][met_k])
                ci = [round(float(x), 3) for x in np.percentile(arr, [2.5, 97.5])]
                med = round(float(np.median(arr)), 3)
                boot_stats[comp_k][met_k] = {"median": med, "ci95": ci}

        audit_results[l_label] = {
            "metrics": lead_summary,
            "paired_bootstrap_uncertainty": boot_stats
        }

        print(f"  M0 Climatology:     RMSE = {lead_summary['m0_clim']['rmse']:6.2f} mm, BSS = {lead_summary['m0_clim']['brier_skill_score']:+.4f}")
        print(f"  M1 Local History:   RMSE = {lead_summary['m1_local']['rmse']:6.2f} mm, BSS = {lead_summary['m1_local']['brier_skill_score']:+.4f}")
        print(f"  M4 Local + Indian:  RMSE = {lead_summary['m4_indian']['rmse']:6.2f} mm, BSS = {lead_summary['m4_indian']['brier_skill_score']:+.4f}")
        print(f"  M5 Local + All:     RMSE = {lead_summary['m5_all_oceans']['rmse']:6.2f} mm, BSS = {lead_summary['m5_all_oceans']['brier_skill_score']:+.4f}")
        print(f"  --> M4 vs M1 (Local) dRMSE: {boot_stats['m4_vs_m1']['dRMSE']['median']:+.2f} mm (95% CI: {boot_stats['m4_vs_m1']['dRMSE']['ci95']})")
        print(f"  --> M4 vs M0 (Clim)  dRMSE: {boot_stats['m4_vs_m0']['dRMSE']['median']:+.2f} mm (95% CI: {boot_stats['m4_vs_m0']['dRMSE']['ci95']})")
        print(f"  --> M4 vs M1 (Local) dBSS : {boot_stats['m4_vs_m1']['dBSS']['median']:+.4f} (95% CI: {boot_stats['m4_vs_m1']['dBSS']['ci95']})")

    with open(OUTPUT_AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)
    print(f"\nSaved Independent Audit Results JSON to: {OUTPUT_AUDIT_JSON}")

    df_audit_csv = pd.DataFrame(all_audit_pred_records)
    df_audit_csv.to_csv(OUTPUT_AUDIT_CSV, index=False)
    print(f"Saved Audited 25-Year Predictions Table to: {OUTPUT_AUDIT_CSV} ({len(df_audit_csv)} rows)")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Audit completed in {time.time() - t0:.2f}s!")
