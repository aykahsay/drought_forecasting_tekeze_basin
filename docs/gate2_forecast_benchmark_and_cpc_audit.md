# Scientific Audit: Canonical Forecast Benchmark, Spatial Extraction & Temporal Evaluation

**Study Area:** Tanqua Abergele Woreda & Tekezé River Basin, Northern Ethiopia  
**Primary Target Metric:** 3-Month Standardized Precipitation Index ($\text{SPI-3}$)  
**Complementary Benchmark Target:** Future Monthly Rainfall Anomaly ($P_{t+h} - \bar{P}_{\text{month}}$, mm)  
**Boundary Provenance:** Official Ethiopia National Administrative Boundaries (CSA/EDRI, EPSG:4326, SHA-256: `90BB8FFF...E22B`)  
**Evaluation Windows:**
1. *Fixed-Holdout Ablation:* 2016-01 to 2023-12 (96 continuous months, pre-2016 fixed training baseline, $\alpha=2.0$).
2. *Retrospective Walk-Forward Evaluation:* 2017-01 to 2024-12 (96 continuous months, dynamic expanding-window updating, lead-specific validated $\alpha$).  
**Governance Standard:** Gate 1 & Gate 2 Scientific Quality Standards, Strictly Zero Synthetic Data Rule  

---

## Executive Summary & Core Scientific Insights

1. **Two Distinct Experimental Paradigms:**
   - **Experiment 1 (Fixed-Holdout Ablation, 2016–2023):** Evaluates performance under a static historical training design ($1981\text{-}03$ to $2015\text{-}12$, 418 continuous months) with fixed Ridge shrinkage ($\alpha=2.0$).
   - **Experiment 2 (Expanding-Window Walk-Forward, 2017–2024):** Evaluates performance under a simulated operational updating process, where models are re-fitted at each monthly forecast origin $t$ strictly on observed historical pairs ($\tau + h \le t$), using lead-specific regularization parameters selected during validation ($2011\text{--}2016$).
   - *Designation Note:* The 2017–2024 period is properly designated as a **withheld retrospective walk-forward evaluation period**, not an untouched blind test set, because prior exploratory experiments informed iterative model development.

2. **Ocean Basin Teleconnection Findings:**
   - **Indian Ocean Dipole (IOD DMI):** The strongest single-ocean candidate across both evaluation regimes. In the rolling-origin evaluation, Model $M_4$ achieves $\text{RMSE} = 0.9010$ at Lead 2 (vs Local AR $M_2$ $\text{RMSE} = 0.9203$, $\Delta\text{RMSE} = -0.0193$, 95% CI: $[-0.0355, -0.0023]$) and $\text{RMSE} = 0.9362$ at Lead 3 (vs $M_2$ $0.9474$, $\Delta\text{RMSE} = -0.0112$, 95% CI: $[-0.0202, -0.0008]$). However, at Lead 1, the 95% confidence intervals straddle zero in both experiments ($[-0.0243, +0.0004]$ in fixed holdout, $[-0.0262, +0.0034]$ in rolling origin), so an incremental advantage over local autoregression is not established at the 95% confidence level.
   - **Multi-Ocean Coupling ($M_6$) vs Single Basin ($M_4$):** Adding Pacific and Atlantic predictors did not demonstrate a consistent, statistically robust improvement over Indian Ocean information alone. At Lead 2, $M_6$ has higher point error than $M_4$ ($0.9057$ vs $0.9010$); at Lead 3, point estimates are virtually indistinguishable ($0.9361$ vs $0.9362$), with overlapping uncertainty intervals.
   - **Pacific ENSO (Niño 3.4):** Across both evaluation designs, linear regression on Niño 3.4 consistently adds noise rather than predictive skill ($\Delta\text{RMSE} \ge 0$).
   - **Lead 3 Correlation Caution:** The rolling-origin $M_4$ correlation at Lead 3 ($r = +0.0578$) is near-zero. Although numerically positive, that fact alone does not demonstrate predictive skill; comparisons against climatology and local autoregression with uncertainty intervals remain the appropriate benchmark.

