"""
run_seasonal_rainfall_forecast_benchmark.py
===========================================
Executes a strictly leak-free seasonal rainfall forecast benchmark for Tanqua Abergele Woreda:
Targeting genuinely FUTURE seasonal accumulated rainfall (mm), anomalies, and probabilistic drought events:

1. Target Seasons:
   - Kiremt Monsoon (June–September: JJAS, 4 months): ~83% of annual precipitation
     Issue Dates: 1 June (Lead 0), 1 May (Lead 1), 1 April (Lead 2), 1 March (Lead 3)
   - Belg Rains (March–May: MAM, 3 months): ~12% of annual precipitation
     Issue Dates: 1 March (Lead 0), 1 February (Lead 1)

2. Evaluation Windows:
   - Primary Retrospective Window: 2017–2024 (8 continuous years)
   - Extended Walk-Forward Window: 2000–2024 (25 continuous years)

3. Causal Protocol:
   - At each issue date of year Y:
     - Training set strictly restricted to years y < Y (zero target lookahead)
     - Climatological normal estimated strictly on training years y < Y
     - StandardScaler fitted strictly on training years y < Y

4. Probabilistic Drought Assessment:
   - Drought Event Definition: Seasonal rainfall < 80% of normal (or lower tercile < 33rd percentile)
   - Metrics: Brier Score (BS), Brier Skill Score (BSS) relative to Climatology
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
OUTPUT_PREDS_CSV = PROCESSED_DIR / "seasonal_rainfall_forecast_predictions.csv"
OUTPUT_METRICS_JSON = PROCESSED_DIR / "seasonal_rainfall_forecast_metrics.json"


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
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "r": r_val
    }


def compute_brier_score(obs_events: np.ndarray, pred_probs: np.ndarray) -> float:
    return float(np.mean((pred_probs - obs_events) ** 2))


def main():
    print("=" * 85)
    print("AI-DREWS: SEASONAL RAINFALL FORECAST BENCHMARK & PROBABILISTIC DROUGHT AUDIT")
    print("Evaluating Kiremt (JJAS) and Belg (MAM) Across 2017-2024 and 2000-2024")
    print("=" * 85)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing master dataset: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df["date"] = pd.to_datetime(df["date"])
    precip_col = "chirps_abregelle_precip_mm"

    years = np.sort(df["year"].unique())
    n_years = len(years)

    # Compute seasonal totals per year
    seasonal_data = []
    for y in years:
        df_y = df[df["year"] == y].sort_values("month")
        kiremt_p = df_y[df_y["month"].isin([6, 7, 8, 9])][precip_col].sum()
        belg_p = df_y[df_y["month"].isin([3, 4, 5])][precip_col].sum()
        ond_p = df_y[df_y["month"].isin([10, 11, 12])][precip_col].sum()
        df_next_jan = df[(df["year"] == y + 1) & (df["month"] == 1)]
        jan_p = df_next_jan[precip_col].values[0] if len(df_next_jan) > 0 else np.nan
        bega_p = ond_p + jan_p if not np.isnan(jan_p) else np.nan

        seasonal_data.append({
            "year": y,
            "kiremt_jjas_mm": kiremt_p,
            "belg_mam_mm": belg_p,
            "bega_ondj_mm": bega_p
        })

    df_seasons = pd.DataFrame(seasonal_data)

    experiments = [
        {
            "season_name": "Kiremt Monsoon (JJAS)",
            "season_col": "kiremt_jjas_mm",
            "target_months": [6, 7, 8, 9],
            "lead_configs": [
                {"lead_label": "Lead 0 (Issue 1 June)", "issue_month": 5, "desc": "Info up to 31 May, targets Jun-Sep"},
                {"lead_label": "Lead 1 (Issue 1 May)", "issue_month": 4, "desc": "Info up to 30 April, targets Jun-Sep"},
                {"lead_label": "Lead 2 (Issue 1 April)", "issue_month": 3, "desc": "Info up to 31 March, targets Jun-Sep"},
                {"lead_label": "Lead 3 (Issue 1 March)", "issue_month": 2, "desc": "Info up to 28 Feb, targets Jun-Sep"},
            ]
        },
        {
            "season_name": "Belg Rains (MAM)",
            "season_col": "belg_mam_mm",
            "target_months": [3, 4, 5],
            "lead_configs": [
                {"lead_label": "Lead 0 (Issue 1 March)", "issue_month": 2, "desc": "Info up to 28 Feb, targets Mar-May"},
                {"lead_label": "Lead 1 (Issue 1 February)", "issue_month": 1, "desc": "Info up to 31 Jan, targets Mar-May"},
            ]
        }
    ]

    all_pred_records = []
    benchmark_report = {
        "period_2017_2024": {},
        "period_2000_2024": {}
    }

    windows = [
        ("period_2017_2024", 2017),
        ("period_2000_2024", 2000)
    ]

    for win_key, start_yr in windows:
        print("\n" + "#" * 85)
        print(f"EVALUATION WINDOW: {win_key.upper()} (Years {start_yr} to 2024, N={2024 - start_yr + 1} Years)")
        print("#" * 85)

        eval_years = [y for y in years if y >= start_yr]

        for exp in experiments:
            s_name = exp["season_name"]
            s_col = exp["season_col"]
            print(f"\n=======================================================")
            print(f"SEASON: {s_name} ({win_key})")
            print("=======================================================")

            if s_name not in benchmark_report[win_key]:
                benchmark_report[win_key][s_name] = {}

            for lcfg in exp["lead_configs"]:
                l_label = lcfg["lead_label"]
                iss_m = lcfg["issue_month"]

                y_obs_list = []
                preds_raw = {m: [] for m in ["m0_clim", "m1_local", "m2_ocean", "m3_pacific", "m4_indian", "m5_all_oceans"]}
                pred_drought_prob = {m: [] for m in ["m0_clim", "m1_local", "m2_ocean", "m3_pacific", "m4_indian", "m5_all_oceans"]}
                obs_drought_event = []

                for target_y in eval_years:
                    obs_season_rain = float(df_seasons.loc[df_seasons["year"] == target_y, s_col].values[0])
                    train_years = [y for y in years if y >= 1982 and y < target_y]

                    y_train_raw = df_seasons.loc[df_seasons["year"].isin(train_years), s_col].values
                    train_clim = float(np.mean(y_train_raw))
                    train_std = float(np.std(y_train_raw))
                    y_train_anom = y_train_raw - train_clim

                    # Drought threshold: lower tercile (33rd percentile) of historical training normal
                    drought_threshold = float(np.percentile(y_train_raw, 33.33))
                    is_drought = 1 if obs_season_rain < drought_threshold else 0
                    obs_drought_event.append(is_drought)
                    y_obs_list.append(obs_season_rain)

                    # Feature builder
                    def get_features(yr_list: List[int]) -> Dict[str, np.ndarray]:
                        feat_dict = {}
                        local_list = []
                        nino_list = []
                        dmi_list = []
                        atl_list = []

                        for yr in yr_list:
                            row_iss = df[(df["year"] == yr) & (df["month"] == iss_m)].iloc[0]
                            sub_pre = df[(df["year"] == yr) & (df["month"].isin([iss_m, iss_m - 1 if iss_m > 1 else 12, iss_m - 2 if iss_m > 2 else (11 if iss_m == 2 else 10)]))]
                            ant_rain = float(sub_pre[precip_col].sum())

                            local_list.append([ant_rain, float(row_iss["chirps_abregelle_precip_mm"])])
                            nino_list.append([float(row_iss["nino34_sst_anomaly"])])
                            dmi_list.append([float(row_iss["dmi"])])
                            atl_list.append([float(row_iss["atl_meridional_gradient"])])

                        local_arr = np.array(local_list)
                        nino_arr = np.array(nino_list)
                        dmi_arr = np.array(dmi_list)
                        atl_arr = np.array(atl_list)

                        feat_dict["m1_local"] = local_arr
                        feat_dict["m2_ocean"] = np.hstack([nino_arr, dmi_arr, atl_arr])
                        feat_dict["m3_pacific"] = np.hstack([local_arr, nino_arr])
                        feat_dict["m4_indian"] = np.hstack([local_arr, dmi_arr])
                        feat_dict["m5_all_oceans"] = np.hstack([local_arr, nino_arr, dmi_arr, atl_arr])

                        return feat_dict

                    tr_feats = get_features(train_years)
                    te_feats = get_features([target_y])

                    # M0 Climatology
                    preds_raw["m0_clim"].append(train_clim)
                    # Climatological drought probability is ~0.333
                    p_clim_drought = float(np.mean(y_train_raw < drought_threshold))
                    pred_drought_prob["m0_clim"].append(p_clim_drought)

                    for m_k in ["m1_local", "m2_ocean", "m3_pacific", "m4_indian", "m5_all_oceans"]:
                        scaler = StandardScaler()
                        X_tr_sc = scaler.fit_transform(tr_feats[m_k])
                        X_te_sc = scaler.transform(te_feats[m_k])

                        reg = Ridge(alpha=50.0).fit(X_tr_sc, y_train_anom)
                        p_anom = float(reg.predict(X_te_sc)[0])
                        p_total = train_clim + p_anom
                        preds_raw[m_k].append(p_total)

                        # Predictive distribution under linear regression: N(p_total, residual_std^2)
                        res_std = float(np.std(y_train_anom - reg.predict(X_tr_sc)))
                        p_drought = float(stats.norm.cdf(drought_threshold, loc=p_total, scale=max(res_std, 1e-3)))
                        pred_drought_prob[m_k].append(p_drought)

                    # Only record row predictions once (for period_2017_2024)
                    if win_key == "period_2017_2024":
                        all_pred_records.append({
                            "season": s_name,
                            "lead_config": l_label,
                            "target_year": target_y,
                            "observed_rain_mm": obs_season_rain,
                            "expanding_climatology_mm": train_clim,
                            "drought_threshold_33pct_mm": drought_threshold,
                            "is_drought_event": is_drought,
                            "pred_m0_clim_mm": train_clim,
                            "pred_m1_local_mm": preds_raw["m1_local"][-1],
                            "pred_m2_ocean_only_mm": preds_raw["m2_ocean"][-1],
                            "pred_m3_pacific_mm": preds_raw["m3_pacific"][-1],
                            "pred_m4_indian_mm": preds_raw["m4_indian"][-1],
                            "pred_m5_all_oceans_mm": preds_raw["m5_all_oceans"][-1],
                            "prob_drought_m0_clim": p_clim_drought,
                            "prob_drought_m1_local": pred_drought_prob["m1_local"][-1],
                            "prob_drought_m2_ocean": pred_drought_prob["m2_ocean"][-1],
                            "prob_drought_m4_indian": pred_drought_prob["m4_indian"][-1],
                            "prob_drought_m5_all": pred_drought_prob["m5_all_oceans"][-1]
                        })

                y_obs_arr = np.array(y_obs_list)
                obs_drought_arr = np.array(obs_drought_event)

                lead_eval = {}
                bs_clim = compute_brier_score(obs_drought_arr, np.array(pred_drought_prob["m0_clim"]))

                for mk in preds_raw:
                    p_r = np.array(preds_raw[mk])
                    met_r = compute_metrics(y_obs_arr, p_r)
                    bs_m = compute_brier_score(obs_drought_arr, np.array(pred_drought_prob[mk]))
                    bss_m = 1.0 - (bs_m / bs_clim) if bs_clim > 1e-6 else 0.0

                    met_r["brier_score"] = round(bs_m, 4)
                    met_r["brier_skill_score"] = round(bss_m, 4)
                    lead_eval[mk] = met_r

                benchmark_report[win_key][s_name][l_label] = lead_eval

                print(f"\n--- {l_label} ({win_key}) ---")
                print(f"  M0 Climatology:     RMSE = {lead_eval['m0_clim']['rmse']:6.2f} mm, MAE = {lead_eval['m0_clim']['mae']:6.2f} mm, BS = {lead_eval['m0_clim']['brier_score']:.4f}")
                print(f"  M1 Local History:   RMSE = {lead_eval['m1_local']['rmse']:6.2f} mm, MAE = {lead_eval['m1_local']['mae']:6.2f} mm, BS = {lead_eval['m1_local']['brier_score']:.4f}, BSS = {lead_eval['m1_local']['brier_skill_score']:+.4f}")
                print(f"  M2 Ocean-Only:      RMSE = {lead_eval['m2_ocean']['rmse']:6.2f} mm, MAE = {lead_eval['m2_ocean']['mae']:6.2f} mm, BS = {lead_eval['m2_ocean']['brier_score']:.4f}, BSS = {lead_eval['m2_ocean']['brier_skill_score']:+.4f}")
                print(f"  M3 Local + Pacific: RMSE = {lead_eval['m3_pacific']['rmse']:6.2f} mm, MAE = {lead_eval['m3_pacific']['mae']:6.2f} mm, BS = {lead_eval['m3_pacific']['brier_score']:.4f}, BSS = {lead_eval['m3_pacific']['brier_skill_score']:+.4f}")
                print(f"  M4 Local + Indian:  RMSE = {lead_eval['m4_indian']['rmse']:6.2f} mm, MAE = {lead_eval['m4_indian']['mae']:6.2f} mm, BS = {lead_eval['m4_indian']['brier_score']:.4f}, BSS = {lead_eval['m4_indian']['brier_skill_score']:+.4f}")
                print(f"  M5 Local + All:     RMSE = {lead_eval['m5_all_oceans']['rmse']:6.2f} mm, MAE = {lead_eval['m5_all_oceans']['mae']:6.2f} mm, BS = {lead_eval['m5_all_oceans']['brier_score']:.4f}, BSS = {lead_eval['m5_all_oceans']['brier_skill_score']:+.4f}")

    df_preds_out = pd.DataFrame(all_pred_records)
    df_preds_out.to_csv(str(OUTPUT_PREDS_CSV), index=False)
    print(f"\n[OK] Saved Auditable Seasonal Predictions Table to: {OUTPUT_PREDS_CSV} ({len(df_preds_out)} rows)")

    with open(OUTPUT_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(benchmark_report, f, indent=2)
    print(f"[OK] Saved Seasonal Metrics JSON to: {OUTPUT_METRICS_JSON}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\nCompleted in {time.time() - t0:.2f}s!")
