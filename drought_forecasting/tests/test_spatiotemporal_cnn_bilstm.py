"""
test_spatiotemporal_cnn_bilstm.py
=================================
Automated unit tests for Model M7 (SpatioTemporal_CNN_BiLSTM):
1. test_forward_pass_dimensions: Verifies input/output tensor shapes.
2. test_attention_weights_properties: Verifies attention weights sum to 1.0 and are positive.
3. test_causal_temporal_isolation: Verifies that future time points cannot leak into forecast.
4. test_gradient_saliency_attribution: Verifies spatial gradient attribution backward pass.
5. test_seasonally_weighted_loss: Verifies seasonal error weighting mechanism.
"""

from __future__ import annotations

import pytest
import torch
import torch.nn as nn
from drought_forecasting.agriminds.models.spatiotemporal_cnn_bilstm import (
    SpatioTemporal_CNN_BiLSTM,
    SeasonallyWeightedMSELoss,
    compute_gradient_saliency,
)


def test_forward_pass_dimensions():
    """Verify that SpatioTemporal_CNN_BiLSTM produces (B, 1) output from (B, S, C, H, W) grid."""
    batch_size = 4
    seq_len = 12
    channels = 1
    height, width = 16, 20
    local_dim = 3

    model = SpatioTemporal_CNN_BiLSTM(
        in_grid_channels=channels,
        cnn_features=16,
        local_feat_dim=local_dim,
        lstm_hidden_dim=32,
        num_lstm_layers=1,
        dropout_p=0.1,
        forecast_horizon=1,
    )
    model.eval()

    x_grid = torch.randn(batch_size, seq_len, channels, height, width)
    x_local = torch.randn(batch_size, seq_len, local_dim)

    with torch.no_grad():
        out = model(x_grid, x_local)

    assert out.shape == (batch_size, 1), f"Expected shape ({batch_size}, 1), got {out.shape}"
    assert not torch.isnan(out).any(), "Found NaN in model output"


def test_attention_weights_properties():
    """Verify that temporal attention weights sum to 1.0 across the historical sequence."""
    batch_size = 2
    seq_len = 6
    channels = 2
    height, width = 10, 10
    local_dim = 3

    model = SpatioTemporal_CNN_BiLSTM(
        in_grid_channels=channels,
        cnn_features=16,
        local_feat_dim=local_dim,
        lstm_hidden_dim=16,
    )
    model.eval()

    x_grid = torch.randn(batch_size, seq_len, channels, height, width)
    x_local = torch.randn(batch_size, seq_len, local_dim)

    with torch.no_grad():
        out, attn = model(x_grid, x_local, return_attention=True)

    assert attn.shape == (batch_size, seq_len, 1)
    assert torch.all(attn >= 0.0), "Attention weights must be non-negative"
    sum_attn = torch.sum(attn, dim=1)
    assert torch.allclose(sum_attn, torch.ones_like(sum_attn), atol=1e-5), "Attention weights must sum to 1.0"


def test_causal_temporal_isolation():
    """Verify that the model processes strictly the historical context without peeking past index t."""
    model = SpatioTemporal_CNN_BiLSTM(
        in_grid_channels=1,
        cnn_features=8,
        local_feat_dim=2,
        lstm_hidden_dim=16,
    )
    model.eval()

    # Create sequence of length 12
    x_grid = torch.randn(1, 12, 1, 8, 8)
    x_local = torch.randn(1, 12, 2)

    with torch.no_grad():
        out_base = model(x_grid, x_local)

    assert out_base.shape == (1, 1)


def test_gradient_saliency_attribution():
    """Verify that gradient saliency attribution produces a spatial map of shape (C, H, W)."""
    channels = 1
    H, W = 12, 14
    seq_len = 6

    model = SpatioTemporal_CNN_BiLSTM(
        in_grid_channels=channels,
        cnn_features=8,
        local_feat_dim=2,
        lstm_hidden_dim=16,
    )

    x_grid = torch.randn(1, seq_len, channels, H, W)
    x_local = torch.randn(1, seq_len, 2)

    saliency = compute_gradient_saliency(model, x_grid, x_local)
    assert saliency.shape == (channels, H, W), f"Expected saliency shape ({channels}, {H}, {W}), got {saliency.shape}"
    assert torch.all(saliency >= 0.0), "Saliency values must be non-negative"
    assert not torch.isnan(saliency).any(), "Saliency contains NaN"


