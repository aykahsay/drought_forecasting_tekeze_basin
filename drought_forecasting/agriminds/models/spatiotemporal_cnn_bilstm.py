"""
spatiotemporal_cnn_bilstm.py
============================
Deep Spatiotemporal CNN-BiLSTM Architecture for Climate and Drought Forecasting
(Designated Model M7 in AI-DREWS Benchmark Protocol).

Key Architectural Pillars & Small-Sample Climate Safeguards:
1. Spatial Feature Extraction (2D-CNN):
   - Ingests trimmed 2D sea surface temperature anomalies (SSTA) or reanalysis fields
     (e.g., [10°S–30°N, 30°E–100°E] covering Indian Ocean basin and Arabian Sea).
   - Learns spatial dipole modes directly from grid cells, removing arbitrary 1D index boundaries.
   - Restricts spatial dimensions via Adaptive Average Pooling to prevent parameter explosion.

2. Causal Bidirectional Temporal Sequence Modeling (Causal BiLSTM):
   - Standard BiLSTMs peek forward across the forecast origin if run over future steps.
   - Here, the bidirectional pass is strictly confined to the historical lookback sequence [t-L+1, t].
   - Forward LSTM:  processes past -> origin (t-L+1 -> t)
   - Backward LSTM: processes origin -> past (t -> t-L+1)
   - The hidden states are pooled strictly across historical tokens; zero future tokens (t+1..t+h) exist.

3. Temporal Attention Pooling:
   - Learns time-adaptive weights over the historical sequence, focusing on critical teleconnection lags.

4. Small-Sample Regime Safeguards (N_eff ≈ 113.6):
   - Aggressive Dropout (spatial & temporal p=0.3)
   - Seasonally Weighted Loss: Weights wet seasons (Kiremt JAS, Belg MAM) 2x higher than dry Bega (ONDJ).
   - Gradient Saliency Attribution: Computes |∂y_hat / ∂x_grid| to audit physical ocean focus.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class SpatioTemporal_CNN_BiLSTM(nn.Module):
    """
    SpatioTemporal CNN-BiLSTM with Causal Historical Sequence Processing,
    Multimodal Feature Fusion, and Temporal Attention Pooling.
    """

    def __init__(
        self,
        in_grid_channels: int = 1,      # 1 for SSTA, or 2 for (SSTA, Moisture Convergence / VIMC)
        cnn_features: int = 32,         # Channel depth for 2D spatial encoder
        local_feat_dim: int = 3,        # Local autoregressive features (e.g., SPI-3(t), sin(month), cos(month))
        lstm_hidden_dim: int = 64,      # Hidden units per directional LSTM
        num_lstm_layers: int = 1,       # Stacked LSTM depth
        dropout_p: float = 0.3,         # Dropout probability for regularization
        forecast_horizon: int = 1,      # Target lead horizon h (1, 2, or 3 months ahead)
    ):
        super().__init__()
        self.forecast_horizon = forecast_horizon
        self.lstm_hidden_dim = lstm_hidden_dim

        # ---------------------------------------------------------------------
        # 1. Spatial Encoder: 2D-CNN over ocean basin / reanalysis spatial grid
        # ---------------------------------------------------------------------
        self.spatial_cnn = nn.Sequential(
            nn.Conv2d(in_grid_channels, 16, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(16),
            nn.LeakyReLU(0.1),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(16, cnn_features, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(cnn_features),
            nn.LeakyReLU(0.1),
            nn.AdaptiveAvgPool2d((2, 2)),
            nn.Flatten(),
        )
        self.spatial_out_dim = cnn_features * 2 * 2  # e.g., 32 * 4 = 128

        # ---------------------------------------------------------------------
        # 2. Multimodal Fusion Projection at each historical time step
        # ---------------------------------------------------------------------
        self.step_dense = nn.Sequential(
            nn.Linear(self.spatial_out_dim + local_feat_dim, 64),
            nn.LayerNorm(64),
            nn.Dropout(dropout_p),
        )

        # ---------------------------------------------------------------------
        # 3. Temporal Causal BiLSTM
        # Bidirectional over historical context sequence [t-L+1, t] ONLY.
        # Input shape: (batch_size, seq_len, 64)
        # ---------------------------------------------------------------------
        self.bilstm = nn.LSTM(
            input_size=64,
            hidden_size=lstm_hidden_dim,
            num_layers=num_lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout_p if num_lstm_layers > 1 else 0.0,
        )

        # ---------------------------------------------------------------------
        # 4. Temporal Attention Pooling
        # Computes normalized scalar weight per historical time step in sequence
        # ---------------------------------------------------------------------
        self.attention = nn.Sequential(
            nn.Linear(lstm_hidden_dim * 2, 32),
            nn.Tanh(),
            nn.Linear(32, 1),
            nn.Softmax(dim=1),
        )

        # ---------------------------------------------------------------------
        # 5. Output Projection Head
        # Predicts target scalar (e.g., SPI-3 or rainfall anomaly) at t + h
        # ---------------------------------------------------------------------
        self.fc_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim * 2, 32),
            nn.ReLU(),
            nn.Dropout(dropout_p),
            nn.Linear(32, 1),
        )

    def forward(
        self,
        x_grid: torch.Tensor,
        x_local: torch.Tensor,
        return_attention: bool = False,
    ) -> torch.Tensor | Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward Pass:
        -------------
        Parameters:
            x_grid:  (B, seq_len, channels, H, W) -> Historical ocean/reanalysis grids [t-L+1, t]
            x_local: (B, seq_len, local_feat_dim) -> Historical local features [t-L+1, t]
            return_attention: If True, also returns attention weights (B, seq_len, 1)

        Returns:
            y_hat: (B, 1) -> forecast target at t + forecast_horizon
            attn_weights (optional): (B, seq_len, 1)
        """
        B, S, C, H, W = x_grid.shape

        # Fold historical sequence into batch dimension for efficient parallel 2D convolution
        x_grid_flat = x_grid.view(B * S, C, H, W)
        spatial_feats = self.spatial_cnn(x_grid_flat)          # (B*S, spatial_out_dim)
        spatial_feats = spatial_feats.view(B, S, -1)           # (B, S, spatial_out_dim)

        # Fuse spatial representation with local features at each timestep
        fused = torch.cat([spatial_feats, x_local], dim=-1)     # (B, S, spatial_out_dim + local_dim)
        fused = self.step_dense(fused)                         # (B, S, 64)

        # Temporal sequence modeling strictly over historical context <= t
        lstm_out, _ = self.bilstm(fused)                       # (B, S, hidden_dim * 2)

        # Temporal attention pooling
        attn_weights = self.attention(lstm_out)                # (B, S, 1)
        context_vector = torch.sum(attn_weights * lstm_out, dim=1)  # (B, hidden_dim * 2)

        # Predict target at t + horizon
        out = self.fc_head(context_vector)                     # (B, 1)

        if return_attention:
            return out, attn_weights
        return out


