# AI-DREWS Gate 5: Predictive Forecasting Architecture & Leakage Prevention Audit
## Anti-Leakage Protocol, Benchmark Baselines, Chronological Partitions, and Probabilistic Evaluation

**Document ID:** `AI-DREWS-GATE5-SPEC-2026-10`  
**Reference Standards:** WMO Lead Centre for Long-Range Forecast Multi-Model Ensemble; Brier (1950); Gneiting & Raftery (2007)  
**Status:** **SPECIFIED & DE-SCOPED (Execution Strictly Paused Pending Gate 4 Certification)**  
**Target Basin:** Tekezé River Basin Catchment ($67,135.4\text{ km}^2$, Northern Ethiopia)

---

### 1. Explicit Prediction Targets & Forecast Horizons

The forecasting system targets seasonal early warning for agricultural planning and food security preparation:

1. **Primary Operational Target:**
   * **September-Ending SPEI-3 ($\text{SPEI-3}_{\text{Sept}}$):** Captures cumulative moisture balance across the core Kiremt monsoon season (July, August, September), governing 80%+ of regional cereal yields (teff, sorghum, barley, wheat).
2. **Secondary Target:**
   * **May-Ending SPEI-3 ($\text{SPEI-3}_{\text{May}}$):** Captures cumulative moisture balance across the Belg short-rain season (March, April, May), critical for pastoral pasture and long-cycle crops.
3. **Operational Lead Times & Issue Schedules:**
   * **Target Accumulation Period:** September-ending SPEI-3 incorporates July, August, and September conditions.
   * **Forecast Issued June 1 (Lead 3 to Target End):** On June 1, July, August, and September rainfall and temperature are **entirely unobserved**. The model must predict this future seasonal water balance using strictly pre-June observations (predictors available on or before May 31).
   * **Forecast Issued April 1 (Lead 5 to Target End):** Seasonal outlook for agricultural planning.
   * **Forecast Issued January 1 (Lead 8 to Target End):** Long-range outlook.
4. **Categorical Drought Early Warning & Predictive Intervals:**
   * **Uncertainty Quantification:** Evaluated via **80% and 95% predictive intervals** (not confidence intervals), with nominal empirical coverage evaluated on frozen test holdout data.
   * **Moderate Drought:** $\text{SPEI-3} \le -1.00$ ($P \le 0.1587$)
   * **Severe Drought:** $\text{SPEI-3} \le -1.50$ ($P \le 0.0668$)
   * **Extreme Drought:** $\text{SPEI-3} \le -2.00$ ($P \le 0.0228$)

---

### 2. Chronological Data Partitioning & Leakage Prevention

To prevent artificial skill inflation and historical data contamination, all model training, feature extraction, and evaluation follow strict chronological boundaries:

```
┌──────────────────────────────────────┬────────────────────────┬─────────────────────────┐
│ Training Reference Set               │ Validation / Tuning    │ Out-of-Sample Holdout   │
│ 1981–2005 (25 years, 300 months)     │ 2006–2014 (9 years)    │ 2015–2024 (10 years)    │
│ Includes 1984/85 & 2002/03 droughts  │ Includes 2009 Belg     │ Includes 2015/16 El Niño│
└──────────────────────────────────────┴────────────────────────┴─────────────────────────┘
```

#### 2.1 Anti-Leakage Rules (Strictly Enforced)
1. **Zero Future Information in Input Features:** For a forecast issued at month $T$, input feature tensors $\mathbf{X}_T$ must strictly contain data observed at or prior to month $T$.
2. **Multi-Month Accumulation Alignment:** If predicting $\text{SPEI-3}$ ending in month $T+L$, rolling multi-month predictors must end at month $T$. No feature may overlap into $[T+1, T+L]$.
3. **Operational Teleconnection Lagging:** Oceanic-atmospheric teleconnection indices (Niño 3.4, IOD Dipole Mode Index, Tropical South Atlantic Index, North Atlantic Oscillation) must reflect real-world publication latency:
   $$\text{Lag}(\text{SST Index}) \ge 1\text{ month}$$
   E.g., an April 1 forecast cannot use March SST anomalies if they are published mid-April.
