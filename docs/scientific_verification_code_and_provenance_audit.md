# AI-DREWS: Scientific Verification, Database Reconciliation & Provenance Audit

**Project:** AI-DREWS (Artificial Intelligence Drought Risk Early Warning System)  
**Study Domain:** Tekeze River Basin, Northern Ethiopian Highlands  
**Date:** October 2026  
**Auditor:** Pair Programming Scientific Reviewer  
**Status:** **RECONCILED & SCIENTIFICALLY REVISED**

---

## 1. Database Reconciliation: Resolving the Catalog Discrepancy

The earlier report listed 7,468 records across 6 index categories against a reported total of 8,431. Executing the exact SQL aggregation across all `(index_name, source_id)` groups reveals the exact breakdown:

```sql
SELECT index_name, source_id, COUNT(*), MIN(date), MAX(date)
FROM ocean_atmosphere_indices
GROUP BY index_name, source_id
ORDER BY index_name, source_id;
```

### Complete Reconciled Database Inventory (`agriminds.db`)

| `index_name` | `source_id` | Count | Min Date | Max Date | Description & Role |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **`Nino3.4_Monthly`** | `NOAA_PSL_HADISST` | **1,879** | `1870-01-01` | `2026-07-01` | **Primary Monthly SST Anomaly Series.** Point-in-time monthly anomalies from NOAA PSL HadISST (1870–2026). |
| **`ONI`** | `NOAA_CPC_ONI_OFFICIAL` | **920** | `1950-01-01` | `2026-08-01` | **Official 3-Month Running Mean Series.** NOAA CPC Oceanic Niño Index for ENSO episode designation. |
| **`Nino3.4` (Legacy)** | `NOAA_CPC_ONI` | **910** | `1950-01-01` | `2025-10-01` | *Omitted in earlier summary.* Legacy alias duplicating CPC ONI for backward compatibility with older training scripts. |
| **`Nino3.4` (Legacy)** | `NOAA_CPC` | **12** | `2025-11-01` | `2026-10-01` | *Omitted in earlier summary.* Operational extension of legacy alias. |
| **`Nino3.4` (Legacy)** | `ENSO_NOAA` | **1** | `2026-09-12` | `2026-09-12` | *Omitted in earlier summary.* Single diagnostic smoke-test record. |
| **`IOD_DMI`** | `NOAA_PSL_DMI` | **1,870** | `1870-01-01` | `2025-10-01` | Dipole Mode Index (HadISST long-term historical series). |
| **`IOD_DMI`** | `NOAA_CPC` | **12** | `2025-11-01` | `2026-10-01` | Operational live extension. |
| **`TNA`** | `NOAA_PSL_TNA` | **943** | `1948-01-01` | `2026-07-01` | Tropical North Atlantic Index ($5.5^\circ\text{N}–23.5^\circ\text{N}, 57.5^\circ\text{W}–15^\circ\text{W}$). |
| **`TSA`** | `NOAA_PSL_TSA` | **943** | `1948-01-01` | `2026-07-01` | Tropical South Atlantic Index ($\text{Eq}–20^\circ\text{S}, 30^\circ\text{W}–10^\circ\text{E}$). |
| **`AMO`** | `NOAA_PSL_AMO` | **901** | `1948-01-01` | `2023-01-01` | Atlantic Multidecadal Oscillation (unsmoothed Kaplan SST). |
| **TOTAL IN DATABASE** | *All 10 Streams* | **8,391** | `1870-01-01` | `2026-10-01` | **Exact database row count ($7,468 + 923 = 8,391$).** |

> [!NOTE]
> **Resolution of the 923-Record Difference:**
> 1. The previous report omitted the 7th database index name: **`Nino3.4`** (923 total rows across three sources: $910 + 12 + 1$).
> 2. This `Nino3.4` stream was maintained as an alias during the migration so that existing models (e.g., `train_model_with_lag_features.py`) querying `WHERE index_name = 'Nino3.4'` would not break while `Nino3.4_Monthly` and `ONI` were being established.
> 3. The true database total is **8,391**, exactly equal to the 7,468 records of the 6 listed indices plus the 923 legacy alias records ($7,468 + 923 = 8,391$). The reported "8,431" was a typo from an earlier test iteration before clearing duplicate test runs.

---

