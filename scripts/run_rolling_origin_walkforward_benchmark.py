"""
run_rolling_origin_walkforward_benchmark.py
===========================================
Executes the rigorous temporal machine learning evaluation framework for
Tanqua Abergele Woreda SPI-3 drought forecasting:

1. Temporal Partitions:
   - Historical Training: 1981-03 to 2010-12 (358 months)
   - Validation & Hyperparameter Tuning: 2011-01 to 2016-12 (72 months)
   - Final Untouched Test Set: 2017-01 to 2024-12 (96 continuous months)

2. Evaluation Regimes:
   - Regime A: Fixed Model (Trained on historical data up to 2016-12, evaluated on 2017-2024)
   - Regime B: Rolling-Origin Expanding-Window Walk-Forward Model
     (Re-trained at each origin t from 2017-01 to 2024-12 using strictly past examples tau+h <= t)

3. Information Barrier at Origin t:
   - Known at t: Ocean SST indices (Nino 3.4, DMI, Atlantic Gradient), Local SPI-3_t, Seasonality
   - Target at t+h: SPI-3_{t+h} for leads h in {1, 2, 3} months

4. Statistical & Physical Diagnostics:
   - Baseline M0: Climatological Mean
   - Baseline M1: Autoregressive Persistence (SPI-3_t)
   - Benchmark M2: Local Climate AR (SPI-3_t + sin/cos season)
   - Ablation M3: Pacific Informed (M2 + Nino 3.4 at t and t-6)
   - Ablation M4: Indian Ocean Informed (M2 + IOD DMI at t)
   - Ablation M5: Atlantic Informed (M2 + Atlantic Gradient at t)
   - Ablation M6: All Three Oceans Coupled (M2 + Pacific + Indian + Atlantic)
   - Temporal Autocorrelation & Effective Sample Size (N_eff)
   - Seasonal MSE Partitions (Kiremt JJAS, Belg MAM, Bega ONDJF)
   - Paired Year-Block Bootstrap (8 complete years, B=2000)
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
CSV_PATH = PROCESSED_DIR / "abregelle_tekeze_unified_monthly_1981_2024.csv"
OUTPUT_PREDS_CSV = PROCESSED_DIR / "rolling_origin_walkforward_predictions_2017_2024.csv"
OUTPUT_METRICS_JSON = PROCESSED_DIR / "rolling_origin_walkforward_metrics_2017_2024.json"


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    mse = float(np.mean((y_true - y_pred) ** 2))
    rmse = float(np.sqrt(mse))
    mae = float(np.mean(np.abs(y_true - y_pred)))
    if np.std(y_pred) > 1e-6 and np.std(y_true) > 1e-6:
        r_val = float(stats.pearsonr(y_true, y_pred)[0])
    else:
        r_val = 0.0
    return {
        "rmse": round(rmse, 4),
        "mse": round(mse, 4),
        "mae": round(mae, 4),
        "r": round(r_val, 4)
    }


def analyze_autocorrelation(series: np.ndarray, max_lag: int = 12) -> Dict[str, Any]:
    n = len(series)
    mean = np.mean(series)
    var = np.var(series)
    autocorr = {}
    for lag in range(1, max_lag + 1):
        ac = np.sum((series[:n-lag] - mean) * (series[lag:] - mean)) / ((n - lag) * var)
        autocorr[f"lag_{lag}"] = round(float(ac), 4)
    
    rho1 = autocorr["lag_1"]
    n_eff = n * (1.0 - rho1) / (1.0 + rho1) if rho1 < 0.999 else 1.0
    return {
        "autocorrelations": autocorr,
        "n_raw": n,
        "rho_1": rho1,
        "n_effective": round(float(n_eff), 1),
        "dof_reduction_factor": round(float(n_eff / n), 3)
    }


def main():
    print("=" * 80)
    print("AI-DREWS: ROLLING-ORIGIN WALK-FORWARD BENCHMARK (1981-2024)")
    print("Evaluating Ocean Teleconnection Generalization for Tanqua Abergele")
    print("=" * 80)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing master dataset: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"])
    target_col = "spi3"

    # Verify chronological integrity
    if len(df) != 528:
        raise ValueError(f"Expected 528 months, got {len(df)}")

    # 1. Autocorrelation analysis on the full valid SPI-3 series (1981-03 to 2024-12, 526 months)
    valid_spi_mask = df[target_col].notna()
    spi_series = df.loc[valid_spi_mask, target_col].values
    ac_diag = analyze_autocorrelation(spi_series, max_lag=12)
    print(f"\n[1] TEMPORAL DEPENDENCE ANALYSIS (SPI-3 Series, N={ac_diag['n_raw']}):")
    print(f"  Autocorrelation Lag 1: {ac_diag['autocorrelations']['lag_1']} (shares 2 of 3 rainfall months)")
    print(f"  Autocorrelation Lag 2: {ac_diag['autocorrelations']['lag_2']} (shares 1 of 3 rainfall months)")
    print(f"  Autocorrelation Lag 3: {ac_diag['autocorrelations']['lag_3']} (shares 0 rainfall months: orthogonal window)")
    print(f"  Autocorrelation Lag 4: {ac_diag['autocorrelations']['lag_4']}")
    print(f"  Autocorrelation Lag 6: {ac_diag['autocorrelations']['lag_6']}")
    print(f"  Autocorrelation Lag 12: {ac_diag['autocorrelations']['lag_12']}")
    print(f"  Effective Sample Size: N_eff = {ac_diag['n_effective']} (raw N={ac_diag['n_raw']}, ratio={ac_diag['dof_reduction_factor']})")

    # 2. Partitions
    # Train: 1981 to 2010
    # Val: 2011 to 2016
    # Test: 2017 to 2024 (96 months)
    test_mask = (df["year"] >= 2017) & (df["year"] <= 2024)
    val_mask = (df["year"] >= 2011) & (df["year"] <= 2016)
    train_mask = (df["year"] >= 1981) & (df["year"] <= 2010) & valid_spi_mask

    test_indices = df.index[test_mask]
    val_indices = df.index[val_mask]
    train_indices = df.index[train_mask]

    print(f"\n[2] TEMPORAL SPLIT ARCHITECTURE:")
    print(f"  Historical Training Period:   1981-03 to 2010-12 ({len(train_indices)} months)")
    print(f"  Validation & Tuning Period:   2011-01 to 2016-12 ({len(val_indices)} months)")
    print(f"  Untouched Final Test Period: 2017-01 to 2024-12 ({len(test_indices)} months)")

    # Feature extraction helper
    def build_feature_dict(idx: pd.Index, lead: int) -> Dict[str, np.ndarray]:
        # Origin index is idx - lead
        orig_idx = idx - lead
        sp = df.loc[orig_idx, target_col].values[:, None]
        mo = df.loc[idx, "month"].values
        sin_mo = np.sin(2 * np.pi * mo / 12.0)[:, None]
        cos_mo = np.cos(2 * np.pi * mo / 12.0)[:, None]
        feat_m2 = np.hstack([sp, sin_mo, cos_mo])

        nino = df.loc[orig_idx, "nino34_sst_anomaly"].values[:, None]
        nino_lag6 = df.loc[orig_idx - 6, "nino34_sst_anomaly"].values[:, None]
        feat_m3 = np.hstack([feat_m2, nino, nino_lag6])

        dmi = df.loc[orig_idx, "dmi"].values[:, None]
        feat_m4 = np.hstack([feat_m2, dmi])

        atl = df.loc[orig_idx, "atl_meridional_gradient"].values[:, None]
        feat_m5 = np.hstack([feat_m2, atl])

        feat_m6 = np.hstack([feat_m2, nino, nino_lag6, dmi, atl])

        return {
            "m1": sp,
            "m2": feat_m2,
            "m3": feat_m3,
            "m4": feat_m4,
            "m5": feat_m5,
            "m6": feat_m6
        }

    # 3. Hyperparameter selection on Validation Period (2011-2016)
    # Test alphas on validation set for M2 through M6
    print(f"\n[3] HYPERPARAMETER SELECTION ON VALIDATION SET (2011-2016):")
    candidate_alphas = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0]
    best_alphas = {}

    for lead in [1, 2, 3]:
        min_tr = 2 + lead + 6
        tr_idx = df.index[(df["year"] <= 2010) & (df.index >= min_tr)]
        y_tr = df.loc[tr_idx, target_col].values
        v_idx = val_indices
        y_val = df.loc[v_idx, target_col].values

        tr_feats = build_feature_dict(tr_idx, lead)
        v_feats = build_feature_dict(v_idx, lead)

        best_alphas[lead] = {}
        for m_name in ["m2", "m3", "m4", "m5", "m6"]:
            best_rmse = float("inf")
            chosen_a = 2.0
            for a in candidate_alphas:
                reg = Ridge(alpha=a).fit(tr_feats[m_name], y_tr)
                pred_v = reg.predict(v_feats[m_name])
                rmse_v = np.sqrt(np.mean((y_val - pred_v) ** 2))
                if rmse_v < best_rmse:
                    best_rmse = rmse_v
                    chosen_a = a
            best_alphas[lead][m_name] = chosen_a
        print(f"  Lead h={lead}: Chosen Alphas: {best_alphas[lead]}")

    # 4. Evaluation on Untouched Test Period (2017-2024, 96 months)
    # We will run both:
    # A) Fixed Model (Trained on 1981-2016)
    # B) Rolling-Origin Walk-Forward Model (Expanding training window, re-fit at each month t)

    prediction_rows = []
    final_metrics_report = {
        "temporal_dependence": ac_diag,
        "best_alphas_validation": best_alphas,
        "regime_fixed": {},
        "regime_rolling_origin": {}
    }

    # Seasonal definition masks on Test Period
    test_df = df.loc[test_indices]
    seasons = {
        "kiremt_jjas": test_mask & df["month"].isin([6, 7, 8, 9]),
        "belg_mam": test_mask & df["month"].isin([3, 4, 5]),
        "bega_ondjf": test_mask & df["month"].isin([10, 11, 12, 1, 2])
    }

    for lead in [1, 2, 3]:
        print(f"\n=======================================================")
        print(f"EVALUATING FORECAST LEAD HORIZON h = {lead} MONTH(S) AHEAD")
        print(f"=======================================================")
        y_test = df.loc[test_indices, target_col].values
        n_test = len(y_test)

        # ----------------------------------------------------
        # REGIME A: FIXED MODEL (Trained on 1981-2016)
        # ----------------------------------------------------
        min_tr = 2 + lead + 6
        fixed_tr_idx = df.index[(df["year"] <= 2016) & (df.index >= min_tr)]
        y_tr_fixed = df.loc[fixed_tr_idx, target_col].values

        tr_feats_fixed = build_feature_dict(fixed_tr_idx, lead)
        te_feats = build_feature_dict(test_indices, lead)

        fixed_preds = {
            "m0_clim": np.full(n_test, float(np.mean(y_tr_fixed))),
            "m1_pers": te_feats["m1"].flatten()
        }

        for m_name in ["m2", "m3", "m4", "m5", "m6"]:
            a = best_alphas[lead][m_name]
            reg = Ridge(alpha=a).fit(tr_feats_fixed[m_name], y_tr_fixed)
            fixed_preds[m_name] = reg.predict(te_feats[m_name])

        fixed_eval = {m: compute_metrics(y_test, fixed_preds[m]) for m in fixed_preds}

        # ----------------------------------------------------
        # REGIME B: ROLLING-ORIGIN EXPANDING WALK-FORWARD MODEL
        # ----------------------------------------------------
        # At each test index t (target month), origin is t - lead.
        # Training set is all historical indices tau where tau <= t - lead.
        # This guarantees STRICT ZERO TARGET LEAKAGE at every step.
        rolling_preds = {
            "m0_clim": np.zeros(n_test),
            "m1_pers": te_feats["m1"].flatten(),
            "m2": np.zeros(n_test),
            "m3": np.zeros(n_test),
            "m4": np.zeros(n_test),
            "m5": np.zeros(n_test),
            "m6": np.zeros(n_test)
        }

        for i, t_idx in enumerate(test_indices):
            origin_idx = t_idx - lead
            # Allowed training indices: targets observed on or before origin_idx
            # Target for historical index tau is tau.
            # So tau must be <= origin_idx
            hist_tr_idx = df.index[(df.index <= origin_idx) & (df.index >= min_tr)]
            y_tr_hist = df.loc[hist_tr_idx, target_col].values

            # Climatology up to origin
            rolling_preds["m0_clim"][i] = float(np.mean(y_tr_hist))

            # Train features
            tr_feats_step = build_feature_dict(hist_tr_idx, lead)
            # Test features for this single step
            te_step_feats = build_feature_dict(pd.Index([t_idx]), lead)

            for m_name in ["m2", "m3", "m4", "m5", "m6"]:
                a = best_alphas[lead][m_name]
                reg = Ridge(alpha=a).fit(tr_feats_step[m_name], y_tr_hist)
                rolling_preds[m_name][i] = float(reg.predict(te_step_feats[m_name])[0])

        rolling_eval = {m: compute_metrics(y_test, rolling_preds[m]) for m in rolling_preds}

        # Record predictions row-by-row
        for i, t_idx in enumerate(test_indices):
            row = df.loc[t_idx]
            prediction_rows.append({
                "date": row["date"].strftime("%Y-%m-%d"),
                "year": int(row["year"]),
                "month": int(row["month"]),
                "lead_months": lead,
                "y_true": float(y_test[i]),
                # Fixed regime
                "fixed_pred_m0_clim": float(fixed_preds["m0_clim"][i]),
                "fixed_pred_m1_pers": float(fixed_preds["m1_pers"][i]),
                "fixed_pred_m2_local": float(fixed_preds["m2"][i]),
                "fixed_pred_m3_pacific": float(fixed_preds["m3"][i]),
                "fixed_pred_m4_indian": float(fixed_preds["m4"][i]),
                "fixed_pred_m5_atlantic": float(fixed_preds["m5"][i]),
                "fixed_pred_m6_all_oceans": float(fixed_preds["m6"][i]),
                # Rolling-origin walk-forward regime
                "rolling_pred_m0_clim": float(rolling_preds["m0_clim"][i]),
                "rolling_pred_m1_pers": float(rolling_preds["m1_pers"][i]),
                "rolling_pred_m2_local": float(rolling_preds["m2"][i]),
                "rolling_pred_m3_pacific": float(rolling_preds["m3"][i]),
                "rolling_pred_m4_indian": float(rolling_preds["m4"][i]),
                "rolling_pred_m5_atlantic": float(rolling_preds["m5"][i]),
                "rolling_pred_m6_all_oceans": float(rolling_preds["m6"][i])
            })

        # Paired Joint Calendar Year-Block Bootstrap (8 complete years, B=2000)
        np.random.seed(42)
        B = 2000
        years_arr = test_df["year"].values
        diff_clim_boot = {k: [] for k in ["m1_pers", "m2", "m3", "m4", "m5", "m6"]}
        diff_local_boot = {k: [] for k in ["m3", "m4", "m5", "m6"]}

        for _ in range(B):
            sampled_years = np.random.choice(np.arange(2017, 2025), size=8, replace=True)
            boot_idx = []
            for sy in sampled_years:
                boot_idx.extend(np.where(years_arr == sy)[0])
            boot_idx = np.array(boot_idx)

            yt_b = y_test[boot_idx]
            rmse_c_b = np.sqrt(np.mean((yt_b - rolling_preds["m0_clim"][boot_idx])**2))
            rmse_loc_b = np.sqrt(np.mean((yt_b - rolling_preds["m2"][boot_idx])**2))

            for k in diff_clim_boot.keys():
                r_m_b = np.sqrt(np.mean((yt_b - rolling_preds[k][boot_idx])**2))
                diff_clim_boot[k].append(r_m_b - rmse_c_b)

            for k in diff_local_boot.keys():
                r_m_b = np.sqrt(np.mean((yt_b - rolling_preds[k][boot_idx])**2))
                diff_local_boot[k].append(r_m_b - rmse_loc_b)

        boot_stats = {}
        for k in diff_clim_boot.keys():
            arr = np.array(diff_clim_boot[k])
            ci = [round(float(x), 4) for x in np.percentile(arr, [2.5, 97.5])]
            p_val = round(float(min(1.0, 2.0 * min(np.mean(arr >= 0.0), np.mean(arr <= 0.0)))), 4)
            boot_stats[f"{k}_vs_climatology"] = {
                "dRMSE": round(float(rolling_eval[k]["rmse"] - rolling_eval["m0_clim"]["rmse"]), 4),
                "ci95": ci,
                "p_value": p_val
            }

        for k in diff_local_boot.keys():
            arr = np.array(diff_local_boot[k])
            ci = [round(float(x), 4) for x in np.percentile(arr, [2.5, 97.5])]
            p_val = round(float(min(1.0, 2.0 * min(np.mean(arr >= 0.0), np.mean(arr <= 0.0)))), 4)
            boot_stats[f"{k}_vs_local_m2"] = {
                "dRMSE": round(float(rolling_eval[k]["rmse"] - rolling_eval["m2"]["rmse"]), 4),
                "ci95": ci,
                "p_value": p_val
            }

        # Seasonal decomposition for Rolling Origin
        seasonal_decomp = {}
        for s_name, s_mask in seasons.items():
            s_idx = df.index[s_mask]
            yt_s = df.loc[s_idx, target_col].values
            w = len(yt_s) / n_test
            part_eval = {"n_months": len(yt_s), "weight": round(w, 4)}
            for mk in rolling_preds:
                yp_s = rolling_preds[mk][test_df.index.isin(s_idx)]
                mse_s = float(np.mean((yt_s - yp_s)**2))
                part_eval[f"{mk}_rmse"] = round(float(np.sqrt(mse_s)), 4)
                part_eval[f"{mk}_mse"] = round(mse_s, 4)
            part_eval["delta_mse_m4_minus_m2"] = round(part_eval["m4_mse"] - part_eval["m2_mse"], 4)
            part_eval["delta_mse_m6_minus_clim"] = round(part_eval["m6_mse"] - part_eval["m0_clim_mse"], 4)
            seasonal_decomp[s_name] = part_eval

        final_metrics_report["regime_fixed"][f"lead_{lead}"] = fixed_eval
        final_metrics_report["regime_rolling_origin"][f"lead_{lead}"] = {
            "metrics": rolling_eval,
            "bootstrap": boot_stats,
            "seasonal_decomposition": seasonal_decomp
        }

        print(f"\n--- RESULTS: FIXED MODEL REGIME (Trained 1981-2016) ---")
        for m, met in fixed_eval.items():
            print(f"  {m:10s}: RMSE = {met['rmse']:.4f}, MAE = {met['mae']:.4f}, r = {met['r']}")

        print(f"\n--- RESULTS: ROLLING-ORIGIN WALK-FORWARD REGIME (Re-trained dynamically at each month t) ---")
        for m, met in rolling_eval.items():
            print(f"  {m:10s}: RMSE = {met['rmse']:.4f}, MAE = {met['mae']:.4f}, r = {met['r']}")

        print(f"\n--- STATISTICAL SIGNIFICANCE & HYPOTHESIS TESTS (Rolling Origin, Lead {lead}) ---")
        print(f"  M1 Persistence vs Climatology: dRMSE = {boot_stats['m1_pers_vs_climatology']['dRMSE']:+.4f} (p = {boot_stats['m1_pers_vs_climatology']['p_value']:.4f})")
        print(f"  M2 Local AR vs Climatology:    dRMSE = {boot_stats['m2_vs_climatology']['dRMSE']:+.4f} (p = {boot_stats['m2_vs_climatology']['p_value']:.4f})")
        print(f"  M3 Pacific vs Local AR:        dRMSE = {boot_stats['m3_vs_local_m2']['dRMSE']:+.4f} (p = {boot_stats['m3_vs_local_m2']['p_value']:.4f})")
        print(f"  M4 Indian Ocean vs Local AR:   dRMSE = {boot_stats['m4_vs_local_m2']['dRMSE']:+.4f} (p = {boot_stats['m4_vs_local_m2']['p_value']:.4f})")
        print(f"  M5 Atlantic vs Local AR:       dRMSE = {boot_stats['m5_vs_local_m2']['dRMSE']:+.4f} (p = {boot_stats['m5_vs_local_m2']['p_value']:.4f})")
        print(f"  M6 All 3 Oceans vs Local AR:   dRMSE = {boot_stats['m6_vs_local_m2']['dRMSE']:+.4f} (p = {boot_stats['m6_vs_local_m2']['p_value']:.4f})")

    # Save predictions
    df_out = pd.DataFrame(prediction_rows)
    df_out.to_csv(str(OUTPUT_PREDS_CSV), index=False)
    print(f"\nSaved Rolling Origin Walk-Forward Predictions to: {OUTPUT_PREDS_CSV} ({len(df_out)} rows)")

    with open(OUTPUT_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(final_metrics_report, f, indent=2)
    print(f"Saved Full Metrics Report to: {OUTPUT_METRICS_JSON}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\nCompleted rolling-origin walk-forward execution in {time.time() - t0:.2f}s!")
