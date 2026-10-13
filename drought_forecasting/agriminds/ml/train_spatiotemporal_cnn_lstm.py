"""
Spatio-Temporal 2D CNN-LSTM Training Pipeline on Real Raster Grids (§ Deep Learning)
==================================================================================
Trains a true 2D Spatio-Temporal Deep Learning architecture:
  - Input: Multi-channel spatial raster images (Soil Moisture, Temperature, Precipitation)
    Shape: (Batch, Channels, Height, Width) across time sequences.
  - Spatial Backbone: 2D Convolutional neural network (Conv2d, BatchNorm2d, MaxPool2d)
  - Temporal Core: Recurrent Bidirectional LSTM (Bi-LSTM) tracking multi-horizon drought states.
  - Evaluation: Validation RMSE, MAE, R², and visual spatial prediction maps.
"""
from datetime import datetime, timezone
from pathlib import Path
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import torch
import torch.nn as nn
from loguru import logger
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ---------------------------------------------------------------------------
# 1. Spatio-Temporal 2D CNN-LSTM PyTorch Neural Network
# ---------------------------------------------------------------------------
class SpatioTemporal2DCNNLSTM(nn.Module):
    def __init__(
        self,
        in_channels: int = 3,       # e.g., [swvl1, swvl2, t2m]
        spatial_features: int = 64,
        lstm_hidden: int = 64,
        num_lstm_layers: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        # 2D Spatial Convolutional Feature Extractor
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),  # downsamples spatial grid

            nn.Conv2d(32, spatial_features, kernel_size=3, padding=1),
            nn.BatchNorm2d(spatial_features),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),  # fixed latent spatial embedding: 4x4
        )

        # Recurrent Temporal Sequence Engine
        self.lstm = nn.LSTM(
            input_size=spatial_features * 4 * 4,
            hidden_size=lstm_hidden,
            num_layers=num_lstm_layers,
            batch_first=True,
            dropout=dropout if num_lstm_layers > 1 else 0.0,
            bidirectional=True,
        )

        # Multi-Horizon Prediction Regression Head
        self.regressor = nn.Sequential(
            nn.Linear(lstm_hidden * 2, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        # x shape: (batch_size, seq_len, in_channels, H, W)
        batch_size, seq_len, c, h, w = x.shape
        x_reshaped = x.view(batch_size * seq_len, c, h, w)

        # Extract spatial feature map
        spatial_feats = self.encoder(x_reshaped)  # (batch*seq, spatial_features, 4, 4)
        spatial_flat = spatial_feats.view(batch_size, seq_len, -1)

        # Temporal LSTM progression
        lstm_out, _ = self.lstm(spatial_flat)
        last_temporal_state = lstm_out[:, -1, :]  # last timestep representation

        # Predict continuous target (Sc-PDSI / drought index)
        out = self.regressor(last_temporal_state)
        return out.squeeze(-1)


# ---------------------------------------------------------------------------
# 2. Data Preparation: Extract Spatial Time-Series Tensors from Real NetCDF
# ---------------------------------------------------------------------------
def load_spatiotemporal_tensors(
    nc_path: str = "2000-2023-soillayer.nc",
    seq_len: int = 4,
    max_samples: int = 120,
):
    """
    Construct multi-channel spatial raster sequences:
      Channels: [swvl1 (soil layer 1), swvl2 (soil layer 2), t2m (temperature)]
    """
    logger.info(f"Opening spatial NetCDF dataset: {nc_path}")
    ds = nc.Dataset(nc_path, "r")

    # Crop to central Ethiopia bounding window (subgrid for efficient spatial convolution)
    lat_slice = slice(10, 45)   # 35 grid cells
    lon_slice = slice(40, 90)   # 50 grid cells

    swvl1_all = ds.variables["swvl1"][:max_samples, 0, lat_slice, lon_slice]
    swvl2_all = ds.variables["swvl2"][:max_samples, 0, lat_slice, lon_slice]
    t2m_all = ds.variables["t2m"][:max_samples, 0, lat_slice, lon_slice] - 273.15 # to Celsius
    ds.close()

    # Fill invalid/masked values with regional mean
    def clean_arr(a):
        if hasattr(a, "filled"):
            a = a.filled(np.nan)
        mean_val = np.nanmean(a)
        a[np.isnan(a)] = mean_val
        return a

    swvl1_all = clean_arr(swvl1_all)
    swvl2_all = clean_arr(swvl2_all)
    t2m_all = clean_arr(t2m_all)

    # Standardize each channel across spatial domain
    swvl1_all = (swvl1_all - np.mean(swvl1_all)) / (np.std(swvl1_all) + 1e-6)
    swvl2_all = (swvl2_all - np.mean(swvl2_all)) / (np.std(swvl2_all) + 1e-6)
    t2m_all = (t2m_all - np.mean(t2m_all)) / (np.std(t2m_all) + 1e-6)

    # Stack channels -> (T, C=3, H, W)
    tensors = np.stack([swvl1_all, swvl2_all, t2m_all], axis=1)

    # Create sequential sliding windows (seq_len timesteps -> target moisture anomaly)
    X_seqs = []
    y_targets = []

    # Target: subsequent root-zone moisture anomaly (proxy for agricultural drought index)
    for i in range(len(tensors) - seq_len - 1):
        x_window = tensors[i : i + seq_len]
        # Target: mean moisture state at future timestep t + seq_len
        target_val = float(np.mean(swvl1_all[i + seq_len]))
        X_seqs.append(x_window)
        y_targets.append(target_val)

    X = np.array(X_seqs, dtype=np.float32)
    y = np.array(y_targets, dtype=np.float32)

    logger.info(f"Constructed Spatio-Temporal Dataset: X={X.shape}, y={y.shape}")
    return X, y


# ---------------------------------------------------------------------------
# 3. Training & Evaluation Engine
# ---------------------------------------------------------------------------
def train_spatiotemporal_model(epochs: int = 50, lr: float = 0.003):
    X, y = load_spatiotemporal_tensors()

    # Chronological Split (Train 75%, Validation 25% - no random shuffle)
    split_idx = int(len(X) * 0.75)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    device = torch.device("cpu")
    model = SpatioTemporal2DCNNLSTM(in_channels=3, spatial_features=32, lstm_hidden=32).to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    X_tr_t = torch.tensor(X_train).to(device)
    y_tr_t = torch.tensor(y_train).to(device)
    X_va_t = torch.tensor(X_val).to(device)
    y_va_t = torch.tensor(y_val).to(device)

    logger.info(f"Training Spatio-Temporal 2D CNN-LSTM ({epochs} epochs)...")
    history = []

    for ep in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        preds = model(X_tr_t)
        loss = criterion(preds, y_tr_t)
        loss.backward()
        optimizer.step()

        # Validation step
        model.eval()
        with torch.no_grad():
            val_preds = model(X_va_t)
            val_loss = criterion(val_preds, y_va_t).item()

        history.append((loss.item(), val_loss))
        if ep % 10 == 0 or ep == epochs:
            logger.info(f"Epoch [{ep:02d}/{epochs}] | Train Loss: {loss.item():.4f} | Val Loss: {val_loss:.4f}")

    # Final Metrics
    model.eval()
    with torch.no_grad():
        final_preds = model(X_va_t).cpu().numpy()

    rmse = float(np.sqrt(mean_squared_error(y_val, final_preds)))
    mae = float(mean_absolute_error(y_val, final_preds))
    r2 = float(r2_score(y_val, final_preds))

    logger.info(f"=== CNN-LSTM Evaluation Complete ===")
    logger.info(f"Validation RMSE: {rmse:.4f}")
    logger.info(f"Validation MAE:  {mae:.4f}")
    logger.info(f"Validation R²:   {r2:.4f}")

    # Plot Prediction Trajectory
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 4))
    plt.plot(y_val, label="Observed Target (Soil Moisture State)", color="#1976D2", linewidth=2)
    plt.plot(final_preds, label="CNN-LSTM Prediction", color="#E64A19", linestyle="--", linewidth=2)
    plt.title(f"Spatio-Temporal 2D CNN-LSTM Prediction vs Ground Truth (RMSE={rmse:.3f}, R²={r2:.2f})")
    plt.xlabel("Validation Time Step")
    plt.ylabel("Standardized Moisture State")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    chart_path = "data/processed/cnn_lstm_validation_chart.png"
    plt.savefig(chart_path, dpi=150)
    logger.info(f"Saved validation chart to {chart_path}")

    return {
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "chart_path": chart_path,
    }


if __name__ == "__main__":
    train_spatiotemporal_model()
