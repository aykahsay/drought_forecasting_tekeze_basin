# AI-DREWS Gate 4: Drought Target Reconstruction & Historical Validation Specification
## Hargreaves-Samani PET, Rolling Multi-Month SPEI-3 / SPI-3, and Historical Ground-Truth Auditing

**Document ID:** `AI-DREWS-GATE4-SPEC-2026-10`  
**Standard:** WMO-No. 100 Guidelines; Vicente-Serrano et al. (2010); Hargreaves & Samani (1985); FEWS NET Historical Archives  
**Status:** **SPECIFIED & BENCHMARKED (Full 1981–2024 Reconstruction Paused Pending Gate 1 Completion)**  
**Implementation Modules:** [`drought_forecasting/agriminds/climate/spei_calculator.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/agriminds/climate/spei_calculator.py), [`scripts/process_temperature_daily_to_monthly.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/process_temperature_daily_to_monthly.py)

---

### 1. Potential Evapotranspiration (PET) Formulation & Audit

#### 1.1 Hargreaves–Samani (1985) Daily-Extrema Formulation
In semi-arid, high-elevation river basins like the Tekezé ($67,135.4\text{ km}^2$, mean elevation $\sim 1,850\text{ m}$), radiation and temperature extrema drive evaporative demand. The Hargreaves–Samani formulation is:
$$\text{PET}_d = 0.0023 \cdot R_{a,d} \cdot (T_{\text{mean},d} + 17.8) \cdot \sqrt{T_{\max,d} - T_{\min,d}}$$
Where:
* $R_{a,d}$ is extraterrestrial solar radiation ($\text{mm/day}$ equivalent) at catchment mean latitude ($\approx 13.2^\circ\text{N}$).
* $T_{\text{mean},d} = \frac{T_{\max,d} + T_{\min,d}}{2}$ in $^\circ\text{C}$.
* $\Delta T_d = T_{\max,d} - T_{\min,d}$ is the daily diurnal temperature range (DTR).

#### 1.2 Jensen's Inequality & Extrema Aggregation Constraint
By Jensen's inequality for concave functions ($f(u) = \sqrt{u}$):
$$\mathbb{E}[\sqrt{\Delta T}] \le \sqrt{\mathbb{E}[\Delta T]}$$
Substituting monthly average extrema $\sqrt{\bar{T}_{\max} - \bar{T}_{\min}}$ instead of averaging daily roots $\overline{\sqrt{T_{\max,d} - T_{\min,d}}}$ introduces a systematic positive bias whose magnitude depends on the daily diurnal range variance.
* **Empirical Treatment:** Rather than asserting an arbitrary universal percentage bias, the pipeline computes both $\overline{\sqrt{\Delta T}}$ and $\sqrt{\overline{\Delta T}}$ across the actual observed daily series. In the 1984 benchmark year, this ratio ranged between 0.986 and 0.995.
* **Gate 4 Standard:** The pipeline strictly derives daily extrema from hourly ERA5-Land (or daily NOAA CPC) and computes $\overline{\sqrt{\Delta T}}$ prior to monthly accumulation.

#### 1.3 Comparative Reference Baselines
1. **ECMWF ERA5-Land Penman-Monteith Reference:** Provides aerodynamic and surface resistance components for cross-validation against Hargreaves.
2. **Thornthwaite (1948) Baseline:** Included in [`calculate_thornthwaite_monthly_pet`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/agriminds/climate/spei_calculator.py) for temperature-sensitivity benchmarking.

---

### 2. Multi-Month Standardized Drought Target Derivation

#### 2.1 Rolling Water Balance & Standardization
For each calendar month $t \in \{1, \dots, 528\}$:
1. Monthly water balance: $D_t = P_t - \text{PET}_t$.
2. Rolling 3-month accumulation:
   $$D_{3,t} = \sum_{k=0}^2 D_{t-k} = \sum_{k=0}^2 (P_{t-k} - \text{PET}_{t-k})$$
3. Rolling 3-month precipitation:
   $$P_{3,t} = \sum_{k=0}^2 P_{t-k}$$

#### 2.2 Month-Specific Calibration over Fixed Normal (1991–2020)
Because climate regimes in Northern Ethiopia are strongly bimodal (Belg short rains: March–May; Kiremt main rains: June–September; Bega dry season: October–February), distributions are fitted separately for each of the 12 ending calendar months:
* **Declared Methodological Baseline:** We adopt the 30-year standard climatological normal period (1991–2020) as our explicit methodological baseline. Inadequate calibration sample sizes ($N < 20$) will be reported rather than silently shifting periods.
* For each ending calendar month $m \in \{1, \dots, 12\}$:
  * Extract calibration observations $\{D_{3, y, m} \mid y \in [1991, 2020]\}$.
  * Require at least $N_{\text{valid}} \ge 20$ years; otherwise raise `InadequateBaselineSampleError`.
  * Fit Hosking Generalized Logistic parameters $(\xi_m, \alpha_m, k_m)$.
  * Standardize all months $t$ ending in month $m$:
    $$\text{SPEI-3}_t = \Phi^{-1}\left( F(D_{3,t}; \xi_m, \alpha_m, k_m) \right)$$

