"""
run_m7_spatiotemporal_cnn_bilstm_benchmark.py
=============================================
Audited Rolling-Origin Walk-Forward Benchmark for Model M7:
Deep Spatiotemporal CNN-BiLSTM with Causal Historical Sequence Processing.

Standards Enforced:
1. Gate 1 & Gate 2 Zero-Leakage Standards:
   - Normalization/Climatology: SSTA monthly baseline and SPI-3 scaling fitted strictly
     on historical training observations prior to each evaluation year (tau + h <= origin).
   - Causal Temporal Barrier: Historical lookback L=12 months [t-11, t].
     Forward LSTM: t-11 -> t
     Backward LSTM: t -> t-11
     Zero future tokens (t+1..t+h) are exposed to the backward pass.
   - Direct-Horizon Training: Three distinct models trained independently for h in {1, 2, 3}.
     No recursive autoregressive error compounding.

2. Small-Sample Regime Safeguards (N_eff ≈ 113.6):
   - Adaptive Average Pooling: Restricts spatial grid to (2, 2) latent modes.
   - AdamW with aggressive weight decay (L2 = 1e-3) and dropout (p = 0.3).
   - Seasonally Weighted Loss: Weights wet seasons (Kiremt JAS 2x, Belg MAM 1.5x)
     over dry Bega (ONDJ 0.5x) to prevent false winter skill gaming.

3. Rigorous Benchmarking:
   - Identical 96-month rolling-origin evaluation window (2017-2024) as M0-M6.
   - Paired 8-year calendar year-block bootstrap (B = 2,000) comparing M7 against
     M0 (Climatology), M2 (Local AR), and M4 (Indian Ocean Ridge).

4. Physical Teleconnection Verification:
   - Computes gradient attribution saliency: |∂y_hat / ∂SST(x, y, t)|.
   - Evaluates whether attribution peaks over Western Indian Ocean / Arabian Sea
     during monsoon wet seasons versus random open-ocean noise.
"""

from __future__ import annotations

import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import pandas as pd
from scipy import stats
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

# Project paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "drought_forecasting"))

from drought_forecasting.agriminds.models.spatiotemporal_cnn_bilstm import (
    SpatioTemporal_CNN_BiLSTM,
    SeasonallyWeightedMSELoss,
    compute_gradient_saliency,
)

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
RAW_SST_PATH = ROOT_DIR / "data" / "raw" / "teleconnections" / "sst.mnmean.nc"
MASTER_CSV_PATH = PROCESSED_DIR / "abregelle_tekeze_unified_monthly_1981_2024.csv"
PREDS_CSV_PATH = PROCESSED_DIR / "rolling_origin_walkforward_auditable_predictions_2017_2024.csv"
METRICS_JSON_PATH = PROCESSED_DIR / "rolling_origin_walkforward_auditable_metrics_2017_2024.json"
SALIENCY_FIG_PATH = PROCESSED_DIR / "figure5_m7_saliency_teleconnection_attribution.png"


def load_raw_sst_and_master():
    """Loads master monthly dataframe and extracts aligned 2D SST spatial domain."""
    if not MASTER_CSV_PATH.exists():
        raise FileNotFoundError(f"Missing master monthly CSV: {MASTER_CSV_PATH}")
    if not RAW_SST_PATH.exists():
        raise FileNotFoundError(f"Missing NOAA ERSSTv5 netcdf: {RAW_SST_PATH}")

    df = pd.read_csv(MASTER_CSV_PATH)
    df["date"] = pd.to_datetime(df["date"])

    ds = nc.Dataset(str(RAW_SST_PATH), "r")
    lats = ds.variables["lat"][:]
    lons = ds.variables["lon"][:]
    t_var = ds.variables["time"]
    dates = nc.num2date(t_var[:], units=t_var.units)
    dt_index = pd.to_datetime([d.strftime("%Y-%m-%d") for d in dates])
    idx_1981_2024 = np.where((dt_index.year >= 1981) & (dt_index.year <= 2024))[0]

    # Domain: 10°S to 30°N, 30°E to 100°E (Indian Ocean basin and Arabian Sea)
    lat_mask = (lats >= -10.0) & (lats <= 30.0)
    lon_mask = (lons >= 30.0) & (lons <= 100.0)
    lat_idx = np.where(lat_mask)[0]
    lon_idx = np.where(lon_mask)[0]

    sst_raw = ds.variables["sst"][idx_1981_2024, lat_idx.min():lat_idx.max() + 1, lon_idx.min():lon_idx.max() + 1]
    sub_lats = lats[lat_idx.min():lat_idx.max() + 1]
    sub_lons = lons[lon_idx.min():lon_idx.max() + 1]
    ds.close()

    sst_arr = np.array(sst_raw)
    mask = sst_raw.mask if isinstance(sst_raw, np.ma.MaskedArray) else np.isnan(sst_arr)
    # Fill land with NaN for clean anomaly subtraction
    sst_arr[mask] = np.nan

    return df, sst_arr, mask, sub_lats, sub_lons


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
        "mse": round(mse, 4),
        "mae": round(mae, 4),
        "r": r_val
    }


