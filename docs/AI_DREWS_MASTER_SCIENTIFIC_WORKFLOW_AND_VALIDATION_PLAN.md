# AI-DREWS: Master Scientific Workflow & Multi-Gate Validation Plan
## End-to-End Execution Blueprint for Tekezé Basin Drought Forecasting (1981–2024)

**Document ID:** `AI-DREWS-MASTER-PLAN-2026-10-REV2`  
**Reference Standards:** WMO-No. 100 Guidelines; Copernicus Climate Data Store (CDS); NOAA PSL THREDDS; R `lmom` v2.9 / `SPEI` v1.8.1; HydroBASINS (WWF / USGS)  
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
│  • Coordinate-space fractional area weights without double-counting    │
│  • 95% minimum spatial coverage rule per month                         │
│  • 528-month continuous temporal sequence (1981–2024)                  │
│  • Strict NaN propagation through rolling 3-month accumulations        │
│  • Status: PASS (All 7 Spatial/Temporal Test Functions Passing)        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 4: Reconstruct & Validate Drought Indices Target                 │
│  • Hargreaves-Samani (1985) monthly PET using daily extrema            │
│  • Thornthwaite (1948) PET baseline sensitivity                        │
│  • 3-month rolling accumulation with 12 calendar-month calibrations    │
│  • Fixed calibration baseline: 1991–2020 (declared methodological choice)│
│  • Historical drought event validation treated as testable hypotheses  │
│  • Status: NOT RUN (Explicitly Paused for Gate 1 Archive Ingestion)    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 5: Build & Evaluate Predictive Forecasting Models                │
│  • Chronological split: Train (1981–2005), Val (2006–2014), Test (2015+)│
│  • Zero future information leakage; rolling-origin cross-validation    │
│  • Forecast task definition: Issue June 1 for Sept-ending SPEI-3 (Lead 3)│
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
   * **Nature:** Numerical reanalysis produced by the European Centre for Medium-Range Weather Forecasts (ECMWF) combining model physics with assimilated observations; **not direct in-situ ground station observations**.
   * **Domain:** Tekezé Bounding Box $[15.0^\circ\text{N}, 35.5^\circ\text{E}, 11.5^\circ\text{N}, 40.0^\circ\text{E}]$.
   * **Resolution:** $0.1^\circ \times 0.1^\circ$ (~9 km native), hourly timesteps, 1981–2024.
   * **Extrema Derivation:** Ingests hourly 2 m temperature (`2m_temperature`) to derive daily $T_{\max, d} = \max_{h} T_{2\text{m}}(d, h)$ and $T_{\min, d} = \min_{h} T_{2\text{m}}(d, h)$.
   * **Unit Conversion:** Converted from Kelvin to Celsius via $T(^\circ\text{C}) = T(\text{K}) - 273.15$.
2. **NOAA CPC Global Unified Temperature (Independent Gridded Comparison):**
   * **Nature:** Gridded analysis product produced by the NOAA Climate Prediction Center based on gauge reports and GTS telecommunication bulletins interpolated over land; **an independent gridded comparison dataset, not automatic in-situ ground truth**.
   * **Resolution:** $0.5^\circ \times 0.5^\circ$ (~55 km), daily $T_{\max}$ and $T_{\min}$ in $^\circ\text{C}$.
   * **Application:** Provides independent validation checks and spatial cross-comparison against ERA5-Land.

### 2.2 Gate 1 Status & Pass Condition
* **Current Status:** `PARTIAL`
* **Evidence:** The reproducible downloaders [`scripts/download_era5_land_tekeze_1981_2024.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/download_era5_land_tekeze_1981_2024.py) and [`scripts/download_noaa_cpc_tekeze_1981_2024.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/download_noaa_cpc_tekeze_1981_2024.py) are operational, and the 1984 CPC benchmark NetCDF files are acquired and verified with SHA-256 hashes.
* **Pass Condition:** The full 1981–2024 temperature archive must exist locally, pass timestamp continuity checks across all 528 months, and be recorded in the immutable SHA-256 manifest. The existence of downloaders alone does not pass this gate.

---

## 3. Gate 2 — Validate the Mathematical Implementation

### 3.1 Reconciled Benchmark Fixtures (7 Test Cases, 5 Test Functions)

Independent reference fixtures are stored in [`drought_forecasting/tests/fixtures/r_spei_lmom_reference_benchmark.json`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/fixtures/r_spei_lmom_reference_benchmark.json). They record source packages (R `lmom` v2.9, R `SPEI` v1.8.1), functions (`pelglo`, `cdfglo`, `quaglo`, `spei`), parameter values, and independent expected quantiles:

