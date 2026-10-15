# AI-DREWS: Master Scientific Workflow & Multi-Gate Validation Plan
## End-to-End Execution Blueprint for Tekezé Basin Drought Forecasting (1981–2024)

**Document ID:** `AI-DREWS-MASTER-PLAN-2026-10-REV3`  
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
│  • Strict raw immutability in data/raw/temperature/ & SHA-256 manifest │
│  • Status: PARTIAL (1984 Benchmark Certified; 1981–2024 Ingestion Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 2: Mathematical Implementation Cross-Validation                  │
│  • Hosking (1990) GLO parameterization & CDF complete pair validation   │
│  • Independent R lmom/SPEI benchmark fixtures (7 test cases: 5 GLO, 2 Gamma)│
│  • McKee/Thom Gamma SPI-3 MLE with zero-precipitation treatment q      │
│  • Inverse normal conversion (ndtri) with unclipped core mathematics   │
│  • Status: PASS (All 5 Automated Benchmark Test Functions Passing)     │
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
│  • Status: PASS (All 7 Spatial/Temporal Test Functions Passing)        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 4: Reconstruct & Validate Drought Indices Target                 │
│  • Hargreaves-Samani (1985) monthly PET using daily extrema            │
│  • 3-month rolling water balance: D_3,t = sum_{k=0}^2 (P_{t-k}-PET_{t-k})│
│  • Separate distribution calibration for each of 12 calendar months    │
│  • Fixed calibration baseline: 1991–2020 (declared methodological choice)│
│  • Historical drought event validation treated as testable hypotheses  │
│  • Status: NOT RUN (Explicitly Paused for Gate 1 Archive Ingestion)    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 5: Build & Evaluate Predictive Forecasting Models                │
│  • Operational forecast task: June 1 issue for Sept-ending SPEI-3 (Lead 3)│
│  • Information cutoff strictly May 31 (zero future target data in features)│
│  • Chronological split: Train (1981–2005), Val (2006–2014), Test (2015+)│
│  • Baselines first: Climatology, Persistence, ARIMA before neural nets │
│  • Probabilistic predictive intervals evaluated for nominal coverage   │
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

### 2.2 Forensic File Ingestion Audit (Current Local Holdings)

A comprehensive forensic audit of all raw climate data files currently on disk is documented in [`docs/gate1_raw_temperature_ingestion_audit_report.md`](docs/gate1_raw_temperature_ingestion_audit_report.md). Summary of verified holdings:

| Product | Local Path | Coverage | Spatial Resolution | Units | Valid Cells (%) | Size | SHA-256 Hash |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **NOAA CPC** | `data/raw/temperature/cpc/tmax.1984.nc` | 1984 (366 days) | $0.5^\circ \times 0.5^\circ$ ($360 \times 720$) | $^\circ\text{C}$ | 99.73% (Tekezé) | 87.7 MB | `476fae44...` |
| **NOAA CPC** | `data/raw/temperature/cpc/tmin.1984.nc` | 1984 (366 days) | $0.5^\circ \times 0.5^\circ$ ($360 \times 720$) | $^\circ\text{C}$ | 99.73% (Tekezé) | 89.1 MB | `b14e8bba...` |
| **CHIRPS 2.0** | `data/raw/chirps_ethiopia_2000_2024.nc` | 2000–2024 (84 mos) | $0.05^\circ \times 0.05^\circ$ ($250 \times 300$) | $\text{mm}$ | 91.83% | 18.1 MB | `39a0dc65...` |
| **CHIRPS 2.0** | `data/raw/chirps_monthly/*.tif.gz` | 168 months | $0.05^\circ \times 0.05^\circ$ ($1600 \times 1500$) | $\text{mm}$ | 100% (land) | 758.4 MB | Logged in manifest |

### 2.3 Gate 1 Status & Pass Condition
* **Current Status:** `PARTIAL`
* **Pass Condition:** The complete 1981–2024 archive (all 44 years) must be acquired for both ERA5-Land and CPC, with verified timestamps, continuous coverage across all 528 months, and complete SHA-256 hashes recorded in the immutable manifest. The existence of downloaders alone does not pass this gate.

---

## 3. Gate 2 — Validate the Mathematical Implementation

### 3.1 Mathematical Formulation & Complete Pair Validation

1. **Hosking (1990) Generalized Logistic (GLO) Distribution:**
   Parameter vector: location $\xi \in \mathbb{R}$, scale $\alpha > 0$, shape $k \in \mathbb{R}$.
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
   * **Complete Pair Round-Trip Identity:**
     $$\forall F \in (0, 1), \quad |F(x(F)) - F| < 10^{-10}$$

2. **McKee / Thom (1958) Gamma SPI-3 MLE with Zero-Precipitation Adjustment:**
   For cumulative 3-month precipitation $x \ge 0$:
   * Let $q = \frac{n_{\text{zero}}}{n_{\text{total}}}$ be the empirical probability of zero precipitation.
   * On non-zero observations ($x > 0$), calculate $A = \ln(\bar{x}) - \frac{1}{m}\sum_{i=1}^m \ln(x_i)$.
   * Thom's MLE shape and scale parameters:
     $$\hat{\alpha}_g = \frac{1 + \sqrt{1 + 4A/3}}{4A}, \quad \hat{\beta}_g = \frac{\bar{x}}{\hat{\alpha}_g}$$
   * Cumulative probability incorporating zeros:
     $$H(x) = q + (1 - q) G(x; \hat{\alpha}_g, \hat{\beta}_g)$$

3. **Standard Normal Transformation:**
   * $Z = \Phi^{-1}(H(x))$ via rational approximation / `scipy.special.ndtri`.
   * Unclipped mathematical precision preserved throughout scientific pipelines; clipping to $[-3.5, 3.5]$ is confined exclusively to visual display contracts.

### 3.2 Reference Environment & Test Evidence
* **Reference Software Environment:** R version 4.3.2 (2023-10-31), `lmom` package version 2.9, `SPEI` package version 1.8.1.
* **Fixtures:** 7 benchmark test cases stored in [`drought_forecasting/tests/fixtures/r_spei_lmom_reference_benchmark.json`](drought_forecasting/tests/fixtures/r_spei_lmom_reference_benchmark.json).
* **Automated Test Suite:** [`drought_forecasting/tests/test_gate2_mathematical_benchmarks.py`](drought_forecasting/tests/test_gate2_mathematical_benchmarks.py) exercises all 7 cases across 5 test functions, passing in 0.45s with absolute error $|F_{\text{py}} - F_{\text{ref}}| < 10^{-5}$.
* **Current Status:** `PASS`

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
* **Current Status:** `PASS` (All 7 spatial/temporal integrity tests passing in [`test_gate3_spatial_and_temporal_integrity.py`](drought_forecasting/tests/test_gate3_spatial_and_temporal_integrity.py)).

---

## 5. Gate 4 — Reconstruct and Validate Drought Indices Target

### 5.1 Distinction between Accumulation Window and Month-Specific Calibration

* **Target Metric:** Standardized Precipitation-Evapotranspiration Index at 3-month scale ($\text{SPEI-3}$).
* **Accumulation Window:** Rolling 3-month climatic water balance:
  $$D_{3,t} = \sum_{k=0}^2 (P_{t-k} - \text{PET}_{t-k})$$
* **Month-Specific Distribution Fitting:**
  To account for Northern Ethiopia's extreme seasonality (Bega dry season vs. Kiremt summer monsoon), **12 separate probability distributions are fitted, one for each ending calendar month** ($m \in \{1, \dots, 12\}$).
  * For September-ending SPEI-3 ($m=9$): accumulate July, August, and September water balances, then fit the September distribution using historical September-ending 3-month accumulations ($D_{3, \text{Sep}}$) over the declared calibration baseline.
  * For March-ending SPEI-3 ($m=3$): accumulate January, February, and March water balances, then fit the March distribution using historical March-ending 3-month accumulations ($D_{3, \text{Mar}}$).

### 5.2 Hargreaves–Samani PET & Radiative Formulation

* **Formula:**
  $$\text{PET}_{\text{daily}} = 0.0023 \cdot R_a \cdot (T_{\text{mean}} + 17.8) \cdot \sqrt{T_{\max} - T_{\min}}$$
  Where:
  * $T_{\text{mean}} = \frac{T_{\max} + T_{\min}}{2}$ ($^\circ\text{C}$).
  * $R_a$ is extraterrestrial solar radiation expressed in equivalent water evaporation ($\text{mm/day}$), computed as a function of latitude and day of the year via solar declination and sunset hour angle equations.
  * $\text{PET}_{\text{monthly}} = \sum_{d \in \text{month}} \text{PET}_{\text{daily}}$ ($\text{mm/month}$).
* **Jensen's Inequality Concavity:**
  Because $\sqrt{\Delta T}$ is strictly concave, $\mathbb{E}[\sqrt{\Delta T}] \le \sqrt{\mathbb{E}[\Delta T]}$. Monthly PET derived from daily extrema strictly avoids overestimation bias.
* **Declared Calibration Baseline:** 1991–2020 WMO standard normal period (30 years, $N=30$ observations per calendar month).

### 5.3 Historical Drought Events as Validation Hypotheses
Historical drought shocks (1984/85, 1987, 2002/03, 2015/16) and pluvial events (1988, 1998) are treated as **testable validation hypotheses**:
* Target calculations will never be tuned or forced to match predetermined values.
* Meteorological drought ($\text{SPEI-3} \le -2.0$) will be strictly disambiguated from socio-economic food insecurity and human famine.
* **Current Status:** `NOT RUN` (Paused pending Gate 1 completion).

---

## 6. Gate 5 — Build and Evaluate Predictive Forecasting Models

### 6.1 Operational Forecast Task Formulation

To eliminate temporal data leakage and establish operational realism:
* **Target Index:** September-ending SPEI-3 (capturing full Kiremt seasonal moisture: July, August, September).
* **Operational Issue Date:** June 1.
* **Lead Time:** 3 months to target accumulation end (September 30).
* **Information Cutoff:** Strictly **May 31**.
  * Predictor features are restricted exclusively to data observed on or before May 31.
  * July, August, and September rainfall and temperature are completely unobserved on June 1 and **must never enter predictor features**.
  * Operational latency of ocean SST teleconnection indices (minimum 30 days) is strictly enforced.

### 6.2 Model Hierarchy & Out-of-Sample Evaluation
1. **Baselines First:**
   * Dynamic Climatology (monthly empirical distribution over training period).
   * Persistence (SPEI-3 at issue date $t_0$).
   * Autoregressive (ARIMA / seasonal ARIMAX).
2. **Machine Learning & Deep Learning Benchmarks:**
   * Regularized Linear / Ridge Regression.
   * Gradient Boosted Decision Trees (XGBoost).
   * Recurrent Neural Networks (LSTM / BiLSTM).
   * Spatiotemporal Architectures (CNN-LSTM, Fourier Neural Operator).
3. **Data Splits:**
   * Training: 1981–2005 (25 years).
   * Validation: 2006–2014 (9 years).
   * Frozen Out-of-Sample Test Holdout: 2015–2024 (10 years, untouched during model selection).
4. **Evaluation Metrics:**
   * Brier Score ($BS$) and Brier Skill Score ($\text{BSS} > 0$ relative to dynamic climatology).
   * Continuous Ranked Probability Score (CRPS).
   * Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE).
   * Reliability / Calibration curves and Receiver Operating Characteristic (ROC-AUC).
   * 80% and 95% predictive intervals evaluated for empirical coverage.
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
| **Gate 1** | Climate Data Acquisition & Provenance | **PARTIAL** | 1981–2024 ERA5-Land & CPC Ingestion & Manifest | [`docs/gate1_raw_temperature_ingestion_audit_report.md`](docs/gate1_raw_temperature_ingestion_audit_report.md) |
| **Gate 2** | Mathematical Implementation Cross-Validation | **PASS** | R `lmom`/`SPEI` benchmark fixtures & 5 tests | [`docs/gate2_cross_language_mathematical_validation_report.md`](docs/gate2_cross_language_mathematical_validation_report.md) |
| **Gate 3** | Spatial and Temporal Integrity Auditing | **PASS** | 528-month sequence & physical spatial weighting tests | [`docs/gate3_spatial_and_temporal_integrity_audit.md`](docs/gate3_spatial_and_temporal_integrity_audit.md) |
| **Gate 4** | Drought Target Reconstruction & Event Validation | **NOT RUN** | Validated SPEI-3/SPI-3 table & event evaluation | [`docs/gate4_drought_indices_reconstruction_and_validation.md`](docs/gate4_drought_indices_reconstruction_and_validation.md) |
| **Gate 5** | Predictive Forecasting Model Formulation | **NOT RUN** | Out-of-sample Brier benchmarks & leakage audit | [`docs/gate5_predictive_model_architecture_and_leakage_audit.md`](docs/gate5_predictive_model_architecture_and_leakage_audit.md) |
| **Gate 6** | Operational AgriMinds Dashboard Interface | **NOT RUN** | Documented API, fail-safe UI, and telemetry | [`docs/gate6_agriminds_dashboard_interface_and_monitoring.md`](docs/gate6_agriminds_dashboard_interface_and_monitoring.md) |