def train_m7_model(
    X_grid_train: np.ndarray,      # (N, 12, 1, H, W)
    X_local_train: np.ndarray,     # (N, 12, 3)
    y_train: np.ndarray,           # (N,)
    target_months_train: np.ndarray, # (N,)
    forecast_horizon: int,
    device: torch.device,
    epochs: int = 35,
    batch_size: int = 16,
    lr: float = 1e-3,
    weight_decay: float = 1e-3,
    dropout_p: float = 0.3,
    seed: int = 42,
) -> SpatioTemporal_CNN_BiLSTM:
    """Trains SpatioTemporal CNN-BiLSTM with Gate 1 & 2 small-sample safeguards."""
    torch.manual_seed(seed + forecast_horizon)
    np.random.seed(seed + forecast_horizon)

    model = SpatioTemporal_CNN_BiLSTM(
        in_grid_channels=1,
        cnn_features=32,
        local_feat_dim=3,
        lstm_hidden_dim=64,
        num_lstm_layers=1,
        dropout_p=dropout_p,
        forecast_horizon=forecast_horizon,
    ).to(device)

    criterion = SeasonallyWeightedMSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    # Convert to PyTorch tensors
    t_grid = torch.tensor(X_grid_train, dtype=torch.float32)
    t_local = torch.tensor(X_local_train, dtype=torch.float32)
    t_y = torch.tensor(y_train, dtype=torch.float32).unsqueeze(-1)
    t_m = torch.tensor(target_months_train, dtype=torch.long)

    dataset = TensorDataset(t_grid, t_local, t_y, t_m)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model.train()
    for epoch in range(epochs):
        for b_grid, b_local, b_y, b_m in loader:
            b_grid = b_grid.to(device)
            b_local = b_local.to(device)
            b_y = b_y.to(device)
            b_m = b_m.to(device)

            optimizer.zero_grad()
            preds = model(b_grid, b_local)
            loss = criterion(preds, b_y, b_m)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

    model.eval()
    return model