1. **Case 1 (Kiremt Wet Season):** $\xi = 45.0, \alpha = 30.0, k = -0.15$ (Lower bound: $-155.0$).
2. **Case 2 (Bega Dry Season):** $\xi = -85.0, \alpha = 15.0, k = -0.22$ (Lower bound: $-153.18$).
3. **Case 3 (Standard Logistic Limit $k \to 0$):** $\xi = 0.0, \alpha = 20.0, k = 0.00$ (Unbounded).
4. **Case 4 (Positive Shape Upper Bound):** $\xi = 10.0, \alpha = 12.0, k = +0.18$ (Upper bound: $+76.67$).
5. **Case 5 (Extreme Tail Drought):** $\xi = -20.0, \alpha = 40.0, k = -0.28$ (Lower bound: $-162.86$).
6. **Case 6 (Gamma SPI Belg Short Season):** $\alpha_g = 2.2, \beta_g = 35.0, q = 0.08$ (Thom MLE recovery).
7. **Case 7 (Gamma SPI Kiremt Peak Rains):** $\alpha_g = 4.5, \beta_g = 50.0, q = 0.0$ (Zero-free Gamma).

### 3.2 Verification beyond Round-Trip Identity
* In addition to verifying round-trip identity ($F(x(F)) \equiv F$), [`test_gate2_mathematical_benchmarks.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/test_gate2_mathematical_benchmarks.py) independently tests:
  1. Parameter recovery from synthetic samples via unbiased L-moments against theoretical $(\xi, \alpha, k)$.
  2. Non-exceedance probabilities matching independently computed R `cdfglo` quantiles across 15 probability levels ($P \in [0.001, 0.999]$).
  3. Strict physical support enforcement ($F(x) = 1.0$ for $x \ge \text{upper bound}$; $F(x) = 0.0$ for $x \le \text{lower bound}$).
  4. Thom (1958) Gamma MLE parameter estimation and zero-adjustment $H(x) = q + (1 - q)G(x)$.
  5. Unclipped mathematical standard normal transformation via `scipy.special.ndtri` (with $[-3.5, 3.5]$ clipping reserved exclusively as an optional operational display policy).
* **Current Status:** `PASS` (All 5 automated tests passing in 0.45s).

---

## 4. Gate 3 — Spatial and Temporal Integrity Auditing

### 4.1 Provisional Catchment Boundary & Spatial Weighting
* **Boundary:** HydroBASINS Level 5/6/7 polygon representing the complete Tekezé catchment down to the Sudanese border outlet near Humera.
* **Provisional Area:** $67,135.4\text{ km}^2$ spherical geodesic excess area (EPSG:4326). Marked **provisional** until the exact constituent unit topology, sub-basin selection, and border delineation are fully documented in the final report.
* **Spatial Weighting Formulation:**
  Grid cells are defined in geographic coordinate space. To avoid double-counting latitude adjustments:
  $$w_{i,j} = \left(\frac{\text{Area}(\mathcal{C}_{i,j} \cap \mathcal{P})}{\text{Area}(\mathcal{C}_{i,j})}\right)_{\text{degree space}} \cdot \cos(\phi_i), \quad \sum_{(i,j) \in \text{valid}} w_{i,j} = 1.0$$
  Where coordinate-space fractional intersection is scaled by the relative physical area of the latitude band ($\cos \phi_i$). Actual geodesic intersection area may be used directly without the cosine multiplier.

### 4.2 Quality-Control Rules
* **NoData Exclusion:** Negative sentinels (e.g. CHIRPS $-9999.0$) are strictly excluded from both numerator and denominator.
* **95% Spatial Coverage Threshold:** If $\sum_{(i,j) \in \text{valid}} w_{i,j} < 0.95$, the month is flagged `INSUFFICIENT_SPATIAL_COVERAGE` and recorded as `NaN`.
* **528-Month Continuity:** January 1981 through December 2024 (528 consecutive months).
* **NaN Propagation:** Missing values strictly propagate through rolling 3-month accumulations; zero silent interpolation.
* **Current Status:** `PASS` (All 7 spatial/temporal integrity tests passing in [`test_gate3_spatial_and_temporal_integrity.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/test_gate3_spatial_and_temporal_integrity.py)).

---

## 5. Gate 4 — Reconstruct and Validate Drought Indices Target

### 5.1 Clarification: 3-Month Rolling Accumulation with Month-Specific Calibrations
The term "rolling 12-calendar-month engine" is clarified:
* The target index is **SPEI-3** (a rolling 3-month accumulation: $D_{3,t} = \sum_{k=0}^2 (P_{t-k} - \text{PET}_{t-k})$).
* To respect the strong seasonal cycle of northern Ethiopia, **separate probability distributions are fitted for each of the 12 ending calendar months** ($m \in \{1, \dots, 12\}$). E.g., September-ending SPEI-3 is fitted using historical July–September water balances; March-ending SPEI-3 is fitted using historical January–March water balances.

