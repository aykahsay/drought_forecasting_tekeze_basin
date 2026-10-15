# AI-DREWS Gate 5: Predictive Forecasting Architecture & Leakage Prevention Audit
## Anti-Leakage Protocol, Forecast Issue Metadata Table, Benchmark Baselines, Chronological Partitions, and Probabilistic Evaluation

**Document ID:** `AI-DREWS-GATE5-SPEC-2026-10-REV7.2`  
**Reference Standards:** WMO Lead Centre for Long-Range Forecast Multi-Model Ensemble; Brier (1950); Gneiting & Raftery (2007)  
**Status:** **SPECIFIED & DE-SCOPED (Execution Strictly Paused Pending Gate 4 Certification)**  
**Target Basin:** Tekezé River Basin Catchment ($67,135.4\text{ km}^2$, Northern Ethiopia)

---

### 1. Explicit Prediction Targets & Operational Issue Protocol

The forecasting system targets seasonal early warning for agricultural planning and food security preparation:

1. **Primary Operational Target:**
   * **September-Ending SPEI-3 ($\text{SPEI-3}_{\text{Sept}}$):** Captures cumulative moisture balance across the core Kiremt monsoon season (July, August, September), governing 80%+ of regional cereal yields (teff, sorghum, barley, wheat).
2. **Secondary Target:**
   * **May-Ending SPEI-3 ($\text{SPEI-3}_{\text{May}}$):** Captures cumulative moisture balance across the Belg short-rain season (March, April, May), critical for pastoral pasture and long-cycle crops.
3. **Operational Lead Times & Issue Schedules:**
   * **Target Accumulation Period:** September-ending SPEI-3 incorporates July, August, and September conditions.
   * **Forecast Issued June 1 (Lead 3 to Target End):** On June 1, July, August, and September rainfall and temperature are **entirely unobserved**. The model must predict this future seasonal water balance using strictly pre-June observations (predictors available on or before May 31 23:59 UTC).
   * **Forecast Issued April 1 (Lead 5 to Target End):** Seasonal outlook for agricultural planning.
   * **Forecast Issued January 1 (Lead 8 to Target End):** Long-range outlook.
4. **Categorical Drought Early Warning & Predictive Intervals:**
   * **Uncertainty Quantification:** Evaluated via **80% and 95% predictive intervals** (not confidence intervals), with nominal empirical coverage evaluated on frozen test holdout data.
   * **Moderate Drought:** $\text{SPEI-3} \le -1.00$ ($P \le 0.1587$)
   * **Severe Drought:** $\text{SPEI-3} \le -1.50$ ($P \le 0.0668$)
   * **Extreme Drought:** $\text{SPEI-3} \le -2.00$ ($P \le 0.0228$)

---

### 2. Operational Issue Metadata Table & Latency Governance

To prevent look-ahead bias and distinguish operational constraints from retrospective assumptions, every forecast issue is governed by explicit metadata tracking:

| Field | Required Operational Specification | Historical Retrospective Status |
|---|---|---|
| **Issue Timestamp** | June 1, 00:00 UTC | Declared operational release boundary |
| **Information Cutoff** | May 31, 23:59 UTC | Strict temporal boundary for all predictor data |
| **Latest Eligible Precipitation Month** | April (Final) / May (Preliminary, if verified) | Determined by verified release archive |
| **SPEI-3 Ending Month** | April 30 (February–April rolling triad) | Explicit calendar month-end date |
| **Product Status** | CHIRPS Final / ERA5-Land Final | Documented data product tier |
| **Release Timestamp** | Actual verified UTC publication timestamp | Archived publication record |
| **Baseline Source** | Verified April-ending SPEI-3 value | Exact numerical baseline value |

#### 2.1 Distinction: Retrospective Latency Simulation vs Historical Timestamp Replay
* **Retrospective Latency Simulation:** When historical product publication timestamps are unarchived, retrospective evaluations are explicitly documented as **retrospective simulations under an assumed 3-week publication latency rule**, rather than claimed as genuine historical replays.
* **Genuine Historical Replay:** Prospective evaluations must ingest actual archived publication timestamps to prove information availability at the exact forecast issue moment.

---

### 3. Chronological Data Partitioning & Leakage Prevention

To prevent artificial skill inflation and historical data contamination, all model training, feature extraction, and evaluation follow strict chronological boundaries:

```
┌──────────────────────────────────────┬────────────────────────┬─────────────────────────┐
│ Training Reference Set               │ Validation / Tuning    │ Out-of-Sample Holdout   │
│ 1981–2005 (25 years, 300 months)     │ 2006–2014 (9 years)    │ 2015–2024 (10 years)    │
│ Includes 1984/85 & 2002/03 droughts  │ Includes 2009 Belg     │ Includes 2015/16 El Niño│
└──────────────────────────────────────┴────────────────────────┴─────────────────────────┘
```

