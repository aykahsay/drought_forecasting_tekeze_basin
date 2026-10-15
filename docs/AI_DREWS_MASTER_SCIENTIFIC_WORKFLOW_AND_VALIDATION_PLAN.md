# AI-DREWS: Master Scientific Workflow & Multi-Gate Validation Plan
## End-to-End Execution Blueprint for Tekezé Basin Drought Forecasting (1981–2024)

**Document ID:** `AI-DREWS-MASTER-PLAN-2026-10-REV6`  
**Reference Standards:** WMO-No. 100 Climatological Guidelines; Copernicus Climate Data Store (CDS); NOAA PSL THREDDS; R `lmom` v2.9 / `SPEI` v1.8.1; HydroBASINS (WWF / USGS)  
**Strategy Selection:** **Option A (ECMWF ERA5-Land Reanalysis Primary + NOAA CPC Global Gridded Temperature Independent Comparison)**  
**Overall Pipeline Status:** **HISTORICAL RECONSTRUCTION PAUSED PENDING COMPLETION OF GATE 1 INGESTION**  
**Gate Qualification Notice:** Gates 2 and 3 are retained as working specifications with 31 passing software implementation tests, but are strictly qualified as **reported/provisional** pending complete raw archive ingestion, independent reference calculations, and end-to-end provenance audits.  
**Spatial Domain:** Ethiopian Tekezé River Catchment ($67,135.4\text{ km}^2$; HydroBASINS Level 5 Union of `1050648030`, `1050692800`, `1050692900`; Lat: $11.6619^\circ\text{N}–14.7958^\circ\text{N}$, Lon: $35.8583^\circ\text{E}–39.7917^\circ\text{E}$)  
**Target Sequence:** January 1981 – December 2024 (528 consecutive calendar months)

---

## 1. Executive Workflow Architecture & Gate Certification Status

The scientific workflow of the AI-Driven Drought Early Warning System (AI-DREWS) operates under strict **progressive certification gates**. A downstream gate cannot begin or claim validity until all prerequisite gates achieve certified `PASS` status.