3. **Target Sensitivity: Overlapping $\text{SPI-3}$ vs Pure Future Monthly Rainfall Anomaly:**
   - In a complementary benchmark predicting **pure future 1-month rainfall anomalies** ($y_{t+h} = P_{t+h} - \bar{P}_{\text{month}}$, zero window overlap across all leads):
     - Zero-anomaly Climatology achieves $\text{RMSE} = 26.93\text{ mm}$.
     - None of the linear statistical models (local AR or ocean basins) beats Climatology out-of-sample ($\text{RMSE} = 26.94\text{ to } 28.26\text{ mm}$, negative correlations).
   - *Defensible Scientific Conclusion:* The results are consistent with overlapping rainfall windows contributing substantially to short-lead $\text{SPI-3}$ prediction skill. The current experiments do not demonstrate corresponding skill for future monthly rainfall anomalies.

4. **Seasonal Error Decomposition & Statistical Gain:**
   - Seasonal MSE partitioning demonstrates that the pooled error reduction of multi-ocean forecasts at Lead 2 is generated during the **Bega season (Oct–Jan)**. During the main Kiremt monsoon (JAS), Belg rains (MAM), and transition months, ocean model errors exceed Climatology.
   - *Impact Qualification:* Bega is identified as the calendar season contributing most to the pooled statistical gain; this finding describes statistical error timing and does not make claims regarding agricultural vulnerability.

5. **Spatial Extraction & Mathematical Precision:**
   - Tanqua Abergele extraction uses the **official 16-kebele MultiPolygon** ($0.11993\text{ sq deg}$, fill fraction $58.41\%$ of bounding box), isolating 71 intersecting $0.05^\circ$ CHIRPS cells.
   - Planar cosine-latitude weighting was audited against exact authalic spherical integration, confirming an absolute weight difference of $< 10^{-15}$ ($r = 1.0000000000$).

---

## 1. Experiment 1: Fixed-Holdout Ablation Benchmark (2016–2023)

All models were trained strictly on the pre-2016 baseline ($1981\text{-}03$ to $2015\text{-}12$, 418 continuous months), with standardized features and identical Ridge regularization ($\alpha = 2.0$), evaluated on the 96 continuous holdout months (2016-01 to 2023-12).

### Multi-Lead Ablation Performance Summary

| Model | Inputs / Feature Formulation | Lead 1 RMSE ($r$) | Lead 2 RMSE ($r$) | Lead 3 RMSE ($r$) | Primary Scientific Finding |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **$M_0$: Climatology** | Historical mean ($E[y] = 0.0$) | 0.9267 (—) | 0.9267 (—) | **0.9267** (—) | Reference standard for zero-skill |
| **$M_1$: Persistence** | $\text{SPI-3}_{t-h}$ | 0.8910 ($0.525$) | 1.1548 ($0.202$) | 1.3693 ($-0.127$) | Decays as window overlap vanishes |
| **$M_2$: Local Climate** | $M_1 + \sin/\cos(\text{month})$ | 0.7918 ($0.524$) | 0.9145 ($0.198$) | 0.9376 ($-0.143$) | Seasonal cycle stabilizes autoregression |
| **$M_3$: Pacific Only** | $M_2 + \text{Niño 3.4}_{t-h, t-h-6}$ | 0.7934 ($0.522$) | 0.9224 ($0.177$) | 0.9520 ($-0.180$) | Adds noise; degrades performance |
| **$M_4$: Indian Only** | $M_2 + \text{IOD DMI}_{t-h}$ | **0.7807** ($0.540$) | **0.8968** ($0.247$) | **0.9220** ($+0.040$) | Strongest single-ocean candidate |
| **$M_5$: Atlantic Only** | $M_2 + \text{Atlantic Grad}_{t-h}$ | 0.7915 ($0.525$) | 0.9133 ($0.204$) | 0.9331 ($-0.046$) | Minimal incremental value |
| **$M_6$: All 3 Oceans** | $M_2 + \text{Pacific} + \text{Indian} + \text{Atl}$ | 0.7808 ($0.541$) | 0.8989 ($0.244$) | 0.9282 ($+0.021$) | No robust advantage over $M_4$ alone |

