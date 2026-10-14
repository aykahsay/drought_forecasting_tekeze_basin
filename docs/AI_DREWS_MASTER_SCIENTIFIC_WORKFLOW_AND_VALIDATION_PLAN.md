# AI-DREWS: Master Scientific Workflow & Multi-Gate Validation Plan
## End-to-End Execution Blueprint for Tekezé Basin Drought Forecasting (1981–2024)

**Document ID:** `AI-DREWS-MASTER-PLAN-2026-10`  
**Standard:** WMO-No. 100 / Copernicus CDS / NOAA PSL / R lmom-SPEI Reference Standards  
**Strategy Selection:** **Option A (ERA5-Land Primary + NOAA CPC Independent Comparison)**  
**Status:** **RECONSTRUCTION PAUSED PENDING PROGRESSIVE GATE VALIDATION**  
**Spatial Domain:** Tekezé River Basin Catchment ($67,135.4\text{ km}^2$, Northern Ethiopia; Lat: $11.6619^\circ\text{N}–14.7958^\circ\text{N}$, Lon: $35.8583^\circ\text{E}–39.7917^\circ\text{E}$)  
**Target Sequence:** January 1981 – December 2024 (528 consecutive calendar months)

---

## 1. Executive Workflow Architecture

This document governs the end-to-end scientific workflow of the AI-Driven Drought Early Warning System (AI-DREWS). Rather than making ad-hoc decisions after isolated tasks, the entire system is structured into **six sequential, dependent validation gates**. 

```
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 1: Climate Data Acquisition & Provenance Integrity              │
│  • Primary: ECMWF ERA5-Land (9 km hourly extrema derivation)           │
│  • Independent Comparison: NOAA CPC Global Daily Temperature (0.5°)    │
│  • Strict raw immutability in data/raw/temperature/ & SHA-256 manifest │
│  • Status: EXECUTING (1984 Benchmark Complete; Downloader Ready)       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 2: Mathematical Implementation Cross-Validation                  │
│  • Hosking (1990) GLO parameterization & CDF complete pair validation   │
│  • Standard R lmom/SPEI benchmark fixtures (5 test cases, |err| < 1e-5)│
│  • McKee/Thom Gamma SPI-3 MLE with zero-precipitation treatment q      │
│  • Inverse normal conversion (ndtri) with finite clipping [-3.5, 3.5]  │
│  • Status: VERIFIED & TESTED (5/5 Fixture Tests Passing)               │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 3: Spatial and Temporal Integrity Auditing                       │
│  • Tekezé 67,135.4 km² catchment (HydroBASINS Lev 5/6/7 polygon)       │
│  • Exact polygon fractional area & cosine latitude weights             │
│  • 95% minimum spatial coverage rule per month                         │
│  • 528-month continuous temporal sequence (1981–2024)                  │
│  • Strict NaN propagation through rolling 3-month windows              │
│  • Status: AUDITED (Pipeline Script Configured)                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 4: Reconstruct & Validate Drought Indices Target                 │
│  • Hargreaves-Samani (1985) monthly PET using daily extrema            │
│  • Thornthwaite (1948) PET baseline sensitivity                        │
│  • Continuous rolling 12-calendar-month SPEI-3 & SPI-3 engines         │
│  • Strict WMO 1991–2020 fixed calibration baseline                     │
│  • Independent validation against historical Ethiopian droughts        │
│  • Status: PAUSED (Awaiting Gate 1 Full Archive Ingestion)             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 5: Build & Evaluate Predictive Forecasting Models                │
│  • Chronological split: Train (1981–2005), Val (2006–2014), Test (2015+)│
│  • Zero future information leakage; rolling-origin cross-validation    │
│  • Benchmarked against dynamic climatology (Brier score) & persistence │
│  • Teleconnection lags: Pacific (Niño 3.4), Indian (DMI), Atlantic     │
│  • Status: DE-SCOPED & PAUSED (Awaiting Gate 4 Validated Target)       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 6: Operational AgriMinds Dashboard & Decision Interface          │
│  • Versioned data interface between pipeline and Streamlit dashboard   │
│  • Clear separation between observed indices and probabilistic forecast│
│  • Transparent risk categories, uncertainty intervals, failure states  │
│  • Automated data-refresh audits and monitoring                        │
│  • Status: PLANNED                                                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Gate 1 — Climate Data Acquisition & Provenance Integrity

### 2.1 Strategy: Option A (ERA5-Land Primary + NOAA CPC Independent Comparison)

1. **ECMWF ERA5-Land Reanalysis (Primary):**
   * **Domain:** Tekezé Bounding Box $[15.0^\circ\text{N}, 35.5^\circ\text{E}, 11.5^\circ\text{N}, 40.0^\circ\text{E}]$.
   * **Resolution:** $0.1^\circ \times 0.1^\circ$ (~9 km native), 1981–2024.
   * **Hourly Ingestion:** Ingest hourly 2 m temperature (`reanalysis-era5-land`) to derive daily $T_{\max, d} = \max_{h} T_{2\text{m}}(d, h)$ and $T_{\min, d} = \min_{h} T_{2\text{m}}(d, h)$.
   * **Kelvin Conversion:** Converted via $T(^\circ\text{C}) = T(\text{K}) - 273.15$.
   * **Monthly Mean Preservation:** Ingest `reanalysis-era5-land-monthly-means` separately for Thornthwaite comparative baselines.
2. **NOAA CPC Global Unified Temperature (Independent Comparison):**
   * **Domain:** Global land $0.5^\circ \times 0.5^\circ$ ($720 \times 360$).
   * **Resolution:** $0.5^\circ \times 0.5^\circ$ (~55 km), 1981–2024.
   * **Variables:** Daily maximum (`tmax`) and minimum (`tmin`) surface air temperatures ($^\circ\text{C}$).
   * **Application:** Provides station-observed ground-truth cross-checks against ERA5-Land.

### 2.2 Security, Storage & Provenance Protocols

* **Zero Credential Leakage:** API credentials for Copernicus CDS are never printed in logs or committed to Git. The downloader reads from `~/.cdsapirc` or environment variable `CDS_API_KEY`.
* **Immutability:** Raw downloads are stored in `data/raw/temperature/` with read-only permissions and are never overwritten.
* **Manifest & Checksums:** Every downloaded year is hashed with SHA-256 and recorded in `data/processed/temperature_provenance_manifest.json`.

### 2.3 Gate 1 Implementation Scripts

* **ERA5-Land Downloader:** [`scripts/download_era5_land_tekeze_1981_2024.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/download_era5_land_tekeze_1981_2024.py)
* **NOAA CPC Downloader:** [`scripts/download_noaa_cpc_tekeze_1981_2024.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/download_noaa_cpc_tekeze_1981_2024.py)
* **Standardized Daily-to-Monthly Engine:** [`scripts/process_temperature_daily_to_monthly.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/process_temperature_daily_to_monthly.py)