```
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 1: Climate Data Acquisition & Provenance Integrity              │
│  • Primary: ECMWF ERA5-Land (0.1° hourly reanalysis extrema)           │
│  • Independent Comparison: NOAA CPC Global Daily Temperature (0.5°)    │
│  • Reconciled CHIRPS archive: Full 528-month requirement (1981–2024)   │
│  • Strict raw immutability in data/raw/temperature/ & SHA-256 manifest │
│  • Status: PARTIAL (1984 Benchmark Certified; 1981–2024 Ingestion Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 2: Mathematical Implementation Cross-Validation                  │
│  • Hosking (1990) GLO parameterization (deliberate alternative to log-logistic)│
│  • Exact support bounds & float64 deliberate endpoint safeguards       │
│  • Independent R lmom v2.9 benchmark fixtures (7 test cases, 13 tests) │
│  • Hargreaves-Samani FAO-56 radiation units & daily summation tests    │
│  • Thom (1958) shape approximation for Gamma SPI-3 with zero treatment q│
│  • Status: PASS — reported (31 Tests Passing; External Empirical Audit Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 3: Spatial and Temporal Integrity Auditing                       │
│  • Reproducible HydroBASINS Lev 5 Catchment Geometry (67,135.4 km²)    │
│  • Constituent IDs: 1050648030, 1050692800, 1050692900 (Humera outlet) │
│  • Explicit physical intersection area weights: a_i in km²             │
│  • 95% minimum spatial coverage rule: C_t = sum(v_i a_i) / sum(a_i)    │
│  • 528-month continuous temporal sequence (1981–2024)                  │
│  • Status: PASS — reported (Internal Suite Passing; External Topology Audit Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 4: Reconstruct & Validate Drought Indices Target                 │
│  • Hargreaves-Samani (1985; FAO-56) daily extrema PET (MJ/m²/day units)│
│  • Continuous 528-month sequence ensures Nov/Dec 1990 boundary for Jan 1991│
│  • 4-Tier Target Schema: spei3_retro, spei3_train, spei3_val, spei3_test│
│  • Frozen training parameters (1981–2005) applied to validation & test │
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
│  • Target standardized strictly on training data (no future leakage)   │
│  • Chronological split: Train (1981–2005), Val (2006–2014), Test (2015+)│
│  • Predefined drought threshold (SPEI-3 <= -1.0) & BSS vs climatology  │
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

### 2.2 Forensic File Ingestion Audit & Full 528-Month CHIRPS Requirement

A comprehensive forensic audit of all raw climate data files currently on disk is documented in [`docs/gate1_raw_temperature_ingestion_audit_report.md`](docs/gate1_raw_temperature_ingestion_audit_report.md).

#### Reconciliation of Precipitation Holdings:
* **Master Study Period:** Full 1981–2024 historical period requires **528 continuous calendar months**, not 300 months (which only spanned 2000–2024).
* **Local Incomplete Holdings:**
  * `chirps_ethiopia_2000_2024.nc` contains only 84 months (2018–2024) and lacks a standard CF `time` coordinate variable. It is a legacy exploratory file.
  * `data/raw/chirps_monthly/*.tif.gz` contains exactly 168 files (14 sampled 12-month years: `1984, 1987, 1991, 1994, 1997, 2000, 2002, 2009, 2011, 2015, 2018, 2020, 2023, 2024`).
  * Exactly **30 years ($360$ months)** of continuous CHIRPS GeoTIFFs are unacquired and must be downloaded from the CHC archive prior to Gate 4 execution.

### 2.3 Timezone & Daily Extrema Grouping Boundaries

1. **ERA5-Land Diurnal Grouping (Primary Standard: UTC Day):**
   * ERA5-Land records hourly temperatures in UTC. Local time is East Africa Time ($\text{EAT} = \text{UTC} + 3\text{h}$).
   * Daily extrema are calculated over $00:00\text{ UTC} - 23:00\text{ UTC}$ of date $d$, corresponding to $03:00\text{ EAT}(d)$ to $02:00\text{ EAT}(d+1)$.
   * Because diurnal minimum occurs near sunrise (~$06:00\text{ EAT} = 03:00\text{ UTC}$) and maximum occurs in early afternoon (~$14:00\text{ EAT} = 11:00\text{ UTC}$), the UTC day captures the entire diurnal solar heating cycle without splitting across night.
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

2. **Hosking (1990) GLO Parameterization & Support Boundaries:**
   * Parameter vector: location $\xi \in \mathbb{R}$, scale $\alpha > 0$, shape $k \in \mathbb{R}$.
   * **Sample L-Moments:** Computed via unbiased sample PWM estimators:
     $$b_r = \frac{1}{n} \sum_{i=1}^n \frac{\binom{i-1}{r}}{\binom{n-1}{r}} x_{(i)}$$
     $$l_1 = b_0, \quad l_2 = 2b_1 - b_0, \quad l_3 = 6b_2 - 6b_1 + b_0, \quad t_3 = \frac{l_3}{l_2}$$
   * **Parameter Estimation:**
     $$k = -t_3$$
     $$\alpha = \frac{l_2 \sin(\pi k)}{\pi k} \quad (\text{for } k \ne 0, \text{ with limit } \alpha = l_2 \text{ as } k \to 0)$$
     $$\xi = l_1 - \frac{\alpha}{k}\left(1 - \frac{\pi k}{\sin(\pi k)}\right)$$
   * **Support Condition:** $1 - \frac{k(x - \xi)}{\alpha} > 0$.
     * If $k > 0$: $x < \xi + \alpha/k$ (upper bounded; $F(x) = 1.0$ for $x \ge \xi + \alpha/k$).
     * If $k < 0$: $x > \xi + \alpha/k$ (lower bounded; $F(x) = 0.0$ for $x \le \xi + \alpha/k$).
     * If $k = 0$: Support on $(-\infty, +\infty)$, evaluated via the exact logistic limit:
       $$F(x) = \frac{1}{1 + e^{-(x - \xi)/\alpha}}, \quad x(F) = \xi - \alpha \ln\left(\frac{1 - F}{F}\right)$$
   * **Cumulative Distribution Function (CDF):**
     $$F(x) = \frac{1}{1 + \left(1 - \frac{k(x - \xi)}{\alpha}\right)^{1/k}} \quad (\text{for } k \ne 0 \text{ within support})$$

3. **Gamma SPI-3 Formulation (Thom Shape Approximation):**
   * For cumulative 3-month precipitation $x \ge 0$:
   * Let $q = \frac{n_{\text{zero}}}{n_{\text{total}}}$ be the empirical probability of zero precipitation.
   * On non-zero observations ($x > 0$), calculate $A = \ln(\bar{x}) - \frac{1}{m}\sum_{i=1}^m \ln(x_i)$.
   * Shape estimate using **Thom's (1958) approximation for Gamma shape estimation**:
     $$\hat{\alpha}_g = \frac{1 + \sqrt{1 + 4A/3}}{4A}, \quad \hat{\beta}_g = \frac{\bar{x}}{\hat{\alpha}_g}$$
   * Cumulative probability incorporating zeros:
     $$H(x) = q + (1 - q) G(x; \hat{\alpha}_g, \hat{\beta}_g)$$

4. **Standard Normal Transformation:**
   * $Z = \Phi^{-1}(H(x))$ via rational approximation / `scipy.special.ndtri`.
   * Unclipped mathematical precision preserved throughout scientific pipelines; clipping to $[-3.5, 3.5]$ is confined exclusively to visual display contracts.

### 3.2 Three Levels of Mathematical Evidence & Gate 2 Status

1. **Numerical Consistency:** Verified that CDF and quantile invert each other across all supports ($|F(x(F)) - F| < 10^{-10}$).
2. **Parameter Recovery:** Verified that unbiased sample L-moments recover synthetic parameters $(\xi, \alpha, k)$ within documented Monte Carlo error.
3. **Independent Reference Agreement:** Python implementation matches values generated by R version 4.3.2, package `lmom` v2.9 functions (`pelglo`, `cdfglo`, `quaglo`) across 7 test cases in [`fixtures/r_spei_lmom_reference_benchmark.json`](drought_forecasting/tests/fixtures/r_spei_lmom_reference_benchmark.json) with $|F_{\text{py}} - F_{\text{ref}}| < 10^{-5}$.
4. **Enhanced Mathematical Verifications (8 Automated Tests in [`test_gate2_mathematical_benchmarks.py`](drought_forecasting/tests/test_gate2_mathematical_benchmarks.py)):**
   * `test_glo_support_boundaries_epsilon`: Verifies behavior immediately inside and outside finite support bounds within IEEE 754 float64 precision.
   * `test_glo_shape_approaching_zero`: Verifies continuity of GLO CDF as shape $k$ approaches zero from both positive ($k \to 0^+$) and negative ($k \to 0^-$) sides.
   * `test_glo_monotonicity_and_symmetric_fitting`: Verifies strict monotonicity ($\frac{dF}{dx} > 0$) within support and stable, finite parameter estimation on nearly symmetric samples.
* **Current Status:** `PASS — reported` (All 8 automated tests passing in 0.49s; marked as "reported" pending independent external audit of R session generation scripts and test logs).

---

## 4. Gate 3 — Spatial and Temporal Integrity Auditing

### 4.1 Reproducible Catchment Geometry & Spatial Weighting Formula

* **Boundary Dataset:** HydroBASINS African dataset version 1c (`hybas_af_lev05_v1c.shp`), Pfafstetter Level 5.
* **Constituent Sub-Basins (Exact Polygon IDs):**
  1. `HYBAS_ID: 1050648030` (Middle and Lower Tekezé, including the catchment outlet downstream of Humera at the Sudanese border, $\sim 14.28^\circ\text{N}, 36.55^\circ\text{E}$; `SUB_AREA` = $46,396.1\text{ km}^2$).
  2. `HYBAS_ID: 1050692800` (Eastern Upper Tekezé headwaters in Tigray / Amhara; `SUB_AREA` = $8,527.2\text{ km}^2$).
  3. `HYBAS_ID: 1050692900` (Southern Upper Tekezé headwaters in Wag Himra, Amhara; `SUB_AREA` = $12,212.1\text{ km}^2$).
* **Topological Operation:** Unary union:
  $$\mathcal{P}_{\text{Tekeze}} = \text{unary\_union}\left(\left[\mathcal{P}_{1050648030}, \mathcal{P}_{1050692800}, \mathcal{P}_{1050692900}\right]\right)$$
* **Catchment Area:** Total HydroBASINS attribute sum = $67,135.4\text{ km}^2$. Independent spherical excess area calculation in EPSG:4326 matches $67,135.4\text{ km}^2$ ($< 0.01\%$ difference).

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
  Calculating the rolling 3-month water balance for January 1991 ($t = \text{1991-01}$) requires climate observations from **November 1990 and December 1990**, even though Nov/Dec 1990 fall outside the 1991–2020 calibration period!
  Likewise, the final target month (December 2024) requires October and November 2024. The pipeline maintains the complete continuous 528-month climate series, selecting calibration samples by ending calendar month only when estimating distribution parameters.

### 5.2 Multi-Protocol 4-Tier Target Calibration Schema (Zero Leakage)

To guarantee that target construction strictly avoids information leakage and prevents conflation of different calibration baselines, the pipeline produces and stores four separate standardized series:

1. **Retrospective Climatological Target (`spei3_retro`):**
   * Calibrated over the declared 30-year WMO normal period (**1991–2020**; $N=30$ observations per calendar month).
   * Used exclusively for retrospective historical hazard analysis, decadal climatology, and long-term monitoring.
2. **Training-Era Target (`spei3_train`):**
   * Calibrated strictly using observations from the training split (**1981–2005**, $N=25$ observations per calendar month).
   * Quantifies historical drought severity on the training era with training-available information only.
3. **Validation Target (`spei3_validation`):**
   * Standardized across the validation split (**2006–2014**, $N=9$) using **FROZEN 1981–2005 distribution parameters**.
   * Under no circumstances are validation observations used to estimate distribution parameters.
4. **Primary Test Target (`spei3_test`):**
   * Standardized across the frozen holdout split (**2015–2024**, $N=10$) using **FROZEN 1981–2005 distribution parameters**.
   * Zero test observations are used in parameter fitting, ensuring a common mathematical scale between training and test holdouts.
5. **Auxiliary Sensitivity Target (`spei3_test_expanded_sensitivity`):**
   * An alternative test target standardized using parameters fitted on the expanded pre-test archive (**1981–2014**, $N=34$).
   * Maintained and reported strictly as a separately labelled sensitivity comparison to evaluate the trade-off between sample size ($N=25$ vs $N=34$) and temporal stationarity.

* **Parameter Uncertainty & Sample Size Reality ($N=25$):**
  Estimating a three-parameter Generalized Logistic distribution $(\xi, \alpha, k)$ from $N=25$ observations incurs shape parameter sampling variance. The pipeline computes parametric bootstrap standard errors for $(\xi, \alpha, k)$ and outputs them in target metadata.
* **Frozen Training-Calibration Parameter Rule:**
  The predictive forecasting models must strictly use the frozen training-calibration parameters (`spei3_train`, 1981–2005) to transform all validation (`spei3_validation`) and test (`spei3_test`) targets. The expanded calibration (`spei3_test_expanded_sensitivity`) is strictly an auxiliary sensitivity analysis, not a replacement test target chosen post-hoc after inspecting predictive skill.
* **Distribution Goodness-of-Fit Diagnostics:**
  For every calibration fold, the pipeline executes and records Kolmogorov-Smirnov (KS) test statistics and p-values alongside support boundary audits (boundary limits $\xi + \alpha/k$ and violation counts) to verify that the fitted GLO distribution adequately represents the month-specific water-balance samples.

### 5.3 Hargreaves–Samani PET & Radiative Formulation (FAO-56 Standard)

* **Physical Units and Equations:**
  In the conventional Hargreaves–Samani formulation (FAO-56 Eq. 52; Hargreaves & Samani 1985), extraterrestrial radiation $R_a$ is computed in energy units:
  $$R_a \quad [\text{MJ}\cdot\text{m}^{-2}\cdot\text{day}^{-1}]$$
  Converting energy into equivalent water depth evaporation requires multiplying by $\frac{1}{\lambda \rho_w} \approx 0.408 \text{ mm}/(\text{MJ}\cdot\text{m}^{-2})$ (where latent heat of vaporization $\lambda \approx 2.45\text{ MJ/kg}$):
  $$R_{a,\text{eq}} = 0.408 \cdot R_a \quad [\text{mm}\cdot\text{day}^{-1}]$$
  The daily reference evapotranspiration ($\text{PET}_d$) is therefore:
  $$\text{PET}_d = 0.0023 \times 0.408 \times R_{a,\text{MJ}} \times (T_{\text{mean}} + 17.8) \sqrt{T_{\max} - T_{\min}} \quad [\text{mm/day}]$$
  $$\equiv 0.0023 \times R_{a,\text{eq}} \times (T_{\text{mean}} + 17.8) \sqrt{T_{\max} - T_{\min}} \quad [\text{mm/day}]$$
  Where $0.0023 \times 0.408 = 0.0009384$.
* **Monthly Accumulation from Daily Extrema:**
  Monthly PET is accumulated as the exact sum of daily values:
  $$\text{PET}_{\text{month}} = \sum_{d=1}^{N_m} \text{PET}_{d} \quad [\text{mm/month}]$$
  This explicitly accounts for:
  1. Leap-year day counts ($N_m = 29$ days in February 1984, 1988, ..., 2024 vs $28$ days in non-leap years).
  2. Daily solar declination and astronomical radiation dynamics across the catchment.
  3. Strict input validity rejection: $T_{\max} < T_{\min}$ or non-finite inputs immediately return `NaN`.
* **Scientific Distinction: Reference Evapotranspiration ($\text{ET}_0$) vs Actual Evapotranspiration ($\text{ET}_a$):**
  Hargreaves–Samani estimates reference evapotranspiration ($\text{ET}_0$) of a hypothetical well-watered grass surface from ambient air temperature and extraterrestrial radiation. It does not measure actual catchment evapotranspiration ($\text{ET}_a$), which is heavily constrained by soil moisture depletion during semi-arid dry spells. The resulting climatic water balance $D = P - \text{ET}_0$ measures atmospheric evaporative demand vs precipitation supply. Before final drought severity interpretation, the pipeline evaluates SPEI sensitivity across alternative PET methods (Hargreaves vs Thornthwaite vs ERA5-Land Penman-Monteith).
* **Interpretation of Jensen's Inequality:**
  Because $f(u) = \sqrt{u}$ is strictly concave, $\mathbb{E}[\sqrt{\Delta T}] \le \sqrt{\mathbb{E}[\Delta T]}$. Summing daily PET avoids the positive bias introduced by evaluating monthly average diurnal range $\sqrt{\bar{T}_{\max} - \bar{T}_{\min}}$.

### 5.4 GLO Distribution Numerical Stability & Deliberate Endpoint Safeguards

Under Hosking (1990) Generalized Logistic distribution:
* **CDF Evaluation:** The cumulative distribution function $F(x) = \frac{1}{1 + (1 - k(x - \xi)/\alpha)^{1/k}}$ is evaluated directly in double precision without an arbitrary probability floor, returning the most accurate representable float in $[0.0, 1.0]$.
* **Normal-Score Transformation:** In IEEE 754 float64, extreme tail probabilities can round to exactly `0.0` or `1.0` near support boundaries. The transformation `compute_standardized_z_score` deliberately intercepts endpoints:
  * $p \le 0.0 \implies z = -5.0$, logged with `LOWER_ENDPOINT_SAFEGUARD`.
  * $p \ge 1.0 \implies z = +5.0$, logged with `UPPER_ENDPOINT_SAFEGUARD`.
  * Finite bounds $[-5.0, 5.0]$ prevent `ndtri(0)` or `ndtri(1)` from silently producing infinite ($\pm\infty$) drought indices.
* **Endpoint Event Tallying & Diagnostic Output:**
  The pipeline reports the exact occurrence count of lower-endpoint safeguards, upper-endpoint safeguards, and tail clamps across all splits (`safeguard_summary`). The raw non-exceedance probabilities $p_{\text{raw}}$ and safeguard audit flags are preserved alongside standardized z-scores.
* **Categorical Invariance of the Operational Cap:**
  Because all operational drought thresholds ($\text{SPEI-3} \le -1.0, -1.5, -2.0$) lie well within $[-5.0, +5.0]$, mapping extreme lower-tail probabilities to $-5.0$ (rather than evaluating an unbounded asymptotic normal tail score $z \approx -8.0$) has zero impact on categorical drought classification (mild, moderate, or severe). Drought classification is mathematically invariant to the safeguard.
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

### 6.2 Model Progression & Small-Sample Evaluation Rigor

1. **Predefined Drought Event Threshold:**
   * Declared in advance: $\text{SPEI-3}_{\text{eval}} \le -1.0$ represents moderate-or-worse drought.
2. **Baselines First (Fit on Training Data Only):**
   * Dynamic Climatology (monthly empirical distribution over 1981–2005).
   * Persistence ($\text{SPEI-3}_{\text{eval}}$ at issue date $t_0$).
   * Autoregressive (ARIMA / seasonal ARIMAX).
3. **Machine Learning Benchmarks:**
   * Regularized Linear / Ridge Regression.
   * Gradient Boosted Decision Trees (XGBoost).
   * Recurrent Neural Networks (LSTM / BiLSTM).
   * Spatiotemporal Architectures (CNN-LSTM, Fourier Neural Operator).
4. **Small-Sample Test Set Realities ($N=10$):**
   * The frozen test set (2015–2024) contains exactly **10 annual September forecasts**.
   * With only 10 cases, bootstrap confidence intervals are unstable, especially if few events cross the $\text{SPEI-3} \le -1.0$ threshold.
   * **Mandatory Reporting:** The pipeline must report the exact number of drought events and non-events alongside Brier Score ($BS$), Brier Skill Score ($\text{BSS}$), and CRPS.
   * **Uncertainty Qualification:** Use paired resampling procedures and explicitly label all uncertainty estimates as **exploratory**.
   * **Generalization Caveat:** A positive Brier Skill Score over ten years is encouraging preliminary evidence, but it is not strong evidence by itself that a model will generalize to other decades or non-stationary climate conditions.
5. **Frozen Holdout Discipline:**
   * Test set decisions remain strictly frozen; no hyperparameters, features, or thresholds may be tuned after inspecting test outcomes.
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
| **Gate 2** | Mathematical Implementation Cross-Validation | **PASS — reported** | Reproducible independent R `lmom` benchmark fixtures & 8 tests | [`docs/gate2_cross_language_mathematical_validation_report.md`](docs/gate2_cross_language_mathematical_validation_report.md) |
| **Gate 3** | Spatial and Temporal Integrity Auditing | **PASS — reported** | 528-month sequence & physical spatial weighting tests ($a_i$ in $\text{km}^2$) | [`docs/gate3_spatial_and_temporal_integrity_audit.md`](docs/gate3_spatial_and_temporal_integrity_audit.md) |
| **Gate 4** | Drought Target Reconstruction & Event Validation | **NOT RUN** | Dual-target SPEI-3 table, boundary audits, and event evaluation | [`docs/gate4_drought_indices_reconstruction_and_validation.md`](docs/gate4_drought_indices_reconstruction_and_validation.md) |
| **Gate 5** | Predictive Forecasting Model Formulation | **NOT RUN** | Out-of-sample Brier benchmarks on frozen test set & leakage audit | [`docs/gate5_predictive_model_architecture_and_leakage_audit.md`](docs/gate5_predictive_model_architecture_and_leakage_audit.md) |
| **Gate 6** | Operational AgriMinds Dashboard Interface | **NOT RUN** | Documented API, fail-safe UI, and telemetry | [`docs/gate6_agriminds_dashboard_interface_and_monitoring.md`](docs/gate6_agriminds_dashboard_interface_and_monitoring.md) |