### Paired Calendar Year-Block Bootstrap Analysis (8 Years Jointly Resampled, B = 2,000, seed = 42)

To preserve within-year serial autocorrelation, 8 complete calendar years (2016 to 2023) were resampled jointly with replacement:

$$\Delta\text{RMSE}^* = \text{RMSE}(y^*, \hat{y}_{\text{model}}^*) - \text{RMSE}(y^*, \hat{y}_{\text{baseline}}^*)$$

| Lead Horizon & Comparison | Metric ($\Delta\text{RMSE}$) | 95% Year-Block Confidence Interval | Statistical Inference Interpretation |
| :--- | :---: | :---: | :--- |
| **Lead 1 Month ($h=1$):** | | | |
| • $M_2$ (Local AR) vs $M_0$ (Clim) | **-0.1349** | $[-0.2305, -0.0096]$ | Statistically robust improvement over Climatology |
| • $M_4$ (Indian) vs $M_2$ (Local AR) | **-0.0111** | $[-0.0243, +0.0004]$ | **Interval includes zero**; improvement not established at 95% level |
| • $M_3$ (Pacific) vs $M_2$ (Local AR) | **+0.0016** | $[-0.0036, +0.0065]$ | Interval straddles zero; point estimate adds error |
| • $M_6$ (All Oceans) vs $M_2$ (Local) | **-0.0110** | $[-0.0317, +0.0047]$ | Interval includes zero; no robust advantage over Local AR |
| • $M_6$ (All Oceans) vs $M_0$ (Clim) | **-0.1459** | $[-0.2513, -0.0167]$ | Statistically robust improvement over Climatology |
| **Lead 2 Months ($h=2$):** | | | |
| • $M_4$ (Indian) vs $M_2$ (Local AR) | **-0.0177** | $[-0.0521, +0.0051]$ | **Interval includes zero**; suggestive point gain, not significant |
| • $M_6$ (All Oceans) vs $M_2$ (Local) | **-0.0156** | $[-0.0527, +0.0120]$ | Interval includes zero; inconclusive |
| • $M_6$ (All Oceans) vs $M_0$ (Clim) | **-0.0278** | $[-0.0744, +0.0268]$ | Interval includes zero; indistinguishable from Climatology |
| **Lead 3 Months ($h=3$):** | | | |
| • $M_4$ (Indian) vs $M_0$ (Clim) | **-0.0047** | $[-0.0421, +0.0298]$ | Interval includes zero; indistinguishable from Climatology |
| • $M_6$ (All Oceans) vs $M_0$ (Clim) | **+0.0015** | $[-0.0404, +0.0344]$ | Interval includes zero; point estimate worse than Climatology |
| • $M_6$ (All Oceans) vs $M_1$ (Pers) | **-0.4411** | $[-0.6494, -0.2252]$ | Substantial error reduction against decaying persistence |

*Note on Bootstrap Inference:* The bootstrap distribution is centered on the sample difference $\widehat{\Delta\text{RMSE}}$ and reflects estimation uncertainty under calendar-year dependence. Where intervals include zero, the evidence does not establish a clear directional difference at the stated 95% confidence level.

---

## 2. Spatial Extraction & Geometry Verification