---

## 3. Gate 2 — Mathematical Implementation Cross-Validation

### 3.1 Generalized Logistic (GLO) Distribution Complete Pair Verification

Hosking (1990) parameterization and closed-form Cumulative Distribution Function must satisfy exact round-trip identity:
$$x(F) = \xi + \frac{\alpha}{k}\left[1 - \left(\frac{1 - F}{F}\right)^k\right] \iff F(x) = \frac{1}{1 + \left[1 - \frac{k(x - \xi)}{\alpha}\right]^{1/k}}$$

* **Limit Case $k \to 0$:** $F(x) = \frac{1}{1 + \exp(-(x - \xi)/\alpha)}$ (Standard Logistic).
* **Upper Support Boundary ($k > 0$):** $x \in (-\infty, \xi + \alpha/k]$. For $x \ge \xi + \alpha/k$, $F(x) \equiv 1.0$.
* **Lower Support Boundary ($k < 0$):** $x \in [\xi + \alpha/k, +\infty)$. For $x \le \xi + \alpha/k$, $F(x) \equiv 0.0$.
* **Round-Trip Tolerance:** Confirmed to $|F(x(F)) - F| < 10^{-15}$.

### 3.2 Standard R `lmom` / `SPEI` Benchmark Fixtures

External reference fixtures are stored in [`drought_forecasting/tests/fixtures/r_spei_lmom_reference_benchmark.json`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/fixtures/r_spei_lmom_reference_benchmark.json):
* **Case 1 (Kiremt Wet Season):** $\xi = 45.0, \alpha = 30.0, k = -0.15$
* **Case 2 (Bega Dry Season):** $\xi = -85.0, \alpha = 15.0, k = -0.22$
* **Case 3 (Logistic Limit $k=0$):** $\xi = 0.0, \alpha = 20.0, k = 0.00$
* **Case 4 (Positive Shape Upper Bound):** $\xi = 10.0, \alpha = 12.0, k = +0.18$
* **Case 5 (Extreme Tail Drought):** $\xi = -20.0, \alpha = 40.0, k = -0.28$
* **Case 6 (Gamma SPI with Zeros):** $\alpha_g = 2.2, \beta_g = 35.0, q = 0.08$

