# Scientific Audit: Drought Forecast Benchmarking, Temporal Alignment & NOAA CPC Ingestion Status

**Study Area:** Tanqua Abergele Woreda & Tekezé River Basin, Northern Ethiopia  
**Target Metric:** 3-Month Standardized Precipitation Index ($\text{SPI-3}$)  
**Evaluation Window:** 2016-01 to 2023-12 (96 Continuous Holdout Calendar Months)  
**Historical Training Period:** 1981-03 to 2015-12 (418 Continuous Historical Months)  
**Governance Standard:** Gate 1 & Gate 2 Scientific Quality Standards, Strictly Zero Synthetic Data Rule  

---

## Executive Scientific Summary & Core Audit Conclusions

1. **Verification of NOAA CPC Daily Temperature Ingestion:**
   - As of the latest automated audit, **10 annual files (120 monthly records, 22.7% of the 44-year archive)** have been fully downloaded, verified with SHA-256 hashes, NetCDF dimension checks (365/366 daily slices), and spatial area-weighting: **1981, 1982, 1983, 1984, 1985, 1986, 1987, 2002, 2015, and 2021**.
   - The remaining 34 years are actively queued and downloading in the background.
   - **Formal Governance Clarification:** The temperature record is **NOT counted as complete** while the background process is running. A formal year-by-year inventory manifest (`cpc_temperature_year_by_year_manifest.json`) tracks verified vs. pending files. In the unified dataset, missing months remain explicitly flagged as `MISSING_DATA` rather than filled with synthetic values.

2. **Causal Lead Alignment & Forecast Timeline:**
   - For any forecast lead horizon $h \in \{1, 2, 3\}$ targeting month $t$, the forecast is issued at the end of month $T = t - h$.
   - Predictors are strictly causal $X_{\le t-h}$. No future climate, ocean, or rainfall observations are used.
   - All four models (Climatology, Persistence, Local Autoregressive, Multi-Ocean Informed) are evaluated on the exact same 96 continuous calendar months (2016-01 to 2023-12).

3. **Structural Autocorrelation Decay in Rolling SPI-3:**
   - $\text{SPI-3}_t$ is based on cumulative precipitation over the 3-month window $\{t-2, t-1, t\}$.
   - At **Lead 1 ($h=1$)**, issued at $t-1$, precipitation for $t-2$ and $t-1$ is already observed. Thus, **$\frac{2}{3}$ of the target window has occurred**, which provides a structural mathematical explanation for why persistence is competitive ($r = 0.525$, $\text{RMSE} = 0.8910$).
   - At **Lead 2 ($h=2$)**, issued at $t-2$, only month $t-2$ has occurred (**$\frac{1}{3}$ of the window**). Overlap decays, and persistence drops to $r = 0.202$, $\text{RMSE} = 1.1548$.
   - At **Lead 3 ($h=3$)**, issued at $t-3$, **$0\%$ of the target window has occurred**. Overlap is zero, and persistence collapses ($r = -0.127$, $\text{RMSE} = 1.3693$).
   - **Methodological Nuance:** Because SPI-3 is a nonlinear transformation of accumulated precipitation, this window overlap explains why persistence decays and why short-lead autoregression is strong, but it is a plausible structural explanation rather than a complete causal demonstration.

4. **Climatology as the True Reference Benchmark (Lead 3 Has Zero Useful Skill):**
   - Beating persistence at Lead 3 ($32.21\%$ reduction in RMSE) does **NOT** establish forecast skill. Decaying persistence at Lead 3 is an artificially weak baseline.
   - Against **Climatology** ($\text{RMSE} = 0.9267$), the Multi-Ocean model achieves $\text{RMSE} = 0.9282$ ($\Delta\text{RMSE} = +0.0015$, $95\%\text{ CI: } [-0.0477, +0.0469]$, $p_{\text{two-sided}} = 0.8620$).
   - **Conclusion:** At Lead 3 months, the linear multi-ocean model has **no demonstrable skill over climatology**, and exhibits near-zero correlation ($r = 0.021$). The earlier 3-month seasonal forecast cannot be described as successful without qualification.

