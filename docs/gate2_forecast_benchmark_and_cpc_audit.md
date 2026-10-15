# Scientific Audit: Drought Forecast Benchmarking, Temporal Alignment & NOAA CPC Ingestion Status

**Study Area:** Tanqua Abergele Woreda & Tekezé River Basin, Northern Ethiopia  
**Target Metric:** 3-Month Standardized Precipitation Index ($\text{SPI-3}$)  
**Evaluation Window:** 2016-01 to 2023-12 (96 Continuous Holdout Calendar Months)  
**Historical Training Period:** 1981-03 to 2015-12 (418 Continuous Historical Months)  
**Governance Standard:** Gate 1 & Gate 2 Scientific Quality Standards, Strictly Zero Synthetic Data Rule  

---

## Executive Scientific Summary & Core Audit Conclusions

1. **Verification of NOAA CPC Daily Temperature Ingestion:**
   - As of the latest audit, **7 annual files (84 monthly records)** have been fully downloaded, verified with SHA-256 hashes, NetCDF dimension checks, and spatial area-weighting: **1981, 1982, 1983, 1984, 1985, 2002, and 2015**.
   - The remaining 37 years (1986–2001, 2003–2014, 2016–2024) are actively queued and downloading in the background.
   - **Formal Clarification:** The temperature record is **NOT counted as complete** while the background process is running. A formal year-by-year inventory manifest (`cpc_temperature_year_by_year_manifest.json`) tracks verified vs. pending files.

2. **Causal Lead Alignment & Forecast Timeline:**
   - For any forecast lead horizon $h \in \{1, 2, 3\}$ targeting month $t$, the forecast is issued at the end of month $T = t - h$.
   - Predictors are strictly causal $X_{\le t-h}$. No future climate, ocean, or rainfall observations are used.
   - All four models (Climatology, Persistence, Local Autoregressive, Multi-Ocean Informed) are evaluated on the exact same 96 continuous calendar months (2016-01 to 2023-12).

3. **Rolling SPI-3 Temporal Window Overlap (Why Persistence Decays Sharply):**
   - $\text{SPI-3}_t$ is calculated from cumulative rainfall over the 3-month window $\{t-2, t-1, t\}$.
   - At **Lead 1 ($h=1$)**, the forecast is issued at $t-1$. Precipitation for $t-2$ and $t-1$ is already observed. Thus, **$\frac{2}{3}$ of the target window is already known**. This explains why persistence achieves $r = 0.525$ and $\text{RMSE} = 0.8910$.
   - At **Lead 2 ($h=2$)**, issued at $t-2$, only month $t-2$ is known (**$\frac{1}{3}$ of the target window**). Overlap decays, and persistence drops to $r = 0.202$ and $\text{RMSE} = 1.1548$.
   - At **Lead 3 ($h=3$)**, issued at $t-3$, **ZERO months** of the target window $\{t-2, t-1, t\}$ have occurred. Temporal overlap is $0\%$. Pure persistence completely collapses ($r = -0.127$, $\text{RMSE} = 1.3693$).

4. **Climatology as the True Reference Benchmark (Lead 3 Has No Useful Skill):**
   - Beating persistence at Lead 3 ($32.21\%$ reduction in RMSE) does **NOT** establish forecast skill. Decaying persistence at Lead 3 is an artificially weak baseline.
   - Against **Climatology** ($\text{RMSE} = 0.9267$), the Multi-Ocean model achieves $\text{RMSE} = 0.9282$ ($\Delta\text{RMSE} = +0.0015$, $95\%\text{ CI: } [-0.0502, +0.0490]$, $p = 0.5690$).
   - **Conclusion:** At Lead 3 months, the linear multi-ocean model has **no demonstrable skill over climatological mean**, and exhibits near-zero correlation ($r = 0.021$). The earlier 3-month seasonal forecast cannot be described as successful without qualification.

5. **Seasonal Decomposition (Artifact of the Bega Dry Season):**
   - Pooling all 12 calendar months masks critical seasonal dynamics. Northern Ethiopia receives $>75\%$ of its annual rainfall during the **Kiremt monsoon (Jul–Sep)**.
   - During Kiremt ($N=24$ holdout months):
     - Climatological RMSE is $0.5240$.
     - At Lead 2: Ocean model $\text{RMSE} = 0.5792$ ($r = -0.14$), which is **$10.5\%$ worse than Climatology**.
     - At Lead 3: Ocean model $\text{RMSE} = 0.5364$ ($r = -0.15$), which is **$2.4\%$ worse than Climatology**.
   - The statistical "error reduction" of the multi-ocean model occurs almost exclusively during the **Bega dry season (Oct–Jan)**, when rain is negligible and crops have already been harvested.

---

## 1. NOAA CPC Daily Temperature Ingestion Status & Manifest

