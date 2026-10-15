# AI-DREWS: Master Scientific Workflow & Multi-Gate Validation Plan
## End-to-End Execution Blueprint for Tekezé Basin Drought Forecasting (1981–2024)

**Document ID:** `AI-DREWS-MASTER-PLAN-2026-10-REV4`  
**Reference Standards:** WMO-No. 100 Climatological Guidelines; Copernicus Climate Data Store (CDS); NOAA PSL THREDDS; R `lmom` v2.9 / `SPEI` v1.8.1; HydroBASINS (WWF / USGS)  
**Strategy Selection:** **Option A (ECMWF ERA5-Land Reanalysis Primary + NOAA CPC Global Gridded Temperature Independent Comparison)**  
**Overall Pipeline Status:** **HISTORICAL RECONSTRUCTION PAUSED PENDING COMPLETION OF GATE 1 INGESTION**  
**Spatial Domain (Provisional):** Tekezé River Basin Catchment ($67,135.4\text{ km}^2$, Northern Ethiopia; Lat: $11.6619^\circ\text{N}–14.7958^\circ\text{N}$, Lon: $35.8583^\circ\text{E}–39.7917^\circ\text{E}$)  
**Target Sequence:** January 1981 – December 2024 (528 consecutive calendar months)

---

## 1. Executive Workflow Architecture & Gate Certification Status

The scientific workflow of the AI-Driven Drought Early Warning System (AI-DREWS) operates under strict **progressive certification gates**. A downstream gate cannot begin or claim validity until all prerequisite gates achieve `PASS` status.