### 5.2 Hargreaves–Samani PET & Jensen's Inequality
* **Jensen's Inequality:** Because $f(u) = \sqrt{u}$ is strictly concave, $\mathbb{E}[\sqrt{\Delta T}] \le \sqrt{\mathbb{E}[\Delta T]}$.
* **Empirical Treatment:** Substituting monthly mean temperature extrema overestimates PET compared to daily extrema. Rather than assuming an arbitrary universal percentage, the pipeline strictly derives daily extrema from hourly/daily series and evaluates the empirical difference on the observed Tekezé data.
* **Fixed Calibration Baseline:** The 1991–2020 baseline is adopted as our **declared methodological choice** (aligned with standard WMO climatological normal periods), not as a universally mandated requirement. Inadequate baseline samples will be reported rather than silently shifting intervals.

### 5.3 Historical Drought Events as Validation Hypotheses
Historical events (1984/85 Great Famine, 1987 El Niño, 1988 pluvial, 1998 pluvial, 2002/03 drought, 2015/16 El Niño) are treated as **testable validation hypotheses**, not predetermined outcomes:
* The pipeline will calculate the objective physical indices and evaluate whether they detect these historical shocks.
* Index calculations will never be tuned or forced to reproduce arbitrary pre-selected values.
* Meteorological drought ($\text{SPEI-3} \le -2.0$) will be strictly disambiguated from agricultural crop failure and famine.
* **Current Status:** `NOT RUN` (Paused pending Gate 1 completion).

---

## 6. Gate 5 — Build and Evaluate Predictive Forecasting Models

### 6.1 Explicit Forecast Timing & Target Definitions
To prevent target leakage and timing confusion:
* **Task Definition:** Predict September-ending SPEI-3 (which accumulates July, August, and September moisture conditions).
* **Issue Date:** June 1.
* **Lead Time:** 3 months (from issue date to end of target accumulation window).
* **Information Cutoff:** Features available to the model must be strictly restricted to data observed **on or before May 31**, accounting for real-world publication latency (e.g. minimum 30-day lag for SST teleconnection indices). The model must predict unobserved future July–September conditions; it cannot use July–September rainfall or PET.

### 6.2 Model Progression & Evaluation
* **Baselines First:** Persistence, Dynamic Climatology, and Autoregressive/ARIMA models must be established before deep learning.
* **Model Suite:** Linear Baselines $\to$ Recurrent LSTM $\to$ Spatiotemporal CNN-LSTM $\to$ Fourier Neural Operator (FNO).
* **Frozen Holdout:** Chronological train (1981–2005), validation (2006–2014), and frozen out-of-sample test holdout (2015–2024).
* **Predictive Intervals:** Forecast uncertainty will be expressed as **80% and 95% predictive intervals** (not confidence intervals), with empirical coverage verified on held-out test data.
* **Scoring:** Brier Score, Brier Skill Score ($\text{BSS} > 0$ relative to dynamic climatology), CRPS, MAE, and RMSE.
* **Current Status:** `NOT RUN` (Paused pending Gate 4 completion).

---

## 7. Gate 6 — Connect Results to AgriMinds Dashboard

* **Visual Separation:** Historical observed/reanalysis records and probabilistic forecast cones are rendered on distinct layers.
* **Metadata Display:** Shows forecast issue date, valid lead time, predictive intervals, and observation cutoff.
* **Fail-Safe Operation:** If data feeds fail, alerts are suppressed with an explicit warning banner; missing observations never produce synthetic forecasts.
* **Current Status:** `NOT RUN` (Architected & Specified).

---

## 8. Master Gate Status & Acceptance Matrix

| Gate | Scope | Status | Acceptance Deliverable | Evidence Artifact |
|:---:|---|:---:|---|---|
| **Gate 1** | Climate Data Acquisition & Provenance | **PARTIAL** | 1981–2024 ERA5-Land & CPC Ingestion & Manifest | [`docs/temperature_source_and_provenance_audit.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/temperature_source_and_provenance_audit.md) |
| **Gate 2** | Mathematical Implementation Cross-Validation | **PASS** | R `lmom`/`SPEI` benchmark fixtures & 5 tests | [`docs/gate2_cross_language_mathematical_validation_report.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate2_cross_language_mathematical_validation_report.md) |
| **Gate 3** | Spatial and Temporal Integrity Auditing | **PASS** | 528-month sequence & spatial weighting tests | [`docs/gate3_spatial_and_temporal_integrity_audit.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate3_spatial_and_temporal_integrity_audit.md) |
| **Gate 4** | Drought Target Reconstruction & Event Validation | **NOT RUN** | Validated SPEI-3/SPI-3 table & event evaluation | [`docs/gate4_drought_indices_reconstruction_and_validation.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate4_drought_indices_reconstruction_and_validation.md) |
| **Gate 5** | Predictive Forecasting Model Formulation | **NOT RUN** | Out-of-sample Brier benchmarks & leakage audit | [`docs/gate5_predictive_model_architecture_and_leakage_audit.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate5_predictive_model_architecture_and_leakage_audit.md) |
| **Gate 6** | Operational AgriMinds Dashboard Interface | **NOT RUN** | Documented API, fail-safe UI, and telemetry | [`docs/gate6_agriminds_dashboard_interface_and_monitoring.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate6_agriminds_dashboard_interface_and_monitoring.md) |
