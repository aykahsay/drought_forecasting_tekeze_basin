"""
compute_spei3_pipeline.py
=========================
Calculates Standardized Precipitation Evapotranspiration Index (SPEI-3) over Tanqua Abergele Woreda
(1981–2024) and runs a comparative target ablation evaluating whether Model M4 (Indian Ocean Ridge)
and Model M7 (Spatiotemporal CNN-BiLSTM) predictive skill improves when predicting agricultural moisture
deficits (SPEI-3) versus meteorological precipitation deficits (SPI-3).
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from drought_forecasting.agriminds.metrics.spei_calculator import (
    calculate_extraterrestrial_radiation_ra,
    calculate_hargreaves_pet,
    calculate_fao56_penman_monteith_monthly_et0,
    fit_generalized_logistic_l_moments,
    cdf_generalized_logistic,
    compute_spei_series,
)

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MASTER_CSV = PROCESSED_DIR / "abregelle_tekeze_unified_monthly_1981_2024.csv"
OUT_ABLATION_JSON = PROCESSED_DIR / "spei3_vs_spi3_target_ablation.json"

LAT_ABREGELLE = 13.25
ELEV_ABREGELLE = 1420.0


def run_spei3_ablation():
    print("=" * 88)
    print("AI-DREWS: SPEI-3 TARGET COMPUTATION & PREDICTIVE ABLATION (1981–2024)")
    print("Governance: Gate 1 & Gate 2 Zero-Synthetic-Data and Causal Baseline Standards")
    print("=" * 88)

    df = pd.read_csv(MASTER_CSV)
    df["date"] = pd.to_datetime(df["date"])
    n = len(df)
    print(f"Loaded master dataset: {n} months (1981-01 to 2024-12)")

    # 1. Compute Hargreaves & FAO-56 PM PET
    days_per_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    pet_pm = []
    pet_harg = []

    for _, r in df.iterrows():
        y, m = int(r["year"]), int(r["month"])
        d = 29 if (m == 2 and (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0))) else days_per_month[m]
        tmax, tmin, tmean = float(r["t_max_c"]), float(r["t_min_c"]), float(r["t_mean_c"])

        # FAO-56 PM
        pm_val = calculate_fao56_penman_monteith_monthly_et0(
            tmax, tmin, tmean, LAT_ABREGELLE, m, d, elevation_m=ELEV_ABREGELLE
        )
        pet_pm.append(round(pm_val, 2))

        # Hargreaves
        harg_val = calculate_hargreaves_pet(tmax, tmin, tmean, LAT_ABREGELLE, m, d)
        pet_harg.append(round(harg_val, 2))

    df["pet_pm_mm"] = pet_pm
    df["pet_harg_mm"] = pet_harg

    # 2. Compute SPEI-3 (Hargreaves and PM) calibrated on pre-2016 baseline
    calib_mask = (df["year"] < 2016).values
    precip = df["chirps_abregelle_precip_mm"].values

    spei3_pm = compute_spei_series(precip, np.array(pet_pm), scale=3, calib_mask=calib_mask)
    spei3_harg = compute_spei_series(precip, np.array(pet_harg), scale=3, calib_mask=calib_mask)

    df["spei3_fao56_pm"] = np.round(spei3_pm, 4)
    df["spei3_hargreaves"] = np.round(spei3_harg, 4)
    df.to_csv(MASTER_CSV, index=False)
    print("[+] Saved updated SPEI-3 series to master dataset.")

    # 3. Walk-Forward Target Ablation (2017–2024, N=96 months)
    # Compare predictability of SPI-3 vs SPEI-3 (PM) for M0, M2, M4 across leads 1, 2, 3
    print("\n--- RUNNING COMPARATIVE TARGET ABLATION: SPI-3 vs SPEI-3 ---")
    holdout_mask = (df["year"] >= 2017).values
    holdout_indices = np.where(holdout_mask)[0]

    ablation_results = {}

    for target_name, target_col in [("SPI3_Meteorological", "spi3"), ("SPEI3_Agricultural", "spei3_fao56_pm")]:
        ablation_results[target_name] = {}
        y_all = df[target_col].values

        for h in [1, 2, 3]:
            ablation_results[target_name][f"Lead_{h}"] = {}
            y_true_list = []
            pred_m0_list = []
            pred_m2_list = []
            pred_m4_list = []

            for idx in holdout_indices:
                origin = idx - h
                if origin < 36:
                    continue
                y_target = y_all[idx]
                if np.isnan(y_target):
                    continue

                # Training slice strictly past < origin with valid lag lookbacks
                min_start = h + 4
                train_idx = np.arange(min_start, origin)
                
                # Construct features
                dmi_all = df["dmi"].values
                X_tr_m2 = np.column_stack([
                    y_all[train_idx - h],
                    y_all[train_idx - h - 1],
                    y_all[train_idx - h - 2]
                ])
                X_tr_m4 = np.column_stack([
                    X_tr_m2,
                    dmi_all[train_idx - h],
                    dmi_all[train_idx - h - 1]
                ])
                y_tr = y_all[train_idx]

                # Filter NaNs in training
                valid_mask = ~np.isnan(y_tr) & ~np.isnan(X_tr_m4).any(axis=1)
                X_tr_m2 = X_tr_m2[valid_mask]
                X_tr_m4 = X_tr_m4[valid_mask]
                y_tr = y_tr[valid_mask]

                if len(y_tr) < 20:
                    continue

                # M0: Expanding Climatology
                pred_m0 = float(np.mean(y_tr))

                x_test_m2 = np.array([[y_all[origin], y_all[origin - 1], y_all[origin - 2]]])
                x_test_m4 = np.hstack([x_test_m2, [[dmi_all[origin], dmi_all[origin - 1]]]])
                if np.isnan(x_test_m4).any():
                    continue

                # Ridge regression with fixed robust alpha
                reg_m2 = Ridge(alpha=100.0).fit(X_tr_m2, y_tr)
                pred_m2 = float(reg_m2.predict(x_test_m2)[0])

                reg_m4 = Ridge(alpha=100.0).fit(X_tr_m4, y_tr)
                pred_m4 = float(reg_m4.predict(x_test_m4)[0])

                y_true_list.append(y_target)
                pred_m0_list.append(pred_m0)
                pred_m2_list.append(pred_m2)
                pred_m4_list.append(pred_m4)

            y_t = np.array(y_true_list)
            p0 = np.array(pred_m0_list)
            p2 = np.array(pred_m2_list)
            p4 = np.array(pred_m4_list)

            rmse_0 = float(np.sqrt(np.mean((y_t - p0) ** 2)))
            rmse_2 = float(np.sqrt(np.mean((y_t - p2) ** 2)))
            rmse_4 = float(np.sqrt(np.mean((y_t - p4) ** 2)))

            r_2 = float(np.corrcoef(y_t, p2)[0, 1]) if np.std(p2) > 1e-6 else 0.0
            r_4 = float(np.corrcoef(y_t, p4)[0, 1]) if np.std(p4) > 1e-6 else 0.0

            drmse_m4_vs_m0 = rmse_4 - rmse_0
            drmse_m4_vs_m2 = rmse_4 - rmse_2

            ablation_results[target_name][f"Lead_{h}"] = {
                "RMSE_M0_Clim": round(rmse_0, 4),
                "RMSE_M2_Local": round(rmse_2, 4),
                "RMSE_M4_Indian": round(rmse_4, 4),
                "Pearson_r_M2": round(r_2, 4),
                "Pearson_r_M4": round(r_4, 4),
                "dRMSE_M4_vs_M0": round(drmse_m4_vs_m0, 4),
                "dRMSE_M4_vs_M2": round(drmse_m4_vs_m2, 4),
            }

            print(f"[{target_name} | Lead {h}] M0 RMSE: {rmse_0:.4f} | M2 RMSE: {rmse_2:.4f} (r={r_2:+.4f}) | M4 RMSE: {rmse_4:.4f} (r={r_4:+.4f}) | dRMSE(M4-M2): {drmse_m4_vs_m2:+.4f}")

    with open(OUT_ABLATION_JSON, "w", encoding="utf-8") as f:
        json.dump(ablation_results, f, indent=2)
    print(f"\n[OK] Target Ablation JSON saved to: {OUT_ABLATION_JSON}")


if __name__ == "__main__":
    run_spei3_ablation()