```
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 1: Climate Data Acquisition & Provenance Integrity              │
│  • Primary: ECMWF ERA5-Land (0.1° hourly reanalysis extrema)           │
│  • Independent Comparison: NOAA CPC Global Daily Temperature (0.5°)    │
│  • Reconciled CHIRPS archive: 300-month target, 360 missing mos audited│
│  • Strict raw immutability in data/raw/temperature/ & SHA-256 manifest │
│  • Status: PARTIAL (1984 Benchmark Certified; 1981–2024 Ingestion Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 2: Mathematical Implementation Cross-Validation                  │
│  • Hosking (1990) GLO parameterization (deliberate alternative to log-logistic)│
│  • Independent R lmom v2.9 benchmark fixtures (7 test cases: 5 GLO, 2 Gamma)│
│  • Thom (1958) shape approximation for Gamma SPI-3 with zero treatment q│
│  • 3-level evidence: Numerical identity, parameter recovery, R parity  │
│  • Status: PASS — reported (Internal Suite Passing; External R Audit Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 3: Spatial and Temporal Integrity Auditing                       │
│  • Tekezé catchment geometry (HydroBASINS Lev 5/6/7, 67,135.4 km² prov)│
│  • Explicit physical intersection area weights: a_i in km²             │
│  • 95% minimum spatial coverage rule: C_t = sum(v_i a_i) / sum(a_i)    │
│  • 528-month continuous temporal sequence (1981–2024)                  │
│  • Strict NaN propagation through rolling 3-month accumulations        │
│  • Status: PASS — reported (Internal Suite Passing; External Boundary Audit Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 4: Reconstruct & Validate Drought Indices Target                 │
│  • Hargreaves-Samani (1985) monthly PET using daily extrema            │
│  • Continuous 528-month sequence ensures Nov/Dec 1990 boundary for Jan 1991│
│  • Dual-Target Architecture: Retrospective vs Forecast-Evaluation Target│
│  • Separate distribution calibration for each of 12 calendar months    │
│  • Historical drought event validation treated as testable hypotheses  │
│  • Status: NOT RUN (Explicitly Paused for Gate 1 Archive Ingestion)    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 5: Build & Evaluate Predictive Forecasting Models                │
│  • Operational forecast task: June 1 issue for Sept-ending SPEI-3      │
│  • Target valid period: July 1 – Sept 30 (Lead 3 to accumulation end)  │
│  • Information cutoff strictly May 31 (zero future target data in features)│
│  • Target standardized without future leakage (ends prior to test set) │
│  • Chronological split: Train (1981–2005), Val (2006–2014), Test (2015+)│
│  • Baselines first: Climatology, Persistence, ARIMA before neural nets │
│  • Status: NOT RUN (Explicitly Paused for Gate 4 Certification)        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 6: Operational AgriMinds Dashboard & Decision Interface          │
│  • Versioned data interface between pipeline and Streamlit dashboard   │
│  • Clear separation between observed historical indices & forecasts    │
│  • Transparent risk categories, predictive intervals, failure states   │
│  • Automated data-refresh audits and monitoring                        │
│  • Status: NOT RUN (Architected & Specified)                           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Gate 1 — Climate Data Acquisition & Provenance Integrity

### 2.1 Strategy: Option A (ERA5-Land Primary + NOAA CPC Independent Comparison)

1. **ECMWF ERA5-Land Reanalysis (Primary Temperature Source):**
   * **Nature:** Numerical reanalysis produced by ECMWF combining model physics (HTESSEL land surface scheme) with assimilated atmospheric forcing; **not direct in-situ ground station observations**.
   * **Domain:** Tekezé Bounding Box $[15.0^\circ\text{N}, 35.5^\circ\text{E}, 11.5^\circ\text{N}, 40.0^\circ\text{E}]$.
   * **Resolution:** $0.1^\circ \times 0.1^\circ$ (~9 km native), hourly timesteps, 1981–2024.
   * **Extrema Derivation:** Ingests hourly 2 m temperature (`2m_temperature`) to derive daily $T_{\max, d} = \max_{h} T_{2\text{m}}(d, h)$ and $T_{\min, d} = \min_{h} T_{2\text{m}}(d, h)$.
   * **Unit Conversion:** Converted from Kelvin to Celsius via $T(^\circ\text{C}) = T(\text{K}) - 273.15$.
2. **NOAA CPC Global Unified Temperature (Independent Gridded Comparison):**
   * **Nature:** Gridded analysis product produced by NOAA CPC based on GTS daily station bulletins interpolated using Shepard's distance-weighting algorithm and CRU orography; **an independent gridded comparison dataset, not automatic in-situ ground truth**.
   * **Resolution:** $0.5^\circ \times 0.5^\circ$ (~55 km), daily $T_{\max}$ and $T_{\min}$ in $^\circ\text{C}$.
   * **Application:** Provides independent validation checks and spatial cross-comparison against ERA5-Land reanalysis.

### 2.2 Forensic File Ingestion Audit & CHIRPS Inventory Reconciliation

A comprehensive forensic audit of all raw climate data files currently on disk is documented in [`docs/gate1_raw_temperature_ingestion_audit_report.md`](docs/gate1_raw_temperature_ingestion_audit_report.md). Summary of verified holdings:

| Product | Local Path | Coverage & Reconciled Span | Spatial Resolution | Units | Valid Cells (%) | Size | SHA-256 Hash |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **NOAA CPC** | `data/raw/temperature/cpc/tmax.1984.nc` | 1984 (366 days, leap year) | $0.5^\circ \times 0.5^\circ$ ($360 \times 720$) | $^\circ\text{C}$ | 99.73% (Tekezé) | 87.7 MB | `476fae44...` |
| **NOAA CPC** | `data/raw/temperature/cpc/tmin.1984.nc` | 1984 (366 days, leap year) | $0.5^\circ \times 0.5^\circ$ ($360 \times 720$) | $^\circ\text{C}$ | 99.73% (Tekezé) | 89.1 MB | `b14e8bba...` |
| **CHIRPS 2.0** | `data/raw/chirps_ethiopia_2000_2024.nc` | **Reconciled Reality:** 2018–2024 only (84 months).<br>*Defect:* Filename claims 2000–2024 (300 mos), but lacks CF `time` var and missing 1981–2017. | $0.05^\circ \times 0.05^\circ$ ($250 \times 300$) | $\text{mm}$ | 91.83% | 18.1 MB | `39a0dc65...` |
| **CHIRPS 2.0** | `data/raw/chirps_monthly/*.tif.gz` | **Reconciled Reality:** 14 sampled years ($14 \times 12 = 168$ mos): 1984, 1987, 1991, 1994, 1997, 2000, 2002, 2009, 2011, 2015, 2018, 2020, 2023, 2024.<br>*Defect:* Missing 30 years ($360$ months). | $0.05^\circ \times 0.05^\circ$ ($1600 \times 1500$) | $\text{mm}$ | 100% (land) | 758.4 MB | Logged in manifest |

### 2.3 Timezone & Daily Extrema Grouping Boundaries

1. **ERA5-Land Diurnal Grouping (Primary Standard: UTC Day):**
   * ERA5-Land timestamps are in UTC. Ethiopia local time is East Africa Time ($\text{EAT} = \text{UTC} + 3\text{h}$).
   * Daily extrema are calculated over $00:00\text{ UTC} - 23:00\text{ UTC}$ of date $d$, corresponding to $03:00\text{ EAT}(d)$ to $02:00\text{ EAT}(d+1)$.
   * Because diurnal minimum occurs at sunrise (~$06:00\text{ EAT} = 03:00\text{ UTC}$) and maximum occurs in early afternoon (~$14:00\text{ EAT} = 11:00\text{ UTC}$), the UTC day captures the entire diurnal solar heating cycle without splitting across night.
   * Local civil day ($00:00–23:00\text{ EAT}$, i.e. $21:00\text{ UTC}(d-1)$ to $20:00\text{ UTC}(d)$) is supported as an explicit sensitivity check.
2. **NOAA CPC Observation Window:**
   * NOAA CPC Global Daily Temperature compiles GTS reports over a 24-hour observation cycle (typically $12:00\text{ UTC} - 12:00\text{ UTC}$).
   * CPC and ERA5-Land daily extrema represent slightly shifted 24-hour observation windows and cannot be assumed to be identical to the second, though their monthly and seasonal averages converge.

### 2.4 Gate 1 Status & Pass Condition
* **Current Status:** `PARTIAL`
* **Pass Condition:** The complete 1981–2024 archive (all 44 years) must be acquired for both ERA5-Land and CPC, with verified timestamps, continuous coverage across all 528 months, and complete SHA-256 hashes recorded in the immutable manifest. The existence of downloaders alone does not pass this gate.

---

## 3. Gate 2 — Validate the Mathematical Implementation

### 3.1 Mathematical Formulation: Hosking GLO as Deliberate Alternative to Log-Logistic

1. **Distribution Distinction (CRAN SPEI vs. AI-DREWS):**
   * The conventional CRAN `SPEI` R package defaults to the 3-parameter Log-Logistic distribution fitted via unbiased probability-weighted moments (`ub-pwm`).
   * In AI-DREWS, we deliberately adopt the 3-parameter **Generalized Logistic (GLO)** distribution parameterization of Hosking (1990) fitted via unbiased sample L-moments ($l_1, l_2, t_3$), as implemented in R `lmom::pelglo` and `lmom::cdfglo`.
   * GLO and Log-Logistic are related but distinct distribution families with different parameterizations, support bounds, and extreme tail decay. GLO is evaluated as an explicit methodological choice against R `lmom` fixtures rather than claimed as equivalent to the CRAN `SPEI` default.

2. **Hosking (1990) GLO Parameterization:**
   * Parameter vector: location $\xi \in \mathbb{R}$, scale $\alpha > 0$, shape $k \in \mathbb{R}$.
   * **Sample L-Moments:** Computed via unbiased estimators: mean $l_1$, scale $l_2$, and L-skewness $t_3 = l_3 / l_2$.
   * **Parameter Estimation:**
     $$k = -t_3$$
     $$\alpha = \frac{l_2 \sin(\pi k)}{\pi k} \quad (\text{for } k \ne 0, \text{ with limit } \alpha = l_2 \text{ as } k \to 0)$$
     $$\xi = l_1 - \frac{\alpha}{k}\left(1 - \frac{\pi k}{\sin(\pi k)}\right)$$
   * **Cumulative Distribution Function (CDF):**
     $$F(x) = \frac{1}{1 + \left(1 - \frac{k(x - \xi)}{\alpha}\right)^{1/k}} \quad (\text{for } k \ne 0)$$
   * **Quantile Function:**
     $$x(F) = \xi + \frac{\alpha}{k}\left(1 - \left(\frac{1 - F}{F}\right)^k\right)$$
   * **Physical Support Boundaries:**
     * If $k > 0$: $x < \xi + \alpha/k$ (upper bounded; $F(x) = 1.0$ for $x \ge \xi + \alpha/k$).
     * If $k < 0$: $x > \xi + \alpha/k$ (lower bounded; $F(x) = 0.0$ for $x \le \xi + \alpha/k$).
     * If $k = 0$: Standard logistic distribution, support on $(-\infty, +\infty)$.

3. **Gamma SPI-3 Formulation (Thom Shape Approximation):**
   * For cumulative 3-month precipitation $x \ge 0$:
   * Let $q = \frac{n_{\text{zero}}}{n_{\text{total}}}$ be the empirical probability of zero precipitation.
   * On non-zero observations ($x > 0$), calculate $A = \ln(\bar{x}) - \frac{1}{m}\sum_{i=1}^m \ln(x_i)$.
   * Shape estimate using **Thom's (1958) approximation**:
     $$\hat{\alpha}_g = \frac{1 + \sqrt{1 + 4A/3}}{4A}, \quad \hat{\beta}_g = \frac{\bar{x}}{\hat{\alpha}_g}$$
   * Cumulative probability incorporating zeros:
     $$H(x) = q + (1 - q) G(x; \hat{\alpha}_g, \hat{\beta}_g)$$

4. **Standard Normal Transformation:**
   * $Z = \Phi^{-1}(H(x))$ via rational approximation / `scipy.special.ndtri`.
   * Unclipped mathematical precision preserved throughout scientific pipelines; clipping to $[-3.5, 3.5]$ is confined exclusively to visual display contracts.

### 3.2 Three Levels of Mathematical Evidence & Gate 2 Status

To establish complete scientific rigor, the pipeline separates three distinct levels of mathematical proof:
1. **Numerical Consistency:** Verified that CDF and quantile invert each other across all supports ($|F(x(F)) - F| < 10^{-10}$).
2. **Parameter Recovery:** Verified that unbiased sample L-moments recover synthetic parameters $(\xi, \alpha, k)$ within documented Monte Carlo error.
3. **Independent Reference Agreement:** Python implementation matches values generated by R version 4.3.2, package `lmom` v2.9 functions (`pelglo`, `cdfglo`, `quaglo`) across 7 test cases in [`fixtures/r_spei_lmom_reference_benchmark.json`](drought_forecasting/tests/fixtures/r_spei_lmom_reference_benchmark.json) with $|F_{\text{py}} - F_{\text{ref}}| < 10^{-5}$.
* **Current Status:** `PASS — reported` (All 5 automated tests passing in [`test_gate2_mathematical_benchmarks.py`](drought_forecasting/tests/test_gate2_mathematical_benchmarks.py); marked as "reported" pending independent external audit of R session generation scripts and test logs).

---

## 4. Gate 3 — Spatial and Temporal Integrity Auditing

### 4.1 Catchment Boundary & Spatial Weighting Formula

* **Boundary:** HydroBASINS Pfafstetter Level 5, 6, and 7 closed polygon representing the complete Ethiopian Tekezé Catchment down to the Sudanese border outlet near Humera.
* **Provisional Area:** $67,135.4\text{ km}^2$ spherical geodesic excess area (EPSG:4326). Marked **provisional** until the constituent unit topology, sub-basin selection, and border delineation are fully documented in the final report.
* **Spatial Aggregation Formulation (Physical Intersection Area):**
  Let $a_i$ be the actual physical intersection area between grid cell $i$ and the catchment boundary (in $\text{km}^2$).
  Let $v_{i,t} \in \{0, 1\}$ equal 1 for valid observations (not NoData) at time $t$, and 0 otherwise.
  
  **1. Spatial Coverage Metric:**
  $$C_t = \frac{\sum_i v_{i,t} a_i}{\sum_i a_i}$$
  
  **2. Quality-Control Rule (95% Threshold):**
  If $C_t < 0.95$, the month is flagged as `INSUFFICIENT_SPATIAL_COVERAGE` and recorded as `NaN`.
  
  **3. Valid Basin Mean:**
  If $C_t \ge 0.95$, calculate the basin average exclusively over valid cells:
  $$\bar{x}_t = \frac{\sum_i v_{i,t} a_i x_{i,t}}{\sum_i v_{i,t} a_i}$$

* **Disambiguation of Area Scaling:**
  * When using coordinate-space polygon intersection fractions $f_{i,j} = \frac{\text{area}(\mathcal{C}_{i,j} \cap \mathcal{P})}{\text{area}(\mathcal{C}_{i,j})}$, multiply by the cell-area factor $\cos \phi_i$ to account for meridional convergence on a spherical Earth: $a_{i,j} \propto f_{i,j} \cos \phi_i$.
  * When using true geodesic intersection areas $a_i$ directly (in $\text{km}^2$), omit the $\cos \phi_i$ multiplier to avoid double-counting latitude adjustments.

### 4.2 Quality-Control Safeguards
* **NoData Exclusion:** Negative sentinels (CHIRPS $-9999.0$) are strictly excluded from both numerator and denominator.
* **528-Month Continuity:** January 1981 through December 2024 (528 consecutive months).
* **NaN Propagation:** Missing values strictly propagate through rolling 3-month accumulations; zero silent forward-filling or interpolation.
* **Current Status:** `PASS — reported` (All 7 spatial/temporal integrity tests passing in [`test_gate3_spatial_and_temporal_integrity.py`](drought_forecasting/tests/test_gate3_spatial_and_temporal_integrity.py); marked as "reported" pending external boundary topology verification).

---

## 5. Gate 4 — Reconstruct and Validate Drought Indices Target

### 5.1 Accumulation Window vs. Month-Specific Calibration

* **Target Metric:** Standardized Precipitation-Evapotranspiration Index at 3-month scale ($\text{SPEI-3}$).
* **Rolling Accumulation Window:**
  $$D_{3,t} = \sum_{k=0}^2 (P_{t-k} - \text{PET}_{t-k})$$
* **Boundary Condition Requirement:**
  Calculating the rolling 3-month water balance for January 1991 ($t = \text{1991-01}$) requires climate observations from **November 1990 and December 1990**, even though Nov/Dec 1990 fall outside the 1991–2020 calibration sample!
  Likewise, the final target month (December 2024) requires October and November 2024. The pipeline maintains the complete continuous 528-month climate series, selecting calibration samples by ending calendar month only when estimating distribution parameters.

### 5.2 Dual-Target Architecture: Retrospective vs. Forecast-Evaluation Target

To completely eliminate future-information leakage in predictive forecasting:
1. **Retrospective Historical Index ($\text{SPEI-3}_{\text{retro}}$):**
   * Standardized over the declared 1991–2020 WMO baseline ($N=30$ observations per calendar month).
   * Used exclusively for retrospective climatological analysis, long-term historical trend evaluation, and dashboard historical visualization.
2. **Forecast-Evaluation Target ($\text{SPEI-3}_{\text{eval}}$):**
   * Designed strictly for training and evaluating predictive models on the 2015–2024 test holdout.
   * Standardized using distribution parameters estimated **exclusively from data available prior to the evaluation window** (e.g. 1981–2010 fixed reference baseline, or expanding rolling calibration using observations strictly prior to the issue date).
   * Observations from 2015–2024 **never** enter the distribution parameter estimation for the target used in forecasting.
   * $\text{SPEI-3}_{\text{retro}}$ and $\text{SPEI-3}_{\text{eval}}$ are documented as distinct indices and are not assumed to be numerically interchangeable.

### 5.3 Hargreaves–Samani PET & Radiative Formulation

* **Formula:**
  $$\text{PET}_{\text{daily}} = 0.0023 \cdot R_a \cdot (T_{\text{mean}} + 17.8) \cdot \sqrt{T_{\max} - T_{\min}}$$
  Where $R_a$ is extraterrestrial solar radiation ($\text{mm/day}$ equivalent) computed from latitude and calendar day, and $\text{PET}_{\text{monthly}} = \sum_{d \in \text{month}} \text{PET}_{\text{daily}}$ ($\text{mm/month}$).
* **Jensen's Inequality Concavity:**
  Because $\sqrt{\Delta T}$ is strictly concave, $\mathbb{E}[\sqrt{\Delta T}] \le \sqrt{\mathbb{E}[\Delta T]}$. Monthly PET derived from daily extrema strictly avoids overestimation bias.
* **Fit Diagnostics for $N=30$:**
  With 30 observations per calendar month, the pipeline reports parameter stability checks, Kolmogorov-Smirnov goodness-of-fit, and tail behavior.
* **Historical Validation Hypotheses:** 1984/85, 1987, 2002/03, 2015/16 shocks and 1988, 1998 pluvials are treated as testable hypotheses; target calculations are never forced to predetermined numbers.
* **Current Status:** `NOT RUN` (Paused pending Gate 1 completion).

---

## 6. Gate 5 — Build and Evaluate Predictive Forecasting Models

### 6.1 Operational Forecast Task Formulation

To eliminate temporal data leakage and establish operational realism:
* **Target Index:** September-ending $\text{SPEI-3}_{\text{eval}}$ (capturing Kiremt seasonal moisture: July, August, September).
* **Operational Issue Date:** June 1.
* **Valid Target Period:** July 1 through September 30.
* **Lead Time Definition:** 3 months from issue date to accumulation end (September 30), or 1 month from issue date to accumulation start (July 1).
* **Information Cutoff:** Strictly **May 31**.
  * Predictor features are restricted exclusively to data observed on or before May 31.
  * July, August, and September rainfall and temperature are completely unobserved on June 1 and **must never enter predictor features**.
  * Actual operational publication schedules (e.g. real-world latency of ocean SST teleconnection products) are documented and enforced, rather than assuming an arbitrary nominal lag.

### 6.2 Model Progression & Evaluation Rigor
1. **Baselines First:**
   * Dynamic Climatology (monthly empirical distribution over training period).
   * Persistence ($\text{SPEI-3}_{\text{eval}}$ at issue date $t_0$).
   * Autoregressive (ARIMA / seasonal ARIMAX).
2. **Machine Learning Benchmarks:**
   * Regularized Linear / Ridge Regression.
   * Gradient Boosted Decision Trees (XGBoost).
   * Recurrent Neural Networks (LSTM / BiLSTM).
   * Spatiotemporal Architectures (CNN-LSTM, Fourier Neural Operator).
3. **Statistical Sample Size Constraint:**
   * 44 years of observations yield only 44 annual seasonal realizations.
   * Correlated spatial grid cells within the Tekezé catchment cannot be treated as independent degrees of freedom. Spatial deep learning must demonstrate that the data design justifies the added model complexity against strong regularized tabular baselines.
4. **Data Splits:**
   * Training: 1981–2005 (25 years).
   * Validation: 2006–2014 (9 years).
   * Frozen Out-of-Sample Test Holdout: 2015–2024 (10 years, untouched during model selection).
5. **Evaluation Metrics:**
   * Brier Score ($BS$) and Brier Skill Score ($\text{BSS} > 0$ relative to dynamic climatology).
   * Continuous Ranked Probability Score (CRPS).
   * Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE).
   * Reliability / Calibration curves and 80%/95% predictive intervals evaluated for empirical coverage.
* **Current Status:** `NOT RUN` (Paused pending Gate 4 completion).

---

## 7. Gate 6 — Connect Results to AgriMinds Dashboard

* **Visual Separation:** Historical observed/reanalysis drought records and probabilistic forecasts are displayed on distinct visual layers.
* **Metadata Display:** Explicitly renders issue date, valid accumulation window, predictive intervals, and observation cutoff.
* **Fail-Safe Operation:** Data ingestion failures trigger explicit warning banners; missing observations never generate synthetic predictions.
* **Current Status:** `NOT RUN` (Architected & Specified).

---

## 8. Master Gate Status & Acceptance Matrix

| Gate | Scope | Status | Acceptance Deliverable | Evidence Artifact |
|:---:|---|:---:|---|---|
| **Gate 1** | Climate Data Acquisition & Provenance | **PARTIAL** | Complete 1981–2024 ERA5-Land & CPC Ingestion & Manifest | [`docs/gate1_raw_temperature_ingestion_audit_report.md`](docs/gate1_raw_temperature_ingestion_audit_report.md) |
| **Gate 2** | Mathematical Implementation Cross-Validation | **PASS — reported** | Reproducible independent R `lmom` benchmark fixtures & 5 tests | [`docs/gate2_cross_language_mathematical_validation_report.md`](docs/gate2_cross_language_mathematical_validation_report.md) |
| **Gate 3** | Spatial and Temporal Integrity Auditing | **PASS — reported** | 528-month sequence & physical spatial weighting tests ($a_i$ in $\text{km}^2$) | [`docs/gate3_spatial_and_temporal_integrity_audit.md`](docs/gate3_spatial_and_temporal_integrity_audit.md) |
| **Gate 4** | Drought Target Reconstruction & Event Validation | **NOT RUN** | Dual-target SPEI-3 table, boundary audits, and event evaluation | [`docs/gate4_drought_indices_reconstruction_and_validation.md`](docs/gate4_drought_indices_reconstruction_and_validation.md) |
| **Gate 5** | Predictive Forecasting Model Formulation | **NOT RUN** | Out-of-sample Brier benchmarks on frozen test set & leakage audit | [`docs/gate5_predictive_model_architecture_and_leakage_audit.md`](docs/gate5_predictive_model_architecture_and_leakage_audit.md) |
| **Gate 6** | Operational AgriMinds Dashboard Interface | **NOT RUN** | Documented API, fail-safe UI, and telemetry | [`docs/gate6_agriminds_dashboard_interface_and_monitoring.md`](docs/gate6_agriminds_dashboard_interface_and_monitoring.md) |
