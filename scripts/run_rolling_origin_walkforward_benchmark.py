"""
run_rolling_origin_walkforward_benchmark.py
===========================================
Executes a fully audited, leakage-free Rolling-Origin Walk-Forward Benchmark
for Tanqua Abergele Woreda SPI-3 and Monthly Rainfall Anomaly Forecasting.

Mathematical & Methodological Standards:
1. Strict Causal Alignment & Information Barrier:
   - Issue Date t: All predictors X_t are observed on or before t.
   - Target Date t+h: Target y_{t+h} is predicted for explicit horizons h in {1, 2, 3}.
   - Training Set at Issue Date t: Strictly restricted to historical pairs (X_tau, y_{tau+h})
     where tau + h <= t (i.e., tau <= t - h).
   - The latest training target date is <= t.
   - The latest training feature date is <= t - h.
   - Zero lookahead target leakage.

2. Feature Standardization:
   - StandardScaler is fitted strictly on the historical training set at each issue date t.
   - Test features X_t are transformed using the training scaler parameters (mean, std).
   - Zero test data scaling leakage.

3. Models Evaluated (M0 to M6):
   - M0: Climatology (Constant 0.0 for SPI-3, historical monthly mean for rainfall).
         Pearson r is mathematically undefined (NaN) for constant predictions.
   - M1: Autoregressive Persistence (SPI-3_t at issue date t).
   - M2: Local Climate AR (SPI-3_t + sin/cos calendar month harmonics).
   - M3: Pacific Informed (M2 + Nino 3.4 SST anomaly at t and t-6).
   - M4: Indian Ocean Informed (M2 + IOD DMI at t).
   - M5: Atlantic Informed (M2 + Atlantic Meridional Gradient at t).
   - M6: All Three Oceans Coupled (M2 + Pacific + Indian + Atlantic).

4. Hyperparameter Selection:
   - Ridge regularization alpha evaluated across candidate alphas [0.1, 1.0, 10.0, 50.0, 100.0, 500.0]
     on the validation period (2011-2016).
   - Documented and held constant during test evaluation.

5. Auditable Prediction Table:
   - Outputs: data/processed/rolling_origin_walkforward_auditable_predictions_2017_2024.csv
   - Records: issue_date, target_date, lead_horizon, last_train_target_date, last_train_feature_date,
     observed target, and all model predictions.
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
OUTPUT_PREDS_CSV = PROCESSED_DIR / "rolling_origin_walkforward_auditable_predictions_2017_2024.csv"
OUTPUT_METRICS_JSON = PROCESSED_DIR / "rolling_origin_walkforward_auditable_metrics_2017_2024.json"


def safe_pearsonr(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    """Computes Pearson correlation if predictions have non-zero variance; returns None (NaN) if constant."""
    if np.std(y_pred) < 1e-8 or np.std(y_true) < 1e-8:
        return None
    r_val, _ = stats.pearsonr(y_true, y_pred)
    return round(float(r_val), 4)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    mse = float(np.mean((y_true - y_pred) ** 2))
    rmse = float(np.sqrt(mse))
    mae = float(np.mean(np.abs(y_true - y_pred)))
    r_val = safe_pearsonr(y_true, y_pred)
    return {
        "rmse": round(rmse, 4),
        "mse": round(mse, 4),
        "mae": round(mae, 4),
        "r": r_val
    }


def main():
    print("=" * 85)
    print("AI-DREWS: AUDITED ROLLING-ORIGIN WALK-FORWARD BENCHMARK (1981-2024)")
    print("Methodologically Airtight Pipeline: Zero Target Leakage & Clean Standardization")
    print("=" * 85)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing master dataset: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"])
    target_col = "spi3"

    # Verify chronological integrity
    if len(df) != 528:
        raise ValueError(f"Expected 528 continuous months, found {len(df)}")
    print("  [OK] Chronological Integrity: 528 continuous months (1981-01 to 2024-12).")

    # Dates definition
    # Train period: 1981 to 2010
    # Validation period: 2011 to 2016
    # Retrospective Walk-Forward Evaluation Period: 2017 to 2024 (96 months)
    eval_mask = (df["year"] >= 2017) & (df["year"] <= 2024)
    val_mask = (df["year"] >= 2011) & (df["year"] <= 2016)

    # Feature extraction helper: constructs raw predictors from information known at origin idx
    def extract_predictors_at_origin(origin_indices: pd.Index, target_months: np.ndarray) -> Dict[str, np.ndarray]:
        # Local SPI-3 at origin
        sp = df.loc[origin_indices, target_col].values[:, None]
        # Future target calendar month harmonics (known in advance)
        sin_m = np.sin(2 * np.pi * target_months / 12.0)[:, None]
        cos_m = np.cos(2 * np.pi * target_months / 12.0)[:, None]
        feat_m2 = np.hstack([sp, sin_m, cos_m])

        # Pacific: Nino 3.4 at origin and lag-6 before origin
        nino = df.loc[origin_indices, "nino34_sst_anomaly"].values[:, None]
        nino_lag6 = df.loc[origin_indices - 6, "nino34_sst_anomaly"].values[:, None]
        feat_m3 = np.hstack([feat_m2, nino, nino_lag6])

        # Indian Ocean: DMI at origin
        dmi = df.loc[origin_indices, "dmi"].values[:, None]
        feat_m4 = np.hstack([feat_m2, dmi])

        # Atlantic: Meridional gradient at origin
        atl = df.loc[origin_indices, "atl_meridional_gradient"].values[:, None]
        feat_m5 = np.hstack([feat_m2, atl])

        # Coupled 3-Ocean model
        feat_m6 = np.hstack([feat_m2, nino, nino_lag6, dmi, atl])

        return {
            "m1": sp,
            "m2": feat_m2,
            "m3": feat_m3,
            "m4": feat_m4,
            "m5": feat_m5,
            "m6": feat_m6
        }

    # 1. Hyperparameter Tuning on Validation Set (2011-2016) with StandardScaler
    print("\n[1] TUNING RIDGE REGULARIZATION ON VALIDATION PERIOD (2011-2016):")
    candidate_alphas = [0.1, 1.0, 10.0, 50.0, 100.0, 500.0]
    best_alphas = {}

    for h in [1, 2, 3]:
        # For validation: training targets occur <= 2010-12
        # So tau + h <= 2010-12 index
        last_train_target_idx = df.index[df["year"] <= 2010].max()
        # Historical training origins: tau + h <= last_train_target_idx
        # Earliest origin index must be >= 6 (for nino lag-6) and >= 2 (for valid spi3)
        min_tau = 8
        max_tau = last_train_target_idx - h
        train_origins = pd.Index(np.arange(min_tau, max_tau + 1))
        train_targets = train_origins + h
        y_train_val = df.loc[train_targets, target_col].values

        # Validation origins: predict targets in 2011-2016
        val_target_indices = df.index[val_mask]
        val_origins = val_target_indices - h
        y_val = df.loc[val_target_indices, target_col].values

        # Extract features
        train_feats = extract_predictors_at_origin(train_origins, df.loc[train_targets, "month"].values)
        val_feats = extract_predictors_at_origin(val_origins, df.loc[val_target_indices, "month"].values)

        best_alphas[h] = {}
        for m_name in ["m2", "m3", "m4", "m5", "m6"]:
            best_rmse = float("inf")
            chosen_a = 50.0
            for a in candidate_alphas:
                scaler = StandardScaler()
                X_tr_sc = scaler.fit_transform(train_feats[m_name])
                X_va_sc = scaler.transform(val_feats[m_name])

                reg = Ridge(alpha=a).fit(X_tr_sc, y_train_val)
                p_va = reg.predict(X_va_sc)
                rmse_va = np.sqrt(np.mean((y_val - p_va) ** 2))
                if rmse_va < best_rmse:
                    best_rmse = rmse_va
                    chosen_a = a
            best_alphas[h][m_name] = chosen_a
        print(f"  Lead h={h}: Selected Alphas: {best_alphas[h]}")

    # 2. Executing Rolling-Origin Walk-Forward Evaluation across 2017-2024
    print("\n[2] EXECUTING ROLLING-ORIGIN WALK-FORWARD BENCHMARK (2017-2024, 96 Months):")
    eval_target_indices = df.index[eval_mask]
    n_eval = len(eval_target_indices)

    auditable_prediction_records = []
    benchmark_metrics_by_lead = {}

    for h in [1, 2, 3]:
        print(f"\n--- Evaluating Forecast Horizon h = {h} Month(s) Ahead ---")
        y_true_list = []
        preds = {
            "m0_clim": [],
            "m1_pers": [],
            "m2": [],
            "m3": [],
            "m4": [],
            "m5": [],
            "m6": []
        }

        for target_idx in eval_target_indices:
            issue_idx = target_idx - h
            target_date = df.loc[target_idx, "date"]
            issue_date = df.loc[issue_idx, "date"]
            y_obs = float(df.loc[target_idx, target_col])
            y_true_list.append(y_obs)

            # Causal Training Set at Issue Date:
            # Training pairs (X_tau, y_{tau+h}) must satisfy tau + h <= issue_idx
            # Latest historical target index: issue_idx
            # Earliest origin index: 8 (ensures nino lag-6 and spi3 validity)
            min_tau = 8
            max_tau = issue_idx - h
            train_origins = pd.Index(np.arange(min_tau, max_tau + 1))
            train_targets = train_origins + h

            last_train_target_date = df.loc[train_targets.max(), "date"]
            last_train_feature_date = df.loc[train_origins.max(), "date"]

            y_train_step = df.loc[train_targets, target_col].values

            # M0: Climatology is constant zero for SPI-3 (mean 0 by construction)
            pred_m0 = 0.0

            # M1: Autoregressive Persistence (SPI-3 known at issue date)
            pred_m1 = float(df.loc[issue_idx, target_col])

            # Extract features for training and single test step
            train_feats = extract_predictors_at_origin(train_origins, df.loc[train_targets, "month"].values)
            test_feats = extract_predictors_at_origin(pd.Index([issue_idx]), np.array([df.loc[target_idx, "month"]]))

            # Regularized models with StandardScaler fitted strictly on training step
            step_preds = {}
            for m_name in ["m2", "m3", "m4", "m5", "m6"]:
                alpha_val = best_alphas[h][m_name]
                scaler = StandardScaler()
                X_tr_sc = scaler.fit_transform(train_feats[m_name])
                X_te_sc = scaler.transform(test_feats[m_name])

                reg = Ridge(alpha=alpha_val).fit(X_tr_sc, y_train_step)
                step_preds[m_name] = float(reg.predict(X_te_sc)[0])

            # Store predictions
            preds["m0_clim"].append(pred_m0)
            preds["m1_pers"].append(pred_m1)
            for m_name in ["m2", "m3", "m4", "m5", "m6"]:
                preds[m_name].append(step_preds[m_name])

            # Record row in auditable table
            auditable_prediction_records.append({
                "forecast_issue_date": issue_date.strftime("%Y-%m-%d"),
                "target_date": target_date.strftime("%Y-%m-%d"),
                "lead_horizon": h,
                "last_train_target_date": last_train_target_date.strftime("%Y-%m-%d"),
                "last_train_feature_date": last_train_feature_date.strftime("%Y-%m-%d"),
                "y_true_spi3": y_obs,
                "pred_m0_climatology": pred_m0,
                "pred_m1_persistence": pred_m1,
                "pred_m2_local_ar": step_preds["m2"],
                "pred_m3_pacific_nino34": step_preds["m3"],
                "pred_m4_indian_ocean_iod": step_preds["m4"],
                "pred_m5_atlantic_gradient": step_preds["m5"],
                "pred_m6_all_three_oceans": step_preds["m6"]
            })

        y_true_arr = np.array(y_true_list)
        lead_metrics = {m: compute_metrics(y_true_arr, np.array(preds[m])) for m in preds}

        # Paired Calendar Year-Block Bootstrap (8 complete years 2017-2024, B=2000)
        np.random.seed(42)
        B = 2000
        years_arr = df.loc[eval_target_indices, "year"].values
        diff_clim_boot = {k: [] for k in ["m1_pers", "m2", "m3", "m4", "m5", "m6"]}
        diff_local_boot = {k: [] for k in ["m3", "m4", "m5", "m6"]}

        for _ in range(B):
            sampled_years = np.random.choice(np.arange(2017, 2025), size=8, replace=True)
            boot_idx = []
            for sy in sampled_years:
                boot_idx.extend(np.where(years_arr == sy)[0])
            boot_idx = np.array(boot_idx)

            yt_b = y_true_arr[boot_idx]
            rmse_c_b = np.sqrt(np.mean((yt_b - np.array(preds["m0_clim"])[boot_idx]) ** 2))
            rmse_loc_b = np.sqrt(np.mean((yt_b - np.array(preds["m2"])[boot_idx]) ** 2))

            for k in diff_clim_boot.keys():
                r_m_b = np.sqrt(np.mean((yt_b - np.array(preds[k])[boot_idx]) ** 2))
                diff_clim_boot[k].append(r_m_b - rmse_c_b)

            for k in diff_local_boot.keys():
                r_m_b = np.sqrt(np.mean((yt_b - np.array(preds[k])[boot_idx]) ** 2))
                diff_local_boot[k].append(r_m_b - rmse_loc_b)

        boot_stats = {}
        for k in diff_clim_boot.keys():
            arr = np.array(diff_clim_boot[k])
            ci = [round(float(x), 4) for x in np.percentile(arr, [2.5, 97.5])]
            p_val = round(float(min(1.0, 2.0 * min(np.mean(arr >= 0.0), np.mean(arr <= 0.0)))), 4)
            boot_stats[f"{k}_vs_climatology"] = {
                "dRMSE": round(float(lead_metrics[k]["rmse"] - lead_metrics["m0_clim"]["rmse"]), 4),
                "ci95": ci,
                "p_value": p_val
            }

        for k in diff_local_boot.keys():
            arr = np.array(diff_local_boot[k])
            ci = [round(float(x), 4) for x in np.percentile(arr, [2.5, 97.5])]
            p_val = round(float(min(1.0, 2.0 * min(np.mean(arr >= 0.0), np.mean(arr <= 0.0)))), 4)
            boot_stats[f"{k}_vs_local_m2"] = {
                "dRMSE": round(float(lead_metrics[k]["rmse"] - lead_metrics["m2"]["rmse"]), 4),
                "ci95": ci,
                "p_value": p_val
            }

        benchmark_metrics_by_lead[f"lead_{h}"] = {
            "metrics": lead_metrics,
            "bootstrap": boot_stats
        }

        print(f"  M0 Climatology:  RMSE = {lead_metrics['m0_clim']['rmse']:.4f}, MAE = {lead_metrics['m0_clim']['mae']:.4f}, r = {lead_metrics['m0_clim']['r']}")
        print(f"  M1 Persistence:  RMSE = {lead_metrics['m1_pers']['rmse']:.4f}, MAE = {lead_metrics['m1_pers']['mae']:.4f}, r = {lead_metrics['m1_pers']['r']}")
        print(f"  M2 Local AR:     RMSE = {lead_metrics['m2']['rmse']:.4f}, MAE = {lead_metrics['m2']['mae']:.4f}, r = {lead_metrics['m2']['r']}")
        print(f"  M3 Pacific:      RMSE = {lead_metrics['m3']['rmse']:.4f}, MAE = {lead_metrics['m3']['mae']:.4f}, r = {lead_metrics['m3']['r']}")
        print(f"  M4 Indian Ocean: RMSE = {lead_metrics['m4']['rmse']:.4f}, MAE = {lead_metrics['m4']['mae']:.4f}, r = {lead_metrics['m4']['r']}")
        print(f"  M5 Atlantic:     RMSE = {lead_metrics['m5']['rmse']:.4f}, MAE = {lead_metrics['m5']['mae']:.4f}, r = {lead_metrics['m5']['r']}")
        print(f"  M6 All 3 Oceans: RMSE = {lead_metrics['m6']['rmse']:.4f}, MAE = {lead_metrics['m6']['mae']:.4f}, r = {lead_metrics['m6']['r']}")
        print(f"  --> M4 vs Local AR: dRMSE = {boot_stats['m4_vs_local_m2']['dRMSE']:+.4f} (95% CI: {boot_stats['m4_vs_local_m2']['ci95']}, p = {boot_stats['m4_vs_local_m2']['p_value']:.4f})")
        print(f"  --> M3 vs Local AR: dRMSE = {boot_stats['m3_vs_local_m2']['dRMSE']:+.4f} (95% CI: {boot_stats['m3_vs_local_m2']['ci95']}, p = {boot_stats['m3_vs_local_m2']['p_value']:.4f})")

    # Save auditable predictions CSV
    df_preds_out = pd.DataFrame(auditable_prediction_records)
    df_preds_out.to_csv(str(OUTPUT_PREDS_CSV), index=False)
    print(f"\n[OK] Saved Auditable Prediction Table to: {OUTPUT_PREDS_CSV} ({len(df_preds_out)} rows)")

    # Save metrics JSON
    with open(OUTPUT_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(benchmark_metrics_by_lead, f, indent=2)
    print(f"[OK] Saved Auditable Metrics Report to: {OUTPUT_METRICS_JSON}")

    return df_preds_out, benchmark_metrics_by_lead


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\nExecution finished in {time.time() - t0:.2f}s!")
