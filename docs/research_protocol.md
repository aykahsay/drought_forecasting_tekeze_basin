# AI-DREWS Scientific Research Protocol
## Multi-Gate Methodological Framework for Drought Early Warning in the Tekezé River Basin

**Document ID:** `AI-DREWS-DOC-RP-2026-10`  
**Standard:** Open Science / WMO Hydro-Climatology Guidelines / FAIR Data Principles  
**Status:** **ACTIVE PROTOCOL**  
**Geographic Focus:** Tekezé River Basin Catchment ($67,135.4\text{ km}^2$ provisional, Northern Ethiopia; Tigray and Amhara regions)

---

### 1. Research Objectives & Scope

The AI-Driven Drought Early Warning System (AI-DREWS) investigates hydro-meteorological drought dynamics across the Tekezé Basin to provide transparent early warning indicators for agricultural decision-makers and regional planners in Northern Ethiopia.

The protocol establishes four scientific pillars:
1. **Traceable Climate Ingestion:** Assemble an immutable, quality-controlled monthly climate dataset spanning January 1981 through December 2024 (528 consecutive months).
2. **Mathematically Certified Drought Targets:** Reconstruct standardized drought indices ($\text{SPEI-3}$ and $\text{SPI-3}$) adhering strictly to CRAN `SPEI` / Hosking (1990) Generalized Logistic and Thom (1958) Gamma distribution standards.
3. **Hypothesis-Driven Event Validation:** Compare reconstructed drought signals against documented historical records (1984/85, 1987, 2002/03, 2015/16) as testable hypotheses without forcing target values.
4. **Leakage-Safe Forecasting Benchmarking:** Formulate seasonal prediction tasks with strict information cutoffs, benchmarking deep learning architectures (CNN-LSTM, Fourier Neural Operators) against persistence, climatology, and linear models.

---

### 2. Progressive Validation Gates Architecture

To prevent premature modeling or reporting of uncalibrated skill, the protocol enforces six sequential validation gates:

| Gate | Title | Scope | Pass Criteria | Current Status |
|:---:|---|---|---|:---:|
| **Gate 1** | Climate Ingestion & Provenance | Hourly ERA5-Land & daily NOAA CPC downloads; SHA-256 checksums | Full 1981–2024 archive acquired, verified timestamps, checksum manifest | **PARTIAL** |
| **Gate 2** | Mathematical Cross-Validation | GLO & Gamma fitting, complete pair CDF, inverse normal conversion | Agreement with R `lmom` / `SPEI` fixtures ($|F_{\text{py}} - F_{\text{ref}}| < 10^{-5}$) | **PASS** |
| **Gate 3** | Spatial & Temporal Integrity | Fractional area raster weighting, NoData exclusion, 528-month continuity | Validated geometry, 95% minimum spatial coverage rule, strict NaN propagation | **PASS** |
| **Gate 4** | Drought Target Reconstruction | Hargreaves daily extrema PET, rolling 3-month water balance, WMO baseline | Calibrated 1991–2020 distributions, independent event validation | **NOT RUN (Paused)** |
| **Gate 5** | Predictive Model Formulation | Chronological splits, dynamic climatology benchmarks, predictive intervals | Proven positive Brier skill score ($\text{BSS} > 0$), zero temporal leakage | **NOT RUN (Paused)** |
| **Gate 6** | Operational Dashboard Integration | Versioned API, visual layer separation, fail-safe alerts | OGC compliance, transparent predictive intervals, zero synthetic fallbacks | **NOT RUN (Planned)** |

---

### 3. Non-Negotiable Scientific Safeguards

1. **Zero Synthetic Observations:** The synthetic temperature generation routine (`get_verified_monthly_temperature` fallback) is permanently disabled in production code paths.
2. **Explicit Failure States:** Ingestion scripts must explicitly raise `MissingTemperatureDataError` when raw observational files are unavailable.
3. **Immutable Raw Data:** Original downloaded NetCDF/GeoTIFF files are stored in `data/raw/` with read-only permissions and never modified or overwritten by derivatives.
4. **Declared Methodological Baseline:** The 1991–2020 climatological normal period is adopted as our declared baseline for distribution fitting.
5. **No Data Re-Labeling:** Gaussian $z$-scores must never be labeled as SPI or SPEI.
6. **No Pre-Gate Modeling:** Machine learning training and evaluation are strictly prohibited until Gates 1–4 are certified.
7. **Disambiguation of Drought vs Famine:** Meteorological drought ($\text{SPEI-3} \le -2.0$) represents physical water deficit; it is not a direct substitute for socio-economic food insecurity or famine.
8. **Continuous Dual-Platform Synchronization:** Every code revision, documentation amendment, audit finding, test suite addition, and data manifest update must be committed and pushed immediately to GitHub (`aykahsay/drought_forecasting_tekeze_basin`, branches `research/verified-tekeze-drought-pipeline` and `main`) and synchronized to Hugging Face Model Hub (`aykgeh/drought_forecasting_tekeze_basin`) to ensure 100% open-science provenance and zero platform divergence.