To prevent premature claims of data completeness, the exact state of the NOAA CPC Global Unified Daily Temperature record is audited below.

### Verified Complete Years (Double-File: Tmax + Tmin, NetCDF4, SHA-256 Validated)

| Year | Variable | Days Count | File Size (Bytes) | SHA-256 Checksum | Extraction Status in Tekezé Series |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1981** | `tmax` | 365 | 87,362,645 | `d1536d773502f5764e19e2425330e1372db7541c60d4ed689013e993a96553ab` | Extracted & Verified (12 mo) |
| **1981** | `tmin` | 365 | 88,855,206 | `8d6bdb6a8c4e084f6bc0fbef3496d298cd7a5cd651464510b14743b4c933931c` | Extracted & Verified (12 mo) |
| **1982** | `tmax` | 365 | 87,713,462 | `04ba5cd358068729ab393deee95d77e46b22ad9772e7701aac5099390a7573be` | Extracted & Verified (12 mo) |
| **1982** | `tmin` | 365 | 89,070,187 | `d5abe7bf55d141a2b0f9f521f71f6aa42353641dc37c0bef0629da2bb466967a` | Extracted & Verified (12 mo) |
| **1983** | `tmax` | 365 | 86,536,543 | `f95b0e869bdf38e1b12d276b60f03749b969d4af5b3204ce9d2a650937865e6b` | Extracted & Verified (12 mo) |
| **1983** | `tmin` | 365 | 87,967,958 | `2d76f486cd85800b1a1b6ffe6733fd4387882fa98f3e40235af60eb1cfed4bf0` | Extracted & Verified (12 mo) |
| **1984** | `tmax` | 366 (leap) | 87,688,044 | `476fae4406612df935be06fc95ce1f544607ff4cf690772d5b6e06b9ea04aa5a` | Extracted & Verified (12 mo) |
| **1984** | `tmin` | 366 (leap) | 89,076,688 | `b14e8bba53531f82f25603ca9d54559b9ce4f3d1e1f74db7ce1d491be7fe023a` | Extracted & Verified (12 mo) |
| **1985** | `tmax` | 365 | 85,351,963 | `91ac1bac4eee4c69b9b3fc86a38fd219beea7cbfdc91fcc2ea9449224c2dfcb7` | Extracted & Verified (12 mo) |
| **1985** | `tmin` | 365 | 86,693,976 | `4030932ee85f962bb147067faed22833f5dcbbf90412ed75b88e2626b6cff552` | Extracted & Verified (12 mo) |
| **2002** | `tmax` | 365 | 87,811,661 | `c01fde676320d880bd04a85c34e511c7f7d14e7b927ca86137e7826731512259` | Extracted & Verified (12 mo) |
| **2002** | `tmin` | 365 | 89,121,680 | `f52e96d69336b15832582b1f9ffec908de0fa921827362fe9c2dbe9185b9cb86` | Extracted & Verified (12 mo) |
| **2015** | `tmax` | 365 | 80,901,862 | `c6d0e9b32ba9a08b6946b6b73fb33f1ffad38e49a78e77554483cde7b2121911` | Extracted & Verified (12 mo) |
| **2015** | `tmin` | 365 | 82,288,305 | `294d58bb82e590d3bae920c8fb054709059a4fa333bc700687086afbc011576b` | Extracted & Verified (12 mo) |

### Ingestion Inventory Summary
- **Total Years Required (1981–2024):** 44 years (528 calendar months)
- **Years Fully Verified & Extracted:** **7 years** (84 calendar months, 15.9%)
- **Years Currently Queued / Ingesting:** **37 years** (444 calendar months, 84.1%)
- **Spatial Grid Intersections:** 38 active CPC cells ($0.5^\circ \times 0.5^\circ$) intersecting the Tekezé catchment polygon ($67,135.4\text{ km}^2$).
- **Methodological Rule:** Daily $\sqrt{\text{DTR}}$ is calculated on each individual day before monthly averaging, eliminating Jensen's inequality bias. Missing months in the master file are explicitly flagged as `MISSING_DATA` rather than imputed with synthetic noise.

---

## 2. Forecast Benchmark Implementation & Causal Timeline Audit

### Mathematical Timeline & Observation Availability

Let $t$ index calendar months ($t = 1, \dots, N$).
When making a forecast for lead time $h \in \{1, 2, 3\}$, the target is $\text{SPI-3}_t$.
The forecast issue date is the conclusion of month $T = t - h$.

$$\text{Forecast Issue Time: } T = t - h$$
$$\text{Available Information Set: } \mathcal{F}_{T} = \{ X_\tau : \tau \le T \}$$
$$\text{Target Variable: } y_t = \text{SPI-3}_t$$

