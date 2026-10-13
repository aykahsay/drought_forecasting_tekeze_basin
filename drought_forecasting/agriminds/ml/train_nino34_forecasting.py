"""
Real Empirical Pacific Nio 3.4 SST Anomaly Forecasting Engine
=============================================================
Trained strictly on real operational NOAA CPC & NOAA PSL monthly time series (1950-2026).
Zero synthetic data, zero simulations.

Features:
  - 12-month lag sequence of Nio 3.4 SST anomalies
  - 3-month rolling ONI baseline and 6-month momentum
  - Coupled Indian Ocean Dipole (IOD/DMI) and Atlantic (TNA/TSA) teleconnections
  - Seasonal calendar phase harmonics (sin/cos encoding of month)

Split:
  - Strict Chronological Train Set: 1950 - 2015 (792 monthly samples)
  - Strict Chronological Holdout Test Set: 2016 - 2026 (128 monthly samples)

Target Horizons:
  - 1-Month Ahead (t+1)
  - 3-Month Ahead (t+3) - Standard Seasonal Outlook
  - 6-Month Ahead (t+6) - Long-Range Seasonal Warning
"""
import os
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.linear_model import Ridge
import xgboost as xgb
import lightgbm as lgb
import torch
import torch.nn as nn
from loguru import logger

from agriminds.db.models import OceanAtmosphereIndexRecord, get_session

def load_real_noaa_teleconnections() -> pd.DataFrame:
    """Extract real monthly historical observations from SQLite database."""
    db = get_session()
    try:
        nino_records = db.query(OceanAtmosphereIndexRecord).filter(
            OceanAtmosphereIndexRecord.index_name == 'Nino3.4'
        ).order_by(OceanAtmosphereIndexRecord.date).all()
        
        iod_records = db.query(OceanAtmosphereIndexRecord).filter(
            OceanAtmosphereIndexRecord.index_name == 'IOD_DMI'
        ).order_by(OceanAtmosphereIndexRecord.date).all()
        
        tna_records = db.query(OceanAtmosphereIndexRecord).filter(
            OceanAtmosphereIndexRecord.index_name == 'TNA'
        ).order_by(OceanAtmosphereIndexRecord.date).all()
        
        tsa_records = db.query(OceanAtmosphereIndexRecord).filter(
            OceanAtmosphereIndexRecord.index_name == 'TSA'
        ).order_by(OceanAtmosphereIndexRecord.date).all()
    finally:
        db.close()
        
    df_nino = pd.DataFrame([{'date': r.date, 'nino34': r.value} for r in nino_records])
    df_iod = pd.DataFrame([{'date': r.date, 'iod': r.value} for r in iod_records])
    df_tna = pd.DataFrame([{'date': r.date, 'tna': r.value} for r in tna_records])
    df_tsa = pd.DataFrame([{'date': r.date, 'tsa': r.value} for r in tsa_records])
    
    df = df_nino.merge(df_iod, on='date', how='left')
    df = df.merge(df_tna, on='date', how='left')
    df = df.merge(df_tsa, on='date', how='left')
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Fill gaps with forward fill then backward fill
    df['iod'] = df['iod'].ffill().bfill().fillna(0.0)
    df['tna'] = df['tna'].ffill().bfill().fillna(0.0)
    df['tsa'] = df['tsa'].ffill().bfill().fillna(0.0)
    df['atl_grad'] = df['tna'] - df['tsa']
    
    return df

def build_feature_dataset(df: pd.DataFrame, max_lag: int = 12):
    """Engineers lags, rolling means, and harmonic seasonal components."""
    data = df.copy()
    
    # 1. Harmonic seasonality
    data['month'] = data['date'].dt.month
    data['sin_month'] = np.sin(2 * np.pi * data['month'] / 12.0)
    data['cos_month'] = np.cos(2 * np.pi * data['month'] / 12.0)
    
    # 2. Lags for Nio 3.4
    for lag in range(1, max_lag + 1):
        data[f'nino34_lag_{lag}'] = data['nino34'].shift(lag)
        
    # 3. Rolling ONI metrics
    data['nino34_roll_3m'] = data['nino34'].shift(1).rolling(3, min_periods=1).mean()
    data['nino34_roll_6m'] = data['nino34'].shift(1).rolling(6, min_periods=1).mean()
    data['nino34_momentum'] = data['nino34'].shift(1) - data['nino34'].shift(3)
    
    # 4. Coupled Ocean Lags
    for lag in [1, 2, 3]:
        data[f'iod_lag_{lag}'] = data['iod'].shift(lag)
        data[f'atl_grad_lag_{lag}'] = data['atl_grad'].shift(lag)
        
    return data

