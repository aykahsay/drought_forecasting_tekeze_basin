# AI-DREWS Quality Control & Data Cleansing Protocol
## Automated Auditing, Anomaly Detection, Spatial Coverage Gates, and NaN Propagation Rules

**Document ID:** `AI-DREWS-DOC-QCP-2026-10`  
**Reference Standards:** WMO-No. 100 / Guide to the Global Observing System  
**Status:** **ACTIVE QUALITY PROTOCOL**

---

### 1. Ingestion Quality Control (Gate 1 & Gate 3)

#### 1.1 Physical Bounds Validation
Every raw climate variable is verified against physical and climatological boundaries prior to aggregation:

| Variable | Lower Bound | Upper Bound | Action on Violation |
|---|---|---|---|
| Monthly Precipitation ($P$) | $0.0\text{ mm}$ | $1500.0\text{ mm}$ | Values $< 0.0$ or $> 1500.0$ rejected as NoData |
| Daily Max Temperature ($T_{\max}$) | $-20.0^\circ\text{C}$ | $+60.0^\circ\text{C}$ | Flagged `INVALID_TEMPERATURE_BOUNDS` |
| Daily Min Temperature ($T_{\min}$) | $-30.0^\circ\text{C}$ | $+45.0^\circ\text{C}$ | Flagged `INVALID_TEMPERATURE_BOUNDS` |
| Diurnal Temperature Range ($\Delta T$) | $0.0^\circ\text{C}$ | $+35.0^\circ\text{C}$ | Enforces physical constraint $T_{\max} \ge T_{\min}$ |
| Monthly Hargreaves PET | $0.0\text{ mm}$ | $+500.0\text{ mm}$ | Negative values rejected |

#### 1.2 Coordinate System & Monotonicity Auditing
* **Latitudes:** Verified monotonically decreasing from north to south.
* **Longitudes:** Verified monotonically increasing from west to east.
* **CRS:** Strict WGS 84 (`EPSG:4326`). Any projected raster is reprojected with documented bilinear interpolation.

---

### 2. Spatial Quality Control & Coverage Gates

#### 2.1 The 95% Spatial Area Coverage Threshold
To prevent localized grid artifacts or boundary clipping from biasing the catchment average:
$$\text{Coverage Ratio}_t = \sum_{(i,j) \in \text{valid}_t} w_{i,j}$$
* **Threshold Rule:** $\text{Coverage Ratio}_t \ge 0.95$.
* If $\text{Coverage Ratio}_t < 0.95$:
  * The monthly basin value is marked `NaN`.
  * The record is tagged `INSUFFICIENT_SPATIAL_COVERAGE`.
  * Under no circumstances is the 95% rule relaxed or the missing cells silently filled.

#### 2.2 NoData Sentinel Elimination
Sentinels such as $-9999.0$ (CHIRPS) or $9.9692 \times 10^{36}$ (NetCDF default) are strictly filtered out of both the numerator and denominator:
$$\text{Valid Mask}_{i,j,t} = (X_{i,j,t} \ge 0.0) \land \text{isfinite}(X_{i,j,t}) \land (w_{i,j} > 0)$$
$$\bar{X}_t = \frac{\sum_{\text{valid}} X_{i,j,t} \cdot w_{i,j}}{\sum_{\text{valid}} w_{i,j}}$$

---

### 3. Temporal Quality Control & Missing-Data Propagation

#### 3.1 Strict Rolling 3-Month Window Propagation
For rolling multi-month accumulations ($P_3, D_3$):
$$D_{3,t} = \sum_{k=0}^2 (P_{t-k} - \text{PET}_{t-k})$$
* **Strict Rule:** If *any* month in $\{t-2, t-1, t\}$ contains `NaN`, the rolling accumulation $D_{3,t} \equiv \text{NaN}$.
* **Prohibition:** Zero gap-filling, forward-filling, spline smoothing, or interpolation is permitted in the historical target series.

#### 3.2 528-Month Sequence Integrity
* Checks that every calendar month from `1981-01-01` to `2024-12-01` appears exactly once in strict chronological order.
* Leap days (February 29 in 1984, 1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024) are accounted for in daily-to-monthly aggregations.

---

### 4. Mathematical Distribution Quality Safeguards (Gate 2 & Gate 4)

1. **Adequate Sample Size:** Fitting Generalized Logistic or Gamma parameters over the reference normal requires at least $N_{\text{valid}} \ge 20$ valid years; otherwise raises `InadequateBaselineSampleError`.
2. **Shape Parameter Bounds:**
   * GLO shape parameter must satisfy $|k| < 1.0$ (ensuring finite mean).
   * GLO scale parameter must satisfy $\alpha > 0$.
3. **Probability Guards:** Probabilities are constrained to $[10^{-6}, 1 - 10^{-6}]$ to prevent non-finite standard normal deviates ($\pm \infty$).