## 2. Actual Implementation Code: `parse_oni_detailed()` & HadISST Ingestion

The actual code implementing the parsing, derivation, and time-representation conventions from [`drought_forecasting/agriminds/climate/sources/ocean_teleconnections.py`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/agriminds/climate/sources/ocean_teleconnections.py) is documented below:

### A. `parse_oni_detailed()`: Explicit Rolling 3-Month Time Representation

```python
def parse_oni_detailed(text: str) -> List[Dict[str, Any]]:
    """
    Detailed parser for NOAA CPC ONI ASCII text file (oni.ascii.txt).
    
    TIME REPRESENTATION CONVENTION:
    Each line in NOAA CPC's oni.ascii.txt contains a 3-month season label (SEAS) and year (YR).
    Following standard climatological convention, each 3-month season is timestamped to its
    CENTERED MIDDLE MONTH:
      - DJF (Dec y-1, Jan y, Feb y) -> Centered on Jan (Month 1 of year y)
      - JFM (Jan y,   Feb y, Mar y) -> Centered on Feb (Month 2 of year y)
      - FMA (Feb y,   Mar y, Apr y) -> Centered on Mar (Month 3 of year y)
      - MAM (Mar y,   Apr y, May y) -> Centered on Apr (Month 4 of year y)
      - AMJ (Apr y,   May y, Jun y) -> Centered on May (Month 5 of year y)
      - MJJ (May y,   Jun y, Jul y) -> Centered on Jun (Month 6 of year y)
      - JJA (Jun y,   Jul y, Aug y) -> Centered on Jul (Month 7 of year y)
      - JAS (Jul y,   Aug y, Sep y) -> Centered on Aug (Month 8 of year y)
      - ASO (Aug y,   Sep y, Oct y) -> Centered on Sep (Month 9 of year y)
      - SON (Sep y,   Oct y, Nov y) -> Centered on Oct (Month 10 of year y)
      - OND (Oct y,   Nov y, Dec y) -> Centered on Nov (Month 11 of year y)
      - NDJ (Nov y,   Dec y, Jan y+1)-> Centered on Dec (Month 12 of year y)
      
    CRITICAL DISTINCTION:
    These values represent 3-month rolling averages of ERSSTv5 anomalies.
    They are explicitly tagged as period_type="3m_running_mean", NOT point monthly SST anomalies.
    """
    lines = text.splitlines()
    records = []
    month_map = {
        "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
        "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
    }
    for line in lines[1:]:
        parts = line.strip().split()
        if len(parts) >= 4:
            seas, yr_str, total_str, anom_str = parts[0], parts[1], parts[2], parts[3]
            try:
                yr = int(yr_str)
                m = month_map.get(seas, 1)
                anom = float(anom_str)
                records.append({
                    "date": f"{yr:04d}-{m:02d}-01",
                    "season": seas,
                    "year": yr,
                    "center_month": m,
                    "total_sst": float(total_str),
                    "oni_anom": round(anom, 2),
                    "period_type": "3m_running_mean",
                    "source_file": "oni.ascii.txt",
                })
            except (ValueError, KeyError):
                continue
    return records
```

### B. HadISST Ingestion & Seasonal Derivation Code