5. **Complete 100% Seasonal MSE Decomposition (The Bega Dry Season Confounder):**
   - Decomposing the full 96 holdout months across all seasons reveals that the apparent skill gains in pooled evaluations occur almost exclusively during the **Bega dry season (Oct–Jan)**.
   - In the critical **Kiremt monsoon season (Jul–Sep)**—when $>75\%$ of rainfall occurs and rainfed crops are grown in Abregelle—the multi-ocean model at Leads 2 and 3 is **strictly worse than Climatology** ($r = -0.14$ and $-0.15$).

---

## 1. Observed Local Rainfall Climatology for Abregelle (Tanqua Abergele Woreda)

To avoid assuming generic calendar definitions of northern Ethiopian seasons, the seasonal boundaries were established from the **verified 44-year (1981–2024, 528 months) CHIRPS precipitation series** extracted using the exact Tanqua Abergele Woreda polygon:

### Abregelle Observed Monthly Rainfall Climatology (1981–2024)

| Month | Calendar Name | Mean Precipitation | Standard Deviation | % of Annual Total | Observed Agro-Climatic Character |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | January | 5.92 mm | 11.24 mm | 0.8% | Deep Bega Dry Season |
| **02** | February | 6.16 mm | 11.08 mm | 0.8% | Deep Bega Dry Season |
| **03** | March | 19.14 mm | 22.45 mm | 2.5% | Belg Spring Rains (Early) |
| **04** | April | 14.69 mm | 18.32 mm | 1.9% | Belg Spring Rains (Mid) |
| **05** | May | 56.02 mm | 45.12 mm | 7.4% | Belg Spring Rains (Late / Peak) |
| **06** | June | **90.14 mm** | **44.80 mm** | **11.8%** | **Kiremt Monsoon Onset** |
| **07** | July | **219.52 mm** | **68.21 mm** | **28.8%** | **Kiremt Monsoon Peak** |
| **08** | August | **276.76 mm** | **78.45 mm** | **36.3%** | **Kiremt Monsoon Peak** |
| **09** | September | **45.90 mm** | **31.15 mm** | **6.0%** | **Kiremt Monsoon Cessation** |
| **10** | October | 13.65 mm | 20.84 mm | 1.8% | Bega Dry Season Onset |
| **11** | November | 7.61 mm | 13.50 mm | 1.0% | Bega Dry Season |
| **12** | December | 6.25 mm | 12.18 mm | 0.8% | Bega Dry Season |
| **Total**| **Annual Mean** | **761.75 mm** | — | **100.0%** | — |

### Climatological Insights for Abregelle:
1. **June is Part of Kiremt, Not a Dry Transition:** June receives **$90.14\text{ mm}$ ($11.8\%$ of annual precipitation)**. June rainfall in Abregelle is greater than March, April, and May combined ($89.85\text{ mm}$). Omitting June from the monsoon excludes substantial agricultural precipitation.
2. **Monsoon Dominance:** The extended monsoon period **June–September (JJAS)** accounts for **$632.32\text{ mm}$ ($83.0\%$ of annual rainfall)**.
3. **Belg Rains (March–May, MAM):** Accounts for **$89.85\text{ mm}$ ($11.8\%$)**, characterized by high inter-annual variance.
4. **Bega Dry Season (October–February, ONDJF):** Accounts for only **$39.59\text{ mm}$ ($5.2\%$)**.

---

## 2. Complete 100% Seasonal Evaluation & Exact MSE Decomposition

To ensure no holdout observations are omitted, all **96 continuous holdout calendar months (2016–2023)** are evaluated. Two complete partitioning schemes are examined:
- **Scheme 1 (Standard 4-Part + Transitions):** Kiremt Core (JAS, $N=24$), Belg (MAM, $N=24$), Bega (ONDJ, $N=32$), Transition Feb ($N=8$), Transition Jun ($N=8$). Total: $96$ months ($100\%$).
- **Scheme 2 (Observed Climatology 3-Part):** Extended Kiremt (JJAS, $N=32$, $83.0\%$ rain), Belg Rains (MAM, $N=24$, $11.8\%$ rain), Extended Bega (ONDJF, $N=40$, $5.2\%$ rain). Total: $96$ months ($100\%$).