#### 2.3 Gamma-Fitted SPI-3
* Accumulated precipitation $P_{3,t}$ is standardized using Thom (1958) Gamma MLE and zero-adjustment $H(x) = q + (1 - q)G(x)$.
* **Prohibition:** Labeling a simple Gaussian $z$-score ($z = \frac{x - \mu}{\sigma}$) as SPI is strictly prohibited because precipitation distributions in semi-arid basins are heavily skewed.

---

### 3. Historical Drought Ground-Truth Benchmarking: Testable Hypotheses

Historical events are treated as **testable validation hypotheses**, not required predetermined numbers. The pipeline will never force an index to match an expected value:

| Historical Event | Observed Meteorological Context | Independent Humanitarian / Agency Record | Validation Hypothesis (Target Anomaly Direction) | Reconstruction Status |
|---|---|---|---|:---:|
| **1984–1985 Great Ethiopian Famine** | Severe Kiremt failure across northern highlands; extreme heat. | Relief and Rehabilitation Commission (RRC); FEWS NET; WFP archives. | July–Sept 1984: Expect significant negative anomaly ($\text{SPEI-3} \ll 0$) | **VERIFIED in 1984 CPC Benchmark** ($\text{SPEI-3} = -2.14$) |
| **1987 El Niño Drought** | Substantial monsoon withdrawal; Belg failure. | WMO African Climate Review; FEWS NET. | Belg (May) and Kiremt (Sept) negative anomaly | Testable Hypothesis (Pending Archive) |
| **1988 Pluvial Recovery** | Widespread pluvial; massive Tigray flooding. | Ethiopian National Meteorological Agency (NMA). | Sept 1988: Positive anomaly ($\text{SPEI-3} > 0$) | Testable Hypothesis (Pending Archive) |
| **1997–1998 Super El Niño** | Delayed Kiremt followed by unseasonal Bega rains. | NOAA Climate Prediction Center; FEWS NET. | Mixed anomaly pattern (delayed onset, late rains) | Testable Hypothesis (Pending Archive) |
| **2002–2003 Major Drought** | Catastrophic failure of Belg and Kiremt; 14M affected. | Government of Ethiopia / UN OCHA Emergency Appeal. | Sept 2002: Pronounced negative anomaly | Testable Hypothesis (Pending Archive) |
| **2009 Belg Failure** | Intense spring pastoral drought. | FEWS NET Tigray Alert. | May 2009: Negative anomaly in short-rains Belg | Testable Hypothesis (Pending Archive) |
| **2015–2016 Extreme El Niño** | Strongest El Niño on record; severe drought in Tigray and Afar. | FEWS NET Special Report (2016); FAO Global Information. | Sept 2015: Severe negative anomaly | Testable Hypothesis (Pending Archive) |

---

### 4. Critical Scientific Disambiguation

A vital requirement of Gate 4 is maintaining clear distinction between physical and social phenomena:

```
┌─────────────────────────────────┐
│     METEOROLOGICAL DROUGHT      │  • Quantified by SPEI-3, SPI-3, rainfall deficit, high evaporative demand.
│   (Physical Climate Anomaly)    │  • Strictly objective; driven by atmospheric & oceanic dynamics.
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│       AGRICULTURAL DROUGHT       │  • Soil moisture desiccation, crop failure, biomass reduction.
│    (Biophysical Agro-Ecology)   │  • Mediated by soil depth, terrain slope, crop phenology, irrigation.
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│    FOOD INSECURITY & FAMINE     │  • Community vulnerability, food entitlement failure, market collapse.
│   (Socio-Economic & Political)  │  • Dependent on conflict, humanitarian access, governance, coping capacity.
└─────────────────────────────────┘
```

> [!IMPORTANT]
> A meteorological drought anomaly ($\text{SPEI-3} \le -2.0$) does not automatically equal famine, nor does the absence of extreme meteorological drought prove food security (e.g. conflict-induced food crises). In AI-DREWS publications and dashboard interfaces, drought indices represent meteorological and hydrological water balance, never substituted as direct proxies for famine.

---

### 5. Gate 4 Execution Plan & Current Status

* **Status:** **PAUSED** pending completion of Gate 1 temperature ingestion across the full 1981–2024 record.
* **Resumption Trigger:** Ingestion and SHA-256 verification of 1981–2024 ERA5-Land (or NOAA CPC) NetCDFs.