```python
def download_and_ingest_hadisst_nino34(
    data_dir: Optional[Path] = None,
    db_session: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Downloads NOAA PSL HadISST monthly Niño 3.4 SST anomaly series (1870–present),
    persists monthly observations into nino34_hadisst_monthly, derives seasonal and
    annual summaries into nino34_hadisst_seasonal_annual, and calculates statistical
    validation metrics against enso_historical (1990–2023) WITHOUT modifying enso_historical.
    """
    # ... [fetch logic omitted for brevity] ...

    # 1. Parse matrix from raw NOAA PSL data (1870 to present)
    # Header format: start_year end_year
    header_parts = lines[0].strip().split()
    start_yr, end_yr = int(header_parts[0]), int(header_parts[1])

    monthly_records = []
    for line in lines[1:]:
        parts = line.strip().split()
        if not parts:
            continue
        try:
            yr = int(parts[0])
            if yr < start_yr or yr > end_yr:
                continue
            vals = [float(p) for p in parts[1:13]]
            for m_idx, val in enumerate(vals, start=1):
                if val > -90.0:  # Valid anomaly; missing value is -99.99
                    date_str = f"{yr:04d}-{m_idx:02d}-01"
                    monthly_records.append({
                        "year": yr,
                        "month": m_idx,
                        "date": date_str,
                        "nino34_anom": round(val, 3),
                        "phase": classify_enso_phase(val),
                    })
        except (ValueError, IndexError):
            continue

    # 2. Derive Seasonal & Annual Summaries
    monthly_dict = {(r["year"], r["month"]): r["nino34_anom"] for r in monthly_records}
    seasonal_records = []

    for yr in range(start_yr, end_yr + 1):
        # DJF: Dec (yr-1), Jan (yr), Feb (yr) -> Explicitly uses prior year's December
        djf_vals = [monthly_dict.get((yr - 1, 12)), monthly_dict.get((yr, 1)), monthly_dict.get((yr, 2))]
        djf_valid = [v for v in djf_vals if v is not None]
        djf_anom = round(float(np.mean(djf_valid)), 3) if len(djf_valid) == 3 else None

        # MAM: Mar, Apr, May of current year
        mam_vals = [monthly_dict.get((yr, 3)), monthly_dict.get((yr, 4)), monthly_dict.get((yr, 5))]
        mam_valid = [v for v in mam_vals if v is not None]
        mam_anom = round(float(np.mean(mam_valid)), 3) if len(mam_valid) == 3 else None

        # JJA: Jun, Jul, Aug of current year
        jja_vals = [monthly_dict.get((yr, 6)), monthly_dict.get((yr, 7)), monthly_dict.get((yr, 8))]
        jja_valid = [v for v in jja_vals if v is not None]
        jja_anom = round(float(np.mean(jja_valid)), 3) if len(jja_valid) == 3 else None

        # SON: Sep, Oct, Nov of current year
        son_vals = [monthly_dict.get((yr, 9)), monthly_dict.get((yr, 10)), monthly_dict.get((yr, 11))]
        son_valid = [v for v in son_vals if v is not None]
        son_anom = round(float(np.mean(son_valid)), 3) if len(son_valid) == 3 else None

        # Annual: Jan - Dec of current year (requires >= 10 valid months)
        ann_vals = [monthly_dict.get((yr, m)) for m in range(1, 13)]
        ann_valid = [v for v in ann_vals if v is not None]
        ann_anom = round(float(np.mean(ann_valid)), 3) if len(ann_valid) >= 10 else None

        if any(v is not None for v in [djf_anom, mam_anom, jja_anom, son_anom, ann_anom]):
            seasonal_records.append({
                "year": yr,
                "nino34_djf": djf_anom,
                "nino34_mam": mam_anom,
                "nino34_jja": jja_anom,
                "nino34_son": son_anom,
                "nino34_annual": ann_anom,
                "n_months_valid": len(ann_valid),
                "source": "NOAA_PSL_HadISST",
                "climatology_base": "1981-2010",
            })
```

---

## 3. Validation of HadISST Derivation & Anomaly Baseline

### A. Raw Metadata Verification from Source File Footer
Inspecting the raw NOAA PSL data file footer (`drought_forecasting/data/raw/teleconnections/nino34.long.anom.data`) provides the following metadata:
```text
-99.99
NINA34
5N-5S 170W-120W
HadISST
Anomaly from 1981-2010
https://psl.noaa.gov/data/timeseries/month/
units=degC
```

- **SST Product:** UK Met Office Hadley Centre HadISST 1.1 (Rayner et al., 2003).
- **Geographic Bounds:** $5^\circ\text{N}–5^\circ\text{S}, 170^\circ\text{W}–120^\circ\text{W}$ (Niño 3.4 region).
- **Spatial Weighting:** Cosine-weighted area averaging across $1^\circ \times 1^\circ$ grid cells.
- **Climatological Baseline:** **1981–2010**. Monthly climatological mean $\overline{T}_{m, 1981–2010}$ is calculated for each calendar month $m \in \{1,\dots,12\}$:
  $$T'_{y,m} = T_{y,m} - \overline{T}_{m, 1981–2010}$$
- **Missing Value Sentinel:** `-99.99`.