4. **Scaler and Normalizer Fit Boundaries:** MinMax scalers, z-score normalizers, and PCA projections must be fit exclusively on the Training Set (1981–2005) and applied frozen to Validation and Test sets.
5. **Zero Target-Calibration Leakage:** The forecast-evaluation target ($\text{SPEI-3}_{\text{eval}}$) must be standardized using GLO parameters estimated exclusively from data available prior to the evaluation fold (e.g. 1981–2005 for training and validation, and pre-test 1981–2014 for testing). Test-period observations (2015–2024) must **never** enter target distribution parameter fitting.

---

### 3. Baseline Benchmarks & Evaluation Protocol

Deep learning and spatial neural networks must be evaluated against standard reference baselines:

1. **Predefined Event Threshold:**
   * Declared in advance: $\text{SPEI-3}_{\text{eval}} \le -1.00$ defines moderate-or-worse seasonal drought.
2. **Dynamic Climatology Baseline:**
   * Predicts the historical empirical distribution of the target calendar month over the training period (1981–2005).
   * Serves as the zero-skill anchor for Brier Skill Score ($\text{BSS} = 1 - \frac{\text{BS}_{\text{model}}}{\text{BS}_{\text{clim}}}$).
3. **Persistence Baseline:**
   * $\widehat{\text{SPEI-3}}_{T+L} = \text{SPEI-3}_T$.
4. **Autoregressive / Statistical Baselines:**
   * Standard $\text{ARIMA}(p, d, q)$ and Seasonal ETS models.
5. **Sample Size Constraints & Uncertainty Reporting:**
   * The frozen test holdout (2015–2024) contains exactly **10 annual September forecasts**.
   * Ten events do not support precise unconstrained estimation of rare extremes. All evaluation metrics (Brier Score, BSS, CRPS, RMSE) must report bootstrap confidence intervals accounting for temporal dependence.
   * Spatial deep learning (CNN-LSTM / FNO) must demonstrate a statistically defensible improvement over persistence, climatology, and regularized linear regression rather than merely memorizing training variance.

---

### 4. Candidate Model Architectures

When Gate 5 is initiated, the following models will be evaluated under identical chronological cross-validation:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Classical Statistical: ARIMA / Seasonal ETS / Ridge Regression      │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Temporal Deep Learning: Recurrent LSTM / GRU                        │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Spatiotemporal: Convolutional LSTM (ConvLSTM / CNN-LSTM)            │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Proposed: Fourier Neural Operator (FNO) / Spectral-Enhanced Network │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 5. Multi-Criteria Evaluation Metrics

#### 5.1 Continuous Forecast Evaluation
* **Mean Absolute Error (MAE):** $\text{MAE} = \frac{1}{N} \sum |y_i - \hat{y}_i|$
* **Root Mean Square Error (RMSE):** $\text{RMSE} = \sqrt{\frac{1}{N} \sum (y_i - \hat{y}_i)^2}$
* **Pearson Correlation Coefficient ($r$):** Linear phase alignment.
* **Spearman Rank Correlation ($\rho$):** Monotonic rank ordering.

#### 5.2 Probabilistic & Categorical Drought Evaluation
* **Brier Score (BS) & Brier Skill Score (BSS):**
  $$\text{BS} = \frac{1}{N} \sum_{i=1}^N (p_i - o_i)^2, \quad \text{BSS} = 1 - \frac{\text{BS}_{\text{model}}}{\text{BS}_{\text{climatology}}}$$
* **Continuous Ranked Probability Score (CRPS):** Evaluates entire predicted probability density function.
* **Categorical Contingency Metrics:**
  * Precision, Recall (Probability of Detection, POD), False Alarm Ratio (FAR), and Critical Success Index (CSI / Threat Score) for drought events ($\text{SPEI} \le -1.5$).

---

### 6. Gate 5 Verification Readiness

* **Status:** **PAUSED BY DESIGN**.
* **Integrity Gate:** No neural network training or hyperparameter search will be executed until Gates 1–4 are certified.
