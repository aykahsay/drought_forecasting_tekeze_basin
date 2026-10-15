# Scientific Audit: Canonical Forecast Ablation, Spatial Extraction & Temporal Alignment

**Study Area:** Tanqua Abergele Woreda & Tekezé River Basin, Northern Ethiopia  
**Target Metric:** 3-Month Standardized Precipitation Index ($\text{SPI-3}$)  
**Evaluation Window:** 2016-01 to 2023-12 (Exactly 96 Continuous Holdout Calendar Months)  
**Historical Training Period:** 1981-03 to 2015-12 (418 Continuous Historical Months)  
**Canonical Predictions File:** [`data/processed/canonical_benchmark_holdout_predictions.csv`](file:///c:/Users/User/Desktop/AgriMinds/data/processed/canonical_benchmark_holdout_predictions.csv)  
**Governance Standard:** Gate 1 & Gate 2 Scientific Quality Standards, Strictly Zero Synthetic Data Rule  

---

## Executive Summary & Core Scientific Insights

1. **A Canonical Predictions File for 100% Metric Reproducibility:**
   - To eliminate any internal inconsistency, every single holdout forecast across all horizons $h \in \{1, 2, 3\}$ and all models (M0 through M6) is saved in [`data/processed/canonical_benchmark_holdout_predictions.csv`](file:///c:/Users/User/Desktop/AgriMinds/data/processed/canonical_benchmark_holdout_predictions.csv) ($288$ rows = $96\text{ months} \times 3\text{ leads}$).
   - Every metric, table, seasonal MSE decomposition, and paired year-block bootstrap interval is reproduced directly from this single canonical holdout dataset.

2. **Clean Ocean Basin Ablation Experiment (M0 through M6):**
   - **M0 (Climatological Mean, $\text{RMSE} = 0.9267$):** True reference standard.
   - **M1 (Persistence, $\text{Lagged SPI-3}_{t-h}$):** Decays rapidly from $\text{RMSE} = 0.8910$ ($r = 0.525$) at Lead 1, to $1.1548$ at Lead 2, and collapses to $1.3693$ ($r = -0.127$) at Lead 3.
   - **M2 (Local Climate Model, $\text{M1} + \text{seasonality}$):** Substantially improves over persistence ($\text{RMSE} = 0.7918$ at Lead 1, $0.9145$ at Lead 2).
   - **M3 (Pacific / ENSO Informed):** **Adds NO incremental predictive skill** at any lead time. At Lead 1, adding Niño 3.4 increases RMSE to $0.7934$ (worse than Local AR). At Lead 3, correlation turns negative ($r = -0.180$).
   - **M4 (Indian Ocean / IOD Informed):** **The ONLY ocean basin showing positive incremental skill**. At Lead 1, drops RMSE to $0.7807$ ($r = 0.540$, $p = 0.061$). At Lead 2, achieves the lowest RMSE of any model ($0.8968$, $r = 0.247$).
   - **M5 (Atlantic Gradient Informed):** Shows negligible impact on RMSE ($0.7915$ vs $0.7918$).
   - **M6 (All Three Oceans Coupled):** At Lead 2, M6 ($\text{RMSE} = 0.8989$) performs **worse than Indian Ocean alone (M4, $\text{RMSE} = 0.8968$)**, because adding noisy Pacific and Atlantic predictors introduces parameter estimation variance.

3. **Spatial Extraction & Polygon Delineation Audit:**
   - Verified that extraction uses the **true official 16-kebele Tanqua Abergele Woreda MultiPolygon** ($0.11993\text{ sq deg}$, approx $1,420\text{ km}^2$), NOT a rectangular bounding box.
   - The woreda fills only **$58.41\%$ of its rectangular bounding box** ($0.20534\text{ sq deg}$). Bounding-box extraction would include $41.59\%$ spurious land area outside the woreda.
   - Exact intersection isolates **71 discrete $0.05^\circ$ CHIRPS raster cells** (rows 527–536, cols 1172–1181) with $\cos(\text{lat}_{\text{center}})$ spherical weighting.

4. **Complete 100% Seasonal MSE Decomposition:**
   - Evaluated across all 96 holdout months (no missing transition months).
   - Confirms that at Lead 2 and Lead 3, the multi-ocean model has **positive $\Delta\text{MSE}$ (higher error than Climatology)** in every single rainy season and transition month (Kiremt JAS, Belg MAM, Transition Feb, Transition Jun).
   - The apparent pooled error reduction is generated entirely during the **Bega dry season (Oct–Jan)**, when rainfall is negligible and agricultural vulnerability is low.

---

## 1. Clean Forecast Ablation Benchmark (M0 through M6)

All models were trained strictly on the pre-2016 baseline ($1981\text{-}03$ to $2015\text{-}12$, 418 continuous months), with standardized features and identical Ridge regularization ($\alpha = 2.0$), evaluated on the exact 96 holdout months (2016-01 to 2023-12).

### Multi-Lead Ablation Performance Summary

| Model | Inputs / Feature Formulation | Lead 1 RMSE ($r$) | Lead 2 RMSE ($r$) | Lead 3 RMSE ($r$) | Primary Scientific Finding |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **M0: Climatology** | Historical mean ($E[y] = 0.0$) | 0.9267 (—) | 0.9267 (—) | **0.9267** (—) | Reference standard for zero-skill |
| **M1: Persistence** | $\text{SPI-3}_{t-h}$ | 0.8910 ($0.525$) | 1.1548 ($0.202$) | 1.3693 ($-0.127$) | Decays as window overlap vanishes |
| **M2: Local Climate** | $\text{M1} + \sin/\cos(\text{month})$ | 0.7918 ($0.524$) | 0.9145 ($0.198$) | 0.9376 ($-0.143$) | Seasonal cycle stabilizes autoregression |
| **M3: Pacific Only** | $\text{M2} + \text{Niño 3.4}_{t-h, t-h-6}$ | 0.7934 ($0.522$) | 0.9224 ($0.177$) | 0.9520 ($-0.180$) | **Degrades performance (noise injection)** |
| **M4: Indian Only** | $\text{M2} + \text{IOD DMI}_{t-h}$ | **0.7807** ($0.540$) | **0.8968** ($0.247$) | **0.9220** ($+0.040$) | **Strongest single ocean teleconnection** |
| **M5: Atlantic Only** | $\text{M2} + \text{Atlantic Grad}_{t-h}$ | 0.7915 ($0.525$) | 0.9133 ($0.204$) | 0.9331 ($-0.046$) | Minimal incremental value |
| **M6: All 3 Oceans** | $\text{M2} + \text{Pacific} + \text{Indian} + \text{Atl}$ | 0.7808 ($0.541$) | 0.8989 ($0.244$) | 0.9282 ($+0.021$) | Multi-collinearity degrades M4 skill |

### Paired Calendar Year-Block Bootstrap Analysis (8 Years Jointly Resampled, B = 2,000, seed = 42)

To evaluate paired differences without assuming independent observations, 8 complete calendar years (2016 to 2023) were resampled jointly with replacement:

$$\Delta\text{RMSE}^* = \text{RMSE}(y^*, \hat{y}_{\text{model}}^*) - \text{RMSE}(y^*, \hat{y}_{\text{baseline}}^*)$$

| Lead Horizon & Comparison | Metric ($\Delta\text{RMSE}$) | 95% Year-Block CI | $P^*(\Delta\text{RMSE}^* \ge 0)$ | Two-Sided Empirical $p$ | Scientific Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Lead 1m:** | | | | | |
| • M2 (Local AR) vs M0 (Clim) | **-0.1349** | $[-0.2305, -0.0096]$ | 0.0170 | **0.0340** | **Statistically Significant Skill** |
| • M4 (Indian) vs M2 (Local AR) | **-0.0111** | $[-0.0243, +0.0004]$ | 0.0305 | **0.0610** | Marginal Significance (Promising) |
| • M3 (Pacific) vs M2 (Local AR) | **+0.0016** | $[-0.0036, +0.0065]$ | 0.7465 | 0.5070 | No Improvement (Increases Error) |
| • M6 (All Oceans) vs M2 (Local) | **-0.0110** | $[-0.0317, +0.0047]$ | 0.1415 | 0.2830 | Not Statistically Significant |
| • M6 (All Oceans) vs M0 (Clim) | **-0.1459** | $[-0.2513, -0.0167]$ | 0.0170 | **0.0340** | Significant vs Climatology |
| **Lead 2m:** | | | | | |
| • M4 (Indian) vs M2 (Local AR) | **-0.0177** | $[-0.0521, +0.0051]$ | 0.0820 | 0.1640 | Modest Gain (Not Significant) |
| • M6 (All Oceans) vs M2 (Local) | **-0.0156** | $[-0.0527, +0.0120]$ | 0.3075 | 0.6150 | Not Statistically Significant |
| • M6 (All Oceans) vs M0 (Clim) | **-0.0278** | $[-0.0744, +0.0268]$ | 0.1520 | 0.3040 | 95% CI Straddles Zero |
| **Lead 3m:** | | | | | |
| • M4 (Indian) vs M0 (Clim) | **-0.0047** | $[-0.0421, +0.0298]$ | 0.3950 | 0.7900 | Indistinguishable from Climatology |
| • M6 (All Oceans) vs M0 (Clim) | **+0.0015** | $[-0.0404, +0.0344]$ | 0.4220 | 0.8440 | **Zero Skill (Worse than Climatology)** |
| • M6 (All Oceans) vs M1 (Pers) | **-0.4411** | $[-0.6494, -0.2252]$ | 0.0005 | 0.0010 | Significant over decaying baseline only |

*Note: $P^*(\Delta\text{RMSE}^* \ge 0)$ represents the empirical fraction of bootstrap resamples where the model fails to improve over the baseline. Two-sided empirical $p$-value is $2 \times \min(P^*, 1 - P^*)$.*

---

## 2. Spatial Extraction & Geometry Verification

To verify that the precipitation series reflects Tanqua Abergele Woreda rather than an arbitrary bounding box, the geometry and raster mapping were audited:

### Geometry Parameters
- **Data Source:** `data/spatial/processed/tekeze_basin_kebeles_intersected.geojson` (Official CSA/ECA 2007/2013 administrative boundaries).
- **Aggregated Units:** Exactly 16 discrete kebele polygons within Tanqua Abergele Woreda aggregated via `shapely.ops.unary_union`.
- **Coordinate Reference System (CRS):** Geographic WGS84 (EPSG:4326).
- **Bounding Box:** Longitude $[38.6350^\circ\text{E}, 39.0942^\circ\text{E}]$, Latitude $[13.1690^\circ\text{N}, 13.6162^\circ\text{N}]$.
- **True Polygon Area:** **$0.11993\text{ sq deg}$** (approx $1,420\text{ km}^2$).
- **Bounding Box Area:** **$0.20534\text{ sq deg}$**.
- **Polygon Fill Ratio:** **$58.41\%$**. Naive rectangular extraction includes $41.59\%$ spurious area from adjacent woredas (Kola Tembien, Seharti Samre, Naeder Adet).

### Raster Georeferencing & Intersection Kernel
- **CHIRPS Africa Raster Specification:** Origin $(-20.0^\circ\text{E}, 40.0^\circ\text{N})$, Pixel Scale $0.05^\circ \times 0.05^\circ$, Array size $1500 \times 1600$.
- **Intersecting Grid Cells:** Exactly **71 discrete $0.05^\circ$ cells** (row indices 527–536, column indices 1172–1181).
- **Weighting Formula:** $w_{r, c} = \text{Area}(P_{r, c} \cap \text{Polygon}) \times \cos(\text{lat}_{\text{center}})$.
- **Catchment Comparison:**
  - Tanqua Abergele Woreda Mean Monthly Precipitation: $63.48\text{ mm/mo}$ ($761.75\text{ mm/yr}$).
  - Complete Tekezé River Basin Catchment Mean: $72.23\text{ mm/mo}$ ($866.76\text{ mm/yr}$).
  - Pearson correlation across 528 months: $r = 0.9761$.

---

## 3. Complete 100% Seasonal MSE Decomposition (All 96 Months)

All 96 continuous calendar months (2016–2023) are partitioned without omissions:
$$\text{MSE}_{\text{total}} = \sum_{s} \frac{N_s}{N} \text{MSE}_s \quad \implies \quad \Delta \text{MSE} = \sum_{s} w_s (\text{MSE}_{\text{ocean}, s} - \text{MSE}_{\text{clim}, s})$$

### Additive Decomposition of M6 (All Oceans) vs M0 (Climatology)

| Lead Horizon & Season | Obs ($N_s$) | Weight ($w_s$) | Climatology MSE | Multi-Ocean MSE | Season $\Delta\text{MSE}$ | Weighted Contribution ($w_s \Delta\text{MSE}_s$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Lead 1 Month ($t+1$):** | | | | | | |
| • Kiremt Core (JAS) | 24 | 0.250 | 0.2745 | 0.2432 | -0.0314 | **-0.0078** |
| • Belg Rains (MAM) | 24 | 0.250 | 0.5896 | 0.4048 | -0.1848 | **-0.0462** |
| • Bega Dry Season (ONDJ) | 32 | 0.333 | 1.5637 | 0.7629 | -0.8008 | **-0.2669** |
| • Transition: February | 8 | 0.083 | 0.4491 | 1.5384 | +1.0893 | **+0.0908** |
| • Transition: June | 8 | 0.083 | 1.0102 | 0.7805 | -0.2297 | **-0.0191** |
| **Total Pooled ($N=96$)** | **96** | **1.000** | **0.8588** | **0.6096** | **-0.2493** | **-0.2493** |
| **Lead 2 Months ($t+2$):** | | | | | | |
| • Kiremt Core (JAS) | 24 | 0.250 | 0.2745 | 0.3355 | **+0.0609** | **+0.0152 (Worse)** |
| • Belg Rains (MAM) | 24 | 0.250 | 0.5896 | 0.7653 | **+0.1756** | **+0.0439 (Worse)** |
| • Bega Dry Season (ONDJ) | 32 | 0.333 | 1.5637 | 1.1365 | -0.4272 | **-0.1424 (Better)** |
| • Transition: February | 8 | 0.083 | 0.4491 | 0.7801 | **+0.3309** | **+0.0276 (Worse)** |
| • Transition: June | 8 | 0.083 | 1.0102 | 1.0694 | **+0.0592** | **+0.0049 (Worse)** |
| **Total Pooled ($N=96$)** | **96** | **1.000** | **0.8588** | **0.8080** | **-0.0508** | **-0.0508** |
| **Lead 3 Months ($t+3$):** | | | | | | |
| • Kiremt Core (JAS) | 24 | 0.250 | 0.2745 | 0.2877 | **+0.0132** | **+0.0033 (Worse)** |
| • Belg Rains (MAM) | 24 | 0.250 | 0.5896 | 0.6499 | **+0.0603** | **+0.0151 (Worse)** |
| • Bega Dry Season (ONDJ) | 32 | 0.333 | 1.5637 | 1.4576 | -0.1061 | **-0.0354 (Better)** |
| • Transition: February | 8 | 0.083 | 0.4491 | 0.6280 | **+0.1789** | **+0.0149 (Worse)** |
| • Transition: June | 8 | 0.083 | 1.0102 | 1.0671 | **+0.0569** | **+0.0047 (Worse)** |
| **Total Pooled ($N=96$)** | **96** | **1.000** | **0.8588** | **0.8616** | **+0.0027** | **+0.0027 (Worse)** |

### Mathematical Finding:
At Lead 2, outside of Bega, **every single rainy season and transition month has higher MSE than Climatology** ($\text{JAS: } +0.0609$, $\text{MAM: } +0.1756$, $\text{Feb: } +0.3309$, $\text{Jun: } +0.0592$). The pooled net difference of $-0.0508$ is driven entirely by the dry Bega winter ($-0.1424$). At Lead 3, the total pooled $\Delta\text{MSE}$ is positive ($+0.0027$), confirming zero skill over climatology.

---

## 4. Chronological & Alignment Verification

To confirm that row indexing reflects genuine $t+h$ forecasting without look-ahead:
1. **Consecutive Order:** All 528 rows of `df_master` are in strict chronological order from 1981-01-01 to 2024-12-01 (frequency: `MS`, monthly start, zero duplicates, zero missing dates).
2. **Causal Alignment:** For holdout month $t$ (e.g. 2016-01) at lead $h=1$, features are queried strictly at index $t-1$ (2015-12). Predictors are strictly causal $X_{\le t-h}$.
3. **No Filtering Shifts:** The test dataframe is indexed continuously from integer rows $420$ to $515$ ($96$ months). Row operations use absolute position offsets (`indices - h`), guaranteeing that every prediction uses observations from exactly $h$ months prior.
4. **Target Calculation:** $\text{SPI-3}_t$ is calculated from rainfall up to month $t$. The Gamma distribution parameters $(\alpha_{\text{train}}, \beta_{\text{train}}, p_{0,\text{train}})$ are estimated strictly on pre-2016 historical months ($1981 \le \text{year} < 2016$), preventing test-set calibration leakage.

---

## 5. Atmospheric Bridge & Moisture Transport: Physical Protocol

To establish whether the Indian Ocean teleconnection (M4) is physical or spurious:
$$\text{Indian Ocean DMI / Pacific ENSO} \longrightarrow \text{Regional Wind & Pressure Fields} \longrightarrow \vec{Q} = \frac{1}{g} \int_{p_s}^{p_{\text{top}}} q \vec{v} \, dp \longrightarrow -\nabla \cdot \vec{Q} \longrightarrow \text{Tekezé Rainfall}$$

### Highlands Elevation Masking Protocol
- The Tekezé River Basin originates in the Ethiopian Highlands (elevations exceeding 2,500–4,000 m).
- At high elevations, the surface atmospheric pressure $p_s$ is often between $700\text{ hPa}$ and $800\text{ hPa}$.
- **Protocol:**
  1. Standard pressure levels such as $850\text{ hPa}$ lie **below the physical ground surface** across substantial portions of the basin. Reanalysis values at those levels represent fictitious subterranean extrapolation.
  2. All pressure levels with $p > p_s$ must be explicitly masked out.
  3. Vertical moisture integration will integrate strictly from true surface pressure upward: $\vec{Q} = \frac{1}{g} \sum_{p_k \le p_s} q_k \vec{v}_k \Delta p_k$.
  4. Diagnostics will focus on levels remaining strictly above regional topography ($700\text{ hPa}$ and $500\text{ hPa}$), coupled with surface-level fluxes.