### Additive Mean Squared Error (MSE) Identity
Because the full-period MSE is the exact weighted sum of the seasonal MSEs:

$$\text{MSE}_{\text{total}} = \sum_{s} \frac{N_s}{N} \text{MSE}_s$$
$$\Delta \text{MSE} = \text{MSE}_{\text{ocean}} - \text{MSE}_{\text{clim}} = \sum_{s} w_s (\text{MSE}_{\text{ocean}, s} - \text{MSE}_{\text{clim}, s})$$

### Complete Seasonal MSE Decomposition Table (Holdout 2016–2023)

#### Lead 1 Month ($t+1$) [Total Pooled $\Delta\text{MSE} = -0.2493$, $\text{RMSE}_{\text{clim}} = 0.9267$, $\text{RMSE}_{\text{ocean}} = 0.7808$]

| Partition Scheme & Season | Obs ($N_s$) | Weight ($w_s$) | Climatology RMSE | Multi-Ocean RMSE | Season $\Delta\text{MSE}$ | Weighted Contribution ($w_s \Delta\text{MSE}_s$) | Ocean vs Clim % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scheme 1: Standard 4-Part** | | | | | | | |
| • Kiremt Core (JAS) | 24 | 0.250 | 0.5240 | 0.4931 | -0.0314 | **-0.0078** | +5.89% |
| • Belg Rains (MAM) | 24 | 0.250 | 0.7679 | 0.6363 | -0.1848 | **-0.0462** | +17.14% |
| • Bega Dry Season (ONDJ) | 32 | 0.333 | 1.2505 | 0.8735 | -0.8008 | **-0.2669** | +30.15% |
| • Transition: February | 8 | 0.083 | 0.6701 | 1.2403 | +1.0903 | **+0.0909** | -85.10% |
| • Transition: June | 8 | 0.083 | 1.0051 | 0.8834 | -0.2296 | **-0.0191** | +12.11% |
| *Sum of Weighted $\Delta\text{MSE}$* | **96** | **1.000** | — | — | — | **-0.2493** | *Identity Verified* |
| **Scheme 2: Climatological** | | | | | | | |
| • Extended Kiremt (JJAS) | 32 | 0.333 | 0.6766 | 0.6139 | -0.0809 | **-0.0270** | +9.27% |
| • Belg Rains (MAM) | 24 | 0.250 | 0.7679 | 0.6363 | -0.1848 | **-0.0462** | +17.14% |
| • Extended Bega (ONDJF) | 40 | 0.417 | 1.1578 | 0.9575 | -0.4226 | **-0.1761** | +17.30% |
| *Sum of Weighted $\Delta\text{MSE}$* | **96** | **1.000** | — | — | — | **-0.2493** | *Identity Verified* |

---

#### Lead 2 Months ($t+2$) [Total Pooled $\Delta\text{MSE} = -0.0508$, $\text{RMSE}_{\text{clim}} = 0.9267$, $\text{RMSE}_{\text{ocean}} = 0.8989$]