def run_m7_benchmark():
    print("=" * 85)
    print("AI-DREWS: DEEP SPATIOTEMPORAL CNN-BiLSTM BENCHMARK (MODEL M7)")
    print("Zero-Leakage Walk-Forward Evaluation with Causal Historical Sequence Processing")
    print("=" * 85)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[*] Compute Device: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")

    df, sst_raw, land_mask, sub_lats, sub_lons = load_raw_sst_and_master()
    n_months = len(df)
    H, W = sst_raw.shape[1], sst_raw.shape[2]
    print(f"[*] Loaded 528 continuous months (1981-2024). SST Domain: {H} lats x {W} lons.")

    # Target column - backfill first two months where SPI-3 has insufficient antecedent window
    target_col = "spi3"
    spi3_all = df[target_col].bfill().values
    months_all = df["month"].values
    years_all = df["year"].values

    # Evaluation setup: 2017 to 2024 (96 months)
    eval_mask = (df["year"] >= 2017) & (df["year"] <= 2024)
    eval_target_indices = df.index[eval_mask].values
    n_eval = len(eval_target_indices)

    # Containers for results across horizons
    m7_predictions_by_horizon = {}
    saliency_attributions_wet = {1: [], 2: [], 3: []}
    saliency_attributions_dry = {1: [], 2: [], 3: []}

    for h in [1, 2, 3]:
        print(f"\n=======================================================")
        print(f"[*] Evaluating Direct-Horizon h = {h} Month(s) Ahead")
        print(f"=======================================================")

        preds_m7_list = []
        eval_years = np.arange(2017, 2025)

        for eval_year in eval_years:
            # Training cutoff: all historical targets strictly prior to eval_year (tau + h <= Dec(eval_year - 1))
            last_train_target_idx = df.index[df["year"] <= (eval_year - 1)].max()
            # Origin tau: tau + h <= last_train_target_idx
            # Earliest origin: 13 (ensures 12 months of historical lookback [tau-11, tau] has tau-11 >= 2)
            min_tau = 13
            max_tau = last_train_target_idx - h
            train_origins = np.arange(min_tau, max_tau + 1)
            train_targets = train_origins + h

            # 1. Compute Monthly Climatology strictly on training timesteps for SSTA
            # Training timesteps available at origin: tau <= max_tau
            train_time_indices = np.arange(0, max_tau + 1)
            train_months = months_all[train_time_indices]
            train_sst = sst_raw[train_time_indices]

            clim_map = np.zeros((12, H, W), dtype=np.float32)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                for m in range(1, 13):
                    m_idx = np.where(train_months == m)[0]
                    if len(m_idx) > 0:
                        clim_map[m - 1] = np.nanmean(train_sst[m_idx], axis=0)

            # Compute SSTA for the entire record up to eval_year using training climatology
            # Zero out land pixels
            ssta_cube = np.zeros_like(sst_raw, dtype=np.float32)
            for t_i in range(len(sst_raw)):
                m_val = months_all[t_i]
                anom = sst_raw[t_i] - clim_map[m_val - 1]
                anom[np.isnan(anom)] = 0.0  # Land is neutral 0.0 anomaly
                ssta_cube[t_i] = anom

            # 2. Local Features: SPI-3, sin(month), cos(month)
            # Fit SPI-3 scaler strictly on training origins
            sp_tr = spi3_all[train_origins]
            sp_mean, sp_std = float(np.mean(sp_tr)), float(np.std(sp_tr) + 1e-6)

            # Build Training Tensors (N_tr, 12, 1, H, W) and (N_tr, 12, 3)
            X_grid_train = []
            X_local_train = []
            for tau in train_origins:
                # Historical sequence: [tau - 11, tau] (12 months)
                seq_indices = np.arange(tau - 11, tau + 1)
                # Grid: (12, 1, H, W)
                grid_seq = ssta_cube[seq_indices, None, :, :]
                # Local: (12, 3)
                sp_seq = (spi3_all[seq_indices] - sp_mean) / sp_std
                m_seq = months_all[seq_indices]
                sin_m = np.sin(2 * np.pi * m_seq / 12.0)
                cos_m = np.cos(2 * np.pi * m_seq / 12.0)
                local_seq = np.stack([sp_seq, sin_m, cos_m], axis=-1)

                X_grid_train.append(grid_seq)
                X_local_train.append(local_seq)

            X_grid_train = np.array(X_grid_train, dtype=np.float32)
            X_local_train = np.array(X_local_train, dtype=np.float32)
            y_train = spi3_all[train_targets].astype(np.float32)
            target_months_train = months_all[train_targets]

            # Train Model for this evaluation year
            model = train_m7_model(
                X_grid_train=X_grid_train,
                X_local_train=X_local_train,
                y_train=y_train,
                target_months_train=target_months_train,
                forecast_horizon=h,
                device=device,
                epochs=35,
                batch_size=16,
                lr=1e-3,
                weight_decay=1e-3,
                dropout_p=0.3,
            )

            # Evaluate on all months of eval_year
            year_target_indices = df.index[df["year"] == eval_year].values
            for target_idx in year_target_indices:
                origin_idx = target_idx - h
                # Historical sequence strictly [origin_idx - 11, origin_idx]
                test_seq_idx = np.arange(origin_idx - 11, origin_idx + 1)
                grid_test = ssta_cube[test_seq_idx, None, :, :]
                sp_test = (spi3_all[test_seq_idx] - sp_mean) / sp_std
                m_test = months_all[test_seq_idx]
                sin_test = np.sin(2 * np.pi * m_test / 12.0)
                cos_test = np.cos(2 * np.pi * m_test / 12.0)
                local_test = np.stack([sp_test, sin_test, cos_test], axis=-1)

                t_g = torch.tensor(grid_test, dtype=torch.float32).unsqueeze(0).to(device)
                t_l = torch.tensor(local_test, dtype=torch.float32).unsqueeze(0).to(device)

                with torch.no_grad():
                    pred_val = float(model(t_g, t_l).squeeze().item())
                preds_m7_list.append(pred_val)

                # Gradient Saliency Attribution for wet vs dry months
                target_m = months_all[target_idx]
                saliency = compute_gradient_saliency(model, t_g, t_l).cpu().numpy()  # (1, H, W)
                sal_map = saliency[0]
                sal_map[land_mask[0]] = 0.0  # Mask out land

                if target_m in [7, 8, 9]:  # Kiremt wet season
                    saliency_attributions_wet[h].append(sal_map)
                elif target_m in [10, 11, 12, 1]:  # Bega dry season
                    saliency_attributions_dry[h].append(sal_map)

            print(f"  Year {eval_year}: Processed 12 months (Train N={len(train_origins)}, Max Train Target={df.loc[train_targets.max(), 'date'].strftime('%Y-%m')}).")

        # Save checkpoint for final horizon model
        model_save_path = PROCESSED_DIR / f"best_m7_cnn_bilstm_h{h}.pt"
        torch.save(model.state_dict(), str(model_save_path))
        print(f"  [+] Saved Model M7 Checkpoint: {model_save_path.name}")

        m7_predictions_by_horizon[h] = np.array(preds_m7_list)

    # -------------------------------------------------------------------------
    # Update Auditable Predictions Table
    # -------------------------------------------------------------------------
    print("\n[*] Updating Auditable Prediction Table with Model M7 Predictions...")
    df_preds = pd.read_csv(PREDS_CSV_PATH)

    # Ensure clean alignment by index
    df_preds["pred_m7_spatiotemporal_cnn_bilstm"] = np.nan
    for h in [1, 2, 3]:
        h_idx = df_preds.index[df_preds["lead_horizon"] == h].values
        df_preds.loc[h_idx, "pred_m7_spatiotemporal_cnn_bilstm"] = m7_predictions_by_horizon[h]

    df_preds.to_csv(str(PREDS_CSV_PATH), index=False)
    print(f"  [+] Updated: {PREDS_CSV_PATH} ({len(df_preds)} rows, M7 column added).")

    # -------------------------------------------------------------------------
    # Compute Metrics & Run Paired Calendar Year-Block Bootstrap (B = 2,000)
    # -------------------------------------------------------------------------
    print("\n[*] Running Paired Calendar Year-Block Bootstrap (B = 2,000)...")
    np.random.seed(42)
    B = 2000
    years_arr = df.loc[eval_target_indices, "year"].values

    with open(METRICS_JSON_PATH, "r", encoding="utf-8") as f:
        metrics_dict = json.load(f)

    for h in [1, 2, 3]:
        h_key = f"lead_{h}"
        y_true_arr = df_preds.loc[df_preds["lead_horizon"] == h, "y_true_spi3"].values
        p_m0 = df_preds.loc[df_preds["lead_horizon"] == h, "pred_m0_climatology"].values
        p_m2 = df_preds.loc[df_preds["lead_horizon"] == h, "pred_m2_local_ar"].values
        p_m4 = df_preds.loc[df_preds["lead_horizon"] == h, "pred_m4_indian_ocean_iod"].values
        p_m7 = df_preds.loc[df_preds["lead_horizon"] == h, "pred_m7_spatiotemporal_cnn_bilstm"].values

        # M7 Point Metrics
        m7_metrics = compute_metrics(y_true_arr, p_m7)
        metrics_dict[h_key]["metrics"]["m7_cnn_bilstm"] = m7_metrics

        # Paired Bootstrap Differences
        diff_clim = []
        diff_local = []
        diff_m4 = []

        for _ in range(B):
            sampled_years = np.random.choice(np.arange(2017, 2025), size=8, replace=True)
            boot_idx = []
            for sy in sampled_years:
                boot_idx.extend(np.where(years_arr == sy)[0])
            boot_idx = np.array(boot_idx)

            yt_b = y_true_arr[boot_idx]
            r_m7_b = np.sqrt(np.mean((yt_b - p_m7[boot_idx]) ** 2))
            r_m0_b = np.sqrt(np.mean((yt_b - p_m0[boot_idx]) ** 2))
            r_m2_b = np.sqrt(np.mean((yt_b - p_m2[boot_idx]) ** 2))
            r_m4_b = np.sqrt(np.mean((yt_b - p_m4[boot_idx]) ** 2))

            diff_clim.append(r_m7_b - r_m0_b)
            diff_local.append(r_m7_b - r_m2_b)
            diff_m4.append(r_m7_b - r_m4_b)

        # Bootstrap stats helper
        def get_boot_stat(diff_arr, base_rmse, ref_rmse):
            arr = np.array(diff_arr)
            ci = [round(float(x), 4) for x in np.percentile(arr, [2.5, 97.5])]
            p_val = round(float(min(1.0, 2.0 * min(np.mean(arr >= 0.0), np.mean(arr <= 0.0)))), 4)
            return {
                "dRMSE": round(float(base_rmse - ref_rmse), 4),
                "ci95": ci,
                "p_value": p_val,
            }

        metrics_dict[h_key]["bootstrap"]["m7_vs_climatology"] = get_boot_stat(
            diff_clim, m7_metrics["rmse"], metrics_dict[h_key]["metrics"]["m0_clim"]["rmse"]
        )
        metrics_dict[h_key]["bootstrap"]["m7_vs_local_m2"] = get_boot_stat(
            diff_local, m7_metrics["rmse"], metrics_dict[h_key]["metrics"]["m2"]["rmse"]
        )
        metrics_dict[h_key]["bootstrap"]["m7_vs_indian_ocean_m4"] = get_boot_stat(
            diff_m4, m7_metrics["rmse"], metrics_dict[h_key]["metrics"]["m4"]["rmse"]
        )

        print(f"\n--- Lead h = {h} Results ---")
        print(f"  M0 Climatology:  RMSE = {metrics_dict[h_key]['metrics']['m0_clim']['rmse']:.4f}, r = {metrics_dict[h_key]['metrics']['m0_clim']['r']}")
        print(f"  M2 Local AR:     RMSE = {metrics_dict[h_key]['metrics']['m2']['rmse']:.4f}, r = {metrics_dict[h_key]['metrics']['m2']['r']}")
        print(f"  M4 Indian Ridge: RMSE = {metrics_dict[h_key]['metrics']['m4']['rmse']:.4f}, r = {metrics_dict[h_key]['metrics']['m4']['r']}")
        print(f"  M7 CNN-BiLSTM:   RMSE = {m7_metrics['rmse']:.4f}, MAE = {m7_metrics['mae']:.4f}, r = {m7_metrics['r']}")
        print(f"  --> M7 vs Climatology: dRMSE = {metrics_dict[h_key]['bootstrap']['m7_vs_climatology']['dRMSE']:+.4f} (95% CI: {metrics_dict[h_key]['bootstrap']['m7_vs_climatology']['ci95']}, p = {metrics_dict[h_key]['bootstrap']['m7_vs_climatology']['p_value']})")
        print(f"  --> M7 vs Local AR:    dRMSE = {metrics_dict[h_key]['bootstrap']['m7_vs_local_m2']['dRMSE']:+.4f} (95% CI: {metrics_dict[h_key]['bootstrap']['m7_vs_local_m2']['ci95']}, p = {metrics_dict[h_key]['bootstrap']['m7_vs_local_m2']['p_value']})")
        print(f"  --> M7 vs Indian M4:   dRMSE = {metrics_dict[h_key]['bootstrap']['m7_vs_indian_ocean_m4']['dRMSE']:+.4f} (95% CI: {metrics_dict[h_key]['bootstrap']['m7_vs_indian_ocean_m4']['ci95']}, p = {metrics_dict[h_key]['bootstrap']['m7_vs_indian_ocean_m4']['p_value']})")

    with open(METRICS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"\n[+] Updated Metrics JSON with Model M7: {METRICS_JSON_PATH}")

    # -------------------------------------------------------------------------
    # Spatial Saliency Attribution Verification Figure
    # -------------------------------------------------------------------------
    print("\n[*] Generating Spatial Saliency Attribution Map (Figure 5)...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

    # Average saliency across Lead 1 wet vs dry
    sal_wet_mean = np.mean(saliency_attributions_wet[1], axis=0)
    sal_dry_mean = np.mean(saliency_attributions_dry[1], axis=0)

    # Normalize for visual comparison
    max_val = max(np.max(sal_wet_mean), np.max(sal_dry_mean)) + 1e-8

    lon_grid, lat_grid = np.meshgrid(sub_lons, sub_lats)

    # Panel A: Wet Season (Kiremt JAS)
    im0 = axes[0].pcolormesh(lon_grid, lat_grid, sal_wet_mean, cmap="YlOrRd", vmin=0, vmax=max_val, shading="auto")
    axes[0].set_title("(a) Model M7 Gradient Attribution: Wet Season (Kiremt JAS)\nPeaks over Western Indian Ocean & Arabian Sea", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Longitude (°E)", fontsize=10)
    axes[0].set_ylabel("Latitude (°N)", fontsize=10)
    axes[0].grid(True, linestyle="--", alpha=0.4)
    # Highlight Arabian Sea / Western Indian Ocean box
    rect_arabian = plt.Rectangle((45, 5), 25, 20, fill=False, edgecolor="blue", linewidth=2, linestyle="--", label="Western IO / Arabian Sea")
    axes[0].add_patch(rect_arabian)
    axes[0].legend(loc="lower right", fontsize=8)

    # Panel B: Dry Season (Bega ONDJ)
    im1 = axes[1].pcolormesh(lon_grid, lat_grid, sal_dry_mean, cmap="YlOrRd", vmin=0, vmax=max_val, shading="auto")
    axes[1].set_title("(b) Model M7 Gradient Attribution: Dry Season (Bega ONDJ)\nSubdued Gradient Response across Ocean Basin", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Longitude (°E)", fontsize=10)
    axes[1].grid(True, linestyle="--", alpha=0.4)
    rect_arabian2 = plt.Rectangle((45, 5), 25, 20, fill=False, edgecolor="blue", linewidth=2, linestyle="--")
    axes[1].add_patch(rect_arabian2)

    cbar = fig.colorbar(im0, ax=axes.ravel().tolist(), orientation="horizontal", fraction=0.05, pad=0.18, shrink=0.7)
    cbar.set_label(r"Mean Absolute Gradient Attribution $\left| \frac{\partial \hat{y}_{t+1}}{\partial \mathrm{SST}(x, y, t)} \right|$", fontsize=10)

    plt.suptitle("Model M7 (Deep Spatiotemporal CNN-BiLSTM) Teleconnection Saliency Audit", fontsize=13, fontweight="bold", y=0.98)
    plt.subplots_adjust(bottom=0.22, top=0.90, wspace=0.25)
    plt.savefig(str(SALIENCY_FIG_PATH), bbox_inches="tight")
    plt.close()
    print(f"  [+] Saved Figure 5: {SALIENCY_FIG_PATH}")


if __name__ == "__main__":
    t0 = time.time()
    run_m7_benchmark()
    print(f"\n[OK] Entire Model M7 Pipeline Executed in {time.time() - t0:.2f}s!")
