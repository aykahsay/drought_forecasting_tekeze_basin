# AI-DREWS: Master Scientific Workflow & Multi-Gate Validation Plan
## End-to-End Execution Blueprint for Tekezé Basin Drought Forecasting (1981–2024)

**Document ID:** `AI-DREWS-MASTER-PLAN-2026-10-REV7.2`  
**Reference Standards:** WMO-No. 100 Climatological Guidelines; Copernicus Climate Data Store (CDS); NOAA PSL THREDDS; R `lmom` v2.9 / `SPEI` v1.8.1; HydroBASINS (WWF / USGS) Level 5 Africa standard product  
**Strategy Selection:** **Option A (ECMWF ERA5-Land Reanalysis Primary + NOAA CPC Global Gridded Temperature Independent Comparison)**  
**Overall Pipeline Status:** **HISTORICAL RECONSTRUCTION PAUSED PENDING COMPLETION OF GATE 1 INGESTION**  
**Gate Qualification Notice:** Gates 2 and 3 are retained as working specifications supported by 45 passing cross-validation tests across 3 automated test suites, but are strictly qualified as **reported/provisional** pending complete raw archive ingestion, independent reference calculations, and end-to-end provenance audits.  
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
│  • Zero-shape Taylor series numerically stable approximation (|k| < 0.02)│
│  • Accuracy qualified via 60-digit Decimal analytical grid benchmark   │
│  • Exact support bounds & float64 deliberate endpoint safeguards       │
│  • Independent R lmom v2.9 benchmark fixtures (7 test cases, 25 tests) │
│  • Parametric-bootstrap-calibrated KS test with parameter refitting    │
│  • Finite-simulation correction (Davison & Hinkley 1997) & Monte Carlo SE│
│  • Hargreaves-Samani FAO-56 radiation units & direct benchmark tests   │
│  • Numerically stable log-CDF, log-survival & robust z-score engine    │
│  • Thom (1958) shape approximation for Gamma SPI-3 with edge-case guards│
│  • Status: PASS — reported (45 Tests Passing; External Empirical Audit Pending)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 3: Spatial and Temporal Integrity Auditing                       │
│  • HydroBASINS Lev 5 Catchment Topology (hybas_af_lev05_v1c.shp)       │
│  • Constituent IDs: 1050648030 (38,225.7 km²), 1050692800 (7,592.7 km²),│
│    1050692900 (21,317.0 km²); reconciled from earlier draft numbers    │
│  • Hydrological topology: 1050692800 & 1050692900 drain to 1050648030  │
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
│  • Explicit missing-value propagation & failure flags across 528 months │
│  • Empirical distribution reporting for September target under frozen params│
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
│  • Issue metadata table: release timestamp, verified latency, product status│
│  • Retrospective latency simulation vs genuine historical replay audit │
│  • Frozen 10-year test holdout (2015–2024); event counts, Brier score, │
│    Brier skill score, CRPS, and uncertainty reporting                  │
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