All 5 benchmark test cases are verified in [`drought_forecasting/tests/test_gate2_mathematical_benchmarks.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/test_gate2_mathematical_benchmarks.py) (passing in 0.45s).

---

## 4. Gate 3 — Spatial and Temporal Integrity Auditing

### 4.1 Catchment Geometry & Topological Verification

* **Catchment Boundary:** Verified HydroBASINS Lev 5/6/7 polygon in [`data/spatial/processed/tekeze_basin_hydrological_complete.geojson`](file:///c:/Users/User/Desktop/AgriMinds/data/spatial/processed/tekeze_basin_hydrological_complete.geojson).
* **Area Verification:** $67,135.4\text{ km}^2$ spherical geodesic excess area (EPSG:4326), representing the complete transboundary Tekezé catchment down to the Ethiopian-Sudanese border.

### 4.2 Spatial Masking & Fractional Area Weighting

* **CHIRPS v2.0 (0.05°):** 2,488 active intersecting cells.
* **NOAA CPC (0.50°):** 38 active intersecting cells.
* **Weighting Formulation:**
  $$w_{i,j} = \frac{\text{Area}(\mathcal{C}_{i,j} \cap \mathcal{P})}{\text{Area}(\mathcal{C}_{i,j})} \cdot \cos(\phi_i), \quad \sum_{(i,j) \in \text{valid}} w_{i,j} = 1.0$$
* **Spatial Coverage Threshold:** At least 95% valid basin weight coverage required per month; otherwise flags `INSUFFICIENT_SPATIAL_COVERAGE` and outputs `NaN`.
* **Zero Contamination:** NoData sentinels (e.g. -9999) are strictly excluded from both numerator and denominator.

### 4.3 Continuous 528-Month Sequence

* Sequence spans 528 consecutive months: January 1981 through December 2024.
* Zero gap-bridging or silent heuristics.
* Missing values in rainfall or temperature strictly propagate through rolling 3-month accumulations ($D_3 = \text{NaN}$).

---

## 5. Gate 4 — Reconstruct & Validate Drought Indices Target

### 5.1 Jensen's Inequality & Daily Extrema for PET

Hargreaves–Samani PET is computed from daily extrema before monthly accumulation:
$$\text{PET}_{\text{month}} = \sum_{d=1}^{N_m} 0.0023 \cdot R_{a,d} \cdot (T_{\text{mean},d} + 17.8) \cdot \sqrt{T_{\max,d} - T_{\min,d}}$$

Substituting monthly mean temperature extrema into $\sqrt{\Delta T}$ introduces an artificial **+0.5% to +1.4% positive bias** due to Jensen's inequality ($\mathbb{E}[\sqrt{X}] < \sqrt{\mathbb{E}[X]}$). Daily extrema are strictly preserved.

### 5.2 Month-Specific Calibration over WMO Normal (1991–2020)

* Water balance $D = P - \text{PET}$ is accumulated across 3-month rolling windows.
* Each ending calendar month $m \in \{1, \dots, 12\}$ is fitted to a **separate, calendar-month-specific** GLO distribution using the 30-year WMO normal (1991–2020).
* Standardized SPI-3 is computed from accumulated precipitation using Thom (1958) Gamma MLE and zero-probability adjustment $H(x) = q + (1 - q)G(x)$. Simple $z$-scores are never labeled as SPI.

### 5.3 Historical Drought Ground-Truth Benchmarking

Reconstructed indices must correctly capture documented historical shocks across the Tekezé Basin:
1. **1984–1985 Great Famine:** Peak drought signal in July–September 1984 ($\text{SPEI-3} \le -2.0$, Extreme Drought).
2. **1987 El Niño Drought:** Severe Kiremt failure.
3. **2002–2003 Major Drought:** Extensive crop failure across Tigray and Amhara.
4. **2015–2016 Extreme El Niño:** Major Belg and Kiremt failure.
5. **1988 & 1998 Pluvial Benchmarks:** Pronounced positive anomalies ($\text{SPEI-3} \ge +1.5$).

---

## 6. Gate 5 — Predictive Forecasting Model Formulation

*(Initiated only after Gate 4 passes scientific certification)*

### 6.1 Predictands & Forecast Horizons

* **Primary Predictand:** September-ending SPEI-3 (Kiremt agricultural season) and May-ending SPEI-3 (Belg pastoral season).
* **Lead Times:** 1-month (issued June 1 for Kiremt), 3-month (issued April 1), and 6-month (issued January 1).

### 6.2 Data Splitting & Leakage Prevention

* **Chronological Splits:**
  * Training: 1981–2005 (25 years, 300 months)
  * Validation / Hyperparameter Tuning: 2006–2014 (9 years, 108 months)
  * Out-of-Sample Test Holdout: 2015–2024 (10 years, 120 months)
* **Zero Overlap Leakage:** Rolling 3-month window features are strictly constrained to pre-forecast issue dates.
* **Release Date Defensibility:** Teleconnection indices (Niño 3.4, IOD DMI, TSA, TNA) are lagged according to operational latency (minimum 1-month real-time publication lag).

### 6.3 Baseline Benchmarks & Evaluation Metrics

* **Baselines:** Dynamic Climatology (monthly empirical distribution) and Persistence.
* **Probabilistic Scoring:** Brier Score and Continuous Ranked Probability Score (CRPS). Models must demonstrate Brier Skill Score $\text{BSS} > 0$ over dynamic climatology.
* **Continuous Metrics:** MAE, RMSE, Pearson $r$, Spearman rank correlation.

---

## 7. Gate 6 — AgriMinds Operational Interface & Dashboard

* **Architecture:** Streamlit dashboard interface backed by SQLite / NetCDF cache.
* **Forecast Transparency:** Displays issued date, forecast horizon, valid period, and 80%/95% confidence intervals.
* **Observed vs Forecast Separation:** Historical verified observations and model predictions are rendered on distinct visual layers.
* **Failure Modes:** Explicit UI banners if live data feeds fail; zero silent fallback to synthetic forecasts.

---

## 8. Master Action Plan & Milestones

| Milestone | Gate | Description | Responsible Script | Deliverable | Status |
|:---:|:---:|---|---|---|:---:|
| **M1** | Gate 0 | Catchment boundary verification ($67,135.4\text{ km}^2$) | [`tekeze_basin_boundary.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/agriminds/spatial/tekeze_basin_boundary.py) | GeoJSON & Area Audit | **COMPLETE** |
| **M2** | Gate 1 | Preserved 1984 NOAA CPC raw NetCDFs | [`inspect_tmax_1984.py`](file:///c:/Users/User/Desktop/AgriMinds/scratch/inspect_tmax_1984.py) | Raw NetCDFs & SHA-256 | **COMPLETE** |
| **M3** | Gate 1 | Gate 1 Temperature-Source Audit Deliverable | [`temperature_source_and_provenance_audit.md`](file:///c:/Users/User/Desktop/AgriMinds/docs/temperature_source_and_provenance_audit.md) | Gate 1 Audit Report | **COMPLETE** |
| **M4** | Gate 2 | R-benchmarked GLO & Gamma reference fixtures | [`test_gate2_mathematical_benchmarks.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/test_gate2_mathematical_benchmarks.py) | Fixture JSON & 5 Tests | **COMPLETE** |
| **M5** | Gate 1 | ERA5-Land & CPC 1981–2024 automated downloaders | [`download_era5_land_tekeze_1981_2024.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/download_era5_land_tekeze_1981_2024.py) | Production Downloaders | **COMPLETE** |
| **M6** | Gate 1 | Full 44-year temperature archive ingestion | Downloader execution | Full raw NetCDF archive | **AWAITING CDS KEY** |
| **M7** | Gate 3 | Continuous 528-month CHIRPS & Temp integration | [`build_verified_tekeze_monthly_climate_1981_2024.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/build_verified_tekeze_monthly_climate_1981_2024.py) | 528-month Climate Table | **PAUSED FOR M6** |
| **M8** | Gate 4 | SPEI-3 & SPI-3 drought target reconstruction | [`spei_calculator.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/agriminds/climate/spei_calculator.py) | Historical Drought Target | **PAUSED FOR M7** |
| **M9** | Gate 5 | Chronological model training & Brier evaluation | Model training pipeline | Model Card & Benchmarks | **PAUSED FOR M8** |
| **M10** | Gate 6 | AgriMinds dashboard operational integration | Streamlit application | Operational UI | **PAUSED FOR M9** |