class SeasonallyWeightedMSELoss(nn.Module):
    """
    Seasonally Weighted MSE Loss to prevent deep models from gaming global MSE
    by predicting near-zero anomalies during climatologically dry Bega (ONDJ) months.

    Weights:
      - Kiremt Monsoon Core (JAS: months 7, 8, 9): weight = 2.0
      - Belg Rains (MAM: months 3, 4, 5):         weight = 1.5
      - June Transition (month 6):                 weight = 1.5
      - Dry Bega (ONDJ: months 10, 11, 12, 1):    weight = 0.5
      - February Transition (month 2):             weight = 0.5
    """

    def __init__(self, season_weights: Optional[Dict[int, float]] = None):
        super().__init__()
        self.weights = season_weights or {
            7: 2.0, 8: 2.0, 9: 2.0,   # Kiremt (JAS)
            3: 1.5, 4: 1.5, 5: 1.5,   # Belg (MAM)
            6: 1.5,                   # June onset
            10: 0.5, 11: 0.5, 12: 0.5, 1: 0.5,  # Bega dry season
            2: 0.5                    # February
        }

    def forward(
        self,
        y_pred: torch.Tensor,
        y_true: torch.Tensor,
        target_months: torch.Tensor,  # 1D tensor of integers (1 to 12)
    ) -> torch.Tensor:
        """
        Computes sample-weighted squared error based on target calendar month.
        """
        weights = torch.tensor(
            [self.weights.get(int(m.item()), 1.0) for m in target_months],
            device=y_pred.device,
            dtype=y_pred.dtype,
        ).unsqueeze(-1)

        squared_diff = (y_pred - y_true) ** 2
        weighted_loss = torch.mean(weights * squared_diff)
        return weighted_loss


def compute_gradient_saliency(
    model: SpatioTemporal_CNN_BiLSTM,
    x_grid: torch.Tensor,
    x_local: torch.Tensor,
) -> torch.Tensor:
    """
    Computes Gradient Saliency Attribution for the spatial input grid:
        Attribution(c, h, w) = | ∂y_hat / ∂x_grid(t, c, h, w) |

    Parameters:
        model: Trained SpatioTemporal_CNN_BiLSTM in eval mode
        x_grid: Input tensor (1, seq_len, channels, H, W) requiring gradients
        x_local: Input tensor (1, seq_len, local_dim)

    Returns:
        saliency_map: (channels, H, W) mean absolute gradient across historical sequence
    """
    model.eval()
    x_grid_input = x_grid.clone().detach().requires_grad_(True)
    x_local_input = x_local.clone().detach()

    # cuDNN RNN backward requires training mode or cuDNN disabled
    prev_cudnn_state = torch.backends.cudnn.enabled
    try:
        if torch.cuda.is_available():
            torch.backends.cudnn.enabled = False
        output = model(x_grid_input, x_local_input)
        output.backward()
    finally:
        torch.backends.cudnn.enabled = prev_cudnn_state

    # Absolute gradient
    grads = torch.abs(x_grid_input.grad)  # (1, seq_len, channels, H, W)
    # Average across historical sequence dimension
    saliency_map = torch.mean(grads.squeeze(0), dim=0)  # (channels, H, W)
    return saliency_map
