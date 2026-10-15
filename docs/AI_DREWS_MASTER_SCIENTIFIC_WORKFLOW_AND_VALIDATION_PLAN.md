# AI-DREWS: Master Scientific Workflow & Multi-Gate Validation Plan
## End-to-End Execution Blueprint for Tekezé Basin Drought Forecasting (1981–2024)

**Document ID:** `AI-DREWS-MASTER-PLAN-2026-10-REV7.1`  
**Reference Standards:** WMO-No. 100 Climatological Guidelines; Copernicus Climate Data Store (CDS); NOAA PSL THREDDS; R `lmom` v2.9 / `SPEI` v1.8.1; HydroBASINS (WWF / USGS)  
**Strategy Selection:** **Option A (ECMWF ERA5-Land Reanalysis Primary + NOAA CPC Global Gridded Temperature Independent Comparison)**  
**Overall Pipeline Status:** **HISTORICAL RECONSTRUCTION PAUSED PENDING COMPLETION OF GATE 1 INGESTION**  
**Gate Qualification Notice:** Gates 2 and 3 are retained as working specifications supported by 42 passing cross-validation tests, but are strictly qualified as **reported/provisional** pending complete raw archive ingestion, independent reference calculations, and end-to-end provenance audits.  
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
│  • Zero-shape Taylor series for scale alpha and location xi (|k| < 0.02)│
│  • Exact support bounds & float64 deliberate endpoint safeguards       │
│  • Independent R lmom v2.9 benchmark fixtures (7 test cases, 22 tests) │
│  • Parametric bootstrap goodness-of-fit refitting (Lilliefors/Stute)   │
│  • Hargreaves-Samani FAO-56 radiation units & direct benchmark tests   │
│  • Numerically stable log-CDF, log-survival & robust z-score engine    │
│  • Thom (1958) shape approximation for Gamma SPI-3 with zero treatment q│
│  • Status: PASS — reported (42 Tests Passing; External Empirical Audit Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 3: Spatial and Temporal Integrity Auditing                       │
│  • Independent HydroBASINS Lev 5 Catchment Topology (hybas_af_lev05_v1c)│
│  • Constituent IDs: 1050648030, 1050692800, 1050692900 (Humera outlet) │
│  • Pairwise disjoint interiors (0.00 km² overlap) & single valid polygon│
│  • Separate reporting: attribute sum 67,135.40 km² vs geodesic 67,135.57 km²│
│  • Explicit physical intersection area weights: a_i in km²             │
│  • 95% minimum spatial coverage rule: C_t = sum(v_i a_i) / sum(a_i)    │
│  • 1980 Pre-Period Buffer Reality: N=24 for Jan/Feb, N=25 for Mar–Dec  │
│  • Status: PASS — reported (Internal Suite Passing; External Audit Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 4: Reconstruct & Validate Drought Indices Target                 │
│  • Hargreaves-Samani (1985; FAO-56) daily extrema PET (MJ/m²/day units)│
│  • Empirical evaluation of daily vs monthly input non-linear covariance│
│  • 4-Tier Target Schema: spei3_retro, spei3_train, spei3_val, spei3_test│
│  • Frozen training parameters (1981–2005) applied to validation & test │
│  • Separate distribution calibration for each of 12 calendar months    │
│  • Historical drought event validation treated as testable hypotheses  │
│  • Status: NOT RUN (Explicitly Paused for Gate 1 Archive Ingestion)    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 5: Predictive Forecasting Model Formulation                      │
│  • Fixed seasonal target: September SPEI-3 (July–September Kiremt)     │
│  • Operational issue cutoff: June 1 00:00 UTC (May 31 information end) │
│  • Operational persistence baseline: April-ending SPEI-3 (data latency)│
│  • Frozen 10-year test holdout (2015–2024); strictly zero leakage      │
│  • Brier Score & CRPS evaluated against climatology & persistence      │
│  • Status: NOT RUN (Paused for Gates 1 & 4)                            │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 6: Operational Dashboard & Delivery Verification                 │
│  • Decoupled visualization: historical observed vs predictive layer    │
│  • Transparent risk categories, predictive intervals, failure states   │
│  • Automated data-refresh audits and monitoring                        │
│  • Status: NOT RUN (Architected & Specified)                           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Gate 1 — Climate Data Acquisition & Provenance Integrity

### 2.1 Strategy: Option A (ERA5-Land Primary + NOAA CPC Independent Comparison)

1. **ECMWF ERA5-Land Reanalysis (Primary Temperature Source):**
   * **Nature:** High-resolution numerical reanalysis produced by ECMWF combining model physics (HTESSEL land surface model) with atmospheric forcing; **not direct in-situ ground station observations**.
   * **Domain:** Tekezé Bounding Box $[15.0^\circ\text{N}, 35.5^\circ\text{E}, 11.5^\circ\text{N}, 40.0^\circ\text{E}]$.
   * **Resolution:** $0.1^\circ \times 0.1^\circ$ (~9 km native), hourly timesteps, 1981–2024.
   * **Extrema Derivation:** Ingests hourly 2 m temperature (`2m_temperature`) to derive daily $T_{\max, d} = \max_{h} T_{2\text{m}}(d, h)$ and $T_{\min, d} = \min_{h} T_{2\text{m}}(d, h)$.
   * **Unit Conversion:** Converted from Kelvin to Celsius via $T(^\circ\text{C}) = T(\text{K}) - 273.15$.
2. **NOAA CPC Global Unified Temperature (Independent Gridded Comparison):**
   * **Nature:** Gridded analysis product produced by NOAA CPC based on GTS daily station bulletins interpolated using Shepard's distance-weighting algorithm and CRU orography; **an independent gridded comparison dataset, not automatic in-situ ground truth**.
   * **Resolution:** $0.5^\circ \times 0.5^\circ$ (~55 km), daily $T_{\max}$ and $T_{\min}$ in $^\circ\text{C}$.
   * **Application:** Provides independent validation checks and spatial cross-comparison against ERA5-Land reanalysis.
   * **Non-Interchangeability:** ERA5-Land and CPC are distinct gridded products with different spatial resolutions, land-surface physics, and daily observation windows. They are maintained as separate feeds to quantify epistemic uncertainty rather than treated as interchangeable drop-in substitutes.

### 2.2 Forensic File Ingestion Audit & Dynamic Inventory Reconciliation

A comprehensive forensic audit of all raw climate data files currently on disk is documented in [`docs/gate1_raw_temperature_ingestion_audit_report.md`](docs/gate1_raw_temperature_ingestion_audit_report.md).

#### Reconciliation of CHIRPS Precipitation Holdings:
* **Master Study Period:** Full 1981–2024 historical period requires **528 continuous calendar months** (44 years $\times$ 12 months).
* **Inventory Reconciliation:**
  * Initially present: Exactly **168 monthly GeoTIFF files** (`data/raw/chirps_monthly/*.tif.gz`), representing 14 complete 12-month calendar years (`1984, 1987, 1991, 1994, 1997, 2000, 2002, 2009, 2011, 2015, 2018, 2020, 2023, 2024`).
  * Initial missing count: $528 - 168 = \mathbf{360\text{ missing months}}$.
  * Test download: 1 month (`chirps-v2.0.1981.01.tif.gz`) was downloaded and SHA-256 verified by `scripts/download_chirps_monthly_missing_1981_2024.py`, making 169 files currently present on disk.
  * Current missing count: $528 - 169 = \mathbf{359\text{ GeoTIFFs}}$ remaining to be downloaded.
  * **Dynamic Inventory Policy:** File counts must be recomputed dynamically from a month-by-month file inventory rather than hard-coded.
* **Forensic Ingestion Validation Rules:**
  Each downloaded file must pass five strict integrity checks before counting toward Gate 1:
  1. **Temporal Match:** Expected year and month must match the internal raster metadata and filename.
  2. **Archive Integrity:** Gzip archive must decompress without CRC errors.
  3. **Spatial Extent:** Raster bounding box must completely enclose the Tekezé catchment ($11.66^\circ\text{N}–14.80^\circ\text{N}, 35.86^\circ\text{E}–39.79^\circ\text{E}$).
  4. **Value Validity:** No uniform fields, all values finite floats with non-zero spatial variance within basin mask.
  5. **Deduplication:** Zero duplicate calendar months permitted.

### 2.3 Timezone & Daily Extrema Grouping Boundaries

1. **ERA5-Land Diurnal Grouping (Primary Standard: UTC Day):**
   * ERA5-Land records hourly temperatures in UTC. Local time is East Africa Time ($\text{EAT} = \text{UTC} + 3\text{h}$).
   * Daily extrema are calculated over $00:00\text{ UTC} - 23:00\text{ UTC}$ of date $d$, corresponding to $03:00\text{ EAT}(d)$ to $02:00\text{ EAT}(d+1)$.
   * Because diurnal minimum occurs near sunrise (~$06:00\text{ EAT} = 03:00\text{ UTC}$) and maximum occurs in early afternoon (~$14:00\text{ EAT} = 11:00\text{ UTC}$), the UTC day captures the entire diurnal solar heating cycle without splitting across night.
   * Local civil day ($00:00–23:00\text{ EAT}$, i.e. $21:00\text{ UTC}(d-1)$ to $20:00\text{ UTC}(d)$) is supported as an explicit sensitivity check.
2. **NOAA CPC Observation Window:**
   * NOAA CPC Global Daily Temperature compiles GTS reports over national meteorological observation windows (nominally $12:00\text{ UTC} - 12:00\text{ UTC}$, varying by reporting country).
   * CPC and ERA5-Land daily extrema represent distinct 24-hour observation windows and cannot be assumed to be identical to the second, though their monthly and seasonal averages converge.

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
   * **Zero-Shape Limit & Numerical Stability Expansion ($|k| < 0.02$):**
     Near $k=0$, direct evaluation of $(1 - \frac{\pi k}{\sin(\pi k)}) / k$ suffers catastrophic cancellation in double precision floating point. To ensure machine-precision numerical stability down to $k=0$, high-order Taylor series expansions are evaluated whenever $|k| < 0.02$:
     $$\alpha = l_2 \left(1 - \frac{\pi^2 k^2}{6} + \frac{\pi^4 k^4}{120} - \frac{\pi^6 k^6}{5040} + \frac{\pi^8 k^8}{362880}\right)$$
     $$\xi = l_1 + \alpha k \left(\frac{\pi^2}{6} + \frac{7\pi^4 k^2}{360} + \frac{31\pi^6 k^4}{15120} + \frac{127\pi^8 k^6}{604800}\right)$$
     This guarantees continuous differentiability and $< 10^{-15}$ error across the transition to $k=0$.
   * **Support Condition:** $1 - \frac{k(x - \xi)}{\alpha} > 0$.
     * If $k > 0$: $x < \xi + \alpha/k$ (upper bounded; $F(x) = 1.0$ for $x \ge \xi + \alpha/k$).
     * If $k < 0$: $x > \xi + \alpha/k$ (lower bounded; $F(x) = 0.0$ for $x \le \xi + \alpha/k$).
     * If $k = 0$: Support on $(-\infty, +\infty)$, evaluated via the exact logistic limit:
       $$F(x) = \frac{1}{1 + e^{-(x - \xi)/\alpha}}, \quad x(F) = \xi - \alpha \ln\left(\frac{1 - F}{F}\right)$$
   * **Quantile Function (quaglo):**
     $$x(F) = \xi + \frac{\alpha}{k}\left(1 - \left(\frac{1 - F}{F}\right)^k\right) \quad (\text{for } k \ne 0)$$
     For small $|k \ln((1-F)/F)| < 0.02$, series expansion of $(1 - u^k)/k$ guarantees numerical stability:
     $$x(F) = \xi - \alpha \ln u \left(1 + \frac{k \ln u}{2} + \frac{(k \ln u)^2}{6} + \frac{(k \ln u)^3}{24} + \frac{(k \ln u)^4}{120}\right)$$

3. **Gamma SPI-3 Formulation (Thom Shape Approximation):**
   * For cumulative 3-month precipitation $x \ge 0$:
   * Let $q = \frac{n_{\text{zero}}}{n_{\text{total}}}$ be the empirical probability of zero precipitation.
   * On non-zero observations ($x > 0$), calculate $A = \ln(\bar{x}) - \frac{1}{m}\sum_{i=1}^m \ln(x_i)$.
   * Thom (1958) MLE shape $\hat{\beta} = \frac{1 + \sqrt{1 + 4A/3}}{4A}$, scale $\hat{\alpha} = \frac{\bar{x}}{\hat{\beta}}$.
   * Non-exceedance probability: $H(x) = q + (1 - q) G(x; \hat{\alpha}, \hat{\beta})$.

### 3.2 Goodness-of-Fit Qualification: Parametric Bootstrap vs Asymptotic KS

* **Statistical Qualification:**
  Ordinary asymptotic Kolmogorov-Smirnov test p-values assume a known, pre-specified reference distribution. When distribution parameters $(\xi, \alpha, k)$ are estimated from the same sample (especially on small monthly calibration samples $N=24–25$), ordinary asymptotic p-values are uncalibrated (the classical Lilliefors / Stute complication).
* **Calibrated Parametric Bootstrap Protocol:**
  1. The Kolmogorov-Smirnov statistic $D_{\text{obs}} = \sup_x |F_n(x) - F_{\text{GLO}}(x; \hat{\xi}, \hat{\alpha}, \hat{k})|$ is retained as a descriptive measure of distance between empirical and theoretical distributions.
  2. A parametric bootstrap procedure ($B=200$ replicates) is executed: synthetic samples of size $N$ are drawn from $\text{GLO}(\hat{\xi}, \hat{\alpha}, \hat{k})$, parameters are refitted on each replicate using sample L-moments, and bootstrap test statistics $D^{*(b)}$ are computed against each replicate's own refitted distribution.
  3. The calibrated bootstrap p-value is computed as:
     $$p_{\text{boot}} = \frac{1}{B} \sum_{b=1}^B \mathbb{I}(D^{*(b)} \ge D_{\text{obs}})$$
  4. Q-Q diagnostics ($R^2$ correlation and maximum absolute quantile deviation) are evaluated and reported.

---

## 4. Gate 3 — Spatial and Temporal Integrity Auditing

### 4.1 Independent Catchment Topology & Area Verification

* **Constituent HydroBASINS Units (Africa Level 5 standard product `hybas_af_lev05_v1c.shp`):**
  1. `HYBAS_ID: 1050648030` (PFAF 17227; Middle & Lower Tekezé, `SUB_AREA` = $38,225.7\text{ km}^2$; basin outlet draining transboundary across Ethiopia-Sudan border).
  2. `HYBAS_ID: 1050692800` (PFAF 17228; Eastern Upper Tekezé headwaters, `SUB_AREA` = $7,592.7\text{ km}^2$; drains to `1050648030`).
  3. `HYBAS_ID: 1050692900` (PFAF 17229; Southern Upper Tekezé headwaters, `SUB_AREA` = $21,317.0\text{ km}^2$; drains to `1050648030`).

* **Topological Topology Audit:**
  * **Pairwise Disjoint Interiors:** All 3 constituent polygons share common boundaries along 1D line segments (MultiLineString contact), with intersection area $= \mathbf{0.00\text{ km}^2}$ (zero overlaps, zero gaps).
  * **Union Topology:** The topological union forms a single valid `Polygon` (not a disconnected MultiPolygon) with 1 exterior ring and **zero interior holes**.
  * **Area Reporting:**
    * Source `SUB_AREA` attribute sum: $\mathbf{67,135.40\text{ km}^2}$.
    * Independently calculated spherical geodesic union area (WGS84 authalic sphere, $R = 6,371.0088\text{ km}$): $\mathbf{67,135.57\text{ km}^2}$.
    * Absolute discrepancy: $\mathbf{0.1682\text{ km}^2}$ ($0.0003\%$).
    * Both values and their difference are maintained and reported as separate quantities.

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

---

## 5. Gate 4 — Reconstruct and Validate Drought Indices Target

### 5.1 1980 Pre-Period Buffer Reality & Month-Specific Calibration Sample Counts

* **Boundary Condition Requirement:**
  Calculating the rolling 3-month water balance for January 1981 requires climate observations from **November 1980 and December 1980**:
  $$D_{3,\text{Jan 1981}} = D_{\text{Nov 1980}} + D_{\text{Dec 1980}} + D_{\text{Jan 1981}}$$
  $$D_{3,\text{Feb 1981}} = D_{\text{Dec 1980}} + D_{\text{Jan 1981}} + D_{\text{Feb 1981}}$$
* **CHIRPS-2.0 Product Boundary Reality:**
  CHIRPS-2.0 precipitation data begins strictly in January 1981 (UCSB CHC data server returns `HTTP Error 404` for 1980). A pre-1981 precipitation buffer cannot be obtained from CHIRPS-2.0.
* **Zero Synthetic Fallback Policy:**
  Under the zero synthetic fallback rule, the first two rolling 3-month values in the 1981–2024 series are mathematically unavailable (`NaN`). Artificial backfilling, climatological substitution, or synthetic padding is strictly prohibited.
* **Exact Calibration Sample Counts (1981–2005 Training Baseline):**
  * Calendar Month 1 (January SPEI-3): $N = \mathbf{24\text{ valid observations}}$ (1982–2005).
  * Calendar Month 2 (February SPEI-3): $N = \mathbf{24\text{ valid observations}}$ (1982–2005).
  * Calendar Months 3 to 12 (March to December SPEI-3): $N = \mathbf{25\text{ valid observations}}$ (1981–2005).
  * **Primary Seasonal Forecast Target (September SPEI-3, Month 9):** Captures July, August, and September water balance. All 3 constituent months exist in 1981, yielding the full $N = \mathbf{25\text{ valid observations}}$ (1981–2005).

### 5.2 Multi-Protocol 4-Tier Target Calibration Schema (Zero Leakage)

To guarantee that target construction strictly avoids information leakage, four separate standardized series are produced and stored:

1. **Retrospective Climatological Target (`spei3_retro`):**
   * Calibrated over the declared 30-year WMO normal period (**1991–2020**; $N=30$ observations per calendar month).
   * Used exclusively for retrospective historical hazard analysis and decadal benchmarking.
2. **Training-Era Target (`spei3_train`):**
   * Calibrated strictly using observations from the training split (**1981–2005**, $N=24$ for Jan/Feb, $N=25$ for Mar–Dec).
   * Quantifies historical drought severity on the training era with training-available information only.
3. **Validation Target (`spei3_validation`):**
   * Standardized across the validation split (**2006–2014**, $N=9$) using **FROZEN 1981–2005 distribution parameters**.
   * Under no circumstances are validation observations used to estimate distribution parameters.
4. **Primary Test Target (`spei3_test`):**
   * Standardized across the frozen holdout split (**2015–2024**, $N=10$) using **FROZEN 1981–2005 distribution parameters**.
   * Zero test observations are used in parameter fitting, ensuring a common mathematical scale between training and test holdouts.
5. **Auxiliary Sensitivity Target (`spei3_test_expanded_sensitivity`):**
   * Standardized using parameters fitted on the expanded pre-test archive (**1981–2014**, $N=34$).
   * Maintained strictly as a separately labelled sensitivity comparison to evaluate the trade-off between sample size ($N=25$ vs $N=34$) and temporal stationarity.

### 5.3 Hargreaves–Samani PET & Non-Linear Daily Covariance

* **Physical Equations (FAO-56 Standard):**
  $$ET_{0,d} = 0.0023 \times 0.408 \times R_{a,\text{MJ}} \times (T_{\text{mean}} + 17.8) \sqrt{T_{\max} - T_{\min}} \quad [\text{mm/day}]$$
* **Interpretation of Daily Summation vs Monthly-Mean Inputs:**
  * Because $g(u) = \sqrt{u}$ is strictly concave, Jensen's inequality guarantees $\overline{\sqrt{\text{DTR}}} \le \sqrt{\overline{\text{DTR}}}$.
  * However, Jensen's inequality on the square-root term alone **does not establish the net direction of bias** in the complete Hargreaves–Samani equation.
  * In the full equation, daily radiation $R_a$, temperature $(T_{\text{mean}} + 17.8)$, and $\sqrt{\text{DTR}}$ covary synoptically across days within a month:
    $$\overline{R_a (T_{\text{mean}} + 17.8) \sqrt{\text{DTR}}} = \overline{R_a} \cdot \overline{(T_{\text{mean}} + 17.8)} \cdot \overline{\sqrt{\text{DTR}}} + \text{Covariance Terms}$$
  * Daily calculation preserves day-to-day joint variation in temperature, diurnal range, and extraterrestrial radiation.
  * The net empirical difference between daily summation and monthly-input calculation reflects the competition between concavity and synoptic covariance, and must be evaluated empirically for the Tekezé catchment rather than asserted a priori.

### 5.4 GLO Distribution Numerical Stability & Safeguard Qualification

* **CDF Evaluation:** The cumulative distribution function $F(x) = \frac{1}{1 + (1 - k(x - \xi)/\alpha)^{1/k}}$ is evaluated directly in double precision without an arbitrary probability floor, returning the most accurate representable float in $[0.0, 1.0]$.
* **Operational Safeguards vs Asymptotic Normal-Score:**
  * Mapping endpoint probabilities ($p \le 0 \mapsto z = -5.0$, $p \ge 1 \mapsto z = +5.0$) is an **operational safeguard**, not an exact normal-score transformation.
  * Exact log-scale transformations are implemented:
    $$\ln F(x) = -\text{logaddexp}\left(0, \frac{1}{k}\ln\left(1 - \frac{k(x - \xi)}{\alpha}\right)\right)$$
    $$\ln(1 - F(x)) = -\text{logaddexp}\left(0, -\frac{1}{k}\ln\left(1 - \frac{k(x - \xi)}{\alpha}\right)\right)$$
  * Combined with `scipy.special.ndtri_exp`, this evaluates uncapped asymptotic scores ($z < -5.0$ to $z \approx -10.8$) without underflow.
  * Categorical drought classification is **100% invariant** across all standard thresholds ($\text{SPEI} \le -1.0, -1.5, -2.0, -2.5$).

---

## 6. Gate 5 — Build and Evaluate Predictive Forecasting Models

### 6.1 Operational Forecast Task Formulation & Data Publication Latency

* **Target Index:** September-ending $\text{SPEI-3}_{\text{eval}}$ (capturing Kiremt seasonal moisture: July, August, September).
* **Operational Issue Date:** June 1.
* **Information Availability Cutoff:** Strictly **May 31 23:59 UTC**.
* **Operational Persistence Baseline:**
  * The persistence baseline is defined as the **latest eligible observed SPEI-3 value available by the June 1 issue cutoff**, accounting for verified product publication latency.
  * CHIRPS Final monthly precipitation is typically published 2–3 weeks after month-end. Therefore, on June 1, **April-ending SPEI-3** (covering February–April) is the latest verified quality-controlled SPEI-3 observation. If CHIRPS Preliminary for May is published by May 31, May SPEI-3 is recorded as preliminary.
  * The pipeline records the ending month and publication timestamp for each persistence baseline.
* **Separation of Leakage-Safe Predictor Cutoff and Target Definition:**
  1. *No Future Predictor Information:* Predictor features (including SST teleconnections ONI, DMI, TNA) are strictly limited to indices published on or before June 1 00:00 UTC.
  2. *Fixed Target Calibration:* The September SPEI-3 forecast target strictly uses the frozen 1981–2005 training calibration. Feature selection, preprocessing, and hyperparameter tuning must never inspect validation or test outcomes.

---

## 7. Master Gate Status & Acceptance Matrix

| Gate | Scope | Status | Acceptance Deliverable | Evidence Artifact |
|:---:|---|:---:|---|---|
| **Gate 1** | Climate Data Acquisition & Provenance | **PARTIAL** | Complete 1981–2024 ERA5-Land & CPC Ingestion & Manifest | [`docs/gate1_raw_temperature_ingestion_audit_report.md`](docs/gate1_raw_temperature_ingestion_audit_report.md) |
| **Gate 2** | Mathematical Implementation Cross-Validation | **PASS — reported** | GLO Taylor expansions, bootstrap KS p-values, R `lmom` fixtures (22 tests) | [`docs/gate2_cross_language_mathematical_validation_report.md`](docs/gate2_cross_language_mathematical_validation_report.md) |
| **Gate 3** | Spatial and Temporal Integrity Auditing | **PASS — reported** | Independent topology verification, buffer sample counts & 528-month sequence (9 tests) | [`docs/gate3_spatial_and_temporal_integrity_audit.md`](docs/gate3_spatial_and_temporal_integrity_audit.md) |
| **Gate 4** | Drought Target Reconstruction & Event Validation | **NOT RUN** | 4-Tier SPEI-3 table, boundary audits, and event evaluation | [`docs/gate4_drought_indices_reconstruction_and_validation.md`](docs/gate4_drought_indices_reconstruction_and_validation.md) |
| **Gate 5** | Predictive Forecasting Model Formulation | **NOT RUN** | Out-of-sample Brier benchmarks on frozen test set & latency-safe persistence | [`docs/gate5_predictive_model_architecture_and_leakage_audit.md`](docs/gate5_predictive_model_architecture_and_leakage_audit.md) |
| **Gate 6** | Operational AgriMinds Dashboard Interface | **NOT RUN** | Documented API, fail-safe UI, and telemetry | [`docs/gate6_agriminds_dashboard_interface_and_monitoring.md`](docs/gate6_agriminds_dashboard_interface_and_monitoring.md) |

---

## 8. Scientific Execution Checklist (REV7.1 Verification)

- [x] **1. CHIRPS Missing-File Count Reconciled:** Reconciled from initial inventory (168 present, 360 missing) to post-test state (169 present, 359 missing). Dynamic month-by-month inventory verified.
- [x] **2. 1980 Pre-Period Buffer Reality Documented:** Verified CHIRPS-2.0 returns HTTP 404 for 1980; rolling 3-month values are strictly `NaN` for Jan/Feb 1981, yielding $N=24$ for months 1 & 2, and $N=25$ for months 3–12 (including September target).
- [x] **3. Parametric Bootstrap Goodness-of-Fit Implemented:** Retained descriptive KS statistic; implemented $B=200$ parametric bootstrap refitting (Lilliefors / Stute procedure) and Q-Q diagnostics ($R^2 > 0.95$).
- [x] **4. Jensen's Inequality PET Claim Corrected:** Removed directional bias assertion based solely on $\sqrt{\text{DTR}}$ concavity; explained synoptic covariance $\text{Cov}(R_a, T_{\text{mean}}+17.8, \sqrt{\text{DTR}})$ and empirical assessment requirement.
- [x] **5. Zero-Shape Taylor Series Implemented:** Implemented 8th-order Taylor series for scale $\alpha$ and location $\xi$ when $|k| < 0.02$, eliminating catastrophic cancellation in $\xi$. Added unit tests across small shapes down to $k=0.0$.
- [x] **6. Operational Persistence Baseline Formalized:** Defined persistence as the latest eligible observed SPEI-3 available by June 1 cutoff considering verified data publication latency (April-ending SPEI-3 for finalized CHIRPS).
- [x] **7. Catchment Topology & Area Verified:** Verified HydroBASINS Level 5 Africa source polygons (`1050648030`, `1050692800`, `1050692900`), pairwise disjoint interiors ($0.00\text{ km}^2$ overlap), single valid polygon, and reported attribute sum ($67,135.40\text{ km}^2$) vs spherical geodesic area ($67,135.57\text{ km}^2$, $0.0003\%$ diff).
- [x] **8. Gate Status Discipline Enforced:** Gates 2 and 3 kept as reported/provisional with 42 passing tests; Gate 1 kept as PARTIAL; Gate 4 strictly paused.
