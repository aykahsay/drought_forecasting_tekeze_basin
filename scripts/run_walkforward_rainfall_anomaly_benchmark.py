"""
run_walkforward_rainfall_anomaly_benchmark.py
=============================================
Evaluates whether ocean indices predict genuinely FUTURE monthly rainfall anomalies
(zero temporal window overlap across all lead horizons h in {1, 2, 3}).

Target:
  y_{t+h} = P_{t+h} - Climatological_Monthly_Mean(month_{t+h})
  measured in millimeters (mm) of rainfall in Tanqua Abergele.
  Zero moving-window overlap: rainfall at t+1, t+2, t+3 is strictly non-overlapping.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

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
OUTPUT_PREDS_CSV = PROCESSED_DIR / "walkforward_rainfall_anomaly_predictions_2017_2024.csv"
OUTPUT_METRICS_JSON = PROCESSED_DIR / "walkforward_rainfall_anomaly_metrics_2017_2024.json"


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
    return {
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "r": r_val
    }


def main():
    print("=" * 85)
    print("AI-DREWS: PURE FUTURE RAINFALL ANOMALY BENCHMARK (1981-2024)")
    print("Zero Moving-Window Overlap: Evaluating Forecasts of Purely Future Monthly Rain (mm)")
    print("=" * 85)

    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"])
    precip_col = "chirps_abregelle_precip_mm"

    # Compute monthly climatology strictly on pre-2011 historical baseline (1981-2010)
    base_mask = (df["year"] >= 1981) & (df["year"] <= 2010)
    monthly_clim = df[base_mask].groupby("month")[precip_col].mean().to_dict()

    # Define target as anomaly from pre-2011 monthly climatology
    df["precip_anomaly_mm"] = df.apply(lambda r: r[precip_col] - monthly_clim[r["month"]], axis=1)
    target_col = "precip_anomaly_mm"

    eval_mask = (df["year"] >= 2017) & (df["year"] <= 2024)
    eval_target_indices = df.index[eval_mask]

    def extract_predictors_at_origin(origin_indices: pd.Index, target_months: np.ndarray) -> Dict[str, np.ndarray]:
        # Local rainfall anomaly at origin
        pa = df.loc[origin_indices, target_col].values[:, None]
        # Future target calendar month harmonics
        sin_m = np.sin(2 * np.pi * target_months / 12.0)[:, None]
        cos_m = np.cos(2 * np.pi * target_months / 12.0)[:, None]
        feat_m2 = np.hstack([pa, sin_m, cos_m])

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
            "m1": pa,
            "m2": feat_m2,
            "m3": feat_m3,
            "m4": feat_m4,
            "m5": feat_m5,
            "m6": feat_m6
        }

    results = {}
    prediction_records = []

    for h in [1, 2, 3]:
        print(f"\n--- Evaluating Pure Future Monthly Rainfall Anomaly at Horizon h = {h} Month(s) Ahead ---")
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

            min_tau = 8
            max_tau = issue_idx - h
            train_origins = pd.Index(np.arange(min_tau, max_tau + 1))
            train_targets = train_origins + h
            y_train_step = df.loc[train_targets, target_col].values

            # M0 Climatology for anomaly is constant 0.0
            pred_m0 = 0.0
            # M1 Persistence of monthly rainfall anomaly
            pred_m1 = float(df.loc[issue_idx, target_col])

            train_feats = extract_predictors_at_origin(train_origins, df.loc[train_targets, "month"].values)
            test_feats = extract_predictors_at_origin(pd.Index([issue_idx]), np.array([df.loc[target_idx, "month"]]))

            step_preds = {}
            for m_name in ["m2", "m3", "m4", "m5", "m6"]:
                scaler = StandardScaler()
                X_tr_sc = scaler.fit_transform(train_feats[m_name])
                X_te_sc = scaler.transform(test_feats[m_name])

                reg = Ridge(alpha=100.0).fit(X_tr_sc, y_train_step)
                step_preds[m_name] = float(reg.predict(X_te_sc)[0])

            preds["m0_clim"].append(pred_m0)
            preds["m1_pers"].append(pred_m1)
            for m_name in ["m2", "m3", "m4", "m5", "m6"]:
                preds[m_name].append(step_preds[m_name])

            prediction_records.append({
                "forecast_issue_date": issue_date.strftime("%Y-%m-%d"),
                "target_date": target_date.strftime("%Y-%m-%d"),
                "lead_horizon": h,
                "y_true_precip_anom_mm": y_obs,
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

        print(f"  M0 Climatology (0.0): RMSE = {lead_metrics['m0_clim']['rmse']:.2f} mm, MAE = {lead_metrics['m0_clim']['mae']:.2f} mm, r = {lead_metrics['m0_clim']['r']}")
        print(f"  M1 Persistence:       RMSE = {lead_metrics['m1_pers']['rmse']:.2f} mm, MAE = {lead_metrics['m1_pers']['mae']:.2f} mm, r = {lead_metrics['m1_pers']['r']}")
        print(f"  M2 Local AR:          RMSE = {lead_metrics['m2']['rmse']:.2f} mm, MAE = {lead_metrics['m2']['mae']:.2f} mm, r = {lead_metrics['m2']['r']}")
        print(f"  M3 Pacific:           RMSE = {lead_metrics['m3']['rmse']:.2f} mm, MAE = {lead_metrics['m3']['mae']:.2f} mm, r = {lead_metrics['m3']['r']}")
        print(f"  M4 Indian Ocean:      RMSE = {lead_metrics['m4']['rmse']:.2f} mm, MAE = {lead_metrics['m4']['mae']:.2f} mm, r = {lead_metrics['m4']['r']}")
        print(f"  M5 Atlantic:          RMSE = {lead_metrics['m5']['rmse']:.2f} mm, MAE = {lead_metrics['m5']['mae']:.2f} mm, r = {lead_metrics['m5']['r']}")
        print(f"  M6 All 3 Oceans:      RMSE = {lead_metrics['m6']['rmse']:.2f} mm, MAE = {lead_metrics['m6']['mae']:.2f} mm, r = {lead_metrics['m6']['r']}")

        results[f"lead_{h}"] = lead_metrics

    df_preds = pd.DataFrame(prediction_records)
    df_preds.to_csv(str(OUTPUT_PREDS_CSV), index=False)
    print(f"\nSaved Rainfall Anomaly Predictions to {OUTPUT_PREDS_CSV}")

    with open(OUTPUT_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved Rainfall Anomaly Metrics to {OUTPUT_METRICS_JSON}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Finished in {time.time() - t0:.2f}s!")