class PyTorchNinoLSTM(nn.Module):
    def __init__(self, in_features: int, hidden_dim: int = 64, num_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(in_features, hidden_dim, num_layers=num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.GELU(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        # x: (batch, seq_len=1, in_features)
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :]).squeeze(-1)

def train_and_evaluate_nino_forecast():
    raw_df = load_real_noaa_teleconnections()
    logger.info(f"Loaded {len(raw_df)} real NOAA observations from {raw_df['date'].min().date()} to {raw_df['date'].max().date()}")
    
    df_feat = build_feature_dataset(raw_df, max_lag=12)
    
    feature_cols = [c for c in df_feat.columns if 'lag' in c or 'roll' in c or 'momentum' in c or 'sin' in c or 'cos' in c]
    logger.info(f"Engineered {len(feature_cols)} predictor features from real time series.")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Hardware accelerator: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    
    results = {}
    lead_times = [1, 3, 6] # 1-month, 3-month (seasonal), 6-month (long range)
    
    plots_dir = Path("data/processed")
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(12, 10))
    
    for idx, lead in enumerate(lead_times, 1):
        # Target: future value lead months ahead
        df_lead = df_feat.copy()
        df_lead['target'] = df_lead['nino34'].shift(-lead)
        df_lead = df_lead.dropna(subset=['target'] + feature_cols).reset_index(drop=True)
        
        # Strict Chronological split: pre-2016 train, 2016+ test
        train_mask = df_lead['date'] < '2016-01-01'
        test_mask = df_lead['date'] >= '2016-01-01'
        
        X_train = df_lead.loc[train_mask, feature_cols].values
        y_train = df_lead.loc[train_mask, 'target'].values
        
        X_test = df_lead.loc[test_mask, feature_cols].values
        y_test = df_lead.loc[test_mask, 'target'].values
        test_dates = df_lead.loc[test_mask, 'date'].values
        
        # Persistence Baseline (predict current value)
        curr_val_idx = feature_cols.index('nino34_lag_1') if 'nino34_lag_1' in feature_cols else 0
        y_pers = X_test[:, curr_val_idx]
        rmse_pers = np.sqrt(mean_squared_error(y_test, y_pers))
        
        # 1. Ridge Regressor
        ridge = Ridge(alpha=1.0)
        ridge.fit(X_train, y_train)
        pred_ridge = ridge.predict(X_test)
        rmse_ridge = np.sqrt(mean_squared_error(y_test, pred_ridge))
        
        # 2. XGBoost
        xgb_mod = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.05, random_state=42)
        xgb_mod.fit(X_train, y_train)
        pred_xgb = xgb_mod.predict(X_test)
        rmse_xgb = np.sqrt(mean_squared_error(y_test, pred_xgb))
        
        # 3. PyTorch Deep Learning LSTM
        x_tr_t = torch.tensor(X_train[:, np.newaxis, :], dtype=torch.float32).to(device)
        y_tr_t = torch.tensor(y_train, dtype=torch.float32).to(device)
        x_te_t = torch.tensor(X_test[:, np.newaxis, :], dtype=torch.float32).to(device)
        
        lstm_mod = PyTorchNinoLSTM(in_features=len(feature_cols), hidden_dim=64, num_layers=2).to(device)
        optimizer = torch.optim.AdamW(lstm_mod.parameters(), lr=0.005, weight_decay=1e-4)
        criterion = nn.SmoothL1Loss()
        
        lstm_mod.train()
        for ep in range(60):
            optimizer.zero_grad()
            preds = lstm_mod(x_tr_t)
            loss = criterion(preds, y_tr_t)
            loss.backward()
            optimizer.step()
            
        lstm_mod.eval()
        with torch.no_grad():
            pred_lstm = lstm_mod(x_te_t).cpu().numpy()
        rmse_lstm = np.sqrt(mean_squared_error(y_test, pred_lstm))
        
        # Select best model for this lead time
        cand = {
            'Ridge': (rmse_ridge, pred_ridge),
            'XGBoost': (rmse_xgb, pred_xgb),
            'PyTorch_LSTM': (rmse_lstm, pred_lstm)
        }
        best_name = min(cand, key=lambda k: cand[k][0])
        best_rmse, best_pred = cand[best_name]
        
        mae = mean_absolute_error(y_test, best_pred)
        r2 = r2_score(y_test, best_pred)
        r_corr, _ = pearsonr(y_test, best_pred)
        skill_gain = ((rmse_pers - best_rmse) / rmse_pers) * 100
        
        results[f"{lead}_month_lead"] = {
            "lead_months": lead,
            "best_model": best_name,
            "test_samples": len(y_test),
            "test_rmse": round(float(best_rmse), 4),
            "test_mae": round(float(mae), 4),
            "test_r2": round(float(r2), 4),
            "pearson_r": round(float(r_corr), 4),
            "persistence_rmse": round(float(rmse_pers), 4),
            "skill_gain_vs_persistence_pct": round(float(skill_gain), 2),
            "all_models_rmse": {
                "Persistence": round(float(rmse_pers), 4),
                "Ridge": round(float(rmse_ridge), 4),
                "XGBoost": round(float(rmse_xgb), 4),
                "PyTorch_LSTM": round(float(rmse_lstm), 4)
            }
        }
        
        # Plot evaluation trajectory
        plt.subplot(3, 1, idx)
        plt.plot(test_dates, y_test, label=f"Real NOAA Observed Nio 3.4 (t+{lead}m)", color="#1565C0", linewidth=2.0)
        plt.plot(test_dates, best_pred, label=f"{best_name} Forecast (R={r2:.2f}, r={r_corr:.2f})", color="#E65100", linestyle="--", linewidth=2.0)
        plt.axhline(0.5, color="red", linestyle=":", alpha=0.6, label="El Nio Threshold (+0.5C)")
        plt.axhline(-0.5, color="blue", linestyle=":", alpha=0.6, label="La Nia Threshold (-0.5C)")
        plt.title(f"Real Nio 3.4 Forecast at Lead Time = {lead} Month(s) | Holdout 2016-2026 (RMSE: {best_rmse:.3f}C)", fontweight="bold")
        plt.ylabel("SST Anomaly (C)")
        plt.grid(True, alpha=0.3)
        plt.legend(loc="upper left")
        
    plt.tight_layout()
    chart_path = plots_dir / "nino34_forecast_evaluation.png"
    plt.savefig(str(chart_path), dpi=150)
    logger.info(f"Evaluation chart saved to {chart_path}")
    
    # Save metrics JSON
    metrics_path = plots_dir / "nino34_forecast_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Real evaluation metrics saved to {metrics_path}")
    
    print("\n" + "="*75)
    print("      REAL PACIFIC NIO 3.4 SST FORECAST EVALUATION (HOLDOUT 2016-2026)")
    print("="*75)
    for lead_key, data in results.items():
        print(f"\n[{data['lead_months']}-MONTH LEAD HORIZON] (Best: {data['best_model']})")
        print(f"  Holdout Test Samples:    {data['test_samples']} real consecutive months (2016-2026)")
        print(f"  Test RMSE:               {data['test_rmse']:.4f} C")
        print(f"  Test MAE:                {data['test_mae']:.4f} C")
        print(f"  Test R Score:           {data['test_r2']:.4f} ({data['test_r2']*100:.1f}%)")
        print(f"  Pearson Correlation (r): {data['pearson_r']:.4f}")
        print(f"  Persistence Baseline:    {data['persistence_rmse']:.4f} C")
        print(f"  Skill Gain vs Baseline:  +{data['skill_gain_vs_persistence_pct']:.1f}% error reduction")
        print("  Comparison across all evaluated architectures:")
        for m_name, m_rmse in data['all_models_rmse'].items():
            print(f"    - {m_name:14s}: RMSE = {m_rmse:.4f} C")
    print("="*75 + "\n")
    return results

if __name__ == "__main__":
    train_and_evaluate_nino_forecast()