```
Timeline for Lead h = 1:
Month:        t-2       t-1 (Issue T)       t (Target)
Precipitation: [  p_{t-2}  ] [  p_{t-1}  ] | [  p_t (Future) ]
SPI-3 Window: [============= Target SPI-3_t =============]
               <-- 2 months ALREADY OBSERVED --> <-- 1 mo future -->

Timeline for Lead h = 3:
Month:        t-3 (Issue T)       t-2            t-1            t (Target)
Precipitation: [  p_{t-3}  ] | [  p_{t-2}  ]    [  p_{t-1}  ]    [  p_t  ]
SPI-3 Window:                 [============= Target SPI-3_t =============]
                              <--------- ZERO MONTHS OBSERVED --------->
```

### Eliminating Gamma Calibration Leakage
In standard SPI calculations, the Gamma distribution parameters $(\alpha, \beta, p_0)$ are estimated per calendar month.
- **Previous Potential Leakage:** Parameters were fitted on all valid observations across the full 1981–2024 archive, subtly conditioning the calibration on test-period precipitation.
- **Audited Zero-Leakage Implementation:** Parameters $(\alpha_{\text{train}}, \beta_{\text{train}}, p_{0,\text{train}})$ are estimated strictly on the **pre-2016 historical baseline** ($1981\le \text{year} < 2016$, 35 years). The holdout test months (2016–2023) are transformed strictly using these frozen baseline parameters:

$$F(x) = p_{0,\text{train}} + (1 - p_{0,\text{train}}) \int_0^x \frac{t^{\alpha_{\text{train}}-1} e^{-t/\beta_{\text{train}}}}{\beta_{\text{train}}^{\alpha_{\text{train}}} \Gamma(\alpha_{\text{train}})} \, dt$$
$$\text{SPI-3}_t = \Phi^{-1}(F(x_t))$$

---

## 3. Audited Forecast Benchmark Results & Uncertainty Estimates

All models were evaluated on the **exact 96 continuous calendar months** (2016-01 to 2023-12).
Uncertainty was estimated via **Stationary Circular Block Bootstrap** ($B = 2,000$ resamples, block length $L = 6$ months to account for the autocorrelation of rolling 3-month sums).
Controlled tuning budget: Ridge regression $\alpha = 2.0$ for both Local AR and Multi-Ocean models.

### Full Test Set Benchmark (N = 96 Months, 2016–2023)