### Boundary Provenance & Administrative Delineation
- **Official Data Source:** Ethiopia National Administrative Boundaries FeatureServer (Central Statistical Agency / OCHA / EDRI).
- **Coordinate Reference System (CRS):** Geographic WGS84 (EPSG:4326).
- **Boundary File:** `data/spatial/processed/tekeze_basin_kebeles_intersected.geojson` (SHA-256 Checksum: `90BB8FFF778EBCCA37034858108EC30873E1BA36B7636C029EF003686C04E22B`).
- **Aggregated Units:** Exactly 16 discrete kebele polygons within Tanqua Abergele Woreda aggregated via `shapely.ops.unary_union`.
- **True Polygon Area:** **$0.11993\text{ sq deg}$** (approx $1,420\text{ km}^2$).
- **Bounding Box Area:** **$0.20534\text{ sq deg}$**.
- **Polygon Fill Ratio:** **$58.41\%$**. Naive rectangular extraction includes $41.59\%$ spurious land area from adjacent woredas (Kola Tembien, Seharti Samre, Naeder Adet).

### Mathematical Audit: Planar Cosine vs Exact Spherical Authalic Area Weighting
CHIRPS Africa grid cells ($0.05^\circ \times 0.05^\circ$) were intersected with the woreda MultiPolygon, isolating **71 discrete grid cells** (row indices 527–536, column indices 1172–1181). We audited the planar cosine approximation against exact authalic spherical integration:
$$\text{Area}_{\text{authalic}} = R^2 \Delta\lambda (\sin\phi_{\text{top}} - \sin\phi_{\text{bot}})$$
- **Max Absolute Weight Difference:** **$5.24 \times 10^{-16}$** (machine precision).
- **Correlation Between Weighting Schemes:** **$r = 1.0000000000$**.
- *Mathematical Explanation:* Because $\Delta\phi = 0.05^\circ$ ($0.000873\text{ rad}$) is identical across all grid cells, the second-order term $\sin(\Delta\phi/2) / (\Delta\phi/2) \approx 1 - (\Delta\phi)^2 / 24$ is constant to within $3 \times 10^{-8}$ and cancels out completely upon normalization. Planar cosine weighting is mathematically equivalent to authalic spherical weighting for this domain.

### Basin vs Woreda Distinction
- Tanqua Abergele Mean Monthly Precipitation: $63.48\text{ mm/mo}$ ($761.75\text{ mm/yr}$).
- Complete Tekezé River Basin Mean Monthly Precipitation: $72.23\text{ mm/mo}$ ($866.76\text{ mm/yr}$).
- While the two series are correlated across 528 months ($r = 0.9761$), they represent distinct hydrological scales. Tanqua Abergele woreda polygon extraction is maintained as the primary target.

---

## 3. Seasonal Additive MSE Decomposition (All 96 Months)

All 96 holdout months (2016–2023) were partitioned into calendar seasons without omissions:
$$\Delta \text{MSE} = \sum_{s} w_s (\text{MSE}_{\text{ocean}, s} - \text{MSE}_{\text{clim}, s})$$

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

### Finding & Impact Qualification:
At Lead 2, outside of Bega, **every single rainy season and transition month has higher MSE than Climatology** ($\text{JAS: } +0.0609$, $\text{MAM: } +0.1756$, $\text{Feb: } +0.3309$, $\text{Jun: } +0.0592$). The pooled net difference of $-0.0508$ is driven entirely by Bega ($-0.1424$). This demonstrates that pooled statistical metrics can mask degraded accuracy during the main agricultural seasons; this finding describes statistical error timing and does not make claims regarding dry-season agricultural vulnerability.

---

## 4. Chronological & Alignment Verification