#### 3.1 Anti-Leakage Rules (Strictly Enforced)
1. **Zero Future Information in Input Features:** For a forecast issued at month $T$, input feature tensors $\mathbf{X}_T$ must strictly contain data observed at or prior to month $T$.
2. **Multi-Month Accumulation Alignment:** If predicting $\text{SPEI-3}$ ending in month $T+L$, rolling multi-month predictors must end at month $T$. No feature may overlap into $[T+1, T+L]$.
3. **Operational Teleconnection Lagging:** Oceanic-atmospheric teleconnection indices (Niño 3.4, IOD Dipole Mode Index, Tropical South Atlantic Index, North Atlantic Oscillation) must reflect real-world publication latency:
   $$\text{Lag}(\text{SST Index}) \ge 1\text{ month}$$
   E.g., an April 1 forecast cannot use March SST anomalies if they are published mid-April.
4. **Scaler and Normalizer Fit Boundaries:** MinMax scalers, z-score normalizers, and PCA projections must be fit exclusively on the Training Set (1981–2005) and applied frozen to Validation and Test sets.
5. **Zero Target-Calibration Leakage (4-Tier Target Schema):** The primary forecast-evaluation target (`spei3_test`) is standardized across 2015–2024 using **distribution parameters frozen strictly at the end of training (1981–2005, N=25)**. Validation (`spei3_validation`, 2006–2014) is likewise standardized using the frozen 1981–2005 parameters. Under no circumstances are 2006–2024 observations used to fit the primary target distribution. Pre-test 1981–2014 calibration is maintained solely as a separately labelled sensitivity comparison (`spei3_test_expanded_sensitivity`).

---

### 4. Baseline Benchmarks & Evaluation Protocol

Deep learning and spatial neural networks must be evaluated against standard reference baselines:

1. **Predefined Event Threshold:**
   * Declared in advance: $\text{SPEI-3} \le -1.00$ defines moderate-or-worse seasonal drought.
2. **Dynamic Climatology Baseline:**
   * Predicts the historical empirical distribution of the target calendar month over the training period (1981–2005).
   * Serves as the zero-skill anchor for Brier Skill Score ($\text{BSS} = 1 - \frac{\text{BS}_{\text{model}}}{\text{BS}_{\text{clim}}}$).
3. **Operational Persistence Baseline:**
   * Defined as the latest eligible observed SPEI-3 available by the June 1 cutoff: $\widehat{\text{SPEI-3}}_{\text{Sept}} = \text{SPEI-3}_{\text{April}}$.
4. **Autoregressive / Statistical Baselines:**
   * Standard $\text{ARIMA}(p, d, q)$, Seasonal ETS, and Ridge Regression.
5. **Small-Sample Test Set Realities ($N=10$, 2015–2024):**
   * The frozen test holdout (2015–2024) contains exactly **10 annual September forecasts**.
   * Ten cases do not support stable bootstrap confidence intervals, particularly if only 1–3 years cross the drought threshold.
   * **Mandatory Reporting:** The pipeline must report:
     1. Exact count of drought events ($\text{SPEI-3} \le -1.0$) and non-events.
     2. Brier Score (BS) and Brier Skill Score (BSS) against climatology and persistence.
     3. Continuous Ranked Probability Score (CRPS).
     4. Bootstrap uncertainty bounds, explicitly documented as exploratory.
   * **Skill Claim Discipline:** Claiming reliable operational skill from a single favorable metric on $N=10$ is strictly prohibited.
   * **Baselines First:** Spatial deep learning (CNN-LSTM / FNO) must demonstrate a statistically defensible improvement over persistence, climatology, and regularized linear regression rather than merely fitting training noise.

---

### 5. Candidate Model Architectures & Model M7 (Deep Spatiotemporal CNN-BiLSTM)