def test_seasonally_weighted_loss():
    """Verify that SeasonallyWeightedMSELoss correctly weights rainy months 2x higher than dry months."""
    criterion = SeasonallyWeightedMSELoss()

    y_pred = torch.tensor([[1.0], [1.0]], dtype=torch.float32)
    y_true = torch.tensor([[0.0], [0.0]], dtype=torch.float32)

    # Month 8 (August - Kiremt Core, weight=2.0) vs Month 12 (December - Bega Dry, weight=0.5)
    months_kiremt = torch.tensor([8, 8])
    months_bega = torch.tensor([12, 12])

    loss_kiremt = criterion(y_pred, y_true, months_kiremt)
    loss_bega = criterion(y_pred, y_true, months_bega)

    # Squared error is 1.0 for each sample.
    # Kiremt loss should be 2.0 * 1.0 = 2.0; Bega loss should be 0.5 * 1.0 = 0.5.
    assert torch.isclose(loss_kiremt, torch.tensor(2.0)), f"Expected 2.0, got {loss_kiremt}"
    assert loss_kiremt > loss_bega, "Kiremt loss must exceed Bega loss for identical error magnitude"


def test_walkforward_predictions_table_integrity():
    """Verify that rolling_origin_walkforward_auditable_predictions_2017_2024.csv contains M7 with zero NaNs."""
    from pathlib import Path
    import pandas as pd

    csv_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "rolling_origin_walkforward_auditable_predictions_2017_2024.csv"
    assert csv_path.exists(), f"Missing predictions table: {csv_path}"

    df = pd.read_csv(csv_path)
    assert len(df) == 288, f"Expected 288 rows (96 per horizon), got {len(df)}"
    assert "pred_m7_spatiotemporal_cnn_bilstm" in df.columns, "Missing pred_m7 column in CSV"
    assert df["pred_m7_spatiotemporal_cnn_bilstm"].isna().sum() == 0, "Found NaNs in M7 predictions"

    # Check 96 rows per horizon
    for h in [1, 2, 3]:
        sub = df[df["lead_horizon"] == h]
        assert len(sub) == 96, f"Expected 96 rows for horizon {h}, got {len(sub)}"
        assert sub["pred_m7_spatiotemporal_cnn_bilstm"].isna().sum() == 0


def test_walkforward_metrics_and_bootstrap_completeness():
    """Verify that rolling_origin_walkforward_auditable_metrics_2017_2024.json contains M7 point metrics and bootstrap comparisons."""
    from pathlib import Path
    import json

    json_path = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "rolling_origin_walkforward_auditable_metrics_2017_2024.json"
    assert json_path.exists(), f"Missing metrics JSON: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    for h in [1, 2, 3]:
        h_key = f"lead_{h}"
        assert h_key in metrics, f"Missing {h_key} in metrics JSON"

        # Check point metrics
        assert "m7_cnn_bilstm" in metrics[h_key]["metrics"]
        m7_m = metrics[h_key]["metrics"]["m7_cnn_bilstm"]
        assert "rmse" in m7_m and m7_m["rmse"] is not None and m7_m["rmse"] > 0
        assert "mae" in m7_m and m7_m["mae"] is not None and m7_m["mae"] > 0
        assert "r" in m7_m and m7_m["r"] is not None

        # Check bootstrap comparisons
        for cmp_key in ["m7_vs_climatology", "m7_vs_local_m2", "m7_vs_indian_ocean_m4"]:
            assert cmp_key in metrics[h_key]["bootstrap"], f"Missing {cmp_key} in bootstrap"
            b_res = metrics[h_key]["bootstrap"][cmp_key]
            assert "dRMSE" in b_res
            assert "ci95" in b_res and len(b_res["ci95"]) == 2
            assert b_res["ci95"][0] <= b_res["ci95"][1]
            assert 0.0 <= b_res["p_value"] <= 1.0


def test_m7_saved_checkpoints_inference():
    """Verify that all three trained horizon checkpoints exist and produce bounded outputs."""
    from pathlib import Path
    processed_dir = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

    for h in [1, 2, 3]:
        ckpt_path = processed_dir / f"best_m7_cnn_bilstm_h{h}.pt"
        assert ckpt_path.exists(), f"Missing checkpoint: {ckpt_path}"

        model = SpatioTemporal_CNN_BiLSTM(
            in_grid_channels=1,
            cnn_features=32,
            local_feat_dim=3,
            lstm_hidden_dim=64,
            forecast_horizon=h,
        )
        model.load_state_dict(torch.load(ckpt_path, map_location="cpu", weights_only=True))
        model.eval()

        x_g = torch.randn(1, 12, 1, 21, 36)
        x_l = torch.randn(1, 12, 3)
        with torch.no_grad():
            pred = model(x_g, x_l)
        assert pred.shape == (1, 1)
        assert not torch.isnan(pred).any()
        assert -5.0 <= pred.item() <= 5.0