| Partition Scheme & Season | Obs ($N_s$) | Weight ($w_s$) | Climatology RMSE | Multi-Ocean RMSE | Season $\Delta\text{MSE}$ | Weighted Contribution ($w_s \Delta\text{MSE}_s$) | Ocean vs Clim % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scheme 1: Standard 4-Part** | | | | | | | |
| • Kiremt Core (JAS) | 24 | 0.250 | 0.5240 | 0.5792 | **+0.0609** | **+0.0152 (Worse)** | **-10.54%** |
| • Belg Rains (MAM) | 24 | 0.250 | 0.7679 | 0.8748 | **+0.1756** | **+0.0439 (Worse)** | **-13.92%** |
| • Bega Dry Season (ONDJ) | 32 | 0.333 | 1.2505 | 1.0661 | -0.4272 | **-0.1424 (Better)** | +14.75% |
| • Transition: February | 8 | 0.083 | 0.6701 | 0.8832 | **+0.3307** | **+0.0276 (Worse)** | -31.80% |
| • Transition: June | 8 | 0.083 | 1.0051 | 1.0341 | **+0.0591** | **+0.0049 (Worse)** | -2.88% |
| *Sum of Weighted $\Delta\text{MSE}$* | **96** | **1.000** | — | — | — | **-0.0508** | *Identity Verified* |
| **Scheme 2: Climatological** | | | | | | | |
| • Extended Kiremt (JJAS) | 32 | 0.333 | 0.6766 | 0.7202 | **+0.0605** | **+0.0202 (Worse)** | **-6.44%** |
| • Belg Rains (MAM) | 24 | 0.250 | 0.7679 | 0.8748 | **+0.1756** | **+0.0439 (Worse)** | **-13.92%** |
| • Extended Bega (ONDJF) | 40 | 0.417 | 1.1578 | 1.0322 | -0.2757 | **-0.1149 (Better)** | +10.85% |
| *Sum of Weighted $\Delta\text{MSE}$* | **96** | **1.000** | — | — | — | **-0.0508** | *Identity Verified* |

---

#### Lead 3 Months ($t+3$) [Total Pooled $\Delta\text{MSE} = +0.0027$, $\text{RMSE}_{\text{clim}} = 0.9267$, $\text{RMSE}_{\text{ocean}} = 0.9282$]

| Partition Scheme & Season | Obs ($N_s$) | Weight ($w_s$) | Climatology RMSE | Multi-Ocean RMSE | Season $\Delta\text{MSE}$ | Weighted Contribution ($w_s \Delta\text{MSE}_s$) | Ocean vs Clim % |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scheme 1: Standard 4-Part** | | | | | | | |
| • Kiremt Core (JAS) | 24 | 0.250 | 0.5240 | 0.5364 | **+0.0132** | **+0.0033 (Worse)** | **-2.37%** |
| • Belg Rains (MAM) | 24 | 0.250 | 0.7679 | 0.8062 | **+0.0603** | **+0.0151 (Worse)** | **-4.99%** |
| • Bega Dry Season (ONDJ) | 32 | 0.333 | 1.2505 | 1.2073 | -0.1064 | **-0.0355 (Better)** | +3.46% |
| • Transition: February | 8 | 0.083 | 0.6701 | 0.7925 | **+0.1812** | **+0.0151 (Worse)** | -18.27% |
| • Transition: June | 8 | 0.083 | 1.0051 | 1.0330 | **+0.0568** | **+0.0047 (Worse)** | -2.78% |
| *Sum of Weighted $\Delta\text{MSE}$* | **96** | **1.000** | — | — | — | **+0.0027** | *Identity Verified* |
| **Scheme 2: Climatological** | | | | | | | |
| • Extended Kiremt (JJAS) | 32 | 0.333 | 0.6766 | 0.6946 | **+0.0241** | **+0.0080 (Worse)** | **-2.66%** |
| • Belg Rains (MAM) | 24 | 0.250 | 0.7679 | 0.8062 | **+0.0603** | **+0.0151 (Worse)** | **-4.99%** |
| • Extended Bega (ONDJF) | 40 | 0.417 | 1.1578 | 1.1365 | -0.0489 | **-0.0204 (Better)** | +1.84% |
| *Sum of Weighted $\Delta\text{MSE}$* | **96** | **1.000** | — | — | — | **+0.0027** | *Identity Verified* |

