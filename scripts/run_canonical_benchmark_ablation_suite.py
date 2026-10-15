"""
run_canonical_benchmark_ablation_suite.py
=========================================
Executes the clean, leakage-safe forecast ablation suite (M0 through M6)
on Tanqua Abergele Woreda SPI-3 drought predictions across leads h in {1, 2, 3}.

Models Evaluated:
  M0: Climatological Mean (E[y] = 0.0)
  M1: Autoregressive Persistence (Lagged SPI-3_{t-h})
  M2: Local Climate Model (M1 + calendar season harmonics sin/cos)
  M3: Pacific Informed (M2 + Nino 3.4 at t-h & t-h-6)
  M4: Indian Ocean Informed (M2 + IOD DMI at t-h)
  M5: Atlantic Informed (M2 + Atlantic Meridional Gradient at t-h)
  M6: All-Three-Ocean Coupled Model (M2 + Pacific + Indian + Atlantic)

Controlled Protocols:
  - Exact 96 continuous holdout calendar months: 2016-01 to 2023-12.
  - Training window: 1981-03 to 2015-12 (418 continuous historical months).
  - Identical Ridge regularization (alpha=2.0) across all models.
  - Outputs canonical holdout predictions to CSV for 100% reproducible metrics.
  - Computes complete 100% seasonal MSE additive partitions.
  - Computes paired year-block bootstrap (8 complete calendar years resampled jointly, B=2000, seed=42).
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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
CANONICAL_CSV = PROCESSED_DIR / "canonical_benchmark_holdout_predictions.csv"
OUTPUT_JSON = PROCESSED_DIR / "canonical_ablation_benchmark_results.json"


def run_ablation_experiments() -> Tuple[pd.DataFrame, Dict[str, Any]]:
    print("=" * 80)
    print("AI-DREWS: CANONICAL LEAKAGE-SAFE FORECAST ABLATION SUITE (M0 -> M6)")
    print("=" * 80)

    # 1. Load authoritative unified master dataset
    df_path = PROCESSED_DIR / "abregelle_tekeze_unified_monthly_1981_2024.csv"
    if not df_path.exists():
        raise FileNotFoundError(f"Master unified dataset not found at {df_path}")

    df = pd.read_csv(df_path)
    target_col = "spi3"

    # Chronological integrity check
    df["date"] = pd.to_datetime(df["date"])
    expected_dates = pd.date_range("1981-01-01", "2024-12-01", freq="MS")
    if len(df) != 528 or not (df["date"].values == expected_dates.values).all():
        raise ValueError("Chronological integrity failure: Dates do not match continuous 528 months.")
    print("  [OK] Chronological Integrity Verified: Exactly 528 continuous months (1981-01 to 2024-12).")

    test_mask = (df["year"] >= 2016) & (df["year"] <= 2023)
    test_df = df[test_mask]
    test_indices = test_df.index
    y_test = test_df[target_col].values
    n_test = len(y_test)
    print(f"  [OK] Holdout Evaluation Window: 2016-01 to 2023-12 ({n_test} continuous calendar months).")

    # Complete 100% seasonal partitioning schemes
    seasonal_schemes = {
        "scheme_standard_4part": {
            "kiremt_monsoon_jas": test_mask & df["month"].isin([7, 8, 9]),
            "belg_rains_mam": test_mask & df["month"].isin([3, 4, 5]),
            "bega_dry_ondj": test_mask & df["month"].isin([10, 11, 12, 1]),
            "transition_february": test_mask & (df["month"] == 2),
            "transition_june": test_mask & (df["month"] == 6)
        },
        "scheme_climatological_3part": {
            "kiremt_monsoon_jjas": test_mask & df["month"].isin([6, 7, 8, 9]),
            "belg_rains_mam": test_mask & df["month"].isin([3, 4, 5]),
            "bega_dry_ondjf": test_mask & df["month"].isin([10, 11, 12, 1, 2])
        }
    }

    prediction_records = []
    benchmark_results = {}

    for h in [1, 2, 3]:
        print(f"\nEvaluating Lead Horizon h = {h} month(s) ahead...")
        min_train_idx = 2 + h + 6
        train_indices = df.index[(df["year"] < 2016) & (df.index >= min_train_idx)]
        y_train = df.loc[train_indices, target_col].values

        # Feature matrices builder
        def extract_features(idx: pd.Index):
            # M1: Lagged SPI-3 only
            sp = df.loc[idx - h, target_col].values[:, None]

            # M2: Seasonality harmonics
            mo = df.loc[idx, "month"].values
            sin_mo = np.sin(2 * np.pi * mo / 12.0)[:, None]
            cos_mo = np.cos(2 * np.pi * mo / 12.0)[:, None]
            feat_m2 = np.hstack([sp, sin_mo, cos_mo])

            # M3: Pacific Nino 3.4
            nino = df.loc[idx - h, "nino34_sst_anomaly"].values[:, None]
            nino_lag6 = df.loc[idx - h - 6, "nino34_sst_anomaly"].values[:, None]
            feat_m3 = np.hstack([feat_m2, nino, nino_lag6])

            # M4: Indian Ocean DMI
            dmi = df.loc[idx - h, "dmi"].values[:, None]
            feat_m4 = np.hstack([feat_m2, dmi])

            # M5: Atlantic Meridional Gradient
            atl = df.loc[idx - h, "atl_meridional_gradient"].values[:, None]
            feat_m5 = np.hstack([feat_m2, atl])

            # M6: All Three Oceans Coupled
            feat_m6 = np.hstack([feat_m2, nino, nino_lag6, dmi, atl])

            return {
                "m1": sp,
                "m2": feat_m2,
                "m3": feat_m3,
                "m4": feat_m4,
                "m5": feat_m5,
                "m6": feat_m6
            }

        tr_feats = extract_features(train_indices)
        te_feats = extract_features(test_indices)

        # Baseline M0: Training set climatological mean
        pred_m0 = np.full(n_test, 0.0)

        # Baseline M1: Persistence
        pred_m1 = te_feats["m1"].flatten()

        # Regularized models M2 through M6 (controlled alpha=2.0)
        models = {}
        preds = {
            "m0_clim": pred_m0,
            "m1_pers": pred_m1
        }

        for m_name in ["m2", "m3", "m4", "m5", "m6"]:
            reg = Ridge(alpha=2.0).fit(tr_feats[m_name], y_train)
            preds[m_name] = reg.predict(te_feats[m_name])
            models[m_name] = reg

        # Append to canonical holdout records
        for i, tidx in enumerate(test_indices):
            row = df.loc[tidx]
            prediction_records.append({
                "date": row["date"].strftime("%Y-%m-%d"),
                "year": int(row["year"]),
                "month": int(row["month"]),
                "lead_months": h,
                "y_true": float(y_test[i]),
                "y_pred_m0_clim": float(preds["m0_clim"][i]),
                "y_pred_m1_pers": float(preds["m1_pers"][i]),
                "y_pred_m2_local": float(preds["m2"][i]),
                "y_pred_m3_pacific": float(preds["m3"][i]),
                "y_pred_m4_indian": float(preds["m4"][i]),
                "y_pred_m5_atlantic": float(preds["m5"][i]),
                "y_pred_m6_all_oceans": float(preds["m6"][i])
            })

        # Calculate metrics for each model
        def calc_metrics(yp: np.ndarray) -> Dict[str, Any]:
            mse = float(np.mean((y_test - yp)**2))
            rmse = float(np.sqrt(mse))
            mae = float(np.mean(np.abs(y_test - yp)))
            r_val = float(stats.pearsonr(y_test, yp)[0]) if np.std(yp) > 1e-6 else None
            return {"rmse": round(rmse, 4), "mse": round(mse, 4), "mae": round(mae, 4), "r": round(r_val, 4) if r_val is not None else None}

        m_metrics = {
            "m0_climatology": calc_metrics(preds["m0_clim"]),
            "m1_persistence": calc_metrics(preds["m1_pers"]),
            "m2_local_climate": calc_metrics(preds["m2"]),
            "m3_pacific_informed": calc_metrics(preds["m3"]),
            "m4_indian_ocean_informed": calc_metrics(preds["m4"]),
            "m5_atlantic_informed": calc_metrics(preds["m5"]),
            "m6_all_three_oceans": calc_metrics(preds["m6"])
        }

        # Paired Joint Calendar Year-Block Bootstrap (8 years, B=2000, seed=42)
        np.random.seed(42)
        B = 2000
        years_arr = test_df["year"].values
        diff_clim_boot = {k: [] for k in ["m1_pers", "m2", "m3", "m4", "m5", "m6"]}
        diff_local_boot = {k: [] for k in ["m3", "m4", "m5", "m6"]}

        for _ in range(B):
            sampled_years = np.random.choice(np.arange(2016, 2024), size=8, replace=True)
            boot_idx = []
            for sy in sampled_years:
                boot_idx.extend(np.where(years_arr == sy)[0])
            boot_idx = np.array(boot_idx)

            yt_b = y_test[boot_idx]
            rmse_c_b = np.sqrt(np.mean((yt_b - preds["m0_clim"][boot_idx])**2))
            rmse_loc_b = np.sqrt(np.mean((yt_b - preds["m2"][boot_idx])**2))

            for k in diff_clim_boot.keys():
                r_m_b = np.sqrt(np.mean((yt_b - preds[k][boot_idx])**2))
                diff_clim_boot[k].append(r_m_b - rmse_c_b)

            for k in diff_local_boot.keys():
                r_m_b = np.sqrt(np.mean((yt_b - preds[k][boot_idx])**2))
                diff_local_boot[k].append(r_m_b - rmse_loc_b)

        model_key_map = {
            "m0_clim": "m0_climatology",
            "m1_pers": "m1_persistence",
            "m2": "m2_local_climate",
            "m3": "m3_pacific_informed",
            "m4": "m4_indian_ocean_informed",
            "m5": "m5_atlantic_informed",
            "m6": "m6_all_three_oceans"
        }

        bootstrap_stats = {}
        for k in diff_clim_boot.keys():
            arr = np.array(diff_clim_boot[k])
            ci = [round(float(x), 4) for x in np.percentile(arr, [2.5, 97.5])]
            p_non_imp = round(float(np.mean(arr >= 0.0)), 4)
            p_twosided = round(float(min(1.0, 2.0 * min(np.mean(arr >= 0.0), np.mean(arr <= 0.0)))), 4)
            full_k = model_key_map[k]
            point_d = round(m_metrics[full_k]["rmse"] - m_metrics["m0_climatology"]["rmse"], 4)
            bootstrap_stats[f"{full_k}_vs_climatology"] = {
                "point_dRMSE": point_d,
                "ci95_year_block": ci,
                "prob_non_improvement": p_non_imp,
                "p_twosided": p_twosided
            }

        for k in diff_local_boot.keys():
            arr = np.array(diff_local_boot[k])
            ci = [round(float(x), 4) for x in np.percentile(arr, [2.5, 97.5])]
            p_non_imp = round(float(np.mean(arr >= 0.0)), 4)
            p_twosided = round(float(min(1.0, 2.0 * min(np.mean(arr >= 0.0), np.mean(arr <= 0.0)))), 4)
            full_k = model_key_map[k]
            point_d = round(m_metrics[full_k]["rmse"] - m_metrics["m2_local_climate"]["rmse"], 4)
            bootstrap_stats[f"{full_k}_vs_local_m2"] = {
                "point_dRMSE": point_d,
                "ci95_year_block": ci,
                "prob_non_improvement": p_non_imp,
                "p_twosided": p_twosided
            }


        # Exact Additive Seasonal MSE Decompositions
        seasonal_decomp = {}
        for s_scheme_name, partitions in seasonal_schemes.items():
            decomp = {}
            for part_key, part_mask in partitions.items():
                s_idx = df.index[part_mask]
                yt_s = df.loc[s_idx, target_col].values
                weight = len(yt_s) / n_test
                part_eval = {"n_months": len(yt_s), "weight": round(weight, 4)}

                for mk, yp in preds.items():
                    yp_s = yp[test_df.index.isin(s_idx)]
                    mse_s = float(np.mean((yt_s - yp_s)**2))
                    part_eval[f"{mk}_rmse"] = round(float(np.sqrt(mse_s)), 4)
                    part_eval[f"{mk}_mse"] = round(mse_s, 4)

                part_eval["delta_mse_m6_minus_clim"] = round(part_eval["m6_mse"] - part_eval["m0_clim_mse"], 4)
                part_eval["weighted_delta_mse_m6_minus_clim"] = round(weight * (part_eval["m6_mse"] - part_eval["m0_clim_mse"]), 4)
                decomp[part_key] = part_eval

            seasonal_decomp[s_scheme_name] = decomp

        benchmark_results[f"lead_{h}_month"] = {
            "lead_months": h,
            "models_ablation": m_metrics,
            "paired_year_block_bootstrap": bootstrap_stats,
            "seasonal_mse_decompositions": seasonal_decomp
        }

        print(f"  M0 Climatology:  RMSE = {m_metrics['m0_climatology']['rmse']:.4f}")
        print(f"  M1 Persistence:  RMSE = {m_metrics['m1_persistence']['rmse']:.4f}, r = {m_metrics['m1_persistence']['r']}")
        print(f"  M2 Local AR:     RMSE = {m_metrics['m2_local_climate']['rmse']:.4f}, r = {m_metrics['m2_local_climate']['r']}")
        print(f"  M3 Pacific:      RMSE = {m_metrics['m3_pacific_informed']['rmse']:.4f}, r = {m_metrics['m3_pacific_informed']['r']}")
        print(f"  M4 Indian Ocean: RMSE = {m_metrics['m4_indian_ocean_informed']['rmse']:.4f}, r = {m_metrics['m4_indian_ocean_informed']['r']}")
        print(f"  M5 Atlantic:     RMSE = {m_metrics['m5_atlantic_informed']['rmse']:.4f}, r = {m_metrics['m5_atlantic_informed']['r']}")
        print(f"  M6 All 3 Oceans: RMSE = {m_metrics['m6_all_three_oceans']['rmse']:.4f}, r = {m_metrics['m6_all_three_oceans']['r']}")
        print(f"  --> M6 vs Climatology dRMSE = {bootstrap_stats['m6_all_three_oceans_vs_climatology']['point_dRMSE']:+.4f} (95% CI: [{bootstrap_stats['m6_all_three_oceans_vs_climatology']['ci95_year_block'][0]:+.4f}, {bootstrap_stats['m6_all_three_oceans_vs_climatology']['ci95_year_block'][1]:+.4f}], p_twosided = {bootstrap_stats['m6_all_three_oceans_vs_climatology']['p_twosided']:.4f})")
        print(f"  --> M6 vs Local AR dRMSE    = {bootstrap_stats['m6_all_three_oceans_vs_local_m2']['point_dRMSE']:+.4f} (95% CI: [{bootstrap_stats['m6_all_three_oceans_vs_local_m2']['ci95_year_block'][0]:+.4f}, {bootstrap_stats['m6_all_three_oceans_vs_local_m2']['ci95_year_block'][1]:+.4f}], p_twosided = {bootstrap_stats['m6_all_three_oceans_vs_local_m2']['p_twosided']:.4f})")


    # Save Canonical Holdout Predictions CSV
    df_canon = pd.DataFrame(prediction_records)
    df_canon.to_csv(str(CANONICAL_CSV), index=False)
    print(f"\nSaved Canonical Holdout Predictions CSV to: {CANONICAL_CSV} ({len(df_canon)} prediction rows).")

    # Save Benchmark Results JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2)
    print(f"Saved Canonical Benchmark Results JSON to: {OUTPUT_JSON}")

    return df_canon, benchmark_results


if __name__ == "__main__":
    t0 = time.time()
    run_ablation_experiments()
    print(f"\nExecution completed in {time.time() - t0:.2f}s!")