When advancing from linear baselines ($M_0\text{--}M_6$) to deep learning, the pipeline incorporates **Model $M_7$ (Deep Spatiotemporal CNN-BiLSTM)**, implemented in [`drought_forecasting/agriminds/models/spatiotemporal_cnn_bilstm.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/agriminds/models/spatiotemporal_cnn_bilstm.py):

```
[Spatial SSTA / ERA5 Reanalysis Grid (t-L+1 to t)] 
                       │
                       ▼
          [2D-CNN Spatial Encoder]
      (Extracts dipole / gradient modes)
                       │
                       ├───────────────── [Local Autoregressive Features: SPI-3(t), sin/cos(m)]
                       ▼
          [Latent Feature Vector h_t]
                       │
                       ▼
      [Causal BiLSTM over Historical Window]
   (Forward: past -> t | Backward: t -> past)
                       │
                       ▼
          [Temporal Attention Pooling]
                       │
                       ▼
         [Dense Projection Head -> y_{t+h}]
```

#### 5.1 Three Core Vulnerabilities Solved by $M_7$:
1. **The Small-Sample Barrier ($N_{\text{eff}} \approx 113.6$):** Standard deep neural networks easily overfit on 400 monthly climate observations. $M_7$ controls parameter explosion using Adaptive Average Pooling to $(2, 2)$, heavy Dropout ($p=0.3$), and weight decay ($L_2 \ge 10^{-3}$).
2. **The Causal Time Barrier in Bidirectional LSTMs:** Running standard BiLSTMs across forecast origin $t$ leaks future tokens ($t+1, \dots, t+h$) into the backward pass. In $M_7$, the bidirectional pass operates **strictly over the historical context sequence** (lookback length $L \le 12\text{ months}$, spanning $[t-L+1, t]$):
   - Forward LSTM processes: $t-L+1 \to t$
   - Backward LSTM processes: $t \to t-L+1$
   - Pooled hidden states: $h_t = [h_{\text{fwd}, t} \,\|\, h_{\text{bwd}, t}]$
   - Zero future tokens ($t+1 \dots t+h$) exist in the input tensor.
3. **The Non-Linear Teleconnection Mechanism:** Instead of pre-aggregated 1D scalar indices (Niño 3.4, DMI), $M_7$ accepts a trimmed 2D grid ($[10^\circ\text{S}\text{--}30^\circ\text{N}, 30^\circ\text{E}\text{--}100^\circ\text{E}]$ covering the Indian Ocean and Arabian Sea), allowing 2D convolutions to learn spatial dipole patterns directly from grid cells without arbitrary regional boundaries.

#### 5.2 Four Training Safeguards for Small Climate Datasets:
| Failure Mode | Deep Learning Risk | Audited Solution in $M_7$ |
| :--- | :--- | :--- |
| **Data Leakage** | Scalers fitted over entire multi-decadal record | Fit normalization stats **only on $t_{\text{train}} \le \text{origin} - h$** inside the walk-forward loop. |
| **Small-Sample Overfitting** | Thousands of parameters chasing $N_{\text{eff}} \approx 113.6$ | 1. Adaptive Average Pooling $(2, 2)$<br>2. Weight decay ($L_2 \ge 10^{-3}$)<br>3. Sequence length $L \le 12$ months |
| **False Winter Skill** | Minimizing MSE by predicting dry Bega with high certainty | **Seasonally Weighted Loss:** Weight errors during Kiremt (JAS) and Belg (MAM) $2\times$ higher than dry-season (ONDJ) errors. |
| **Lag-Overlap Exploitation** | Over-relying on $P_t$ in SPI-3 rather than physical dynamics | Pre-train on **pure ERA5 moisture convergence anomalies (VIMC)** or non-overlapping monthly rainfall before fine-tuning. |

#### 5.3 Interpretability & Gradient Saliency Verification:
To confirm physical validity, $M_7$ incorporates gradient attribution back to the input SST grid:
$$\text{Attribution}(c, h, w) = \left| \frac{\partial \hat{y}_{t+h}}{\partial x_{\text{grid}}(c, h, w)} \right|$$
If attribution peaks over the **Western Indian Ocean and Arabian Sea** during wet seasons, it physically corroborates the teleconnection pathways identified in diagnostic analyses. If it highlights random open-ocean pixels, the model has overfit to climate noise.

---

### 6. Direct Benchmarking Integration Protocol ($M_0$ through $M_7$)

Model $M_7$ is integrated as the deep spatiotemporal benchmark alongside models $M_0\text{--}M_6$:
1. **Direct-Horizon Training:** Train three separate models for $h=1$, $h=2$, and $h=3$. Autoregressive recursive feeding (which cascades errors) is strictly prohibited.
2. **Paired Calendar Bootstrap Verification:** Evaluated using the identical 8-year paired calendar year-block bootstrap ($B = 2,000$) comparing $M_7$ against $M_2$ (Local AR) and $M_4$ (Indian Ocean Ridge).
3. **Automated Unit Tests:** Verified by [`drought_forecasting/tests/test_spatiotemporal_cnn_bilstm.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/test_spatiotemporal_cnn_bilstm.py), guaranteeing forward-pass dimensions, attention weight normalization ($\sum \alpha_s = 1.0$), causal sequence isolation, gradient saliency, and loss weighting.

---

### 7. Multi-Criteria Evaluation Metrics

#### 7.1 Continuous Forecast Evaluation
* **Mean Absolute Error (MAE):** $\text{MAE} = \frac{1}{N} \sum |y_i - \hat{y}_i|$
* **Root Mean Square Error (RMSE):** $\text{RMSE} = \sqrt{\frac{1}{N} \sum (y_i - \hat{y}_i)^2}$
* **Pearson Correlation Coefficient ($r$):** Linear phase alignment.
* **Spearman Rank Correlation ($\rho$):** Monotonic rank ordering.

#### 7.2 Probabilistic & Categorical Drought Evaluation
* **Brier Score (BS) & Brier Skill Score (BSS):**
  $$\text{BS} = \frac{1}{N} \sum_{i=1}^N (p_i - o_i)^2, \quad \text{BSS} = 1 - \frac{\text{BS}_{\text{model}}}{\text{BS}_{\text{climatology}}}$$
* **Continuous Ranked Probability Score (CRPS):** Evaluates entire predicted probability density function.
* **Categorical Contingency Metrics:** Precision, Recall (POD), False Alarm Ratio (FAR), and Critical Success Index (CSI / Threat Score) for drought events ($\text{SPEI} \le -1.5$).
