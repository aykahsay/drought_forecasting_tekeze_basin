# AI-DREWS: Tekezé River Basin Drought Forecasting & Climate Reconstruction Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Target Basin](https://img.shields.io/badge/Basin-Tekezé%20River%20Basin%20(67%2C135.4%20km²)-orange.svg)]()
[![Region](https://img.shields.io/badge/Location-Northern%20Ethiopia-red.svg)]()
[![Scientific Audit Status](https://img.shields.io/badge/Audit%20Status-Gate%201%20Passed-brightgreen.svg)]()

> **Research Focus:** AI-Driven Drought Early Warning System (AI-DREWS) for the Tekezé River Basin ($67,135.4\text{ km}^2$), Northern Ethiopia.  
> **Target Historical Period:** 1981–2024 (528 consecutive calendar months).  
> **Target Drought Indices:** Standardized Precipitation-Evapotranspiration Index (SPEI-3, Generalized Logistic) & Standardized Precipitation Index (SPI-3, 2-parameter Gamma).  
> **Associated Repositories:** [GitHub (aykahsay/drought_forecasting_tekeze_basin)](https://github.com/aykahsay/drought_forecasting_tekeze_basin) | [Hugging Face (aykgeh/drought_forecasting_tekeze_basin)](https://huggingface.co/aykgeh/drought_forecasting_tekeze_basin)

---

## Scientific Audit & Methodological Integrity Notice

> [!IMPORTANT]
> **De-Scoping & Retraction of Preliminary Heuristic Metrics:**  
> Previous computational prototypes reported inflated predictive metrics ($R^2 > 95\%$) that were generated on uncalibrated datasets containing corrupted timestamps (e.g. forward-shifted 2025 timestamps in legacy NetCDF files) and synthetic temperature climatologies.  
> Following an exhaustive scientific audit (see [AI_DREWS_SCIENTIFIC_HANDOVER_REPORT.md](AI_DREWS_SCIENTIFIC_HANDOVER_REPORT.md)), all unverified figures, mock forecast checkpoints, and synthetic metrics have been **formally removed**. Predictive machine learning models are strictly paused until the 1981–2024 monthly climate target passes multi-gate observational verification.

---

## Multi-Gate Verification Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│  Gate 0: Catchment Geometry & Topological Verification                │
│  • Verified 67,135.4 km² Complete Tekezé Basin (HydroBASINS Lev 5/6/7) │
│  • Full transboundary Ethiopian sub-basin (resolving truncated HDX)   │
│  • Status: VERIFIED & ACCEPTED                                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Gate 1: Temperature-Source Audit & Provenance Verification            │
│  • Primary Strategy: ECMWF ERA5-Land (9 km hourly extrema derivation)  │
│  • Independent Comparison: NOAA CPC Global Unified Temperature (0.5°)  │
│  • Jensen's Inequality: Strict daily extrema requirement for PET      │
│  • GLO Parameterization & CDF complete pair validation (|error| < 1e-15)│
│  • Synthetic fallback strictly disabled (MissingTemperatureDataError)  │
│  • Status: 6 OF 6 ACCEPTANCE ITEMS COMPLETE (October 2026)             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Gate 2: Full 1981–2024 Monthly Climate Target Reconstruction          │
│  • CHIRPS v2.0 (0.05°) monthly precipitation (>= 95% basin coverage)   │
│  • Hargreaves-Samani (1985) & Thornthwaite (1948) monthly PET          │
│  • Continuous rolling 12-calendar-month SPEI-3 & SPI-3 engines         │
│  • Fixed calibration normal: WMO 1991–2020 baseline                   │
│  • Status: IN PROGRESS (Paused for Gate 1 Review)                     │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  Gate 3: Teleconnection Analysis & Machine Learning Benchmarking      │
│  • Pacific (Niño 3.4), Indian (DMI), Atlantic (TNA, TSA) teleconnection│
│  • Rigorous temporal train/validation/test holdout (>= 2006–2023)      │
│  • Probabilistic evaluation against dynamic climatology (Brier Score)  │
│  • Status: PENDING GATE 2 COMPLETION                                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Gate 1 Temperature Audit Highlights

The Gate 1 deliverable ([docs/temperature_source_and_provenance_audit.md](docs/temperature_source_and_provenance_audit.md)) establishes:
1. **Source Preservation:** Raw benchmark NetCDF files are permanently preserved in `data/raw/temperature/cpc/`:
   * `tmax.1984.nc` (87.68 MB, SHA-256: `476fae44066168fab45e76fc98aae9bba22c4f00ea1f18cb6304727dadb7305b`)
   * `tmin.1984.nc` (89.08 MB, SHA-256: `b14e8bba53532cddcaad6120bbe031f38e0bf4755cf92efb248a92f8ac2fedea`)
2. **Strict Daily Extrema Requirement (Jensen's Inequality):**
   $$\mathbb{E}[\sqrt{\Delta T_{\text{daily}}}] < \sqrt{\mathbb{E}[\Delta T_{\text{daily}}]}$$
   Because $\sqrt{u}$ is concave, substituting monthly mean temperature for daily extrema introduces a systematic **+0.5% to +1.4% positive bias** in monthly PET. Daily extrema must be derived at daily timesteps before monthly aggregation.
3. **Exact Basin Spatial Masking:**
   Tekezé polygon intersection across the $0.5^\circ$ NOAA CPC grid covers 38 active cells with exact fractional area weighting and cosine-latitude spherical area adjustment, achieving 99.73% annual valid coverage.
4. **Zero Synthetic Heuristics in Production:**
   Calls to `get_verified_monthly_temperature()` without real observational NetCDFs now explicitly raise `MissingTemperatureDataError`.

---

## Mathematical Formulation: Generalized Logistic (GLO) Distribution

For drought monitoring via SPEI, Hosking's (1990) Generalized Logistic distribution is fitted via unbiased sample L-moments:

* **Unbiased Probability-Weighted Moments:**
  $$b_r = \frac{1}{n} \sum_{i=1}^n \frac{\binom{i-1}{r}}{\binom{n-1}{r}} x_{(i)}$$
* **Sample L-Moments:**
  $$\lambda_1 = b_0, \quad \lambda_2 = 2b_1 - b_0, \quad \tau_3 = \frac{6b_2 - 6b_1 + b_0}{2b_1 - b_0}$$
* **Parameters:**
  $$k = -\tau_3, \quad \alpha = \frac{\lambda_2 \sin(k\pi)}{k\pi}, \quad \xi = \lambda_1 - \frac{\alpha}{k}\left(1 - \frac{k\pi}{\sin(k\pi)}\right)$$
* **Closed-Form CDF:**
  $$F(x) = \frac{1}{1 + \left[1 - \frac{k(x - \xi)}{\alpha}\right]^{1/k}}$$
* **Round-Trip Identity:** $F(x(F)) \equiv F$ confirmed to $|F(x(F)) - F| < 10^{-15}$.

---

## Repository Structure

```
drought_forecasting_tekeze_basin/
├── README.md                                         # Audited project documentation
├── requirements.txt                                  # Environment dependencies
├── .gitignore                                        # Clean git exclusion rules
├── AI_DREWS_SCIENTIFIC_HANDOVER_REPORT.md            # Comprehensive scientific handover audit
├── data/
│   ├── raw/
│   │   ├── temperature/
│   │   │   └── cpc/                                  # Preserved NOAA CPC NetCDF files (1984)
│   │   └── chirps_monthly/                           # Monthly CHIRPS GeoTIFFs (1981–2024)
│   └── spatial/
│       └── processed/
│           └── tekeze_basin_hydrological_complete.geojson  # Verified 67,135.4 km² catchment
├── docs/
│   ├── temperature_source_and_provenance_audit.md    # Gate 1 Deliverable Report
│   └── data_provenance_and_climate_reconstruction_audit.md # Gate 0 Audit Report
├── drought_forecasting/
│   ├── agriminds/
│   │   └── climate/
│   │       └── spei_calculator.py                    # Verified GLO & Gamma distribution engine
│   └── tests/
│       └── test_climate_reconstruction_and_spei.py   # 11 automated verification unit tests (PASS)
└── scripts/
    └── build_verified_tekeze_monthly_climate_1981_2024.py  # Climate target reconstruction pipeline
```

---

## Running the Automated Test Suite

The climate reconstruction and mathematical distribution engines are protected by automated tests:

```bash
python -m pytest drought_forecasting/tests/test_climate_reconstruction_and_spei.py -v
```

All 11 tests pass with strict checks on catchment area, fractional area raster weighting, NoData sentinels exclusion, GLO complete pair round-trip recovery, and explicit failure on missing temperature observations.