### Key Mathematical Findings from Complete Seasonal Decomposition:
1. **Mathematical Proof of Bega Confounding:** At Lead 2, in **every single rainy season and transition month** outside of Bega, the ocean model has **positive $\Delta\text{MSE}$ (worse error than Climatology)**:
   - Kiremt JAS: $\Delta\text{MSE} = +0.0609$ ($-10.54\%$ vs Clim)
   - Belg MAM: $\Delta\text{MSE} = +0.1756$ ($-13.92\%$ vs Clim)
   - February: $\Delta\text{MSE} = +0.3307$ ($-31.80\%$ vs Clim)
   - June: $\Delta\text{MSE} = +0.0591$ ($-2.88\%$ vs Clim)
   The only reason the pooled full-period $\Delta\text{MSE}$ is negative ($-0.0508$) is because Bega has a large negative $\Delta\text{MSE} = -0.4272$ (weighted: $-0.1424$).
2. **At Lead 3:** Every rainy season is worse than climatology ($\text{JJAS: } +0.0241$, $\text{MAM: } +0.0603$). The total pooled $\Delta\text{MSE}$ is positive ($+0.0027$), confirming that **the ocean model fails to beat climatological mean at 3 months**.

---

## 3. Multi-Scheme Bootstrap Sensitivity Analysis

To rigorously evaluate the sensitivity of forecast skill differences to temporal dependence, three resampling procedures were executed ($B = 2,000$ paired resamples, `seed=42`):
1. **Scheme A: 6-Month Circular Block Bootstrap** (serial correlation check).
2. **Scheme B: 12-Month Circular Block Bootstrap** (annual cycle preserving).
3. **Scheme C: Paired Calendar Year-Block Bootstrap** (8 independent blocks of 12 continuous months, 2016–2023).

### Bootstrap Sensitivity Comparison Across Schemes

| Lead Horizon & Comparison | Metric ($\Delta\text{RMSE}$) | 6-Month Block 95% CI ($p_2$) | 12-Month Block 95% CI ($p_2$) | Year-Block (8 Yr) 95% CI ($p_2$) | Robust Conclusion |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Lead 1: Ocean vs Climatology** | **-0.1460** | $[-0.2671, -0.0183]$ ($p=0.0290$) | $[-0.2557, -0.0180]$ ($p=0.0210$) | $[-0.2513, -0.0167]$ ($p=0.0340$) | **Statistically Significant across all schemes** |
| **Lead 1: Ocean vs Local AR** | **-0.0111** | $[-0.0314, +0.0084]$ ($p=0.3910$) | $[-0.0303, +0.0082]$ ($p=0.3810$) | $[-0.0317, +0.0047]$ ($p=0.2830$) | **NOT Significant in any scheme (CIs span 0)** |
| **Lead 1: Ocean vs Persistence** | **-0.1103** | $[-0.1635, -0.0561]$ ($p<0.0001$) | $[-0.1555, -0.0563]$ ($p<0.0001$) | $[-0.1470, -0.0639]$ ($p<0.0001$) | Significant (Persistence Decay) |
| **Lead 2: Ocean vs Climatology** | **-0.0278** | $[-0.1199, +0.0604]$ ($p=0.6240$) | $[-0.0971, +0.0489]$ ($p=0.4970$) | $[-0.0744, +0.0268]$ ($p=0.3040$) | **NOT Significant in any scheme** |
| **Lead 2: Ocean vs Local AR** | **-0.0156** | $[-0.0556, +0.0214]$ ($p=0.5920$) | $[-0.0545, +0.0217]$ ($p=0.6060$) | $[-0.0527, +0.0120]$ ($p=0.6150$) | **NOT Significant in any scheme** |
| **Lead 3: Ocean vs Climatology** | **+0.0015** | $[-0.0502, +0.0490]$ ($p=0.8620$) | $[-0.0477, +0.0469]$ ($p=0.8620$) | $[-0.0404, +0.0344]$ ($p=0.8440$) | **Zero Skill (Equivalent to Climatology)** |
| **Lead 3: Ocean vs Local AR** | **-0.0094** | $[-0.0590, +0.0400]$ ($p=0.8240$) | $[-0.0597, +0.0395]$ ($p=0.8380$) | $[-0.0532, +0.0256]$ ($p=0.7180$) | **NOT Significant in any scheme** |
| **Lead 3: Ocean vs Persistence** | **-0.4411** | $[-0.6467, -0.2448]$ ($p<0.0001$) | $[-0.6220, -0.2473]$ ($p<0.0001$) | $[-0.6494, -0.2252]$ ($p=0.0010$) | Significant over decaying baseline only |

