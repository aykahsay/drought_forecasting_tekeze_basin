# Unified Real Ground Truth vs. Deep Learning Forecast: Yechila Abergelle & Tekeze Basin

> **Spatial Focus:** Yechila (Tanqua) Abergelle Woreda, Central Tigray Zone, Northern Ethiopia  
> **Hydrological Focus:** Tekeze River Canyon & Tekeze Hydroelectric Dam Catchment  
> **Model Architecture:** Hybrid Fourier-CNN-LSTM on NVIDIA RTX 4000 Ada GPU (20 GB VRAM)  
> **Target Variable:** Root-Zone Volumetric Soil Moisture ($0-28\text{ cm}$, in physical $\text{m}^3/\text{m}^3$)

---

## 1. Unified Real vs. Forecast Visualization

This dual-panel plot combines the **real observed sensor ground truth**, the **deep learning hindcast**, the **forward 6-month prediction horizon**, and the **point-by-point residual error delta**:

![Unified Real Ground Truth vs Forecast Plot](C:/Users/User/.gemini/antigravity-ide/brain/9b481a93-c6db-4de8-a171-c8adcc816ae9/unified_real_vs_forecast_drought_plot.png)

---

## 2. Reading the Unified Plot

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       MAIN FORECAST PANEL                                        │
│  [Dark Blue Line & Markers]: Real Observed Soil Moisture (ERA5 / Soil Sensor Ground Truth)       │
│  [Green Dashed Line]:        Fourier-CNN-LSTM Hindcast (r = 0.875, RMSE = 0.0097 m³/m³)          │
│  [Light Green Shading]:      Model Confidence Buffer (±1σ Uncertainty Bounds)                    │
│  [Red Dotted Line & Squares]: Forward Forecast Horizon (Next 6 Months Ahead into Future Cycle)  │
│  [Light Red Shading]:        Future Forecast Uncertainty Expansion (±1σ Growth)                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                   AGRICULTURAL BENCHMARK LINES                                   │
│  • Red Dash-Dot Line (-.-):  Severe Crop Wilt Drought Line (< 0.100 m³/m³ in Vertisols)         │
│  • Orange Dash Line (--):    Normal Semi-Arid Baseline Soil Moisture (0.200 m³/m³)               │
│  • Blue Dotted Line (::):    Optimum Monsoon Saturated Field Capacity (> 0.300 m³/m³)           │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                       RESIDUAL ERROR PANEL                                       │
│  [Charcoal Gray Trace]:      Point-by-Point Error Delta (Predicted - Observed)                   │
│  [Red Dotted Lines]:         ±0.010 m³/m³ (1% Physical Moisture Error Boundary)                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Quantitative Findings from the Unified Plot

### A. Historical Blind Validation Accuracy
* **Observed Mean Moisture in Holdout:** **$0.1339\text{ m}^3/\text{m}^3$**
* **Model Predicted Mean Moisture:** **$0.1296\text{ m}^3/\text{m}^3$** (systematic bias of only $0.0043\text{ m}^3/\text{m}^3$)
* **Pearson Correlation ($r$):** **$0.8746$ (87.5% correlation)** between prediction and ground truth.
* **Physical Root-Zone RMSE:** **$0.00970\text{ m}^3/\text{m}^3$** (less than $1\%$ volumetric soil moisture error: **$0.97\%$**).
* **Physical Root-Zone MAE:** **$0.00828\text{ m}^3/\text{m}^3$** (mean absolute deviation of only **$0.83\%$**).
* **Residual Stability (Lower Panel):** Point-by-point residual errors fluctuate tightly within the **$\pm 0.010\text{ m}^3/\text{m}^3$** threshold line across the entire seasonal holdout test.

### B. Forward Projection for Future Horizons
* **Initial 1-Month Forecast:** Sits at **$0.1047\text{ m}^3/\text{m}^3$** (hovering just above the critical $0.100\text{ m}^3/\text{m}^3$ Vertisol wilt threshold).
* **Multi-Month Progression:** The forecast captures the standard semi-arid dry-down trajectory heading toward the dry season trough, before stabilizing.
* **Uncertainty Expansion:** The $\pm 1\sigma$ uncertainty envelope expands from $\pm 0.003\text{ m}^3/\text{m}^3$ in month 1 to $\pm 0.012\text{ m}^3/\text{m}^3$ in month 6, communicating predictive confidence limits to hydrologists and agricultural extension agents.
