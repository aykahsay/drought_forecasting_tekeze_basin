"""
evaluate_categorical_drought_m4_vs_m7.py
========================================
Evaluates and compares Model M4 (Indian Ocean Ridge) and Model M7 (Spatiotemporal CNN-BiLSTM)
on categorical drought thresholds (Moderate: SPI-3 < -1.0; Severe: SPI-3 < -1.5)
across forecast horizons h in {1, 2, 3} for the 96 holdout months (2017–2024).

Computes:
1. Contingency Matrix: Hits (H), False Alarms (FA), Misses (M), Correct Negatives (CN).
2. Deterministic Early Warning Metrics: CSI (Threat Score), POD, FAR, Bias, EDS.
3. Probabilistic Skill: Brier Score (BS), Climatology BS, Brier Skill Score (BSS).
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
PREDICTIONS_CSV = PROCESSED_DIR / "rolling_origin_walkforward_auditable_predictions_2017_2024.csv"
OUTPUT_JSON = PROCESSED_DIR / "categorical_drought_evaluation_m4_vs_m7.json"


def compute_contingency_metrics(y_true_binary: np.ndarray, y_pred_binary: np.ndarray) -> dict:
    """Computes categorical contingency table statistics and deterministic skill scores."""
    hits = int(np.sum((y_pred_binary == 1) & (y_true_binary == 1)))
    false_alarms = int(np.sum((y_pred_binary == 1) & (y_true_binary == 0)))
    misses = int(np.sum((y_pred_binary == 0) & (y_true_binary == 1)))
    correct_negatives = int(np.sum((y_pred_binary == 0) & (y_true_binary == 0)))
    total = len(y_true_binary)

    # Base rate / climatological frequency
    p_event = (hits + misses) / total if total > 0 else 0.0

    # Critical Success Index (CSI) / Threat Score
    denom_csi = hits + misses + false_alarms
    csi = hits / denom_csi if denom_csi > 0 else 0.0

    # Probability of Detection (POD) / Hit Rate
    denom_pod = hits + misses
    pod = hits / denom_pod if denom_pod > 0 else 0.0

    # False Alarm Ratio (FAR)
    denom_far = hits + false_alarms
    far = false_alarms / denom_far if denom_far > 0 else 0.0

    # Frequency Bias
    bias = (hits + false_alarms) / denom_pod if denom_pod > 0 else 0.0

    # Extreme Dependency Score (EDS): 2 * ln(p_event) / ln(hits / total) - 1
    # Assesses rare tail association without collapsing to zero for extreme thresholds
    if p_event > 0 and hits > 0:
        p_hit = hits / total
        eds = (2.0 * np.log(p_event) / np.log(p_hit)) - 1.0
        eds = float(np.clip(eds, -1.0, 1.0))
    else:
        eds = -1.0 if (hits + misses) > 0 else 0.0

    return {
        "Hits": hits,
        "FalseAlarms": false_alarms,
        "Misses": misses,
        "CorrectNegatives": correct_negatives,
        "BaseRate": round(p_event, 4),
        "CSI": round(csi, 4),
        "POD": round(pod, 4),
        "FAR": round(far, 4),
        "Bias": round(bias, 4),
        "EDS": round(eds, 4),
    }


def compute_probabilistic_brier_skill(
    y_true_continuous: np.ndarray,
    y_pred_continuous: np.ndarray,
    threshold: float,
    train_residual_std: float,
) -> tuple[float, float, float]:
    """Computes Brier Score (BS) and Brier Skill Score (BSS) relative to historical climatology.

    Forecast probabilities are derived parametrically from Gaussian predictive distributions:
    P(Y <= threshold) = Phi((threshold - mu_hat) / sigma_hat)
    """
    y_true_binary = (y_true_continuous < threshold).astype(int)
    climatological_prob = float(np.mean(y_true_binary))

    # Parametric predictive probability using residual standard error
    sigma = max(train_residual_std, 1e-4)
    pred_probabilities = norm.cdf((threshold - y_pred_continuous) / sigma)

    # Brier Score (Model vs Climatology)
    bs_model = float(np.mean((pred_probabilities - y_true_binary) ** 2))
    bs_clim = float(np.mean((climatological_prob - y_true_binary) ** 2))

    # Brier Skill Score
    bss = 1.0 - (bs_model / bs_clim) if bs_clim > 0 else 0.0

    return round(float(bs_model), 4), round(float(bs_clim), 4), round(float(bss), 4)


def run_categorical_audit():
    if not PREDICTIONS_CSV.exists():
        raise FileNotFoundError(f"Prediction file not found: {PREDICTIONS_CSV}")

    df = pd.read_csv(PREDICTIONS_CSV)
    required_cols = [
        "lead_horizon",
        "y_true_spi3",
        "pred_m4_indian_ocean_iod",
        "pred_m7_spatiotemporal_cnn_bilstm",
    ]
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Missing required column in dataframe: {col}")

    thresholds = {
        "Moderate_Drought_SPI_lt_minus1.0": -1.0,
        "Severe_Drought_SPI_lt_minus1.5": -1.5,
    }
    horizons = [1, 2, 3]
    models = {
        "M0_Climatology": "pred_m0_climatology",
        "M2_Local_AR": "pred_m2_local_ar",
        "M4_Indian_Ocean_Ridge": "pred_m4_indian_ocean_iod",
        "M7_Spatiotemporal_CNN_BiLSTM": "pred_m7_spatiotemporal_cnn_bilstm",
    }

    results = {}

    print("=" * 88)
    print("CATEGORICAL DROUGHT VERIFICATION: MODEL M4 vs MODEL M7 (2017–2024)")
    print("Evaluating Contingency Matrix, CSI, POD, FAR, EDS, and Brier Skill Scores")
    print("=" * 88)

    for thresh_label, thresh_val in thresholds.items():
        results[thresh_label] = {}
        print(f"\n--- THRESHOLD: {thresh_label} (SPI-3 < {thresh_val}) ---")

        for h in horizons:
            results[thresh_label][f"Lead_{h}"] = {}
            df_h = df[df["lead_horizon"] == h].copy()

            y_true = df_h["y_true_spi3"].values
            y_true_bin = (y_true < thresh_val).astype(int)
            event_count = int(np.sum(y_true_bin))

            print(f"\n[Lead Horizon h = {h} Months] (Total Months = {len(df_h)}, Drought Events = {event_count}):")
            print(f"{'Model':<30} | {'Hits':<4} {'Miss':<4} {'FA':<4} | {'CSI':<7} {'POD':<7} {'FAR':<7} {'EDS':<7} | {'BSS':<7}")
            print("-" * 88)

            for model_name, pred_col in models.items():
                y_pred = df_h[pred_col].values
                y_pred_bin = (y_pred < thresh_val).astype(int)

                # Deterministic contingency metrics
                cont_metrics = compute_contingency_metrics(y_true_bin, y_pred_bin)

                # Probabilistic Brier metrics
                residual_std = float(np.std(y_true - y_pred))
                bs_mod, bs_clim, bss = compute_probabilistic_brier_skill(
                    y_true, y_pred, thresh_val, residual_std
                )

                cont_metrics["BrierScore_Model"] = bs_mod
                cont_metrics["BrierScore_Clim"] = bs_clim
                cont_metrics["BSS"] = bss

                results[thresh_label][f"Lead_{h}"][model_name] = cont_metrics

                print(
                    f"{model_name:<30} | "
                    f"{cont_metrics['Hits']:<4} {cont_metrics['Misses']:<4} {cont_metrics['FalseAlarms']:<4} | "
                    f"{cont_metrics['CSI']:<7.4f} {cont_metrics['POD']:<7.4f} {cont_metrics['FAR']:<7.4f} {cont_metrics['EDS']:<7.4f} | "
                    f"{bss:<+7.4f}"
                )

    # Export structured results
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nAudit complete. Full results written to: {OUTPUT_JSON}\n")
    return results


if __name__ == "__main__":
    run_categorical_audit()
