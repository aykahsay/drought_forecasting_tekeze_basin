# AI-DREWS Limitations and Uncertainty Report
## Boundary Conditions, Reanalysis Uncertainties, Downscaling Limits, and Socio-Economic Disclaimers

**Document ID:** `AI-DREWS-DOC-LU-2026-10`  
**Reference Standards:** WMO Guidelines on Communicating Uncertainty / IPCC Uncertainty Guidance  
**Status:** **ACTIVE LIMITATIONS SPECIFICATION**

---

### 1. Climate Source & Observational Uncertainties

1. **Reanalysis vs In-Situ Observations:**
   * ECMWF ERA5-Land is a numerical model reanalysis driven by atmospheric forcing, not direct station observations. While it resolves complex topography far better than coarse products, elevation lapse rates and valley inversion layers in the Ethiopian Highlands may contain local biases.
2. **NOAA CPC Gridded Station Density:**
   * The NOAA CPC Global Unified Temperature dataset interpolates operational GTS surface station records. In Northern Ethiopia, station density has varied substantially over the 1981–2024 period, particularly during periods of conflict or infrastructure disruptions. It serves as an independent comparison, not absolute ground truth.
3. **CHIRPS Satellite Rainfall Estimates:**
   * CHIRPS blends satellite infrared cold cloud duration (CCD) with available rain gauge data. In complex terrain like the Simien Mountains (elevations $> 4,000\text{ m}$), warm orographic rain clouds may occasionally be underestimated.

---

### 2. Spatial Scale & Downscaling Constraints

1. **Provisional Basin Delineation:**
   * The complete Tekezé Basin area is calculated as $67,135.4\text{ km}^2$ based on HydroBASINS Level 5/6/7 sub-basins. While it accurately reflects the drainage outlet at the Sudanese border, the exact area remains provisional pending an authoritative topological boundary agreement with the Ethiopian Ministry of Water and Energy.
2. **Woreda / Kebele Downscaling:**
   * Gridded inputs ($0.05^\circ \approx 5.3\text{ km}$ for CHIRPS; $0.1^\circ \approx 9\text{ km}$ for ERA5-Land) cannot resolve field-level microclimates, farm-scale rain-shadow variations, or micro-catchment soil moisture gradients. AI-DREWS outputs represent zonal area-weighted averages, not point agricultural forecasts.

---

### 3. Drought Index Methodological Uncertainties

1. **Potential Evapotranspiration Formulations:**
   * Hargreaves-Samani PET relies on temperature extrema and extraterrestrial radiation. In humid tropical conditions or extreme pluvials, temperature-based PET can diverge from energy-balance Penman-Monteith estimates. Thornthwaite is maintained solely as a sensitivity check.
2. **Distribution Fitting on 30-Year Normals:**
   * Parameter estimation over the 1991–2020 baseline uses $N = 30$ sample points per calendar month. In extreme tails (e.g. 1-in-50 year events), sample uncertainty in L-skewness ($\tau_3$) can produce wider uncertainty intervals in standardized scores.
3. **Jensen's Inequality Concavity:**
   * Averaging non-linear quantities ($\overline{\sqrt{\Delta T}}$ vs $\sqrt{\overline{\Delta T}}$) introduces Jensen's inequality effects. While daily computation mitigates this bias, daily missing observations can introduce small sampling variations.

---

### 4. Forecasting & Teleconnection Limitations

1. **Correlation vs Causation:**
   * Teleconnection relationships (e.g. Niño 3.4 or Indian Ocean Dipole anomalies influencing Kiremt monsoon rains) represent statistical teleconnections, not deterministic causal mechanisms. El Niño events do not guarantee monsoon failure in every historical occurrence.
2. **Lead Time Horizon:**
   * Atmospheric predictability drops sharply beyond 1–3 months. Forecasts issued at 6-month leads carry substantial predictive uncertainty and must be communicated as broad probabilistic shifts, not categorical certainties.

---

### 5. Critical Socio-Economic & Humanitarian Disambiguation

> [!CAUTION]
> **Drought Deficit vs Human Famine:**
> Meteorological drought ($\text{SPEI-3} \le -2.0$) measures physical water balance deficits. It must never be equated with agricultural famine or human suffering. Famine is a complex socio-political outcome mediated by armed conflict, humanitarian access, market entitlements, displacement, and institutional response capacity. A physical drought signal provides early warning for preparedness, not proof of unavoidable starvation.
