# AI-DREWS Gate 4: Drought Target Reconstruction & Historical Validation Specification
## Hargreaves-Samani PET, Rolling Multi-Month SPEI-3 / SPI-3, Target Scale Validation, and Historical Ground-Truth Auditing

**Document ID:** `AI-DREWS-GATE4-SPEC-2026-10-REV7.2`  
**Standard:** WMO-No. 100 Guidelines; Vicente-Serrano et al. (2010); Hargreaves & Samani (1985); FEWS NET Historical Archives; Hosking (1990)  
**Status:** **SPECIFIED & BENCHMARKED (Full 1981–2024 Reconstruction Paused Pending Gate 1 Completion)**  
**Implementation Modules:** [`drought_forecasting/agriminds/climate/spei_calculator.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/agriminds/climate/spei_calculator.py), [`scripts/process_temperature_daily_to_monthly.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/process_temperature_daily_to_monthly.py)

---

### 1. Potential Evapotranspiration (PET) Formulation & Audit

#### 1.1 Hargreaves–Samani (1985; FAO-56) Formulation & Radiation Units
In semi-arid, high-elevation river basins like the Tekezé ($67,135.4\text{ km}^2$, mean elevation $\sim 1,850\text{ m}$), radiation and temperature extrema drive evaporative demand. In the conventional Hargreaves–Samani formulation (FAO-56 Eq. 52; Allen et al. 1998):
$$\text{PET}_d = 0.0023 \times 0.408 \times R_{a,d} \times (T_{\text{mean},d} + 17.8) \sqrt{T_{\max,d} - T_{\min,d}} \quad [\text{mm/day}]$$
$$\equiv 0.0023 \times R_{a,\text{eq},d} \times (T_{\text{mean},d} + 17.8) \sqrt{T_{\max,d} - T_{\min,d}} \quad [\text{mm/day}]$$
Where:
* $R_{a,d}$ is extraterrestrial solar radiation expressed in conventional energy units ($\text{MJ}\cdot\text{m}^{-2}\cdot\text{day}^{-1}$) calculated from astronomical relations (solar constant $G_{sc} = 0.0820\text{ MJ}\cdot\text{m}^{-2}\cdot\text{min}^{-1}$, catchment latitude $\phi \approx 13.2^\circ\text{N}$, and day of year).
* $0.408 \text{ mm}/(\text{MJ}\cdot\text{m}^{-2})$ is the inverse latent heat of vaporization ($\lambda \approx 2.45\text{ MJ/kg}$) converting radiative energy into equivalent water depth ($R_{a,\text{eq}} = 0.408 \cdot R_a$).
* $0.0023 \times 0.408 = 0.0009384$.
* $T_{\text{mean},d} = \frac{T_{\max,d} + T_{\min,d}}{2}$ in $^\circ\text{C}$.
* $\Delta T_d = T_{\max,d} - T_{\min,d}$ is the daily diurnal temperature range (DTR).
* Monthly accumulated PET is computed as the exact sum of daily values: $\text{PET}_{\text{month}} = \sum_{d=1}^{N_m} \text{PET}_d$, strictly preserving leap-year day counts (29 days in Feb for leap years vs 28 in non-leap).

#### 1.2 Jensen's Inequality & Synoptic Covariance
By Jensen's inequality for concave functions ($g(u) = \sqrt{u}$):
$$\overline{\sqrt{\text{DTR}}} \le \sqrt{\overline{\text{DTR}}}$$
* **Covariance Qualification:** While Jensen's inequality guarantees that the average of daily roots is less than the root of the average diurnal range, this alone **does not establish the net direction of bias** in the complete Hargreaves–Samani equation.
* In the full equation, daily radiation $R_a$, temperature $(T_{\text{mean}} + 17.8)$, and $\sqrt{\text{DTR}}$ covary synoptically across days:
  $$\overline{R_a (T_{\text{mean}} + 17.8) \sqrt{\text{DTR}}} = \overline{R_a} \cdot \overline{(T_{\text{mean}} + 17.8)} \cdot \overline{\sqrt{\text{DTR}}} + \text{Covariance Terms}$$
* Daily summation preserves day-to-day joint variation. The net empirical difference between daily summation and monthly-input calculation must be evaluated empirically for the Tekezé catchment rather than asserted a priori.

---