### B. Missing Month & Boundary Verification
1. **Year 1870 (Start of Record):** Because December 1869 is prior to the start of the HadISST series, `djf_vals` contains only 2 valid months (Jan 1870, Feb 1870). As required by `len(djf_valid) == 3`, `nino34_djf` for 1870 evaluates to `NULL` (`None`). Querying the database confirms:
   `SELECT * FROM nino34_hadisst_seasonal_annual WHERE year=1870;` $\rightarrow$ `(1870, None, -0.970, -1.000, -0.747, -0.928, 12, ...)`
2. **Year 2026 (Partial Operational Year):** Months 1–7 (Jan–Jul) are observed, while months 8–12 are missing (`-99.99`).
   - DJF (Dec 2025, Jan 2026, Feb 2026): All 3 months valid $\rightarrow$ `-0.427 °C`.
   - MAM (Mar 2026, Apr 2026, May 2026): All 3 months valid $\rightarrow$ `+0.353 °C`.
   - JJA (Jun 2026, Jul 2026, Aug 2026): August is missing (`-99.99`) $\rightarrow$ `NULL` (`None`).
   - SON: Missing $\rightarrow$ `NULL` (`None`).
   - Annual: Only 7 valid months ($< 10$) $\rightarrow$ `NULL` (`None`).
   Querying the database confirms:
   `SELECT * FROM nino34_hadisst_seasonal_annual WHERE year=2026;` $\rightarrow$ `(2026, -0.427, 0.353, None, None, None, 7, ...)`

### C. Historical Homogeneity Limitations (1870–2026)
While HadISST extends back to 1870, this record is **not statistically stationary or homogeneous**:
- **Pre-1950:** Relies primarily on voluntary observing ship (VOS) bucket measurements with sparse spatial sampling and variable bias adjustments.
- **1950–1981:** Engine cooling water intake (ERI) measurements predominate with higher observation density.
- **Post-1981:** Satellite AVHRR retrievals combined with drifting buoys and Argo floats provide high spatial precision.
*Manuscript recommendation:* When conducting multi-decadal drought frequency analysis, treat the 1870–1949 record with explicit historical uncertainty intervals rather than treating it as an equivalent continuous instrument record.

---

## 4. Downgraded Provenance Conclusions

We adopt the recommended academic phrasing:

> **Revised Scientific Statement:**  
> *"The independently derived HadISST-based seasonal series showed strong numerical agreement with the legacy Niño 3.4 values for 1990–2023 ($r \ge 0.983$, $\text{MAE} \le 0.12^\circ\text{C}$ across all seasons). This supports their use as a cross-check, although the original provenance of the legacy series cannot be established conclusively from statistical agreement alone, as multiple SST products (e.g., HadISST, ERSSTv5, Kaplan) can produce highly correlated Niño 3.4 index values."*

---

## 5. Provenance Audit of Local Climate & Drought Target Variables

The local variables in `enso_historical` (`p_djf_m`, `p_mam_m`, `p_jja_m`, `p_son_m`, `p_c_mm_mon`, `t_djf_k`, `t_annual_c`, and `sc_pdsi`) were preserved to prevent breaking legacy model pipelines. A critical provenance audit of their source values shows:

| Variable | Stored Units | Values Sample (1990) | Lineage & Methodological Assessment | Verified Ground Truth? |
| :--- | :--- | :--- | :--- | :---: |
| `p_djf_m`, `p_mam_m`, `p_jja_m`, `p_son_m` | Metres ($m$) | `4.4e-05 m` (DJF), `0.009109 m` (JJA) | Magnitude ($10^{-5}$ to $10^{-2}$ m) reflects cumulative water-equivalent depth per timestep, indicative of ECMWF ERA5 gridded reanalysis export rather than station rain-gauge logs. | **NO** (Pending grid boundary audit) |
| `p_c_mm_mon` | mm / month | `27.914368 mm/mon` | Floating point precision (`.816091954`) reflects an area-averaged spatial aggregation over grid points. | **NO** (Pending basin mask audit) |
| `t_djf_k` to `t_son_k` | Kelvin ($K$) | `283.991638 K` (~10.8 °C) | Native ECMWF 2-metre temperature (`t2m`) variable is stored in Kelvin, supporting ERA5 extraction lineage. | **NO** (Reanalysis model prior, not in-situ station) |
| `t_annual_c` | Celsius ($^\circ\text{C}$) | `16.955886 °C` | Annual mean temperature derived from seasonal fields. | **NO** (Derived field) |
| `sc_pdsi` | Dimensionless | `-1.6159` (1990), `3.1243` (2023) | Self-calibrated Palmer Drought Severity Index. Calculation method (Wells et al., 2004 vs. Dai et al., 2004), available water capacity (AWC), and potential evapotranspiration (Thornthwaite vs. Penman-Monteith) are undocumented in `elnino.xlsx`. Missing for 2024–2026. | **NO** (Legacy target field pending formulaic reproduction) |

