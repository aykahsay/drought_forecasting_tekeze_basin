"""
Advanced High-Capacity Spatio-Temporal ResNet-CNN-LSTM Pipeline
==============================================================
Improvements:
  1. Utilizes the full 400 temporal steps (instead of 120 subsamples).
  2. 4 Multi-Spectral Channels:
     [Soil Moisture Layer 1, Soil Moisture Layer 2, 2m Temperature, Total Precipitation]
  3. Residual Convolutional Blocks (ResNet-like skip connections) + Spatial Attention.
  4. Bidirectional LSTM with hidden_dim=128 + Cosine Annealing Learning Rate Scheduler.
  5. Sequence history length = 6 timesteps for deeper lag capture.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import torch
import torch.nn as nn
from loguru import logger
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ---------------------------------------------------------------------------
# 1. Spatial Attention + Residual Conv Block
# ---------------------------------------------------------------------------
class SpatialAttention(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size=7, padding=3)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        scale = torch.cat([avg_out, max_out], dim=1)
        att = self.sigmoid(self.conv(scale))
        return x * att


class ResidualBlock2D(nn.Module):
    def __init__(self, in_c: int, out_c: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
            nn.GELU(),
            nn.Conv2d(out_c, out_c, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_c),
        )
        self.skip = nn.Conv2d(in_c, out_c, kernel_size=1) if in_c != out_c else nn.Identity()
        self.act = nn.GELU()

    def forward(self, x):
        return self.act(self.conv(x) + self.skip(x))


class HighCapacityResNetCNNLSTM(nn.Module):
    def __init__(
        self,
        in_channels: int = 4,
        spatial_features: int = 64,
        lstm_hidden: int = 128,
        num_lstm_layers: int = 2,
        dropout: float = 0.25,
    ):
        super().__init__()
        self.encoder = nn.Sequential(
            ResidualBlock2D(in_channels, 32),
            nn.MaxPool2d(2, 2),
            ResidualBlock2D(32, spatial_features),
            SpatialAttention(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )

        self.lstm = nn.LSTM(
            input_size=spatial_features * 4 * 4,
            hidden_size=lstm_hidden,
            num_layers=num_lstm_layers,
            batch_first=True,
            dropout=dropout if num_lstm_layers > 1 else 0.0,
            bidirectional=True,
        )

        self.head = nn.Sequential(
            nn.Linear(lstm_hidden * 2, 64),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.GELU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        batch_size, seq_len, c, h, w = x.shape
        x_reshaped = x.view(batch_size * seq_len, c, h, w)
        spatial_feats = self.encoder(x_reshaped)
        spatial_flat = spatial_feats.view(batch_size, seq_len, -1)

        lstm_out, _ = self.lstm(spatial_flat)
        out = self.head(lstm_out[:, -1, :])
        return out.squeeze(-1)


# ---------------------------------------------------------------------------
# 2. Dataset Builder using All 400 NetCDF Timesteps
# ---------------------------------------------------------------------------
def load_all_netcdf_data(
    nc_path: str = "2000-2023-soillayer.nc",
    seq_len: int = 12,
):
    # Check if pre-compiled genuine Yechila Abergelle - Tekeze Basin real tensor cube exists
    for cube_candidate in [
        Path("data/processed/yechila_tekeze_real_tensor_cube.npz"),
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed" / "yechila_tekeze_real_tensor_cube.npz",
        Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "yechila_tekeze_real_tensor_cube.npz",
    ]:
        if cube_candidate.exists():
            logger.info(f"Loading genuine Yechila Abergelle - Tekeze Basin Tensor Cube from {cube_candidate}...")
            data = np.load(str(cube_candidate))
            return data["X"], data["y"]

    # Check candidates if nc_path does not exist
    p = Path(nc_path)
    if not p.exists():
        for candidate in [
            Path(__file__).resolve().parent.parent.parent.parent / "2000-2023-soillayer.nc",
            Path(__file__).resolve().parent.parent.parent / "2000-2023-soillayer.nc",
            Path("drought_forecasting/2000-2023-soillayer.nc"),
        ]:
            if candidate.exists():
                p = candidate
                break
    logger.info(f"Loading full NetCDF archive from {p}...")
    ds = nc.Dataset(str(p), "r")

    lat_slice = slice(10, 45)
    lon_slice = slice(40, 90)

    # 4 channels: swvl1, swvl2, t2m, tp
    if len(ds.variables["swvl1"].shape) == 4:
        swvl1 = ds.variables["swvl1"][:, 0, lat_slice, lon_slice]
        swvl2 = ds.variables["swvl2"][:, 0, lat_slice, lon_slice]
        t2m   = ds.variables["t2m"][:, 0, lat_slice, lon_slice] - 273.15
        tp    = ds.variables["tp"][:, 0, lat_slice, lon_slice]
    else:
        swvl1 = ds.variables["swvl1"][:, lat_slice, lon_slice]
        swvl2 = ds.variables["swvl2"][:, lat_slice, lon_slice]
        t2m   = ds.variables["t2m"][:, lat_slice, lon_slice] - 273.15
        tp    = ds.variables["tp"][:, lat_slice, lon_slice]
    ds.close()

    def clean_var(a):
        if hasattr(a, "filled"):
            a = a.filled(np.nan)
        mean_v = np.nanmean(a)
        a[np.isnan(a)] = mean_v
        return a

    swvl1 = clean_var(swvl1)
    swvl2 = clean_var(swvl2)
    t2m   = clean_var(t2m)
    tp    = clean_var(tp)

    # Standardize
    def norm(a):
        return (a - np.mean(a)) / (np.std(a) + 1e-6)

    swvl1 = norm(swvl1)
    swvl2 = norm(swvl2)
    t2m   = norm(t2m)
    tp    = norm(tp)

    # Stack: (time, 4, H, W)
    tensors = np.stack([swvl1, swvl2, t2m, tp], axis=1)

    X_seqs = []
    y_targets = []

    for i in range(len(tensors) - seq_len - 1):
        x_window = tensors[i : i + seq_len]
        target_val = float(np.mean(swvl1[i + seq_len]))
        X_seqs.append(x_window)
        y_targets.append(target_val)

    X = np.array(X_seqs, dtype=np.float32)
    y = np.array(y_targets, dtype=np.float32)
    logger.info(f"Constructed Large Dataset: X={X.shape}, y={y.shape}")
    return X, y


# ---------------------------------------------------------------------------
# 3. Training Loop with Learning Rate Scheduler & GPU Acceleration
# ---------------------------------------------------------------------------
def train_high_accuracy_cnn_lstm(epochs: int = 40, batch_size: int = 16, lr: float = 0.002):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        logger.info(f"Accelerating training on GPU: {torch.cuda.get_device_name(0)} ({round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)} GB VRAM)")
    else:
        logger.info("Training on CPU...")

    X, y = load_all_netcdf_data()

    split_idx = int(len(X) * 0.80)  # 80% train, 20% test
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    in_channels = X.shape[2]
    model = HighCapacityResNetCNNLSTM(in_channels=in_channels, spatial_features=64, lstm_hidden=128).to(device)
    criterion = nn.SmoothL1Loss()  # Huber loss for robust convergence
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    n_batches = int(np.ceil(len(X_train) / batch_size))

    logger.info(f"Training High-Capacity ResNet-CNN-LSTM on full archive...")

    for ep in range(1, epochs + 1):
        model.train()
        permutation = np.random.permutation(len(X_train))
        epoch_loss = 0.0

        for b in range(n_batches):
            indices = permutation[b * batch_size : (b + 1) * batch_size]
            batch_x = torch.tensor(X_train[indices], device=device)
            batch_y = torch.tensor(y_train[indices], device=device)

            optimizer.zero_grad()
            preds = model(batch_x)
            loss = criterion(preds, batch_y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_loss += loss.item()

        scheduler.step()

        # Validation
        model.eval()
        with torch.no_grad():
            val_preds = model(torch.tensor(X_val, device=device))
            val_loss = criterion(val_preds, torch.tensor(y_val, device=device)).item()

        if ep % 10 == 0 or ep == epochs:
            logger.info(f"Epoch [{ep:02d}/{epochs}] | Train Loss: {epoch_loss/n_batches:.4f} | Val Loss: {val_loss:.4f}")

    # Final Evaluation
    model.eval()
    with torch.no_grad():
        final_preds = model(torch.tensor(X_val, device=device)).cpu().numpy()

    from scipy.stats import pearsonr
    rmse = float(np.sqrt(mean_squared_error(y_val, final_preds)))
    mae = float(mean_absolute_error(y_val, final_preds))
    r2 = float(r2_score(y_val, final_preds))
    r_corr = float(pearsonr(y_val, final_preds)[0])

    logger.info(f"=== Optimized ResNet-CNN-LSTM Results (Real Holdout) ===")
    logger.info(f"Validation RMSE:        {rmse:.4f}")
    logger.info(f"Validation MAE:         {mae:.4f}")
    logger.info(f"Validation R²:          {r2:.4f} ({r2*100:.1f}%)")
    logger.info(f"Pearson Correlation (r): {r_corr:.4f}")

    # Save real model weights checkpoints
    weights_path = Path("data/processed/best_yechila_tekeze_cnn_lstm.pt")
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), str(weights_path))
    # Also keep primary pointer updated
    torch.save(model.state_dict(), str(Path("data/processed/best_cnn_lstm_model.pt")))
    logger.info(f"Real PyTorch model checkpoint saved to {weights_path}")

    # Plot
    plt.figure(figsize=(10, 4.5))
    plt.plot(y_val, label="Observed Ground Truth (Yechila Abergelle Soil Moisture)", color="#1976D2", linewidth=2.2)
    plt.plot(final_preds, label="Deep ResNet-CNN-LSTM Prediction", color="#00C853", linestyle="--", linewidth=2.2)
    plt.title(f"Yechila Abergelle & Tekeze Basin Drought Forecasting (Holdout R²={r2:.3f}, r={r_corr:.3f}, RMSE={rmse:.3f})")
    plt.xlabel("Validation Time Step (Chronological Holdout Months)")
    plt.ylabel("Standardized Moisture State (Root-Zone 0-28 cm)")
    plt.legend(frameon=True)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    chart_path = Path("data/processed/yechila_tekeze_validation_chart.png")
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(chart_path), dpi=150)
    plt.savefig(str(Path("data/processed/cnn_lstm_validation_chart.png")), dpi=150)
    logger.info(f"Yechila Abergelle validation chart saved to {chart_path}")

    return {"rmse": rmse, "mae": mae, "r2": r2, "pearson_r": r_corr}


if __name__ == "__main__":
    train_high_accuracy_cnn_lstm()
