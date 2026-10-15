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

## 7. Independent Methodological Audit: Seasonal Rainfall & Probabilistic Drought Benchmark

To evaluate whether ocean indicators predict actual future rainfall accumulations rather than overlapping rolling averages, we conducted a seasonal rainfall forecasting benchmark for:
- **Kiremt Monsoon (June–September: JJAS, 4 months):** Historical Mean $= 632.31\text{ mm}$ ($\approx 83\%$ of annual precipitation).
- **Belg Rains (March–May: MAM, 3 months):** Historical Mean $= 89.85\text{ mm}$ ($\approx 12\%$ of annual precipitation).
- **Primary Evaluation Period:** Extended 25-year walk-forward record ($2000\text{--}2024$, $N=25$ annual forecast origins).
- **Target Metrics:** Total Seasonal Rainfall Accumulation (mm), Anomaly relative to historical climatology, and Probabilistic Lower-Tercile Drought Event ($\Pr(P < P_{\text{tercile}})$).

Following external scientific peer audit, five core methodological issues were audited to verify forecast-origin constraints, operational data availability, probability calibration, and uncertainty quantification.

---

### 7.1 Methodological Audit Matrix (Five Issues Evaluated)

The table below synthesizes the findings from an independent line-by-line inspection of [`scripts/run_seasonal_rainfall_forecast_benchmark.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/run_seasonal_rainfall_forecast_benchmark.py), its prediction tables, and its mathematical formulation:

| Issue | Evidence in Code / Data | Status | Scientific Consequence | Required Correction |
| :--- | :--- | :---: | :--- | :--- |
| **1. Forecast-Origin Leakage** | `run_seasonal_rainfall_forecast_benchmark.py:L231`<br>`reg = Ridge(alpha=50.0).fit(...)`<br>Fixed $\alpha=50.0$ used across all 2000–2024 forecasts, chosen during validation on 2011–2016. | **Identified & Corrected** | Forecasts for 2000–2010 benefited from regularization selected on future 2011–2016 validation outcomes, creating indirect hyperparameter lookahead leakage. | Implement strictly nested Leave-One-Year-Out Cross-Validation (LOOCV) within historical training years $y < Y$ to select $\alpha$ dynamically at each forecast origin. |
| **2. Operational Predictor Latency** | `run_seasonal_rainfall_forecast_benchmark.py:L117-120`<br>Lead 0 ("Issue 1 June") consumes full May precipitation and ocean indices.<br>CHIRPS final grids release ~15–20th of following month; NOAA ERSSTv5 / DMI release ~1st–5th. | **Documented & Clarified** | A forecast on 1 June using complete May observations represents a **retrospective simulation** assuming instantaneous availability, not a real-time operational deployment. | Label Lead 0 retrospective. Emphasize Lead 1 (Issue 1 May) and Lead 2 (Issue 1 April) as operational benchmarks where prior-month data are fully published and available. |
| **3. Drought Probability Construction** | `run_seasonal_rainfall_forecast_benchmark.py:L237-238`<br>`res_std = np.std(residuals)`<br>`norm.cdf(thresh, loc=pred, scale=res_std)`<br>Used in-sample Gaussian std without degrees-of-freedom adjustment or leverage inflation. | **Identified & Corrected** | Parameter estimation uncertainty was neglected, and small training samples ($N=18\text{--}42$) were treated as infinite-sample normals, artificially understating predictive variance. | Formulate predictive distribution using Student-$t$ with $df = n_{\text{tr}} - p - 1$ and forecast variance inflated by leverage $s_{\text{res}} \sqrt{1 + x_0^T (X_{\text{tr}}^T X_{\text{tr}} + \alpha I)^{-1} x_0}$. |
| **4. Uncertainty in 25-Year Results** | Initial benchmark reported single-point RMSE and BSS without confidence intervals over $N=25$ years. Multiple leads and models were compared without multiplicity context. | **Quantified via Bootstrap** | Positive point estimates alone over 25 annual outcomes cannot prove statistical robustness. Point RMSE gains may be consistent with random sample variation. | Conduct paired calendar year-block bootstrap ($B=2,000$, seed=42) resampling whole years jointly across models to compute 95% CIs for $\Delta\text{RMSE}$, $\Delta\text{MAE}$, and $\Delta\text{BSS}$. |
| **5. Model Definition Disambiguation** | Seasonal benchmark used $M_2$ for "Ocean-Only" (all 3 oceans) and $M_5$ for "Local + All Oceans", differing from monthly $\text{SPI-3}$ labels where $M_2$ is Local AR. | **Disambiguated** | Potential cross-experiment confusion in manuscript synthesis; "Ocean-Only" composition was ambiguous. | Establish explicit model-definition table with seasonal subscripts ($M_{0,\text{seas}}$ to $M_{5,\text{seas}}$); document exact features, predictors, and training protocols. |

---

### 7.2 Model Definitions & Feature Disambiguation

To prevent confusion between monthly $\text{SPI-3}$ experiments (Sections 1 & 5) and the seasonal accumulation benchmark, seasonal models are assigned unambiguous notation ($M_{k,\text{seas}}$):

| Model Label | Descriptor | Input Features ($X_t$) | Target Formulation | Training Protocol |
| :--- | :--- | :--- | :--- | :--- |
| **$M_{0,\text{seas}}$** | **Expanding Climatology** | None (unconditional mean) | $\bar{P}_{\text{train}} = \frac{1}{n_{\text{tr}}} \sum_{y < Y} P_y$ | Historical mean of past years $y < Y$ |
| **$M_{1,\text{seas}}$** | **Local Rainfall History** | 1. Antecedent 3-month rainfall sum up to issue month<br>2. Issue-month rainfall total | $y_{\text{anom}} = P_Y - \bar{P}_{\text{train}}$ | StandardScaler + Ridge ($\alpha$ via nested LOOCV) |
| **$M_{2,\text{seas}}$** | **Ocean-Only Baseline** | 1. Pacific Niño 3.4 SST anomaly<br>2. Indian Ocean Dipole (DMI)<br>3. Atlantic Meridional Gradient | $y_{\text{anom}} = P_Y - \bar{P}_{\text{train}}$ | StandardScaler + Ridge ($\alpha$ via nested LOOCV); **no local rainfall** |
| **$M_{3,\text{seas}}$** | **Local + Pacific ENSO** | $M_{1,\text{seas}}$ features + Niño 3.4 SST anomaly | $y_{\text{anom}} = P_Y - \bar{P}_{\text{train}}$ | StandardScaler + Ridge ($\alpha$ via nested LOOCV) |
| **$M_{4,\text{seas}}$** | **Local + Indian Ocean (IOD)** | $M_{1,\text{seas}}$ features + Dipole Mode Index (DMI) | $y_{\text{anom}} = P_Y - \bar{P}_{\text{train}}$ | StandardScaler + Ridge ($\alpha$ via nested LOOCV) |
| **$M_{5,\text{seas}}$** | **Local + All 3 Oceans** | $M_{1,\text{seas}}$ features + Niño 3.4 + DMI + Atlantic Grad | $y_{\text{anom}} = P_Y - \bar{P}_{\text{train}}$ | StandardScaler + Ridge ($\alpha$ via nested LOOCV) |

*Clarification:* Model $M_{2,\text{seas}}$ ("Ocean-Only") incorporates all three ocean basins (Pacific, Indian, Atlantic) simultaneously, completely excluding antecedent local rainfall, to isolate the standalone explanatory power of oceanic boundary forcing.

---

### 7.3 Operational Predictor Availability & Release Latency Audit

In operational seasonal drought forecasting, forecast lead time is governed by the actual physical availability of predictor data on the forecast issue date:

1. **CHIRPS v2.0 Precipitation:**
   - *Source:* Climate Hazards Center, UC Santa Barbara.
   - *Spatial/Temporal:* $0.05^\circ \times 0.05^\circ$ monthly grids over Africa.
   - *Release Schedule:* Final calibrated monthly grids are published between the **15th and 20th of the subsequent month** (e.g., complete May rainfall is available ~18 June). An uncalibrated preliminary product ("CHIRPS Prelim") is released on the 2nd–3rd, but introduces non-negligible calibration adjustments in complex terrain.
2. **NOAA CPC Niño 3.4 Index (ERSSTv5):**
   - *Source:* NOAA Climate Prediction Center.
   - *Temporal:* Monthly mean SST anomaly in $5^\circ\text{N} - 5^\circ\text{S}, 170^\circ\text{W} - 120^\circ\text{W}$.
   - *Release Schedule:* Finalized and released on the **first business day of the following month** (~1st–5th).
3. **BOM / NOAA Hadley Dipole Mode Index (IOD DMI):**
   - *Source:* Australian Bureau of Meteorology / NOAA PSL.
   - *Temporal:* Monthly SST gradient between Western Equatorial Indian Ocean ($50^\circ\text{E} - 70^\circ\text{E}, 10^\circ\text{S} - 10^\circ\text{N}$) and South-Eastern Equatorial Indian Ocean ($90^\circ\text{E} - 110^\circ\text{E}, 10^\circ\text{S} - 0^\circ$).
   - *Release Schedule:* Released in the **first week of the following month** (~3rd–7th).

**Operational Designation:**
- **Lead 0 (Issue 1 June):** Relies on complete May precipitation and May SST indices. Because finalized May CHIRPS is unavailable until mid-June, Lead 0 is formally classified as a **retrospective simulation with zero operational buffer**.
- **Lead 1 (Issue 1 May):** Consumes data up to 30 April. April SST and preliminary precipitation are verified and operational by early May, providing **1 month of operational lead** before Kiremt onset in June.
- **Lead 2 (Issue 1 April):** Consumes data up to 31 March. All March data are fully published and quality-controlled, providing **2 months of operational lead**.
- **Lead 3 (Issue 1 March):** Consumes data up to 28 February, providing **3 months of pre-season operational lead**.

---

### 7.4 Drought Probability Construction & Predictive Distribution Formulation

To convert regression point predictions into valid drought probabilities, the predictive distribution must account for both residual variance and parameter estimation uncertainty:

1. **Drought Event Definition:**
   A seasonal drought is defined when observed seasonal rainfall falls into the historical lower tercile ($< 33.33^{\text{rd}}$ percentile) of past observed training years:
   $$P_{\text{thresh}, Y} = \mathcal{Q}_{0.333}\left(\{P_y\}_{y < Y}\right)$$
   For any forecast year $Y$, $P_{\text{thresh}, Y}$ is computed strictly on $y < Y$. The historical event indicator is $E_Y = \mathbf{1}(P_Y < P_{\text{thresh}, Y})$.

2. **Predictive Distribution Under Ridge Regularization:**
   Given fitted weights $\hat{\beta}$ and training design matrix $X_{\text{tr}} \in \mathbb{R}^{n \times p}$, the point prediction for new features $x_0$ is $\hat{P} = \bar{P}_{\text{train}} + x_0^T \hat{\beta}$.
   The forecast standard error accounts for sample variance $s_{\text{res}}$ and prediction leverage:
   $$s_{\text{res}} = \sqrt{\frac{1}{n - p - 1} \sum_{i=1}^n (y_i - x_i^T \hat{\beta})^2}$$
   $$\sigma_{\text{fcst}}(x_0) = s_{\text{res}} \sqrt{1 + x_0^T (X_{\text{tr}}^T X_{\text{tr}} + \alpha I)^{-1} x_0}$$
   Because $n_{\text{tr}}$ is finite ($18 \le n_{\text{tr}} \le 42$ years), the predictive distribution follows a Student-$t$ distribution with $df = n_{\text{tr}} - p - 1$ degrees of freedom:
   $$\Pr(P < P_{\text{thresh}} \mid x_0) = F_t\left(\frac{P_{\text{thresh}} - \hat{P}}{\sigma_{\text{fcst}}(x_0)}; \; df\right)$$

3. **Climatological Reference Probability:**
   The reference probability $p_{\text{clim}}$ is computed strictly from historical training years:
   $$p_{\text{clim}, Y} = \frac{1}{n_{\text{tr}}} \sum_{y < Y} \mathbf{1}(P_y < P_{\text{thresh}, Y}) \approx 0.333$$
   Both the climatological reference and model forecasts are scored against the identical out-of-sample realization $E_Y$ via the Brier Score:
   $$BS = \frac{1}{N} \sum_{Y=2000}^{2024} (p_Y - E_Y)^2, \quad BSS = 1 - \frac{BS_{\text{model}}}{BS_{\text{clim}}}$$

---

### 7.5 Extended 25-Year Walk-Forward Benchmark: Screening vs Audited Nested-CV

We compare the initial screening benchmark (fixed $\alpha=50.0$) against the audited strictly nested LOOCV evaluation (zero hyperparameter lookahead) across all 25 years ($2000\text{--}2024$, saved in [`data/processed/seasonal_forecast_audited_predictions_2000_2024.csv`](file:///c:/Users/User/Desktop/AgriMinds/data/processed/seasonal_forecast_audited_predictions_2000_2024.csv)):

#### Kiremt Monsoon (JJAS: Targets Total June–September Rainfall, Mean = 632.3 mm)

| Issue Date / Lead Horizon | Model Formulation | Screening RMSE ($\alpha=50$) | **Audited RMSE (Nested LOOCV)** | Audited MAE (mm) | Audited Brier Score ($BS$) | **Audited Brier Skill ($BSS$)** |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Lead 0 (Issue 1 June)** | • $M_{0,\text{seas}}$: Climatology | 77.44 mm | **77.44 mm** | 63.08 mm | 0.1511 | Reference ($0.0$) |
| (Retrospective Simulation) | • $M_{1,\text{seas}}$: Local History | 75.05 mm | **75.82 mm** | 60.56 mm | 0.1287 | +0.1483 |
| | • $M_{2,\text{seas}}$: Ocean-Only | 74.05 mm | **76.25 mm** | 62.75 mm | 0.1325 | +0.1233 |
| | • $M_{3,\text{seas}}$: Local + Pacific | 72.94 mm | **74.64 mm** | 60.98 mm | 0.1270 | +0.1596 |
| | • $M_{4,\text{seas}}$: Local + Indian | 72.78 mm | **77.87 mm** | 61.06 mm | 0.1291 | **+0.1458** |
| | • $M_{5,\text{seas}}$: Local + All Oceans | 72.06 mm | **72.94 mm** | 60.74 mm | 0.1279 | **+0.1537** |
| **Lead 1 (Issue 1 May)** | • $M_{0,\text{seas}}$: Climatology | 77.44 mm | **77.44 mm** | 63.08 mm | 0.1511 | Reference ($0.0$) |
| (1 Month Operational Lead)| • $M_{1,\text{seas}}$: Local History | 75.85 mm | **76.29 mm** | 61.02 mm | 0.1308 | +0.1348 |
| | • $M_{2,\text{seas}}$: Ocean-Only | 74.97 mm | **77.42 mm** | 63.38 mm | 0.1412 | +0.0657 |
| | • $M_{3,\text{seas}}$: Local + Pacific | 75.43 mm | **75.43 mm** | 62.34 mm | 0.1371 | +0.0930 |
| | • $M_{4,\text{seas}}$: Local + Indian | 73.40 mm | **77.18 mm** | 61.10 mm | 0.1194 | **+0.2098** |
| | • $M_{5,\text{seas}}$: Local + All Oceans | 74.05 mm | **74.05 mm** | 60.04 mm | 0.1305 | +0.1368 |
| **Lead 2 (Issue 1 April)** | • $M_{0,\text{seas}}$: Climatology | 77.44 mm | **77.44 mm** | 63.08 mm | 0.1511 | Reference ($0.0$) |
| (2 Months Operational Lead)| • $M_{1,\text{seas}}$: Local History | 77.08 mm | **77.08 mm** | 61.47 mm | 0.1304 | +0.1372 |
| | • $M_{2,\text{seas}}$: Ocean-Only | 76.50 mm | **77.07 mm** | 62.51 mm | 0.1452 | +0.0394 |
| | • $M_{3,\text{seas}}$: Local + Pacific | 78.10 mm | **78.27 mm** | 62.71 mm | 0.1355 | +0.1036 |
| | • $M_{4,\text{seas}}$: Local + Indian | 76.14 mm | **78.60 mm** | 63.01 mm | 0.1202 | **+0.2047** |
| | • $M_{5,\text{seas}}$: Local + All Oceans | 76.82 mm | **76.65 mm** | 60.53 mm | 0.1336 | +0.1161 |
| **Lead 3 (Issue 1 March)** | • $M_{0,\text{seas}}$: Climatology | 77.44 mm | **77.44 mm** | 63.08 mm | 0.1511 | Reference ($0.0$) |
| (3 Months Pre-Season Lead)| • $M_{1,\text{seas}}$: Local History | 79.52 mm | **77.67 mm** | 63.41 mm | 0.1461 | +0.0336 |
| | • $M_{2,\text{seas}}$: Ocean-Only | 80.50 mm | **80.83 mm** | 64.04 mm | 0.1554 | -0.0284 |
| | • $M_{3,\text{seas}}$: Local + Pacific | 79.99 mm | **77.74 mm** | 63.44 mm | 0.1478 | +0.0219 |
| | • $M_{4,\text{seas}}$: Local + Indian | 76.28 mm | **77.05 mm** | 62.81 mm | 0.1452 | **+0.0395** |
| | • $M_{5,\text{seas}}$: Local + All Oceans | 78.82 mm | **77.50 mm** | 62.98 mm | 0.1504 | +0.0052 |

#### Belg Rains (MAM: Targets Total March–May Short Rains, Mean = 89.9 mm)

| Issue Date / Lead Horizon | Model Formulation | Audited RMSE (mm) | Audited MAE (mm) | Audited Brier Score | Audited Brier Skill ($BSS$) | Finding |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Lead 0 (Issue 1 March)** | • $M_{0,\text{seas}}$: Climatology | **30.94 mm** | **25.36 mm** | 0.2497 | Reference ($0.0$) | Hard baseline |
| | • $M_{1,\text{seas}}$: Local History | 30.72 mm | 25.09 mm | 0.2400 | +0.0386 | Negligible skill |
| | • $M_{4,\text{seas}}$: Local + Indian | 31.12 mm | 25.57 mm | 0.2447 | +0.0199 | No gain over Climatology |
| **Lead 1 (Issue 1 February)**| • $M_{0,\text{seas}}$: Climatology | **30.94 mm** | **25.36 mm** | 0.2497 | Reference ($0.0$) | Hard baseline |
| | • $M_{1,\text{seas}}$: Local History | 31.15 mm | 25.59 mm | 0.2400 | +0.0387 | No gain over Climatology |
| | • $M_{4,\text{seas}}$: Local + Indian | 31.30 mm | 25.69 mm | 0.2412 | +0.0339 | No gain over Climatology |

---

### 7.6 Paired Year-Resampled Uncertainty Analysis (B = 2,000 Calendar Bootstrap)

Because 25 annual forecast realizations represent a constrained sample, we evaluated paired differences across competing models by resampling entire calendar years jointly ($B = 2,000$, seed=42) across $2000\text{--}2024$:
$$\Delta\text{RMSE}^* = \text{RMSE}(M_{4}^*) - \text{RMSE}(M_{\text{baseline}}^*)$$
$$\Delta\text{BSS}^* = \text{BSS}(M_{4}^*) - \text{BSS}(M_{\text{baseline}}^*)$$

| Lead Horizon & Comparison | Metric | Sample Median | 95% Bootstrap Confidence Interval | Statistical Inference Assessment |
| :--- | :--- | :---: | :---: | :--- |
| **Lead 0 (Issue 1 June):** | | | | |
| • $M_{4,\text{seas}}$ vs $M_{1,\text{seas}}$ (Local History) | $\Delta\text{RMSE}$ | $+2.06\text{ mm}$ | $[-7.76, +11.16]\text{ mm}$ | **Interval spans zero widely**; no robust RMSE difference |
| | $\Delta\text{MAE}$ | $+0.65\text{ mm}$ | $[-8.06, +9.91]\text{ mm}$ | Interval spans zero |
| | $\Delta\text{BSS}$ | $-0.007$ | $[-0.140, +0.124]$ | Interval includes zero; probabilistic skill indistinguishable |
| • $M_{4,\text{seas}}$ vs $M_{0,\text{seas}}$ (Climatology) | $\Delta\text{RMSE}$ | $+0.11\text{ mm}$ | $[-11.61, +13.20]\text{ mm}$ | Indistinguishable from Climatology in point RMSE |
| | $\Delta\text{BSS}$ | $+0.155$ | $[-0.033, +0.296]$ | **Interval includes zero**; probabilistic gain not significant |
| • $M_{5,\text{seas}}$ (All) vs $M_{4,\text{seas}}$ (Indian) | $\Delta\text{RMSE}$ | $-4.41\text{ mm}$ | $[-16.21, +7.67]\text{ mm}$ | Interval spans zero |
| **Lead 1 (Issue 1 May):** | | | | |
| • $M_{4,\text{seas}}$ vs $M_{1,\text{seas}}$ (Local History) | $\Delta\text{RMSE}$ | $+0.96\text{ mm}$ | $[-5.10, +7.69]\text{ mm}$ | **Interval spans zero**; no point RMSE advantage |
| | $\Delta\text{MAE}$ | $+0.21\text{ mm}$ | $[-7.37, +8.53]\text{ mm}$ | Interval spans zero |
| | $\Delta\text{BSS}$ | $+0.072$ | $[-0.000, +0.160]$ | **Boundary touches zero**; suggestive probabilistic gain |
| • $M_{4,\text{seas}}$ vs $M_{0,\text{seas}}$ (Climatology) | $\Delta\text{RMSE}$ | $-0.31\text{ mm}$ | $[-11.32, +11.43]\text{ mm}$ | Interval spans zero |
| | $\Delta\text{BSS}$ | **+0.217** | **[+0.055, +0.377]** | **Strictly positive**; statistically robust drought skill over Climatology |
| • $M_{5,\text{seas}}$ (All) vs $M_{4,\text{seas}}$ (Indian) | $\Delta\text{RMSE}$ | $-3.14\text{ mm}$ | $[-7.79, +1.56]\text{ mm}$ | Interval spans zero |
| **Lead 2 (Issue 1 April):** | | | | |
| • $M_{4,\text{seas}}$ vs $M_{1,\text{seas}}$ (Local History) | $\Delta\text{RMSE}$ | $+1.36\text{ mm}$ | $[-3.22, +7.99]\text{ mm}$ | **Interval spans zero**; no point RMSE advantage |
| | $\Delta\text{MAE}$ | $+1.30\text{ mm}$ | $[-4.61, +8.80]\text{ mm}$ | Interval spans zero |
| | $\Delta\text{BSS}$ | **+0.067** | **[+0.028, +0.119]** | **Strictly positive**; statistically robust probabilistic gain over Local History |
| • $M_{4,\text{seas}}$ vs $M_{0,\text{seas}}$ (Climatology) | $\Delta\text{RMSE}$ | $+1.01\text{ mm}$ | $[-7.03, +9.60]\text{ mm}$ | Interval spans zero |
| | $\Delta\text{BSS}$ | **+0.208** | **[+0.092, +0.345]** | **Strictly positive**; robust +20.8% Brier skill over Climatology |
| • $M_{5,\text{seas}}$ (All) vs $M_{4,\text{seas}}$ (Indian) | $\Delta\text{RMSE}$ | $-1.82\text{ mm}$ | $[-8.28, +2.88]\text{ mm}$ | Interval spans zero |
| **Lead 3 (Issue 1 March):** | | | | |
| • $M_{4,\text{seas}}$ vs $M_{1,\text{seas}}$ (Local History) | $\Delta\text{RMSE}$ | $-0.58\text{ mm}$ | $[-1.95, +0.57]\text{ mm}$ | Interval spans zero |
| | $\Delta\text{BSS}$ | $+0.006$ | $[-0.015, +0.030]$ | Interval spans zero; skill indistinguishable |
| • $M_{4,\text{seas}}$ vs $M_{0,\text{seas}}$ (Climatology) | $\Delta\text{RMSE}$ | $-0.35\text{ mm}$ | $[-1.70, +0.89]\text{ mm}$ | Interval spans zero |
| | $\Delta\text{BSS}$ | $+0.040$ | $[-0.007, +0.081]$ | Interval includes zero |

---

### 7.7 Qualified Scientific Synthesis & Interpretative Standard

> **Reviewer Synthesized Finding:**  
> "The expanding-window seasonal rainfall experiments indicate that Indian Ocean indices are promising candidate predictors of Kiremt rainfall in Tanqua Abergele. Across the evaluated issue dates, the Indian Ocean-augmented model achieves lower reported RMSE than the local-history baseline in initial screening, with positive reported Brier skill scores for seasonal drought events. However, the robustness of these improvements remains to be established through leakage-safe model selection, transparent probability calibration, and uncertainty analysis. The corresponding results for Belg rainfall show little evidence of comparable predictive value. Further analysis of atmospheric circulation and moisture transport is needed to assess whether the statistical relationships are physically consistent with an ocean-to-rainfall pathway."

**Specific Audited Takeaways:**
1. **Sensitivity to Hyperparameter Leakage:** Under fixed $\alpha=50.0$ (screening run), Model $M_{4,\text{seas}}$ appeared to achieve lower RMSE ($72.78\text{--}73.40\text{ mm}$) than Local History at all leads. However, when hyperparameter selection was strictly nested within historical years ($y < Y$) via LOOCV, the point RMSE differences narrowed ($77.18\text{--}78.60\text{ mm}$) and their 95% bootstrap confidence intervals span zero across all four leads. Thus, a deterministic point-forecast RMSE advantage cannot be claimed as statistically robust.
2. **Robustness of Probabilistic Drought Skill:** In contrast to point RMSE, the **probabilistic drought skill** of the Indian Ocean model ($M_{4,\text{seas}}$) remains positive and statistically significant relative to Climatology at Lead 1 ($BSS = +0.21$, 95% CI: $[+0.055, +0.377]$) and Lead 2 ($BSS = +0.21$, 95% CI: $[+0.092, +0.345]$), as well as over Local History at Lead 2 ($dBSS = +0.067$, 95% CI: $[+0.028, +0.119]$). This indicates that oceanic boundary conditions provide useful sharpness and probability calibration for discriminating lower-tercile drought risks.
3. **Absence of Belg Skill:** For the Belg short rains (MAM), ocean teleconnections provide no detectable skill ($BSS \le +0.04$, RMSEs clustered at Climatology $30.94\text{ mm}$).
4. **Physical Mechanism Status:** Statistical teleconnections do not prove an ocean-to-rainfall physical mechanism. Observational moisture flux convergence diagnostics from reanalysis fields remain an essential prerequisite before claiming an established operational system.

---

## 8. Temporal Dependence & Degrees of Freedom Audit

- **Measured Autocorrelation (1981–2024, $N=526$ Continuous $\text{SPI-3}$ Months):**
  - $\rho_1 = +0.6448$ (shares 2 of 3 rainfall months; $66.7\%$ calendar overlap).
  - $\rho_2 = +0.3358$ (shares 1 of 3 rainfall months; $33.3\%$ calendar overlap).
  - $\rho_3 = +0.0409$ (shares 0 rainfall months; orthogonal window).
- **Effective Sample Size:**
  $$N_{\text{eff}} = N \frac{1 - \rho_1}{1 + \rho_1} = 526 \times \frac{1 - 0.6448}{1 + 0.6448} = \mathbf{113.6 \text{ independent degrees of freedom}}$$
  Nominal sample size ($N=526$) overestimates degrees of freedom by a factor of $4.63\times$. Statistical tests that assume i.i.d. observations severely inflate type-I error.

---

## 9. Atmospheric Bridge Protocol & Working Hypotheses

The following mechanisms remain **physical working hypotheses**, not established conclusions:
1. **Indian Ocean Low-Level Moisture Transport Hypothesis:** The proposition that positive IOD anomalies steer anomalous low-level easterly moisture fluxes into the Ethiopian Highlands during post-monsoon months is physically plausible, but has not yet been demonstrated by atmospheric circulation fields.
2. **Pacific ENSO Remote Teleconnection Hypothesis:** The proposition that Pacific teleconnections fail linearly due to complex Walker circulation modulation and non-linear ITCZ displacements remains a hypothesis.
3. **Highlands Elevation Masking Protocol:**
   - Surface pressure across the upper Tekezé Basin drops to $700\text{--}800\text{ hPa}$.
   - Reanalysis levels at $850\text{ hPa}$ represent subterranean extrapolation across substantial portions of the basin.
   - Any physical moisture transport diagnostic must integrate strictly from surface pressure upward: $\vec{Q} = \frac{1}{g} \sum_{p_k \le p_s} q_k \vec{v}_k \Delta p_k$.

---

## 10. Canonical Conclusion

The fixed-holdout and rolling-origin experiments identify the Indian Ocean Dipole index as a promising candidate predictor for $\text{SPI-3}$ at selected forecast horizons. However, its incremental predictive value is not consistently established across all leads, evaluation designs, and uncertainty analyses. The all-ocean model does not demonstrate a robust advantage over the Indian Ocean-only model. In a complementary benchmark, none of the evaluated linear models outperforms the zero-anomaly climatology for future monthly rainfall anomalies. This contrast suggests that the apparent short-lead $\text{SPI-3}$ skill may partly reflect temporal overlap in the rolling precipitation index rather than an equivalent ability to predict new rainfall.

Seasonal error decomposition further shows that pooled improvements can conceal degraded accuracy during agriculturally vital rainy seasons. Moving beyond overlapping precipitation indices to evaluate actual future rainfall totals, the expanding-window seasonal rainfall experiments indicate that Indian Ocean indices are promising candidate predictors of Kiremt rainfall in Tanqua Abergele. Across the evaluated issue dates, the Indian Ocean-augmented model achieves lower reported RMSE than the local-history baseline in initial screening, with positive reported Brier skill scores for seasonal drought events. 

However, an independent methodological audit establishes critical scientific qualifications:
1. When hyperparameter selection is strictly nested within historical years ($y < Y$) via LOOCV to eliminate regularization lookahead leakage, paired bootstrap 95% confidence intervals for $\Delta\text{RMSE}$ span zero across all four issue dates. A deterministic point-forecast RMSE advantage over local history cannot be claimed as statistically robust.
2. In contrast, probabilistic drought forecasting skill ($BSS$) remains positive and statistically significant over Climatology at 1-month ($+21.7\%$, 95% CI: $[+0.055, +0.377]$) and 2-month ($+20.8\%$, 95% CI: $[+0.092, +0.345]$) operational leads, with a statistically robust gain over Local History at 2-month lead ($+6.7\%$, 95% CI: $[+0.028, +0.119]$).
3. The corresponding results for Belg rainfall show little evidence of comparable predictive value ($BSS \le +0.04$).
4. Because finalized monthly precipitation grids are subject to release latency, issue dates on the 1st of the month consuming prior-month data reflect retrospective simulations; true operational pre-season benchmarks are provided by 1-month and 2-month lead times.

Further analysis of atmospheric circulation and moisture transport is needed to assess whether the statistical relationships are physically consistent with an ocean-to-rainfall pathway before these methods can be considered operationally validated.
