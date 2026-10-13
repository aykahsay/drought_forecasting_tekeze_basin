# Spatiotemporal Hybrid ResNet-CNN + XGBoost Drought Forecasting Architecture

[![Hugging Face Models & Data](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Models%20%26%20Data-blue)](https://huggingface.co/aykgeh/drought_forecasting_tekeze_basin)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Target Basin](https://img.shields.io/badge/Basin-Tekeze%20River%20Canyon-orange.svg)]()
[![Region](https://img.shields.io/badge/Location-Central%20Tigray%2C%20Ethiopia-red.svg)]()

> **Study Area:** Yechila (Tanqua) Abergelle Woreda & Tekeze River Basin, Central Tigray Zone, Northern Ethiopia  
> **Temporal Coverage:** 1990 – 2026 (Operational multi-decadal record)  
> **Target Index:** Self-Calibrating Palmer Drought Severity Index ($\text{sc\_PDSI}$) & Root-Zone Soil Moisture Deficit ($0-28\text{ cm}$)  
> **Model & Data Weights on Hugging Face:** [aykgeh/drought_forecasting_tekeze_basin](https://huggingface.co/aykgeh/drought_forecasting_tekeze_basin)

---

## 1. Architectural Motivation & Theoretical Framework

Predicting agricultural drought in the deeply incised, semi-arid topography of Central Tigray requires resolving two distinct physical regimes operating across disparate scales:
1. **Local Mesoscale Topography:** 4D spatio-temporal gridded reanalysis tensors ($B \times 12 \times 4 \times 14 \times 16$) capturing root-zone soil water (`swvl1`, `swvl2`), 2m temperature (`t2m`), and precipitation (`tp`) across the Tekeze River canyon ($0.1^\circ$ resolution).
2. **Planetary Ocean Teleconnections:** Inter-basin Pacific (Niño 3.4), Indian (IOD DMI), and Atlantic (TSA, TNA) sea-surface temperature anomalies and multi-resolution discrete wavelet sub-signals operating on 1-to-6 month lag horizons.

```
┌────────────────────────────────────────────────────────────────────────┐
│  4D Gridded NetCDF Cube (swvl1, swvl2, t2m, tp) [12 × 4 × 14 × 16]     │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  2D ResNet-CNN Spatial Backbone with Spatial Attention                 │
│  • Compresses 4D gridded tensors into 3 primary spatial modes          │
│  • Captures Tekeze canyon micro-climate & elevation lapse rates        │
│  • Contributes 26.6% to predictive weight                              │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  XGBoost Multi-Scale Fusion Regressor                                  │
│  • Ingests CNN spatial modes + Oceanic Teleconnection Lags (73.4%)     │
│  • Pacific Niño 3.4 Wavelets (3-5yr trend, 2yr cycle, τ=3-5m)          │
│  • Atlantic Gradient (TNA - TSA, τ=1-2m) & South Atlantic TSA (τ=2-3m) │
│  • Indian Ocean Dipole (IOD, τ=2-3m) & Soil Memory (sc_PDSI t-1, 1yr)  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Operational Early Warning (RMSE = 0.229 | R² = 97.9% | r = 0.995)     │
│  • 2026 Severe Drought Verification: -2.36 Forecast (Real: -2.76)      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Quantitative Benchmark Across 4D-Compatible CNN Architectures

All benchmarked architectures ingest the 4-channel NetCDF reanalysis cube through the ResNet-CNN spatial backbone:

| Model Architecture | 4D Spatial Handling | Temporal & Climate Engine | Root Mean Squared Error (RMSE) | Variance Explained ($R^2$) | Pearson Correlation ($r$) | Error Reduction vs Spatial CNN |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Spatial ResNet-CNN** | 2D Conv + Spatial Attention | Dense Output Head | $0.669$ | $81.9\%$ | $0.935$ | Baseline |
| **ResNet-CNN + BiLSTM** | 2D Conv + Spatial Attention | Bidirectional LSTM Sequence | $0.507$ | $89.6\%$ | $0.962$ | $-24.2\%$ |
| **CNN + BiLSTM + Fourier** | 2D Conv + Spatial Attention | BiLSTM + Fourier FFT Frequencies | $0.385$ | $94.0\%$ | $0.975$ | $-42.5\%$ |
| **Proposed Hybrid ResNet-CNN + XGBoost** | **2D Conv + Spatial Attention** | **XGBoost on Multi-Ocean Lags & Modes** | **0.229** | **97.9%** | **0.995** | **-65.8%** |

---

## 3. Key Findings

1. **Why Pure XGBoost Fails on 4-Channel Data:**
   * Decision trees have zero spatial inductive bias; flattening a $14 \times 16 \times 4$ grid into 896 scalar columns treats neighboring pixels identically to opposite corners of the map and causes severe $p \gg n$ overfitting.
   * Coupling the **2D ResNet-CNN** as a spatial dimensionality reducer (compressing 896 raw pixel channels into 3 orthogonal spatial modes) solves this fundamental bottleneck.
2. **Unified Feature Importance Hierarchy:**
   * **4D CNN Spatial Convolutions account for $26.6\%$ total weight**, with Spatial Mode 3 (Tekeze valley moisture anomaly) ranking #1 overall at **$24.03\%$**.
   * **Planetary Ocean Lags account for $73.4\%$ total weight**, dominated by the South Atlantic TSA ($15.56\%$), Atlantic Inter-Hemispheric Gradient ($15.39\%$), Pacific Niño Wavelet Trend ($12.40\%$), and Niño Wavelet Cycle ($8.81\%$).
3. **2026 Severe Drought Verification:**
   * Ground Truth $\text{sc\_PDSI} = \mathbf{-2.76}$ (Severe Drought).
   * Proposed Hybrid CNN + XGBoost Forecast: $\mathbf{-2.36}$ (Error: $0.40$).
   * ResNet-CNN + BiLSTM Forecast: $\mathbf{-2.25}$ (Error: $0.51$).

---

## 4. Repository Structure

```
drought_forecasting_tekeze_basin/
├── README.md                                         # Master project documentation
├── requirements.txt                                  # Environment dependencies
├── .gitignore                                        # Clean git exclusion rules
├── app_streamlit_abergele.py                         # Operational early warning dashboard
├── drought_forecasting/
│   └── agriminds/
│       ├── ml/
│       │   ├── train_high_accuracy_cnn_lstm.py       # HighCapacityResNetCNNLSTM implementation
│       │   ├── cnn_lstm_fourier.py                   # Spectral BiLSTM-Fourier module
│       │   └── forecast_engine.py                    # Multi-horizon operational engine
│       ├── models/
│       │   ├── train_hybrid_cnn_xgboost_model.py     # Master Figure 8 Hybrid pipeline
│       │   ├── run_full_validation_up_to_2026.py     # Timeline validation suite (1990-2026)
│       │   └── wavelet_drought_prediction_framework.py
│       └── ingestion/
│           ├── storage_aware_downloader.py           # ERA5-Land NetCDF downloader
│           └── noaa_cpc_ingestion.py                 # NOAA CPC ocean index client
├── data/
│   └── processed/
│       ├── hybrid_cnn_xgboost_architecture_and_validation.png
│       ├── model_training_with_lag_features.png
│       ├── lag_time_feature_importance_and_model_training.png
│       ├── multi_ocean_wavelet_coherence_comparison_1990_2026.png
│       └── real_drought_prediction_validation_1990_2026.png
└── docs/
    ├── academic_research_paper_teleconnection_drought.md
    └── figure_8_hybrid_cnn_xgboost_architecture_and_validation.md
```

---

## 5. Quickstart & Installation

```bash
# Clone the repository
git clone https://github.com/aykahsay/drought_forecasting_tekeze_basin.git
cd drought_forecasting_tekeze_basin

# Install dependencies
pip install -r requirements.txt

# Download model checkpoints and data from Hugging Face
huggingface-cli download aykgeh/drought_forecasting_tekeze_basin --local-dir ./data_hf

# Launch operational early warning dashboard
streamlit run app_streamlit_abergele.py
```

---

## 6. Citation

```bibtex
@article{kahsay2026drought,
  title={Multi-Ocean Teleconnection Dynamics and Spatiotemporal Hybrid ResNet-CNN + XGBoost Architecture for Long-Lead Drought Early Warning in the Tekeze River Basin},
  author={Kahsay, Aykahsay and AgriMinds Research Team},
  journal={Journal of Hydrology / Remote Sensing of Environment},
  year={2026}
}
```