| Lead Time | Climatology RMSE | Persistence RMSE ($r$) | Local AR RMSE ($r$) | Multi-Ocean RMSE ($r$) | $\Delta\text{RMSE}$ vs Climatology (95% CI, $p$) | $\Delta\text{RMSE}$ vs Local AR (95% CI, $p$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 Month ($t+1$)** | 0.9267 | 0.8910 ($0.525$) | 0.7918 ($0.524$) | **0.7808** ($0.541$) | **-0.1460** ($[-0.2671, -0.0183]$, $p=0.0145$)* | **-0.0111** ($[-0.0314, +0.0084]$, $p=0.1955$) |
| **2 Months ($t+2$)** | 0.9267 | 1.1548 ($0.202$) | 0.9145 ($0.198$) | **0.8989** ($0.244$) | **-0.0278** ($[-0.1199, +0.0604]$, $p=0.3120$) | **-0.0156** ($[-0.0556, +0.0214]$, $p=0.2960$) |
| **3 Months ($t+3$)** | **0.9267** | 1.3693 ($-0.127$) | 0.9376 ($-0.143$) | **0.9282** ($+0.021$) | **+0.0015** ($[-0.0502, +0.0490]$, $p=0.5690$) | **-0.0094** ($[-0.0590, +0.0400]$, $p=0.4120$) |

*\*Statistically significant at $\alpha = 0.05$.*

### Critical Findings from the Audit:
1. **At Lead 1 Month:**
   - The Multi-Ocean model achieves a statistically significant $15.75\%$ error reduction over Climatology ($p = 0.0145$).
   - However, the incremental improvement of Ocean predictors over Local AR is marginal ($-0.0111$ RMSE, $1.4\%$) and **not statistically significant** ($p = 0.1955$, 95% CI crosses zero).
   - Most of the skill at Lead 1 stems from the autoregressive retention of the 2 already-observed months in the 3-month rolling precipitation sum.
2. **At Lead 2 Months:**
   - Multi-Ocean error reduction vs Climatology is only $3.00\%$ ($\Delta\text{RMSE} = -0.0278$).
   - The 95% bootstrap confidence interval $[-0.1199, +0.0604]$ broadly straddles zero ($p = 0.3120$). There is no statistically robust evidence that the model outperforms climatology.
3. **At Lead 3 Months:**
   - The Multi-Ocean model ($\text{RMSE} = 0.9282$) is **slightly worse than Climatology** ($\text{RMSE} = 0.9267$).
   - While the ocean model reports a $32.21\%$ error reduction relative to persistence, this is entirely because persistence collapses to $\text{RMSE} = 1.3693$.
   - **Scientific Judgment:** At Lead 3, the unconstrained linear multi-ocean model has **zero predictive skill over climatology**.

---

## 4. Seasonal Disaggregation: Examining the Ocean Contribution

Northern Ethiopia experiences three distinct agro-climatic seasons:
- **Kiremt (Main Rains / Monsoon):** July to September ($>75\%$ of annual precipitation, main cereal cropping season).
- **Belg (Short Spring Rains):** March to May (secondary season, high inter-annual variability).
- **Bega (Dry Season):** October to January (harvesting and dry winter, precipitation $< 10\text{ mm/mo}$).

### Seasonal Breakdown of Model Performance Across the 96 Holdout Months

#### A. Kiremt Monsoon Season (July–September, N = 24 Holdout Months)
*Critical agricultural window for rainfed teff, sorghum, and maize in Abregelle.*

| Lead Time | Climatology RMSE | Persistence RMSE ($r$) | Local AR RMSE ($r$) | Multi-Ocean RMSE ($r$) | Ocean vs Local AR | Ocean vs Climatology |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Lead 1m** | 0.5240 | 0.5923 ($0.342$) | **0.4612** ($0.344$) | 0.4931 ($0.308$) | **-6.92% (Worse)** | +5.89% |
| **Lead 2m** | **0.5240** | 0.9108 ($-0.224$) | 0.5725 ($-0.219$) | 0.5792 ($-0.140$) | **-1.17% (Worse)** | **-10.54% (Worse)** |
| **Lead 3m** | **0.5240** | 1.1228 ($-0.560$) | 0.5512 ($-0.558$) | 0.5364 ($-0.147$) | +2.69% | **-2.37% (Worse)** |

#### B. Bega Dry Season (October–January, N = 32 Holdout Months)
*Post-harvest dry period.*

| Lead Time | Climatology RMSE | Persistence RMSE ($r$) | Local AR RMSE ($r$) | Multi-Ocean RMSE ($r$) | Ocean vs Local AR | Ocean vs Climatology |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Lead 1m** | 1.2505 | 0.8966 ($0.673$) | 0.9113 ($0.672$) | **0.8735** ($0.703$) | **+4.15%** | **+30.15%** |
| **Lead 2m** | 1.2505 | 1.0901 ($0.465$) | 1.1213 ($0.462$) | **1.0661** ($0.550$) | **+4.92%** | **+14.75%** |
| **Lead 3m** | 1.2505 | 1.3546 ($-0.140$) | 1.2519 ($-0.147$) | **1.2073** ($0.174$) | **+3.57%** | **+3.46%** |

### Crucial Methodological Insight:
- During **Kiremt**, variance is small ($\text{RMSE}_{\text{clim}} = 0.5240$). Adding ocean predictors introduces extraneous variance, resulting in **negative skill relative to Local AR at Lead 1 ($-6.92\%$) and negative skill relative to Climatology at Leads 2 ($-10.54\%$) and 3 ($-2.37\%$)**.
- The large pooled skill gains (+30% at Lead 1, +15% at Lead 2) are driven by the **Bega dry season**, where climatology RMSE is inflated ($1.2505$) due to extreme non-normality in dry-month SPI transformations.
- **Physical Implication:** Seasonal drought forecasting for Abregelle cannot rely on linear models pooled across all 12 calendar months. The model must be formulated with season-specific parameter shrinkage or non-linear architectures targeting the Kiremt monsoon specifically.

---

## 5. Next Steps for the Atmospheric Bridge & Physical Grounding

1. **Complete NOAA CPC Verification:** Continue the automated ingestion pipeline to retrieve and verify the remaining 37 years of daily $T_{\max}$ and $T_{\min}$.
2. **ERA5 Atmospheric Bridge Ingestion:** Ingest regional pressure-level wind vectors ($u_{850}, v_{850}$), relative humidity ($\text{RH}_{700}$), and geopotential height ($z_{500}$) over the Horn of Africa domain ($10^\circ\text{–}16^\circ\text{N}, 34^\circ\text{–}42^\circ\text{E}$).
3. **Moisture Flux Divergence:** Compute physical atmospheric moisture divergence $-\nabla \cdot (q \vec{v})$ to establish whether Pacific/Indian SST anomalies genuinely modulate moisture transport into the Tekezé gorge, or whether raw linear SST correlations are coincidental teleconnection artifacts.
4. **Kiremt-Specific Seasonal Model:** Restrict seasonal prediction models to the June–September rainy season to provide actionable early warning for agricultural stakeholders in Abregelle.