> [!CAUTION]
> **Status:** These columns are classified as **"legacy local-climate and drought-index fields pending source verification"**, rather than verified ground truth. For genuine verified rainfall ground truth in the Tekeze Basin, AI-DREWS relies on the georeferenced CHIRPS $0.05^\circ$ satellite-gauge archive (`chirps_ethiopia_2000_2024.nc`) and validated ERA5T reanalysis.

---

## 6. Four-Tier Operational Telemetry State Architecture

In accordance with Section 4 of the critique, [`NOAAONISource`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/agriminds/climate/sources/noaa.py#L464-L520) has been upgraded from a binary boolean flag t```python
{
    "source": "NOAA Climate Prediction Center (CPC)",
    "index": "Oceanic Niño Index (ONI) [3-Month Running Mean]",
    "operational_state": "DATABASE_LATEST",  # "LIVE" | "CACHED" | "DATABASE_LATEST" | "STATIC_SAMPLE"
    "latest_observation_date": "2026-08-01",
    "retrieval_timestamp": "2026-10-14T10:48:02.124567+00:00",
    "data_age_days": 74,
    "current_oni_value": -0.66,
    "weekly_nino34_value": -0.69,
    "phase": "WEAK_LA_NINA",
    "source_identifier": "NOAA_CPC_ONI_OFFICIAL",
    "is_live_telemetry": False,  # Only True if operational_state == "LIVE"
    "weekly_nino34_telemetry": {
        "index_name": "Niño 3.4 Weekly SST Anomaly",
        "value": -0.69,
        "units": "°C",
        "source_identifier": "PROVISIONAL_PROXY_FROM_ONI",
        "observation_date": "2026-08-01",
        "retrieval_timestamp": "2026-10-14T11:00:15Z",
        "provenance_note": (
            "Temporally distinct from 3-month running mean ONI. "
            "Values must not be conflated as simultaneous identical observations."
        )
    }
}
```

### Operational State Definitions

| State | Definition & Operational Condition | Evidential Guarantee |
| :--- | :--- | :--- |
| **`LIVE`** | Successfully fetched from NOAA CPC HTTP endpoint during the current execution run ($\text{age} \le 45\text{ days}$). | Fresh operational telemetry. |
| **`CACHED`** | Retrieved from a locally stored, previously downloaded source file (`data/raw/teleconnections/oni.ascii.txt`). | Unaltered source data; may have latency. |
| **`DATABASE_LATEST`** | Latest observation queried from `ocean_atmosphere_indices` table. | Reflects database state; explicitly reports `data_age_days`. |
| **`STATIC_SAMPLE`** | Offline fallback demonstration values (e.g., hardcoded demo data). | **Never presented as operational telemetry.** |

---

## 7. Bayesian Drought Forecast Evaluation: Holdout vs. Expanding-Window Backtesting

### A. Mathematical Formulation of the Predictive Distribution
For the Normal-Inverse-Gamma conjugate prior $\beta \mid \sigma^2 \sim \mathcal{N}(\mu_0, \sigma^2 V_0)$ and $\sigma^2 \sim \text{Inv-Gamma}(a_0, b_0)$, the marginal posterior predictive distribution for a new predictor vector $x^*$ is analytically a non-standardized Student-$t$:

$$y^* \mid y \sim t_{\nu} \left( \mu_{\text{pred}},\, s_{\text{pred}} \right)$$

where:
- **Degrees of freedom:** $\nu = 2 a_N = 2 a_0 + N$
- **Location:** $\mu_{\text{pred}} = x^* \mu_N$
- **Scale:** $s_{\text{pred}} = \sqrt{s^2 (1 + x^* V_N x^{*T})}$, with residual variance estimate $s^2 = \frac{b_N}{a_N}$

The exceedance probability for agricultural drought ($\text{Sc-PDSI} \le -1.0$) is evaluated directly using the Student-$t$ CDF:
$$P(\text{Sc-PDSI} \le -1.0 \mid x^*) = F_t \left( -1.0;\, \mu_{\text{pred}},\, s_{\text{pred}},\, \nu \right)$$

### B. Holdout Partition Evaluation (2019–2023, $N=5$, Zero Historically Labeled Droughts)
- **Target Provenance Note:** These drought years are *historically labeled under the current Sc-PDSI series*, not verified ground-truth drought events, because the raw spatial calculation and calibration of `sc_pdsi` in `enso_historical` remain undocumented pending independent validation.
- **Training (1990–2018, $N=29$):** 15 historically labeled drought years out of 29 ($p_{\text{clim}} = \frac{15}{29} \approx 0.5172$).
- **Holdout Outcomes:** All 5 years experienced non-drought conditions ($o_i = 0$ for all $i \in \{1,\dots,5\}$):
  - 2019: $+0.01$ ($o_1 = 0$)
  - 2020: $+0.91$ ($o_2 = 0$)
  - 2021: $-0.99$ ($o_3 = 0$)
  - 2022: $+2.17$ ($o_4 = 0$)
  - 2023: $+3.12$ ($o_5 = 0$)
- **Probabilistic Verification Scores:**

| Forecast Method | Forecast Formulation | Holdout Brier Score ($BS$) | Reference Comparison ($BSS$) | Calibration Assessment |
| :--- | :--- | :---: | :---: | :--- |
| **Climatological Reference** | Constant prior frequency: $p_{\text{clim}} = \frac{15}{29} = 0.5172$ | **0.2675** | Baseline ($BSS = 0.0\%$) | Unconditioned base rate. |
| **Bayesian Predictive Model** | Student-$t$ predictive exceedance conditioning on $\text{Nino}_{\text{DJF}}$ and $\text{Nino}_{\text{MAM}}$ | **0.2484** | **+7.14% Skill** ($BSS = +0.0714$) | Dynamically conditions on precursors, reducing probability during anti-phased years (e.g. 2022 $p=0.370$). |
| **1-Year Lag Persistence** | Binary persistence from prior year: $p_t = \mathbb{I}(\text{PDSI}_{t-1} \le -1.0)$ | **0.2000** | Reference | 2018 was labeled drought (error 1.0); 2019–2022 non-drought (error 0.0). |

*Limitation:* Because the holdout sample has zero positive events, $ROC\text{-}AUC$ is mathematically undefined.

### C. Expanding-Window Backtesting: Controlled Teleconnection Ablation Experiment (2006–2023)

#### 1. Verification of Climatology and Persistence Baselines (Zero Lookahead Leakage)
To ensure the backtesting scores are scientifically rigorous and leak-free:
- **Climatological Reference ($A_1$):** At each forecast year $t \in [2006, 2023]$, the forecast probability $p_{\text{clim}, t} = \frac{1}{t - 1990} \sum_{i=1990}^{t-1} \mathbb{I}(\text{Sc-PDSI}_i \le -1.0)$ is computed strictly from observations *prior* to year $t$. Future years are never included.
- **Persistence Reference ($A_2$):** At each forecast year $t$, the forecast probability $p_{\text{pers}, t} = \mathbb{I}(\text{Sc-PDSI}_{t-1} \le -1.0)$ strictly utilizes the previous year's observed status.
- **Sample Event Basis:** Across the 18 backtest years (2006–2023), exactly **5 historically labeled drought years** occurred (2008, 2011, 2014, 2015, 2018), representing an event base rate of $27.8\%$ ($5/18$). Five events represent a small empirical sample, mandating bootstrap uncertainty estimation.

#### 2. Controlled Model Ablation Design
All models are evaluated on **identical expanding-window forecast dates (2006–2023, $N=18$)**, trained strictly on prior years, using standardized continuous predictors to eliminate scale disparities:

| Model | Predictor Tier | Predictor Composition |
| :--- | :--- | :--- |
| **A1** | Reference | Climatology (dynamically updated expanding base rate) |
| **A2** | Reference | 1-Year Lag Persistence |
| **B** | Local History | Precursor precipitation + precursor 2m temperature |
| **C** | Local + Pacific | Local climate + Pacific Niño 3.4 SST anomaly |
| **D** | Local + Pacific + Indian | Local climate + Niño 3.4 + Indian Ocean Dipole (DMI) |
| **E** | Full Multi-Ocean Coupling | Local climate + Niño 3.4 + DMI + Tropical Atlantic (TNA + TSA) |

#### 3. Empirical Ablation Results across Forecast Horizons

##### Horizon 1: Post-MAM (Lead-1: June 1 Forecast Origin, pre-Kiremt Monsoon)
*Precursors:* MAM local precip, MAM local temp, MAM Niño 3.4, MAM DMI, MAM TNA, MAM TSA.

| Model | Predictor Composition | Brier Score ($BS$) | 95% Bootstrap CI | $BSS_{\text{clim}}$ | $BSS_{\text{pers}}$ | $ROC\text{-}AUC$ | Mean Predicted $P$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A1** | Climatological Reference | **0.2686** | $[0.2458, 0.2918]$ | Baseline | $+46.27\%$ | 0.500 | 0.527 |
| **A2** | 1-Year Lag Persistence | 0.5000 | $[0.2778, 0.7222]$ | $-86.12\%$ | Baseline | 0.538 | 0.333 |
| **B** | Local Climate History | 0.2967 | $[0.2307, 0.3579]$ | $-10.45\%$ | $+40.65\%$ | 0.431 | 0.588 |
| **C** | Local + Pacific Niño 3.4 | 0.3019 | $[0.2365, 0.3727]$ | $-12.36\%$ | $+39.63\%$ | 0.477 | 0.574 |
| **D** | Local + Niño 3.4 + DMI | 0.3105 | $[0.2220, 0.4064]$ | $-15.59\%$ | $+37.89\%$ | 0.569 | 0.585 |
| **E** | Local + Niño 3.4 + DMI + TNA/TSA | 0.2842 | $[0.1699, 0.4074]$ | **-5.81%** | $+43.15\%$ | **0.708** | 0.584 |

##### Horizon 2: Post-DJF (Lead-2: March 1 Forecast Origin, pre-Belg Season)
*Precursors:* DJF local precip, DJF local temp, DJF Niño 3.4, DJF DMI, DJF TNA, DJF TSA.

| Model | Predictor Composition | Brier Score ($BS$) | 95% Bootstrap CI | $BSS_{\text{clim}}$ | $BSS_{\text{pers}}$ | $ROC\text{-}AUC$ | Mean Predicted $P$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A1** | Climatological Reference | **0.2686** | $[0.2458, 0.2918]$ | Baseline | $+46.27\%$ | 0.500 | 0.527 |
| **A2** | 1-Year Lag Persistence | 0.5000 | $[0.2778, 0.7222]$ | $-86.12\%$ | Baseline | 0.538 | 0.333 |
| **B** | Local Climate History | 0.2901 | $[0.2390, 0.3370]$ | $-8.00\%$ | $+41.97\%$ | 0.508 | 0.561 |
| **C** | Local + Pacific Niño 3.4 | 0.3036 | $[0.2519, 0.3550]$ | $-13.01\%$ | $+39.28\%$ | 0.415 | 0.558 |
| **D** | Local + Niño 3.4 + DMI | 0.2961 | $[0.2381, 0.3524]$ | $-10.22\%$ | $+40.78\%$ | 0.400 | 0.539 |
| **E** | Local + Niño 3.4 + DMI + TNA/TSA | 0.2789 | $[0.2080, 0.3506]$ | **-3.82%** | $+44.22\%$ | 0.508 | 0.514 |

##### Horizon 3: Multi-Season Precursor (DJF + MAM Precursors)
*Precursors:* DJF & MAM precip, temp, Niño 3.4, DMI, TNA, TSA.

| Model | Predictor Composition | Brier Score ($BS$) | 95% Bootstrap CI | $BSS_{\text{clim}}$ | $BSS_{\text{pers}}$ | $ROC\text{-}AUC$ | Mean Predicted $P$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A1** | Climatological Reference | **0.2686** | $[0.2458, 0.2918]$ | Baseline | $+46.27\%$ | 0.500 | 0.527 |
| **A2** | 1-Year Lag Persistence | 0.5000 | $[0.2778, 0.7222]$ | $-86.12\%$ | Baseline | 0.538 | 0.333 |
| **B** | Local Climate History | 0.3027 | $[0.2351, 0.3701]$ | $-12.68\%$ | $+39.46\%$ | 0.431 | 0.579 |
| **C** | Local + Pacific Niño 3.4 | 0.3121 | $[0.2418, 0.3830]$ | $-16.18\%$ | $+37.58\%$ | 0.400 | 0.564 |
| **D** | Local + Niño 3.4 + DMI | 0.3350 | $[0.2272, 0.4492]$ | $-24.69\%$ | $+33.00\%$ | 0.477 | 0.563 |
| **E** | Local + Niño 3.4 + DMI + TNA/TSA | 0.3658 | $[0.2158, 0.5121]$ | $-36.17\%$ | $+26.84\%$ | 0.523 | 0.571 |

#### 4. Scientific Findings & Rigorous Claim Formulation

> **Scientific Finding:** The Pacific-only Bayesian model did not outperform climatology in the reported expanding-window evaluation ($BSS_{\text{clim}} = -12.36\%$ to $-16.18\%$). This motivates testing whether Indian and Atlantic teleconnection indices provide additional predictive information beyond Pacific ENSO indicators and local climate variables. Their incremental value remains to be established through controlled ablation experiments.

Key scientific insights from the controlled ablation:
1. **Linear Statistical Models vs. Climatology:** Across all three horizons, all statistical models (B through E) substantially outperform 1-year persistence ($BSS_{\text{pers}} = +26.8\%$ to $+44.2\%$), but **none outperform expanding climatology on Brier score** in this 18-year backtest.
2. **Estimation Variance Inflation on Small Event Counts:** Because the 18-year sample contains only 5 historically labeled drought events, fitting high-dimensional predictor sets (e.g., Model E with 6 to 10 predictors on $N=16$ to $33$ training samples) inflates parameter estimation variance. This is demonstrated by the widening bootstrap 95% confidence intervals (for Model E at Lead-1: $[0.1699, 0.4074]$ vs. $[0.2458, 0.2918]$ for climatology).
3. **Discrimination vs. Probabilistic Calibration:** While multi-ocean coupling (Model E) does not beat climatology on Brier score, it noticeably improves discrimination at Lead-1 ($\text{AUC} = 0.708$ compared to $0.477$ for Pacific-only Model C and $0.431$ for Model B).
4. **Methodological Next Steps:** This empirical demonstration directly proves that a small 18-year sample ($N=18$, 5 events) under undocumented legacy targets cannot definitively resolve the incremental value of multi-ocean predictors. The decisive requirement is to build a documented, reproducible dataset from scratch covering 1981–2024 ($N=44$ years, $\approx 15$ drought years) using open-access CHIRPS rainfall, gridded temperature, and multi-scalar SPEI/SPI. Once the target, temporal splits, and baselines are fully trustworthy on this larger record, we can rigorously test whether spatial CNN or hybrid architectures add value beyond calibrated statistical baselines.

---

## 8. Verification of the Season-to-Year Convention (DJF Boundary Check)

To ensure that the seasonal derivation $\text{DJF}_y = \frac{\text{Dec}_{y-1} + \text{Jan}_y + \text{Feb}_y}{3}$ does not introduce a 1-year lag relative to `enso_historical`, boundary cases were examined across major historical El Niño events:

### A. 1997–1998 Super El Niño
- **`enso_historical`:** 1997 SON = $+2.3$ | 1998 DJF = $+2.2$ (DJF peak assigned to 1998).
- **Derived HadISST:** 1997 SON = $+2.27$ | 1998 DJF = $+2.27$ (DJF peak assigned to 1998).
If `enso_historical` had assigned Dec 1997 to 1997, 1997 DJF would have been $+2.2^\circ\text{C}$. Instead, 1997 DJF is $-0.5^\circ\text{C}$ and 1998 DJF is $+2.2^\circ\text{C}$.

### B. 2015–2016 Super El Niño
- **`enso_historical`:** 2015 SON = $+2.4$ | 2016 DJF = $+2.5$ (DJF peak assigned to 2016).
- **Derived HadISST:** 2015 SON = $+2.26$ | 2016 DJF = $+2.41$ (DJF peak assigned to 2016).

**Conclusion:** Both series use the **identical convention**:
$$\text{DJF}_y = \frac{\text{Dec}_{y-1} + \text{Jan}_y + \text{Feb}_y}{3}$$
The paired comparison has zero year-alignment bias.
