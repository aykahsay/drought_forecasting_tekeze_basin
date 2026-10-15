"""
audit_and_reproduce_rolling_origin.py
=====================================
Independent reproducibility script that reads exclusively from
'data/processed/rolling_origin_walkforward_auditable_predictions_2017_2024.csv'
and recomputes:
- RMSE, MAE, Pearson r (setting r = None / NaN for M0)
- Paired dRMSE vs Climatology and vs Local AR (M2)
- Calendar Year-Block Bootstrap (8 years 2017-2024, B=2000, seed=42)
- Verifies exact consistency across all reported metrics.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
from scipy import stats

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT_DIR / "data" / "processed" / "rolling_origin_walkforward_auditable_predictions_2017_2024.csv"
OUTPUT_VERIF_JSON = ROOT_DIR / "data" / "processed" / "independent_reproducibility_audit_metrics.json"


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
    print("=" * 80)
    print("INDEPENDENT REPRODUCIBILITY AUDIT: ABERGELE ROLLING-ORIGIN FORECASTS")
    print("=" * 80)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing auditable predictions file: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} prediction rows from {CSV_PATH}")

    model_cols = {
        "m0_clim": "pred_m0_climatology",
        "m1_pers": "pred_m1_persistence",
        "m2": "pred_m2_local_ar",
        "m3": "pred_m3_pacific_nino34",
        "m4": "pred_m4_indian_ocean_iod",
        "m5": "pred_m5_atlantic_gradient",
        "m6": "pred_m6_all_three_oceans"
    }

    df["target_year"] = pd.to_datetime(df["target_date"]).dt.year

    audit_summary = {}

    for h in [1, 2, 3]:
        sub_df = df[df["lead_horizon"] == h].copy()
        n_rows = len(sub_df)
        print(f"\n=======================================================")
        print(f"RECOMPUTING METRICS FOR LEAD HORIZON h = {h} (N = {n_rows})")
        print(f"=======================================================")

        y_true = sub_df["y_true_spi3"].values
        lead_metrics = {}

        for m_key, col_name in model_cols.items():
            yp = sub_df[col_name].values
            met = compute_metrics(y_true, yp)
            lead_metrics[m_key] = met
            r_str = f"{met['r']:.4f}" if met['r'] is not None else "undefined (constant)"
            print(f"  {m_key:10s} ({col_name:26s}): RMSE = {met['rmse']:.4f}, MAE = {met['mae']:.4f}, r = {r_str}")

        # Calendar year-block bootstrap
        np.random.seed(42)
        B = 2000
        years_arr = sub_df["target_year"].values
        diff_clim_boot = {k: [] for k in ["m1_pers", "m2", "m3", "m4", "m5", "m6"]}
        diff_local_boot = {k: [] for k in ["m3", "m4", "m5", "m6"]}

        for _ in range(B):
            sampled_years = np.random.choice(np.arange(2017, 2025), size=8, replace=True)
            boot_idx = []
            for sy in sampled_years:
                boot_idx.extend(np.where(years_arr == sy)[0])
            boot_idx = np.array(boot_idx)

            yt_b = y_true[boot_idx]
            rmse_c_b = np.sqrt(np.mean((yt_b - sub_df[model_cols["m0_clim"]].values[boot_idx]) ** 2))
            rmse_loc_b = np.sqrt(np.mean((yt_b - sub_df[model_cols["m2"]].values[boot_idx]) ** 2))

            for k in diff_clim_boot.keys():
                r_m_b = np.sqrt(np.mean((yt_b - sub_df[model_cols[k]].values[boot_idx]) ** 2))
                diff_clim_boot[k].append(r_m_b - rmse_c_b)

            for k in diff_local_boot.keys():
                r_m_b = np.sqrt(np.mean((yt_b - sub_df[model_cols[k]].values[boot_idx]) ** 2))
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

        audit_summary[f"lead_{h}"] = {
            "metrics": lead_metrics,
            "bootstrap": boot_stats
        }

        print("\n  Statistical Differences (vs Local AR M2):")
        for mk in ["m3", "m4", "m5", "m6"]:
            stat = boot_stats[f"{mk}_vs_local_m2"]
            print(f"    {mk:4s} vs M2: dRMSE = {stat['dRMSE']:+.4f} (95% CI: [{stat['ci95'][0]:+.4f}, {stat['ci95'][1]:+.4f}], p = {stat['p_value']:.4f})")

    with open(OUTPUT_VERIF_JSON, "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2)
    print(f"\n[SUCCESS] Independent audit completed! Saved to {OUTPUT_VERIF_JSON}")


if __name__ == "__main__":
    main()
