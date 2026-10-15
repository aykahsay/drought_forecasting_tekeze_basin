"""
plot_m7_saliency_figure.py
==========================
Generates publication-quality Figure 5: Model M7 Gradient Attribution Map
with precise layout, no title overlapping, and enhanced geographical readability.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import pandas as pd
import torch

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "drought_forecasting"))

from drought_forecasting.agriminds.models.spatiotemporal_cnn_bilstm import (
    SpatioTemporal_CNN_BiLSTM,
    compute_gradient_saliency,
)

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
RAW_SST_PATH = ROOT_DIR / "data" / "raw" / "teleconnections" / "sst.mnmean.nc"
MASTER_CSV_PATH = PROCESSED_DIR / "abregelle_tekeze_unified_monthly_1981_2024.csv"
MODEL_PATH = PROCESSED_DIR / "best_m7_cnn_bilstm_h1.pt"
OUT_FIG_PATH = PROCESSED_DIR / "figure5_m7_saliency_teleconnection_attribution.png"
ARTIFACT_FIG_PATH = Path(r"C:\Users\User\.gemini\antigravity-ide\brain\916ac0ba-5420-43ef-b5cd-75c1a666b721\figure5_m7_saliency_teleconnection_attribution.png")


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    df = pd.read_csv(MASTER_CSV_PATH)
    spi3_all = df["spi3"].bfill().values
    months_all = df["month"].values

    ds = nc.Dataset(str(RAW_SST_PATH), "r")
    lats = ds.variables["lat"][:]
    lons = ds.variables["lon"][:]
    t_var = ds.variables["time"]
    dates = nc.num2date(t_var[:], units=t_var.units)
    dt_index = pd.to_datetime([d.strftime("%Y-%m-%d") for d in dates])
    idx_1981_2024 = np.where((dt_index.year >= 1981) & (dt_index.year <= 2024))[0]

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
    sst_arr[mask] = np.nan

    # Load model
    model = SpatioTemporal_CNN_BiLSTM(
        in_grid_channels=1,
        cnn_features=32,
        local_feat_dim=3,
        lstm_hidden_dim=64,
        forecast_horizon=1,
    ).to(device)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    model.eval()

    # Compute baseline climatology on historical training data (< 2017)
    train_time_indices = np.where(df["year"] < 2017)[0]
    train_months = months_all[train_time_indices]
    train_sst = sst_arr[train_time_indices]

    clim_map = np.zeros((12, len(sub_lats), len(sub_lons)), dtype=np.float32)
    for m in range(1, 13):
        m_idx = np.where(train_months == m)[0]
        if len(m_idx) > 0:
            clim_map[m - 1] = np.nanmean(train_sst[m_idx], axis=0)

    ssta_cube = np.zeros_like(sst_arr, dtype=np.float32)
    for t_i in range(len(sst_arr)):
        m_val = months_all[t_i]
        anom = sst_arr[t_i] - clim_map[m_val - 1]
        anom[np.isnan(anom)] = 0.0
        ssta_cube[t_i] = anom

    sp_tr = spi3_all[train_time_indices]
    sp_mean, sp_std = float(np.mean(sp_tr)), float(np.std(sp_tr) + 1e-6)

    # Compute saliency across 2017-2024 test cases
    test_indices = np.where((df["year"] >= 2017) & (df["year"] <= 2024))[0]
    sal_wet = []
    sal_dry = []

    for target_idx in test_indices:
        origin_idx = target_idx - 1
        seq_idx = np.arange(origin_idx - 11, origin_idx + 1)
        grid_test = ssta_cube[seq_idx, None, :, :]
        sp_test = (spi3_all[seq_idx] - sp_mean) / sp_std
        m_test = months_all[seq_idx]
        sin_test = np.sin(2 * np.pi * m_test / 12.0)
        cos_test = np.cos(2 * np.pi * m_test / 12.0)
        local_test = np.stack([sp_test, sin_test, cos_test], axis=-1)

        t_g = torch.tensor(grid_test, dtype=torch.float32).unsqueeze(0).to(device)
        t_l = torch.tensor(local_test, dtype=torch.float32).unsqueeze(0).to(device)

        sal = compute_gradient_saliency(model, t_g, t_l).cpu().numpy()[0]
        sal[mask[0]] = 0.0  # Zero out land

        m_tgt = months_all[target_idx]
        if m_tgt in [7, 8, 9]:
            sal_wet.append(sal)
        elif m_tgt in [10, 11, 12, 1]:
            sal_dry.append(sal)

    sal_wet_mean = np.mean(sal_wet, axis=0)
    sal_dry_mean = np.mean(sal_dry, axis=0)
    max_val = max(np.max(sal_wet_mean), np.max(sal_dry_mean)) + 1e-8

    lon_grid, lat_grid = np.meshgrid(sub_lons, sub_lats)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6.0), dpi=300)

    # Panel A: Wet Season
    im0 = axes[0].pcolormesh(lon_grid, lat_grid, sal_wet_mean, cmap="YlOrRd", vmin=0, vmax=max_val, shading="auto")
    axes[0].set_title("(a) Wet Season (Kiremt JAS Monsoon)\nPeak Attribution: Western Indian Ocean & Arabian Sea", fontsize=11, fontweight="bold", pad=10)
    axes[0].set_xlabel("Longitude (°E)", fontsize=10)
    axes[0].set_ylabel("Latitude (°N)", fontsize=10)
    axes[0].grid(True, linestyle="--", alpha=0.35)
    rect0 = plt.Rectangle((45, 5), 25, 20, fill=False, edgecolor="blue", linewidth=2.2, linestyle="--", label="Western IO / Arabian Sea Pathway")
    axes[0].add_patch(rect0)
    axes[0].legend(loc="lower right", fontsize=8.5, framealpha=0.9)

    # Panel B: Dry Season
    im1 = axes[1].pcolormesh(lon_grid, lat_grid, sal_dry_mean, cmap="YlOrRd", vmin=0, vmax=max_val, shading="auto")
    axes[1].set_title("(b) Dry Season (Bega ONDJ)\nSubdued Ocean Saliency Across Entire Basin", fontsize=11, fontweight="bold", pad=10)
    axes[1].set_xlabel("Longitude (°E)", fontsize=10)
    axes[1].grid(True, linestyle="--", alpha=0.35)
    rect1 = plt.Rectangle((45, 5), 25, 20, fill=False, edgecolor="blue", linewidth=2.2, linestyle="--")
    axes[1].add_patch(rect1)

    cbar = fig.colorbar(im0, ax=axes.ravel().tolist(), orientation="horizontal", fraction=0.045, pad=0.16, shrink=0.65)
    cbar.set_label(r"Mean Absolute Gradient Saliency $\left| \frac{\partial \hat{y}_{t+1}}{\partial \mathrm{SST}(x, y, t)} \right|$", fontsize=10)

    fig.suptitle("Model M7 (Deep Spatiotemporal CNN-BiLSTM) Teleconnection Attribution Audit", fontsize=13, fontweight="bold", y=0.98)
    plt.subplots_adjust(bottom=0.20, top=0.86, wspace=0.22)
    plt.savefig(str(OUT_FIG_PATH), bbox_inches="tight")
    plt.savefig(str(ARTIFACT_FIG_PATH), bbox_inches="tight")
    plt.close()
    print("Successfully regenerated publication-ready Figure 5!")


if __name__ == "__main__":
    main()
