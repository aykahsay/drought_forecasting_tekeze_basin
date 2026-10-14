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

## Multi-Gate Scientific Workflow Architecture (Gates 1–6)

```
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 1: Climate Data Acquisition & Provenance Integrity              │
│  • Primary: ECMWF ERA5-Land (9 km hourly extrema derivation)           │
│  • Independent Comparison: NOAA CPC Global Daily Temperature (0.5°)    │
│  • Strict raw immutability in data/raw/temperature/ & SHA-256 manifest │
│  • Jensen's Inequality: Preserves daily extrema before PET calculation │
│  • Status: REPRODUCIBLE DOWNLOADERS READY (1984 Benchmark Certified)   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 2: Mathematical Implementation Cross-Validation                  │
│  • Hosking (1990) GLO parameterization & CDF complete pair validation   │
│  • Standard R lmom/SPEI benchmark fixtures (6 test cases, |err| < 1e-5)│
│  • McKee/Thom Gamma SPI-3 MLE with zero-precipitation treatment q      │
│  • Inverse normal conversion (ndtri) with finite clipping [-3.5, 3.5]  │
│  • Status: PASSED & VALIDATED (5/5 Benchmark Tests Passing)            │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│  GATE 3: Spatial and Temporal Integrity Auditing                       │
│  • Tekezé 67,135.4 km² catchment (HydroBASINS Lev 5/6/7 polygon)       │
│  • Exact polygon fractional area & cosine latitude weights             │
│  • 95% minimum spatial coverage rule per month                         │
│  • 528-month continuous temporal sequence (1981–2024)                  │
│  • Strict NaN propagation through rolling 3-month accumulations        │
│  • Status: PASSED & AUDITED (7/7 Integrity Tests Passing)              │
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
│  • Status: ARCHITECTED & SPECIFIED                                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Deliverables & Documentation Index

* **Master Plan:** [`docs/AI_DREWS_MASTER_SCIENTIFIC_WORKFLOW_AND_VALIDATION_PLAN.md`](docs/AI_DREWS_MASTER_SCIENTIFIC_WORKFLOW_AND_VALIDATION_PLAN.md)
* **Gate 1 Report:** [`docs/temperature_source_and_provenance_audit.md`](docs/temperature_source_and_provenance_audit.md)
* **Gate 2 Report:** [`docs/gate2_cross_language_mathematical_validation_report.md`](docs/gate2_cross_language_mathematical_validation_report.md)
* **Gate 3 Report:** [`docs/gate3_spatial_and_temporal_integrity_audit.md`](docs/gate3_spatial_and_temporal_integrity_audit.md)
* **Gate 4 Specification:** [`docs/gate4_drought_indices_reconstruction_and_validation.md`](docs/gate4_drought_indices_reconstruction_and_validation.md)
* **Gate 5 Specification:** [`docs/gate5_predictive_model_architecture_and_leakage_audit.md`](docs/gate5_predictive_model_architecture_and_leakage_audit.md)
* **Gate 6 Specification:** [`docs/gate6_agriminds_dashboard_interface_and_monitoring.md`](docs/gate6_agriminds_dashboard_interface_and_monitoring.md)

---

## Running the Automated Test Suite

The climate reconstruction, spatial masking, and mathematical distribution engines are protected by **23 automated tests**:

```bash
python -m pytest drought_forecasting/tests/test_climate_reconstruction_and_spei.py \
                 drought_forecasting/tests/test_gate2_mathematical_benchmarks.py \
                 drought_forecasting/tests/test_gate3_spatial_and_temporal_integrity.py -v
```

All 23 tests pass in < 3.0 seconds, certifying:
1. Basin geometry ($67,135.4\text{ km}^2$), topological validity, and CRS.
2. Fractional area raster weighting and exclusion of negative NoData sentinels (-9999).
3. 95% spatial coverage threshold enforcement.
4. Hosking GLO parameter recovery and complete pair round-trip identity ($|F(x(F)) - F| < 10^{-5}$) against R reference fixtures.
5. Thom Gamma SPI-3 MLE and zero-precipitation adjustment $H(x) = q + (1 - q)G(x)$.
6. Continuous 528-month sequence and strict rolling 3-month NaN propagation.
7. Zero synthetic heuristics in production: missing observational feeds explicitly raise `MissingTemperatureDataError`.