1. **Consecutive Order:** All 528 rows of `df_master` are in strict chronological order from 1981-01-01 to 2024-12-01 (frequency: `MS`, monthly start, zero missing dates).
2. **Causal Alignment:** For holdout month $t$ (e.g. 2016-01) at lead $h=1$, features are queried strictly at index $t-1$ (2015-12). Predictors are strictly causal $X_{\le t-h}$.
3. **SPI-3 Calibration Audit:**
   - Evaluated using 3-month rolling sums of precipitation.
   - **Calendar-Month Specificity:** Parameters $(\alpha_m, \beta_m, p_{0,m})$ are fitted **separately for each calendar month $m \in \{1, \dots, 12\}$** to capture month-specific variance and zero-rainfall probabilities.
   - **Training-Only Estimation:** Calibration parameters are estimated strictly on the pre-2016 historical baseline ($1981 \le \text{year} < 2016$), preventing test-set calibration leakage.

---

## 5. Experiment 2: Retrospective Expanding-Window Walk-Forward Benchmark (2017–2024)

- **Evaluation Window:** 2017-01 to 2024-12 (96 continuous months).
- **Validation Period:** 2011-01 to 2016-12 (used to select Ridge regularization: $\alpha=50.0$ at Lead 1, $\alpha=100.0/500.0$ at Lead 2, $\alpha=500.0$ at Lead 3).
- **Auditable Prediction Table:** [`data/processed/rolling_origin_walkforward_auditable_predictions_2017_2024.csv`](file:///c:/Users/User/Desktop/AgriMinds/data/processed/rolling_origin_walkforward_auditable_predictions_2017_2024.csv) ($288$ rows).
- **Independent Verification:** Verified via [`scripts/audit_and_reproduce_rolling_origin.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/audit_and_reproduce_rolling_origin.py).

### Audited Rolling-Origin Performance Summary ($\text{SPI-3}$)

| Lead Horizon & Model | Rolling RMSE | MAE | Pearson $r$ | $\Delta\text{RMSE}$ vs Climatology ($M_0$) | $\Delta\text{RMSE}$ vs Local AR ($M_2$) | Paired 8-Year Bootstrap 95% CI vs $M_2$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Lead 1 Month ($h=1$):** | | | | | | |
| • $M_0$: Climatology | 0.9475 | 0.7357 | Undefined (Const 0.0) | Reference (0.0) | — | — |
| • $M_1$: Persistence | 0.8945 | 0.6651 | 0.5312 | -0.0530 | +0.1034 | $[+0.0401, +0.1712]$ |
| • $M_2$: Local Climate AR | 0.7911 | 0.5923 | 0.5294 | **-0.1564** | Reference (0.0) | — |
| • $M_3$: Pacific Informed | 0.7911 | 0.5941 | 0.5303 | -0.1564 | +0.0000 | $[-0.0040, +0.0040]$ |
| • $M_4$: Indian Ocean (IOD) | **0.7807** | **0.5912** | **0.5405** | **-0.1668** | **-0.0104** | $[-0.0262, +0.0034]$ |
| • $M_5$: Atlantic Informed | 0.7915 | 0.5925 | 0.5293 | -0.1560 | +0.0004 | $[-0.0019, +0.0025]$ |
| • $M_6$: All 3 Oceans Coupled | 0.7811 | 0.5961 | 0.5408 | -0.1664 | -0.0100 | $[-0.0311, +0.0063]$ |
| **Lead 2 Months ($h=2$):** | | | | | | |
| • $M_0$: Climatology | 0.9475 | 0.7357 | Undefined (Const 0.0) | Reference (0.0) | — | — |
| • $M_1$: Persistence | 1.1627 | 0.8985 | 0.2066 | +0.2152 | +0.2424 | $[+0.1245, +0.3701]$ |
| • $M_2$: Local Climate AR | 0.9203 | 0.7328 | 0.2025 | -0.0272 | Reference (0.0) | — |
| • $M_3$: Pacific Informed | 0.9207 | 0.7294 | 0.2030 | -0.0268 | **+0.0004** | $[-0.0190, +0.0236]$ |
| • $M_4$: Indian Ocean (IOD) | **0.9010** | **0.7284** | **0.2504** | **-0.0465** | **-0.0193** | $[-0.0355, -0.0023]$ |
| • $M_5$: Atlantic Informed | 0.9205 | 0.7322 | 0.2046 | -0.0270 | +0.0002 | $[-0.0048, +0.0050]$ |
| • $M_6$: All 3 Oceans Coupled | 0.9057 | 0.7224 | 0.2522 | -0.0418 | -0.0146 | $[-0.0390, +0.0169]$ |
| **Lead 3 Months ($h=3$):** | | | | | | |
| • $M_0$: Climatology | 0.9475 | 0.7357 | Undefined (Const 0.0) | Reference (0.0) | — | — |
| • $M_1$: Persistence | 1.3885 | 1.0738 | -0.1320 | +0.4410 | +0.4411 | $[+0.2190, +0.6654]$ |
| • $M_2$: Local Climate AR | 0.9474 | 0.7323 | -0.0974 | -0.0001 | Reference (0.0) | — |
| • $M_3$: Pacific Informed | 0.9480 | 0.7354 | -0.0665 | +0.0005 | **+0.0006** | $[-0.0080, +0.0093]$ |
| • $M_4$: Indian Ocean (IOD) | **0.9362** | **0.7273** | **+0.0578** | **-0.0113** | **-0.0112** | $[-0.0202, -0.0008]$ |
| • $M_5$: Atlantic Informed | 0.9469 | 0.7314 | -0.0542 | -0.0006 | -0.0005 | $[-0.0063, +0.0063]$ |
| • $M_6$: All 3 Oceans Coupled | 0.9361 | 0.7291 | +0.0632 | -0.0114 | -0.0113 | $[-0.0254, +0.0029]$ |

*Statistical Assessment:*
- At Lead 1, the 95% bootstrap interval for $M_4$ vs $M_2$ ($[-0.0262, +0.0034]$) includes zero; no statistically robust gain over Local AR is demonstrated.
- At Lead 2, $M_4$ exhibits lower RMSE than $M_2$ (interval $[-0.0355, -0.0023]$ excludes zero). $M_6$ has higher error than $M_4$ ($0.9057$ vs $0.9010$).
- At Lead 3, point-estimate RMSEs for $M_4$ ($0.9362$) and $M_6$ ($0.9361$) are virtually identical. The correlation $r = +0.0578$ is near zero and does not establish predictive skill.

---

## 6. Complementary Benchmark: Pure Future Monthly Rainfall Anomaly

To isolate whether ocean indices predict genuinely future rainfall rather than tracking overlapping rainfall within $\text{SPI-3}$, we tested the exact same walk-forward framework on **pure future 1-month precipitation anomalies** ($y_{t+h} = P_{t+h} - \bar{P}_{\text{month}}$, mm), which have **zero moving-window overlap** across all horizons (results saved in [`data/processed/walkforward_rainfall_anomaly_predictions_2017_2024.csv`](file:///c:/Users/User/Desktop/AgriMinds/data/processed/walkforward_rainfall_anomaly_predictions_2017_2024.csv)):

| Model | Lead 1 RMSE ($r$) | Lead 2 RMSE ($r$) | Lead 3 RMSE ($r$) | Core Empirical Finding |
| :--- | :---: | :---: | :---: | :--- |
| **$M_0$: Climatology ($0.0\text{ mm}$ Anomaly)** | **26.93 mm** (—) | **26.93 mm** (—) | **26.93 mm** (—) | **Unconditional reference baseline** |
| **$M_1$: Persistence** | 41.81 mm ($-0.231$) | 40.32 mm ($-0.144$) | 38.07 mm ($-0.020$) | Fails catastrophically (negative $r$) |
| **$M_2$: Local AR** | 28.25 mm ($-0.285$) | 27.07 mm ($-0.268$) | 27.01 mm ($-0.155$) | Worse than Climatology at all leads |
| **$M_3$: Pacific (Niño 3.4)** | 28.21 mm ($-0.236$) | 27.11 mm ($-0.041$) | 27.09 mm ($-0.031$) | No skill over Climatology |
| **$M_4$: Indian Ocean (IOD)** | 28.21 mm ($-0.264$) | 27.05 mm ($-0.134$) | 26.99 mm ($-0.063$) | Lowest error among models, but still $\ge M_0$ |
| **$M_6$: All 3 Oceans Coupled** | 28.05 mm ($-0.198$) | 26.94 mm ($-0.025$) | 27.03 mm ($-0.034$) | Approaches Climatology at Lead 2 ($26.94$ vs $26.93$) |

*Defensible Scientific Conclusion:*
The results are consistent with overlapping rainfall windows contributing substantially to short-lead $\text{SPI-3}$ prediction skill. The current experiments do not demonstrate corresponding skill for future monthly rainfall anomalies.

---

## 7. Temporal Dependence & Degrees of Freedom Audit

- **Measured Autocorrelation (1981–2024, $N=526$ Continuous $\text{SPI-3}$ Months):**
  - $\rho_1 = +0.6448$ (shares 2 of 3 rainfall months; $66.7\%$ calendar overlap).
  - $\rho_2 = +0.3358$ (shares 1 of 3 rainfall months; $33.3\%$ calendar overlap).
  - $\rho_3 = +0.0409$ (shares 0 rainfall months; orthogonal window).
- **Effective Sample Size:**
  $$N_{\text{eff}} = N \frac{1 - \rho_1}{1 + \rho_1} = 526 \times \frac{1 - 0.6448}{1 + 0.6448} = \mathbf{113.6 \text{ independent degrees of freedom}}$$
  Nominal sample size ($N=526$) overestimates degrees of freedom by a factor of $4.63\times$. Statistical tests that assume i.i.d. observations severely inflate type-I error.

---

## 8. Atmospheric Bridge Protocol & Working Hypotheses

The following mechanisms remain **physical working hypotheses**, not established conclusions:
1. **Indian Ocean Low-Level Moisture Transport Hypothesis:** The proposition that positive IOD anomalies steer anomalous low-level easterly moisture fluxes into the Ethiopian Highlands during post-monsoon months is physically plausible, but has not yet been demonstrated by atmospheric circulation fields.
2. **Pacific ENSO Remote Teleconnection Hypothesis:** The proposition that Pacific teleconnections fail linearly due to complex Walker circulation modulation and non-linear ITCZ displacements remains a hypothesis.
3. **Highlands Elevation Masking Protocol:**
   - Surface pressure across the upper Tekezé Basin drops to $700\text{--}800\text{ hPa}$.
   - Reanalysis levels at $850\text{ hPa}$ represent subterranean extrapolation across substantial portions of the basin.
   - Any physical moisture transport diagnostic must integrate strictly from surface pressure upward: $\vec{Q} = \frac{1}{g} \sum_{p_k \le p_s} q_k \vec{v}_k \Delta p_k$.

---

## 9. Canonical Conclusion

The fixed-holdout and rolling-origin experiments identify the Indian Ocean Dipole index as a promising candidate predictor for $\text{SPI-3}$ at selected forecast horizons. However, its incremental predictive value is not consistently established across all leads, evaluation designs, and uncertainty analyses. The all-ocean model does not demonstrate a robust advantage over the Indian Ocean-only model. In a complementary benchmark, none of the evaluated linear models outperforms the zero-anomaly climatology for future monthly rainfall anomalies. This contrast suggests that the apparent short-lead $\text{SPI-3}$ skill may partly reflect temporal overlap in the rolling precipitation index rather than an equivalent ability to predict new rainfall.

Seasonal error decomposition further shows that pooled improvements can conceal worse performance during agriculturally important rainy seasons. These results motivate further testing using carefully calibrated $\text{SPI-3}$, leakage-safe rainfall anomalies, and seasonal rainfall targets, followed by independent evaluation of the atmospheric processes linking ocean variability to rainfall in Tanqua Abergele.
