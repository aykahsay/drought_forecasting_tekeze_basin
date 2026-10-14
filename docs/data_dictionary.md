# AI-DREWS Data Dictionary
## Comprehensive Schema, Physical Units, Precision, and Quality Flags

**Document ID:** `AI-DREWS-DOC-DD-2026-10`  
**Dataset Reference:** `tekeze_monthly_climate_1981_2024.parquet` / `tekeze_monthly_temperature_audit_1981_2024.csv`

---

### 1. Temporal Identifiers

| Field Name | Type | Format / Allowed Values | Description |
|---|---|---|---|
| `date` | String | `YYYY-MM-DD` (e.g. `1984-07-01`) | First calendar day of the observation month. |
| `year` | Integer | `[1981, 2024]` | Calendar year (Gregorian). |
| `month` | Integer | `[1, 12]` | Calendar month (1 = January, 12 = December). |
| `days_in_month` | Integer | `[28, 31]` | Total astronomical calendar days in the month (accounts for leap years). |
| `valid_days` | Integer | `[0, 31]` | Number of daily observations meeting the $\ge 80\%$ daily basin coverage threshold. |

---

### 2. Meteorological Variables & Climate Water Balance

| Field Name | Type | Physical Units | Valid Bounds | Aggregation & Definition |
|---|---|---|---|---|
| `precip_mm` | Float64 | $\text{mm/month}$ | $[0.0, 1500.0]$ | Area-weighted monthly precipitation from CHIRPS v2.0 ($0.05^\circ$). |
| `tmax_c` | Float64 | $^\circ\text{C}$ | $[-10.0, 60.0]$ | Monthly average of daily maximum surface air temperatures: $\frac{1}{N} \sum_{d} T_{\max, d}$. |
| `tmin_c` | Float64 | $^\circ\text{C}$ | $[-20.0, 45.0]$ | Monthly average of daily minimum surface air temperatures: $\frac{1}{N} \sum_{d} T_{\min, d}$. |
| `tmean_c` | Float64 | $^\circ\text{C}$ | $[-15.0, 50.0]$ | Midpoint mean: $\frac{T_{\max} + T_{\min}}{2}$. |
| `dtr_c` | Float64 | $^\circ\text{C}$ | $[0.0, 35.0]$ | Monthly mean diurnal temperature range: $T_{\max} - T_{\min}$. |
| `mean_sqrt_dtr` | Float64 | $\sqrt{^\circ\text{C}}$ | $[0.0, 6.0]$ | Jensen-unbiased daily extrema root: $\frac{1}{N} \sum_{d} \sqrt{T_{\max,d} - T_{\min,d}}$. |
| `sqrt_mean_dtr` | Float64 | $\sqrt{^\circ\text{C}}$ | $[0.0, 6.0]$ | Naive monthly root: $\sqrt{\overline{\Delta T_{\text{monthly}}}}$. |
| `jensen_ratio` | Float64 | Dimensionless | $(0.90, 1.00]$ | Extrema concavity ratio: $\frac{\overline{\sqrt{\Delta T}}}{\sqrt{\overline{\Delta T}}}$. |
| `pet_hargreaves_mm` | Float64 | $\text{mm/month}$ | $[0.0, 500.0]$ | Monthly Hargreaves-Samani PET using daily extrema and extraterrestrial radiation $R_a$. |
| `pet_thornthwaite_mm` | Float64 | $\text{mm/month}$ | $[0.0, 500.0]$ | Monthly Thornthwaite PET using monthly mean temperature and daylength adjustments. |
| `water_balance_mm` | Float64 | $\text{mm/month}$ | $[-500.0, 1500.0]$ | Climatic water balance: $D = P - \text{PET}$. |

---

### 3. Multi-Month Drought Indices

| Field Name | Type | Physical Units | Valid Bounds | Definition & Distribution |
|---|---|---|---|---|
| `p_rolling_3` | Float64 | $\text{mm}$ | $[0.0, 4000.0]$ | Rolling 3-month accumulated precipitation: $P_{3,t} = \sum_{k=0}^2 P_{t-k}$. |
| `d_rolling_3` | Float64 | $\text{mm}$ | $[-1500.0, 4000.0]$ | Rolling 3-month accumulated water balance: $D_{3,t} = \sum_{k=0}^2 D_{t-k}$. |
| `spi_3` | Float64 | Dimensionless (Std. Dev.) | $[-4.75, +4.75]$ | Standardized Precipitation Index fitted via 2-parameter Gamma MLE (Thom 1958) with zero-rain adjustment. |
| `spei_3` | Float64 | Dimensionless (Std. Dev.) | $[-4.75, +4.75]$ | Standardized Precipitation-Evapotranspiration Index fitted via Hosking (1990) GLO L-moments. |

---

### 4. Quality Control & Source Flags

| Field Name | Type | Allowed Values | Definition |
|---|---|---|---|
| `spatial_coverage_fraction` | Float64 | $[0.0, 1.0]$ | Fraction of catchment area weight contributing valid data for the month. |
| `precip_source_id` | String | `CHIRPS_v2.0_p05`, `MISSING` | Unique identifier of precipitation source. |
| `temperature_source_id` | String | `ERA5_LAND_REANALYSIS`, `NOAA_CPC_V1.0`, `MISSING` | Unique identifier of temperature source. |
| `qc_status` | String | `CERTIFIED_OBSERVATION`, `PROVISIONAL_OBSERVATION`, `INSUFFICIENT_COVERAGE`, `MISSING_DATA` | Primary quality certification status. |
| `provenance_hash` | String | Hex string (`sha256:...`) | SHA-256 hash of the underlying source NetCDF/GeoTIFF files. |