### 2. Multi-Month Standardized Drought Target Derivation

#### 2.1 Rolling Water Balance, 1980 Boundary Handling & Missing-Value Propagation
For each calendar month $t \in \{1, \dots, 528\}$:
1. Monthly water balance: $D_t = P_t - \text{PET}_t$.
2. Rolling 3-month accumulation:
   $$D_{3,t} = \sum_{k=0}^2 D_{t-k} = \sum_{k=0}^2 (P_{t-k} - \text{PET}_{t-k})$$
3. Rolling 3-month precipitation:
   $$P_{3,t} = \sum_{k=0}^2 P_{t-k}$$

* **Boundary Condition Reality:** Calculating rolling 3-month water balance for January and February 1981 requires observations from November and December 1980. Because CHIRPS-2.0 precipitation data starts in January 1981 and synthetic backfilling is prohibited, $D_{3,\text{Jan 1981}}$ and $D_{3,\text{Feb 1981}}$ are strictly `NaN`.
* **528-Month Sequence Preservation:** The output archive maintains all 528 calendar months with explicit boolean validity (`is_valid`) and failure flags (`failure_reason`). A 528-row table never implies 528 valid drought scores.
* **Exact Calibration Counts (1981–2005 Baseline):**
  * Months 1 & 2 (Jan, Feb): $N = 24$ observations (1982–2005).
  * Months 3–12 (Mar–Dec): $N = 25$ observations (1981–2005).
  * Primary September Target: $N = 25$ observations (1981–2005).

#### 2.2 Target Scale Validation (REV7.2 Requirement)
Before evaluating forecasting models in Gate 5, the empirical scale and stability of September-ending SPEI-3 under the frozen 1981–2005 training calibration must be reported:
1. Valid training sample size ($N=25$).
2. Fitted GLO parameters ($\hat{\xi}, \hat{\alpha}, \hat{k}$) and support boundary ($\hat{\xi} + \hat{\alpha}/\hat{k}$).
3. Count of observations mapped through operational endpoint safeguards ($z = \pm 5.0$) or support boundaries.
4. Categorical drought counts ($\le -1.0, -1.5, -2.0$) and non-drought counts.
5. Sensitivity comparison against alternative 1981–2014 calibration ($N=34$).

#### 2.3 Multi-Protocol 4-Tier Target Calibration Schema (Zero Leakage)
1. **Retrospective Climatological Target (`spei3_retro`):** Calibrated over 1991–2020 ($N=30$ per month) for retrospective hazard benchmarking.
2. **Training-Era Target (`spei3_train`):** Calibrated strictly on 1981–2005 ($N=24$ for Jan/Feb, $N=25$ for Mar–Dec).
3. **Validation Target (`spei3_validation`):** Standardized across 2006–2014 ($N=9$) using **frozen 1981–2005 parameters**.
4. **Primary Test Target (`spei3_test`):** Standardized across 2015–2024 ($N=10$) using **frozen 1981–2005 parameters**.
5. **Auxiliary Sensitivity Target (`spei3_test_expanded_sensitivity`):** Standardized using 1981–2014 calibration ($N=34$) as a documented sensitivity check.

#### 2.4 Numerical-Safeguard Sensitivity Evaluation
* In the transformation from non-exceedance probability to normal score, mapping endpoint probabilities ($p \le 0 \mapsto -5.0$, $p \ge 1 \mapsto +5.0$) is an operational safeguard, not an exact tail representation.
* The robust log-CDF and log-survival transformation evaluates extreme tails without underflow.
* **Sensitivity Finding:** Drought classifications were identical between the operational cap and robust log-transformation across all standard thresholds ($-1.0, -1.5, -2.0, -2.5$). Zero classification discrepancies occurred on tested observations.

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
> A meteorological drought anomaly ($\text{SPEI-3} \le -2.0$) does not automatically equal famine, nor does the absence of extreme meteorological drought prove food security. In AI-DREWS publications and dashboard interfaces, drought indices represent meteorological and hydrological water balance, never substituted as direct proxies for famine.

---

### 5. Gate 4 Execution Plan & Current Status

* **Status:** **PAUSED** pending completion of Gate 1 temperature ingestion across the full 1981–2024 record.
* **Resumption Trigger:** Ingestion and SHA-256 verification of 1981–2024 ERA5-Land (or NOAA CPC) NetCDFs.