A comprehensive forensic audit of all raw climate data files currently on disk is documented in [`docs/gate1_raw_temperature_ingestion_audit_report.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate1_raw_temperature_ingestion_audit_report.md).

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

3. **Zero-Shape Limit & Numerical Accuracy Qualification ($|k| < 0.02$):**
   * Near $k=0$, direct evaluation of $(1 - \frac{\pi k}{\sin(\pi k)}) / k$ suffers catastrophic cancellation in double precision floating point.
   * To ensure numerical stability, high-order Taylor series approximations are evaluated whenever $|k| < 0.02$:
     $$\alpha = l_2 \left(1 - \frac{\pi^2 k^2}{6} + \frac{\pi^4 k^4}{120} - \frac{\pi^6 k^6}{5040} + \frac{\pi^8 k^8}{362880}\right)$$
     $$\xi = l_1 + \alpha k \left(\frac{\pi^2}{6} + \frac{7\pi^4 k^2}{360} + \frac{31\pi^6 k^4}{15120} + \frac{127\pi^8 k^6}{604800}\right)$$
   * **Qualification of Accuracy (REV7.2 Standard):**
     * Rather than claiming an unconditional $10^{-15}$ absolute error bound across arbitrary scales, the series is qualified as a **numerically stable polynomial approximation** whose accuracy is verified through comparison against 60-digit `Decimal` analytical calculations across a comprehensive test grid in [`test_glo_taylor_high_precision_grid_and_boundary_continuity`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/test_gate2_mathematical_benchmarks.py).
     * **Grid Verification:** Tested at $k = 0$ (exact logistic limit), $k = \pm 10^{-12}, \pm 10^{-8}, \pm 10^{-4}$, and boundary values $k = \pm 0.019999$ and $k = \pm 0.020001$ across diverse moment scales ($(l_1, l_2) = (0, 1), (10, 25), (-50, 100)$).
     * Relative parameter agreement with 60-digit exact calculations is $< 10^{-10}$ across all scales.
     * **Boundary Continuity:** Across the switching boundary $k = 0.02$, parameter steps are continuous within $\Delta \xi < 10^{-4}$ and $\Delta \alpha < 10^{-5}$.
     * The switching threshold ($|k| = 0.02$) is documented as an **implementation choice**, not a mathematical constant.
   * **Support Condition:** $1 - \frac{k(x - \xi)}{\alpha} > 0$.
     * If $k > 0$: $x < \xi + \alpha/k$ (upper bounded; $F(x) = 1.0$ for $x \ge \xi + \alpha/k$).
     * If $k < 0$: $x > \xi + \alpha/k$ (lower bounded; $F(x) = 0.0$ for $x \le \xi + \alpha/k$).
     * If $k = 0$: Support on $(-\infty, +\infty)$, evaluated via the exact logistic limit:
       $$F(x) = \frac{1}{1 + e^{-(x - \xi)/\alpha}}, \quad x(F) = \xi - \alpha \ln\left(\frac{1 - F}{F}\right)$$
   * **Quantile Function (quaglo):**
     $$x(F) = \xi + \frac{\alpha}{k}\left(1 - \left(\frac{1 - F}{F}\right)^k\right) \quad (\text{for } k \ne 0)$$
     For small $|k \ln((1-F)/F)| < 0.02$, series expansion of $(1 - u^k)/k$ guarantees numerical stability:
     $$x(F) = \xi - \alpha \ln u \left(1 + \frac{k \ln u}{2} + \frac{(k \ln u)^2}{6} + \frac{(k \ln u)^3}{24} + \frac{(k \ln u)^4}{120}\right)$$

4. **Gamma SPI-3 Formulation (Thom Shape Approximation) & Edge-Case Safeguards:**
   * For cumulative 3-month precipitation $x \ge 0$:
   * Let $q = \frac{n_{\text{zero}}}{n_{\text{total}}}$ be the empirical probability of zero precipitation. The zero probability is estimated strictly for the corresponding calendar-ending month, not from an unrelated annual or pooled sample.
   * On non-zero observations ($x > 0$), calculate $A = \ln(\bar{x}) - \frac{1}{m}\sum_{i=1}^m \ln(x_i)$.
   * Thom (1958) MLE shape $\hat{\beta} = \frac{1 + \sqrt{1 + 4A/3}}{4A}$, scale $\hat{\alpha} = \frac{\bar{x}}{\hat{\beta}}$.
   * Non-exceedance probability: $H(x) = q + (1 - q) G(x; \hat{\alpha}, \hat{\beta})$.
   * **Explicit Edge-Case Safeguards (REV7.2 Specification):**
     The implementation strictly raises explicit `ValueError` fit-failure flags rather than silently returning an uncalibrated drought score in the following edge cases:
     1. **Degenerate all-zeros ($q = 1.0$):** Raises `ValueError` ("Degenerate sample: 100% of observations are zero precipitation").
     2. **Zero or near-zero variance ($A \le 10^{-12}$):** If positive observations are identical, Thom MLE fails; raises `ValueError`.
     3. **Small sample size ($N < 20$):** Insufficient sample size raises `ValueError`.
     4. **Small positive sample ($m < 10$):** Fewer than 10 positive rain observations raises `ValueError`.
     5. **Negative values:** Physical violation $x < 0$ raises `ValueError`.
     6. **Non-finite values or parameters:** Non-finite inputs or parameters produce `NaN` outputs in CDF evaluation.
     * Fully tested in [`test_gamma_spi_edge_cases_and_fit_failures`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/test_gate2_mathematical_benchmarks.py).

### 3.2 Goodness-of-Fit Qualification: Parametric Bootstrap vs Asymptotic KS

* **Statistical Qualification:**
  Ordinary asymptotic Kolmogorov-Smirnov test p-values assume a known, pre-specified reference distribution. When distribution parameters $(\xi, \alpha, k)$ are estimated from the same sample (especially on small monthly calibration samples $N=24–25$), ordinary asymptotic p-values are uncalibrated (the classical Lilliefors / Stute complication).
* **Calibrated Parametric Bootstrap Protocol (REV7.2 Standard):**
  1. The Kolmogorov-Smirnov statistic $D_{\text{obs}} = \sup_x |F_n(x) - F_{\text{GLO}}(x; \hat{\xi}, \hat{\alpha}, \hat{k})|$ is retained as a descriptive measure of distance between empirical and theoretical distributions.
  2. A **parametric-bootstrap-calibrated KS test with parameter refitting** is executed: synthetic samples of size $N$ are drawn from $\text{GLO}(\hat{\xi}, \hat{\alpha}, \hat{k})$, parameters are refitted on each replicate using sample L-moments, and bootstrap test statistics $D^{*(b)}$ are computed against each replicate's own refitted distribution.
  3. **Finite-Simulation Correction (Davison & Hinkley 1997):**
     $$p_{\text{boot}} = \frac{1 + \sum_{b=1}^B \mathbb{I}(D^{*(b)} \ge D_{\text{obs}})}{B + 1}$$
     This avoids reporting a zero Monte Carlo p-value simply because none of the simulated statistics exceeded the observed statistic.
  4. **Replicate Count & Monte Carlo Uncertainty:**
     * For unit tests and rapid pipeline integration checks, $B=100–200$ replicates are used.
     * For final reported scientific and inferential analyses, $B = \mathbf{2,000\text{ to }5,000}$ replicates are required with a fixed random seed.
     * The Monte Carlo standard error is explicitly computed and documented:
       $$\text{SE}(p_{\text{boot}}) = \sqrt{\frac{p_{\text{boot}}(1 - p_{\text{boot}})}{B}}$$
  5. **Comprehensive Diagnostics (Beyond Stand-Alone Q-Q $R^2$):**
     * Q-Q correlation $R^2 > 0.95$ is **not used as a stand-alone goodness-of-fit criterion**, because high correlation can coexist with systematic tail misfits.
     * The evaluation suite reports Q-Q plots, Blom plotting position probability plots, maximum absolute quantile deviation ($\max |x_{(i)} - x(p_i)|$), and tail-focused diagnostics alongside the bootstrap test.
  6. **Small-Sample Non-Uniqueness Caveat:**
     * A non-significant goodness-of-fit result ($p_{\text{boot}} > 0.05$) on $N=24–25$ monthly observations does not establish that GLO is the uniquely correct distribution; it indicates only that the test did not detect sufficient evidence against GLO at the 5% significance level. This epistemic uncertainty is explicitly factored into downstream drought severity reporting.

---

## 4. Gate 3 — Spatial and Temporal Integrity Auditing

### 4.1 Catchment Topology, Component Area Reconciliation & Source Provenance

#### Authoritative Source Archive & Provenance:
* **Product:** HydroBASINS Africa Level 5 standard product (without lakes, customized Pfafstetter).
* **Source Archive:** `hybas_af_lev05_v1c.zip` (SHA-256: `81387c1bb25b918e2299debeffe15dbf446f280acaff18c1f2a2db01211ab82e`).
* **Source Shapefile:** `data/spatial/extracted/hybas_af_lev05/hybas_af_lev05_v1c.shp` (SHA-256: `dc30e92b971433559620cc60715128a96e73886d497e68c348c589a5adfb4811`).
* **Download Source:** HydroSHEDS project / WWF / USGS (`https://data.hydrosheds.org/file/hydrobasins/standard/hybas_af_lev05_v1c.zip`).
* **Coordinate Reference System:** EPSG:4326 (WGS 84 geographic 2D).
* **Spherical Area Algorithm:** Girard's Theorem / Spherical Excess on WGS 84 authalic sphere ($R = 6,371.0088\text{ km}$).

#### Reconciliation of Earlier Project Plan Draft Areas:
A discrepancy existed between component sub-basin areas reported in early working drafts and those in REV7.1/REV7.2. The origin and resolution are fully documented below:

| HydroBASINS ID | Pfafstetter ID | Sub-Basin Description | Earlier Working Draft | Authoritative Shapefile `SUB_AREA` | Independently Calculated Spherical Area | Agreement Status |
|:---:|:---:|---|:---:|:---:|:---:|:---:|
| `1050648030` | 17227 | Middle & Lower Tekezé (Outlet) | $46,396.1\text{ km}^2$ | $\mathbf{38,225.70\text{ km}^2}$ | $\mathbf{38,225.81\text{ km}^2}$ | Reconciled ($\Delta = 0.11\text{ km}^2$, $0.0003\%$) |
| `1050692800` | 17228 | Eastern Upper Tekezé (Headwaters) | $8,527.2\text{ km}^2$ | $\mathbf{7,592.70\text{ km}^2}$ | $\mathbf{7,592.68\text{ km}^2}$ | Reconciled ($\Delta = 0.02\text{ km}^2$, $0.0002\%$) |
| `1050692900` | 17229 | Southern Upper Tekezé (Headwaters) | $12,212.1\text{ km}^2$ | $\mathbf{21,317.00\text{ km}^2}$ | $\mathbf{21,317.07\text{ km}^2}$ | Reconciled ($\Delta = 0.07\text{ km}^2$, $0.0003\%$) |
| **Catchment Total** | — | **Tekezé Basin (Complete Catchment)** | $\mathbf{67,135.4\text{ km}^2}$ | $\mathbf{67,135.40\text{ km}^2}$ | $\mathbf{67,135.57\text{ km}^2}$ | **Reconciled ($\Delta = 0.1682\text{ km}^2$, $0.0003\%$)** |

* **Origin of Discrepancy:** The earlier draft numbers ($46,396.1, 8,527.2, 12,212.1\text{ km}^2$) originated from an early heuristic attempt in REV3/REV4 to match the nominal descriptive text "$46,396\text{ km}^2$" from a truncated single-polygon HDX shapefile (`data/spatial/extracted/tekeze_hdx/Tekeze Basin.shp`). Inspection of the authoritative HydroBASINS Level 5 DBF attributes demonstrates that the true sub-unit areas are $38,225.7, 7,592.7,$ and $21,317.0\text{ km}^2$. Every individual polygon matches independent spherical excess calculations within $0.0003\%$.
* **Hydrological Downstream Topology:**
  * Sub-basin `1050692800` (`NEXT_DOWN = 1050648030`): Upper East headwaters drain into the Lower Tekezé.
  * Sub-basin `1050692900` (`NEXT_DOWN = 1050648030`): Upper South headwaters drain into the Lower Tekezé.
  * Sub-basin `1050648030` (`NEXT_DOWN = 1050538700`): Lower Tekezé contains the basin outlet draining across the Ethiopian-Sudanese border into the downstream Atbara system (`1050538700`).
* **Topological Rigor:**
  * **Pairwise Disjoint Interiors:** Pairwise intersections of all three polygons yield 1D MultiLineString contact along shared boundaries, with intersection area $= \mathbf{0.00\text{ km}^2}$ (zero internal overlapping area).
  * **Zero Gaps & Single Valid Polygon:** The topological unary union forms a single valid `Polygon` with 1 exterior ring and **zero interior holes**, confirming zero spatial gaps.

### 4.2 Spatial Aggregation Formulation (Physical Intersection Area)
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

### 5.1 1980 Pre-Period Buffer Reality, Missing-Value Propagation & Calibration Counts

* **Boundary Condition Requirement:**
  Calculating the rolling 3-month water balance for January 1981 requires climate observations from **November 1980 and December 1980**:
  $$D_{3,\text{Jan 1981}} = D_{\text{Nov 1980}} + D_{\text{Dec 1980}} + D_{\text{Jan 1981}}$$
  $$D_{3,\text{Feb 1981}} = D_{\text{Dec 1980}} + D_{\text{Jan 1981}} + D_{\text{Feb 1981}}$$
* **CHIRPS-2.0 Product Boundary Reality:**
  CHIRPS-2.0 precipitation data begins strictly in January 1981 (UCSB CHC data server returns `HTTP Error 404` for 1980). A pre-1981 precipitation buffer cannot be obtained from CHIRPS-2.0.
* **Zero Synthetic Fallback Policy:**
  Under the zero synthetic fallback rule, the first two rolling 3-month values in the 1981–2024 series are mathematically unavailable (`NaN`). Artificial backfilling, climatological substitution, or synthetic padding is strictly prohibited.
* **Explicit Missing-Value Propagation Across the 528-Month Archive:**
  * The monthly climate archive contains **528 calendar months**.
  * The rolling 3-month water-balance sequence contains 2 unavailable values at the start (`1981-01` and `1981-02`).
  * The standardized drought target table preserves every calendar month, including explicit boolean validity (`is_valid`) and failure diagnostic flags (`failure_reason: "PRE_PERIOD_BUFFER_MISSING"`).
  * A 528-row table never implies 528 valid drought scores.
* **Exact Calibration Sample Counts (1981–2005 Training Baseline):**
  * Calendar Month 1 (January SPEI-3): $N = \mathbf{24\text{ valid observations}}$ (1982–2005).
  * Calendar Month 2 (February SPEI-3): $N = \mathbf{24\text{ valid observations}}$ (1982–2005).
  * Calendar Months 3 to 12 (March to December SPEI-3): $N = \mathbf{25\text{ valid observations}}$ (1981–2005).
  * **Primary Seasonal Forecast Target (September SPEI-3, Month 9):** Captures July, August, and September water balance. All 3 constituent months exist in 1981, yielding the full $N = \mathbf{25\text{ valid observations}}$ (1981–2005).

### 5.2 Target Scale Validation & September SPEI-3 Empirical Distribution Reporting

Before evaluating any machine learning models in Gate 5, the empirical scale of the September-ending SPEI-3 target under the frozen 1981–2005 training calibration must be evaluated and reported. The Gate 4 completion report must explicitly present:
1. **Valid Training Sample Size:** Exact count of valid observations ($N=25$).
2. **Fitted Distribution Parameters:** Location $\hat{\xi}$, scale $\hat{\alpha}$, shape $\hat{k}$, and analytical support boundary ($\hat{\xi} + \hat{\alpha}/\hat{k}$).
3. **Goodness-of-Fit Diagnostics:** Descriptive KS statistic $D_{\text{obs}}$, parametric-bootstrap p-value $p_{\text{boot}}$, Monte Carlo standard error $\text{SE}(p)$, and maximum absolute quantile deviation.
4. **Endpoint Safeguard Incidences:** Count of training observations mapped through operational safeguards or support bounds.
5. **Categorical Event Counts:** Number of drought events ($\text{SPEI} \le -1.0, -1.5, -2.0$) and non-drought events across the training period.
6. **Sensitivity Comparison:** Target sensitivity under alternative pre-test calibration (1981–2014, $N=34$).

### 5.3 Multi-Protocol 4-Tier Target Calibration Schema (Zero Leakage)

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

### 5.4 Hargreaves–Samani PET & Non-Linear Daily Covariance

* **Physical Equations (FAO-56 Standard):**
  $$ET_{0,d} = 0.0023 \times 0.408 \times R_{a,\text{MJ}} \times (T_{\text{mean}} + 17.8) \sqrt{T_{\max} - T_{\min}} \quad [\text{mm/day}]$$
* **Interpretation of Daily Summation vs Monthly-Mean Inputs:**
  * Because $g(u) = \sqrt{u}$ is strictly concave, Jensen's inequality guarantees $\overline{\sqrt{\text{DTR}}} \le \sqrt{\overline{\text{DTR}}}$.
  * However, Jensen's inequality on the square-root term alone **does not establish the net direction of bias** in the complete Hargreaves–Samani equation.
  * In the full equation, daily radiation $R_a$, temperature $(T_{\text{mean}} + 17.8)$, and $\sqrt{\text{DTR}}$ covary synoptically across days within a month:
    $$\overline{R_a (T_{\text{mean}} + 17.8) \sqrt{\text{DTR}}} = \overline{R_a} \cdot \overline{(T_{\text{mean}} + 17.8)} \cdot \overline{\sqrt{\text{DTR}}} + \text{Covariance Terms}$$
  * Daily calculation preserves day-to-day joint variation in temperature, diurnal range, and extraterrestrial radiation.
  * The net empirical difference between daily summation and monthly-input calculation reflects the competition between concavity and synoptic covariance, and must be evaluated empirically for the Tekezé catchment rather than asserted a priori.

### 5.5 GLO Numerical Stability & Drought Classification Invariance Clarification

* **CDF Evaluation:** The cumulative distribution function $F(x) = \frac{1}{1 + (1 - k(x - \xi)/\alpha)^{1/k}}$ is evaluated directly in double precision without an arbitrary probability floor, returning the most accurate representable float in $[0.0, 1.0]$.
* **Operational Safeguards vs Asymptotic Normal-Score:**
  * Mapping endpoint probabilities ($p \le 0 \mapsto z = -5.0$, $p \ge 1 \mapsto z = +5.0$) is an **operational safeguard**, not an exact representation of the underlying tail.
  * Exact log-scale transformations are implemented:
    $$\ln F(x) = -\text{logaddexp}\left(0, \frac{1}{k}\ln\left(1 - \frac{k(x - \xi)}{\alpha}\right)\right)$$
    $$\ln(1 - F(x)) = -\text{logaddexp}\left(0, -\frac{1}{k}\ln\left(1 - \frac{k(x - \xi)}{\alpha}\right)\right)$$
  * Combined with `scipy.special.ndtri_exp`, this evaluates uncapped asymptotic scores ($z < -5.0$ to $z \approx -10.8$) without underflow.
  * **Numerical-Safeguard Sensitivity (REV7.2 Clarification):**
    Drought classifications were identical between the specified transformation implementations (standard operational $\pm 5.0$ cap vs uncapped robust log-transformation) at thresholds $-1.0, -1.5, -2.0,$ and $-2.5$. This result applies strictly to the tested observations and implementations (zero classification discrepancies across evaluated sample points), confirming that the operational cap does not distort categorical drought assignment on the empirical range of Tekezé water balances.
  * **Primary Transformation Policy:** Robust log-CDF and log-survival calculations are utilized as the primary transformation wherever numerically valid; the endpoint safeguard ($z = \pm 5.0$) is reserved exclusively for cases where the input genuinely violates the distribution support bounds or exceeds floating-point representable ranges.

---

## 6. Gate 5 — Build and Evaluate Predictive Forecasting Models

### 6.1 Operational Forecast Task Formulation, Data Latency & Metadata Table

* **Target Index:** September-ending $\text{SPEI-3}_{\text{eval}}$ (capturing Kiremt seasonal moisture: July, August, September).
* **Operational Issue Date:** June 1, 00:00 UTC.
* **Information Availability Cutoff:** Strictly **May 31, 23:59 UTC**.
* **Operational Persistence Baseline:**
  * The persistence baseline is defined as the **latest eligible observed SPEI-3 value available by the June 1 issue cutoff**, accounting for verified product publication latency.
  * CHIRPS Final monthly precipitation is typically published 2–3 weeks after month-end. Therefore, on June 1, **April-ending SPEI-3** (covering February–April) is the latest verified quality-controlled SPEI-3 observation. If CHIRPS Preliminary for May is published by May 31, May SPEI-3 is recorded as preliminary.
* **Forecast Issue Metadata Table (REV7.2 Standard):**
  For each operational forecast issue, an explicit metadata record is populated:

| Field | Required Operational Specification | Historical Retrospective Status |
|---|---|---|
| **Issue Timestamp** | June 1, 00:00 UTC | Declared operational release boundary |
| **Information Cutoff** | May 31, 23:59 UTC | Strict cutoff for all predictor feeds |
| **Latest Eligible Precipitation Month** | April (Final) / May (Preliminary, if verified) | Verified from archive availability timestamp |
| **SPEI-3 Ending Month** | April 30 (February–April rolling triad) | Explicit month-end date |
| **Product Status** | CHIRPS Final / ERA5-Land Final | Documented data product tier |
| **Release Timestamp** | Actual verified UTC publication timestamp | Archived publication record |
| **Baseline Source** | Verified April-ending SPEI-3 value | Exact numerical baseline value |

* **Distinction: Retrospective Latency Simulation vs Historical Timestamp Replay:**
  * Where historical publication timestamps are unarchived, retrospective evaluations are explicitly documented as **retrospective simulations under an assumed 3-week publication latency rule**, rather than claimed as genuine real-time historical replays.
* **Holdout Evaluation Realities ($N=10$, 2015–2024):**
  * The frozen holdout split contains exactly **10 annual test cases** (2015–2024).
  * Reporting must include:
    1. Exact event and non-event counts at predeclared thresholds ($\text{SPEI} \le -1.0, -1.5$).
    2. Brier Score ($\text{BS}$) and Brier Skill Score ($\text{BSS}$) relative to climatology and persistence baselines.
    3. Continuous Ranked Probability Score ($\text{CRPS}$).
    4. Bootstrap standard error and uncertainty bounds, clearly qualified as exploratory given $N=10$.
  * Operational skill claims based on a single favorable metric or small-sample test set are strictly prohibited.

---

## 7. Master Gate Status & Acceptance Matrix

| Gate | Scope | Status | Acceptance Deliverable | Evidence Artifact |
|:---:|---|:---:|---|---|
| **Gate 1** | Climate Data Acquisition & Provenance | **PARTIAL** | Complete 1981–2024 ERA5-Land & CPC Ingestion & Manifest | [`docs/gate1_raw_temperature_ingestion_audit_report.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate1_raw_temperature_ingestion_audit_report.md) |
| **Gate 2** | Mathematical Implementation Cross-Validation | **PASS — reported** | GLO Taylor expansions, Decimal analytical grid, bootstrap KS finite correction, R `lmom` fixtures (25 tests) | [`docs/gate2_cross_language_mathematical_validation_report.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate2_cross_language_mathematical_validation_report.md) |
| **Gate 3** | Spatial and Temporal Integrity Auditing | **PASS — reported** | HydroBASINS component area reconciliation, topology verification, buffer sample counts & 528-month sequence (9 tests) | [`docs/gate3_spatial_and_temporal_integrity_audit.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate3_spatial_and_temporal_integrity_audit.md) |
| **Gate 4** | Drought Target Reconstruction & Event Validation | **NOT RUN** | 4-Tier SPEI-3 table, boundary audits, empirical scale report, and event evaluation | [`docs/gate4_drought_indices_reconstruction_and_validation.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate4_drought_indices_reconstruction_and_validation.md) |
| **Gate 5** | Predictive Forecasting Model Formulation | **NOT RUN** | Out-of-sample Brier benchmarks on frozen test set & latency-safe persistence | [`docs/gate5_predictive_model_architecture_and_leakage_audit.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate5_predictive_model_architecture_and_leakage_audit.md) |
| **Gate 6** | Operational AgriMinds Dashboard Interface | **NOT RUN** | Documented API, fail-safe UI, and telemetry | [`docs/gate6_agriminds_dashboard_interface_and_monitoring.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/gate6_agriminds_dashboard_interface_and_monitoring.md) |

---

## 8. Scientific Execution Checklist (REV7.2 Verification)

- [x] **1. CHIRPS Missing-File Count Reconciled:** Reconciled from initial inventory (168 present, 360 missing) to post-test state (169 present, 359 missing). Dynamic month-by-month inventory verified across all 528 months.
- [x] **2. HydroBASINS Component Areas Reconciled:** Reconciled earlier draft figures ($46,396.1, 8,527.2, 12,212.1\text{ km}^2$) against authoritative WWF / HydroSHEDS Level 5 Africa vectors ($38,225.7, 7,592.7, 21,317.0\text{ km}^2$, sum $67,135.40\text{ km}^2$, spherical union $67,135.57\text{ km}^2$). Source shapefile SHA-256 (`dc30e92b...`), zip SHA-256 (`81387c1b...`), WGS84 CRS, and Girard spherical excess verified.
- [x] **3. GLO Taylor Series Numerically Qualified:** Replaced absolute $10^{-15}$ claim with qualified numerical stability approximation backed by 60-digit `Decimal` calculations across test grid ($k=0, \pm 10^{-12}, \pm 10^{-8}, \pm 10^{-4}, \pm 0.019999, \pm 0.020001$), diverse moment pairs, and boundary continuity ($\Delta \xi < 10^{-4}, \Delta \alpha < 10^{-5}$).
- [x] **4. Parametric Bootstrap Goodness-of-Fit Refined:** Implemented Davison & Hinkley (1997) finite-simulation correction $p_{\text{boot}} = (1 + \sum \mathbb{I}) / (B + 1)$; documented requirement for $B=2,000–5,000$ with seed and Monte Carlo standard error $\text{SE}(p)$; removed Q-Q $R^2 > 0.95$ as stand-alone criterion; added small-sample non-uniqueness caveat.
- [x] **5. Gamma SPI Edge-Case Safeguards Implemented:** Added explicit `ValueError` raises for degenerate all-zeros ($q=1.0$), identical positive values ($A \le 10^{-12}$), small sample ($N<20, m<10$), negative values, and non-finite inputs/parameters.
- [x] **6. Drought Classification Invariance Phrasing Corrected:** Clarified that invariance refers strictly to numerical safeguard sensitivity (operational $\pm 5.0$ cap vs uncapped robust log-CDF yields zero classification discrepancies across evaluated observations).
- [x] **7. 1980 Pre-Period Buffer & Missing Value Propagation Formalized:** Documented $N=24$ for Jan/Feb and $N=25$ for Mar–Dec; required explicit validity flags (`is_valid`, `failure_reason`) across 528-month table; added empirical distribution reporting requirement for September forecast target under frozen parameters.
- [x] **8. Operational Forecast Issue Metadata Table Added:** Formalized issue table (issue timestamp, information cutoff, latest eligible precipitation month, SPEI-3 ending month, product status, release timestamp, baseline source); distinguished assumed latency simulation from genuine historical replay; noted $N=10$ holdout reporting requirements.
- [x] **9. Test Suite Suite Expanded:** 45 passing cross-validation tests across Gate 2 (25 tests), Gate 3 (9 tests), and climate reconstruction (11 tests).
- [x] **10. Gate Status Discipline Enforced:** Gates 2 and 3 kept as reported/provisional with 45 passing tests; Gate 1 kept as PARTIAL; Gate 4 strictly paused.