*Note: $p_2$ represents the empirical two-sided p-value testing $H_0: \Delta\text{RMSE} = 0$.*

### Invariant Statistical Conclusion Across Resampling Schemes:
- The 1-month model's gain over Climatology is robust ($p_2 \approx 0.02\text{--}0.03$).
- The incremental benefit of Ocean predictors over Local AR is **not statistically significant under any block length or year-block configuration** ($p_2 \ge 0.28$).
- At Lead 3, the Multi-Ocean model fails to reject the null hypothesis of zero difference from Climatology under all three resampling schemes ($p_2 \ge 0.84$).

---

## 4. Separation of Project Milestones

To prevent blocking validation work, the hydro-climatic pipeline is partitioned into two independent milestones:

```
+-------------------------------------------------------------------------------+
| MILESTONE 1: SPI-3 DROUGHT PREDICTION & PHYSICAL TELECONNECTION BENCHMARK      |
| Status: 100% COMPLETE & VERIFIED (1981-2024, 528 MONTHS)                      |
| Inputs: CHIRPS Rainfall (Verified), HadISST/NOAA Ocean Indices (Verified)     |
| Tasks: Causal Lead Evaluation, Block Bootstrapping, Seasonal Partitioning    |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| MILESTONE 2: SPEI WATER BALANCE, TEMPERATURE & LAND-SURFACE INTERACTIONS      |
| Status: IN PROGRESS (10/44 CPC Years Verified, Remaining Ingesting)          |
| Inputs: NOAA CPC Daily Tmax/Tmin (Pending), Hargreaves PET, Soil Moisture    |
| Tasks: Jensen's Inequality Audit, PET Reconstruction, SPEI Calibration        |
+-------------------------------------------------------------------------------+
```

---

## 5. Atmospheric Bridge & Moisture Transport: Physical Roadmap

Rather than adding complex black-box architectures, the physical connection between ocean SSTs and Abregelle rainfall will be investigated through atmospheric moisture dynamics:

### Physical Pathway Hierarchy
$$\text{Ocean SST Anomalies (ENSO, IOD, Atlantic Gradient)}$$
$$\downarrow$$
$$\text{Atmospheric Circulation: } u, v, z_{500}, \text{TEJ, AEJ, Somali Jet}$$
$$\downarrow$$
$$\text{Regional Moisture Transport: } \vec{Q} = \frac{1}{g} \int_{p_s}^{p_{\text{top}}} q \vec{v} \, dp$$
$$\downarrow$$
$$\text{Moisture Convergence over Tekezé: } -\nabla \cdot \vec{Q}$$
$$\downarrow$$
$$\text{Abregelle Rainfall & SPI-3 Response}$$

### Critical Highlands Topographic Masking Rule
- The Tekezé River Basin originates in the Ethiopian Highlands (elevations exceeding 2,500–4,000 m).
- At high elevations, the surface atmospheric pressure $p_s$ is often between $700\text{ hPa}$ and $800\text{ hPa}$.
- **Methodological Mandate:** Standard pressure levels such as $850\text{ hPa}$ lie **below the physical ground surface** across substantial portions of the basin.
- In reanalysis products (ERA5), variables at levels where $p > p_s$ are synthetic extrapolations through subterranean rock.
- **Protocol:**
  1. All pressure levels with $p > p_s$ must be explicitly masked out.
  2. Moisture flux integration must terminate at the true surface pressure: $\vec{Q} = \frac{1}{g} \sum_{p_k \le p_s} q_k \vec{v}_k \Delta p_k$.
  3. Single-level diagnostics will focus on levels remaining strictly above regional topography ($700\text{ hPa}$ and $500\text{ hPa}$), coupled with surface-level fluxes.
