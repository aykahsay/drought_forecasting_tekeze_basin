# Gate 1 Raw Climate Data Ingestion & Provenance Audit Report

**Document ID:** `AI-DREWS-DOC-G1-AUDIT-2026-10`  
**Standard:** Open Science / FAIR Data Principles / WMO Climatological Guidelines  
**Audit Date:** October 15, 2026  
**Gate 1 Status:** **PARTIAL (Historical Drought Reconstruction and Downstream Modeling Paused)**  
**Target Basin:** Tekezé River Basin ($67,135.4\text{ km}^2$ provisional, Northern Ethiopia; $[11.5^\circ\text{N}, 15.3^\circ\text{N}]$, $[36.3^\circ\text{E}, 40.0^\circ\text{E}]$)

---

## 1. Executive Summary & Audit Mandate

In accordance with the scientific review of the AI-DREWS scientific workflow, this document provides a comprehensive, file-by-file forensic audit of all raw climate data files currently acquired and stored on local disk in `data/raw/`.

### Core Certification Finding
> [!IMPORTANT]
> **GATE 1 STATUS IS CERTIFIED AS `PARTIAL`:**
> While reproducible download scripts, automated quality control protocols, and the 1984 historical benchmark dataset have been acquired and verified, **the complete 1981–2024 archive has not yet been fully ingested into the local repository**.
>
> Specifically:
> 1. **NOAA CPC Temperature:** The 1984 daily benchmark (`tmax.1984.nc` and `tmin.1984.nc`) is present, verified, and checksum-locked, but years 1981–1983 and 1985–2024 remain pending batch acquisition.
> 2. **ECMWF ERA5-Land Temperature:** The downloader script (`scripts/download_era5_land_tekeze_1981_2024.py`) is verified and ready, but local ERA5-Land NetCDF storage currently contains 0 files, awaiting Copernicus Climate Data Store (CDS) batch execution.
> 3. **CHIRPS Precipitation:** High-resolution monthly rainfall is locally stored (168 compressed monthly GeoTIFFs in `data/raw/chirps_monthly/` and a 2000–2024 NetCDF in `data/raw/chirps_ethiopia_2000_2024.nc`), but requires completion of the full 528-month continuous archive.
>
> Therefore, in strict compliance with the **Non-Negotiable Research Protocol (Rule 6)**, the full 1981–2024 historical drought target reconstruction (Gate 4) and all machine learning forecasting models (Gate 5) **remain on hold**.

---

## 2. Exhaustive Local Raw File Inventory & Checksums

The table below lists every raw climate file currently residing on the local filesystem in `data/raw/`, detailing product, variable, temporal coverage, spatial grid coordinates, physical units, missing data counts, file size, and cryptographic SHA-256 hashes.

| Product / Dataset | File Name / Path | Variable | Time Coverage & Reconciled Span | Spatial Grid Coordinates | Units | Total Cells | Missing Cells (%) | File Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **NOAA CPC Global Unified** | `data/raw/temperature/cpc/tmax.1984.nc` | `tmax` (Daily Max Temp) | 1984-01-01 to 1984-12-31 (366 days, leap year) | Global $0.5^\circ \times 0.5^\circ$<br>Lat: $[-89.75, 89.75]$ ($N=360$)<br>Lon: $[0.25, 359.75]$ ($N=720$) | $^\circ\text{C}$ | $94,867,200$ | $69,716,712$<br>($73.49\%$ global ocean mask) | $87,688,044\text{ B}$<br>($83.62\text{ MB}$) | `476fae44066168fab45e76fc98aae9bba22c4f00ea1f18cb6304727dadb7305b` |
| **NOAA CPC Global Unified** | `data/raw/temperature/cpc/tmin.1984.nc` | `tmin` (Daily Min Temp) | 1984-01-01 to 1984-12-31 (366 days, leap year) | Global $0.5^\circ \times 0.5^\circ$<br>Lat: $[-89.75, 89.75]$ ($N=360$)<br>Lon: $[0.25, 359.75]$ ($N=720$) | $^\circ\text{C}$ | $94,867,200$ | $69,716,558$<br>($73.49\%$ global ocean mask) | $89,076,688\text{ B}$<br>($84.95\text{ MB}$) | `b14e8bba53532cddcaad6120bbe031f38e0bf4755cf92efb248a92f8ac2fedea` |
| **CHIRPS 2.0 Ethiopia NetCDF** | `data/raw/chirps_ethiopia_2000_2024.nc` | `precip` (Monthly Rainfall) | **Reconciled Reality:** 2018–2024 only (84 months).<br>*Defect:* Filename claims 2000–2024 (300 months), but missing 1981–2017 (216 mos of target span); lacks CF `time` coordinate. | Ethiopia $0.05^\circ \times 0.05^\circ$<br>Lat: $[3.0, 15.5]$ ($N=250$)<br>Lon: $[33.0, 48.0]$ ($N=300$) | $\text{mm/month}$ | $6,300,000$ | $514,500$<br>($8.17\%$ regional mask) | $18,075,588\text{ B}$<br>($17.24\text{ MB}$) | `39a0dc652ff6bf55592b96ac59b6ebe52f0ee33008ba41ed08a39c26afa8f822` |
| **CHIRPS 2.0 Africa GeoTIFF Archive** | `data/raw/chirps_monthly/*.tif.gz` (168 files) | `precip` (Monthly Rainfall) | **Reconciled Reality:** 14 sampled years ($14 \times 12 = 168$ mos): 1984, 1987, 1991, 1994, 1997, 2000, 2002, 2009, 2011, 2015, 2018, 2020, 2023, 2024.<br>*Defect:* Missing 30 years ($360$ months) of continuous 1981–2024 archive. | Africa $0.05^\circ \times 0.05^\circ$<br>Lat: $[-40.0, 40.0]$<br>Lon: $[-20.0, 55.0]$ | $\text{mm/month}$ | $3.84 \times 10^8$ (total) | NoData: $-9999$ excluded | $758,440,003\text{ B}$<br>($723.31\text{ MB}$) | Manifest logged in `temperature_provenance_manifest.json` |

---

### 2.1 Reconciled Resolution of the CHIRPS Inventory Discrepancy

A forensic examination of the CHIRPS holdings resolves the apparent contradiction between filenames and observation counts:
1. **The 84-Month NetCDF (`chirps_ethiopia_2000_2024.nc`):**
   * Inspection of NetCDF dimensions reveals: `time: 84`, `latitude: 250`, `longitude: 300`.
   * Exactly $84\text{ months} = 7\text{ years} \times 12\text{ months/year}$.
   * The file contains only the period **January 2018 through December 2024**. The filename `2000_2024` is a legacy misnomer inherited from an incomplete initial download script. Furthermore, the file omits a standard CF-1.6 `time` coordinate variable.
   * **Verdict:** This file is classified as an incomplete exploratory artifact; it **cannot** support a 1981–2024 reconstruction.
2. **The 168 Monthly GeoTIFFs (`data/raw/chirps_monthly/*.tif.gz`):**
   * File-by-file audit confirms exactly 168 files corresponding to 14 complete 12-month years: `1984, 1987, 1991, 1994, 1997, 2000, 2002, 2009, 2011, 2015, 2018, 2020, 2023, 2024`.
   * These 14 years were sampled around historical drought shocks and 3-year calibration intervals, leaving **30 unacquired years (360 months)**.
   * **Verdict:** Before Gate 1 can achieve certification, the missing 360 monthly GeoTIFFs must be downloaded from the CHC repository (`https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/`) to construct the continuous 528-month sequence.


## 3. Subgrid Inspection: Tekezé Basin Catchment (1984 Benchmark)

To verify the physical fidelity and missingness specifically over the study area, `tmax.1984.nc` and `tmin.1984.nc` were subset to the Tekezé bounding box ($[11.0^\circ\text{N}, 16.0^\circ\text{N}]$, $[36.0^\circ\text{E}, 40.5^\circ\text{E}]$):

```
Subgrid Spatial Coordinates:
  Latitudes (10 grid lines): [15.75, 15.25, 14.75, 14.25, 13.75, 13.25, 12.75, 12.25, 11.75, 11.25]
  Longitudes (9 grid lines):  [36.25, 36.75, 37.25, 37.75, 38.25, 38.75, 39.25, 39.75, 40.25]
  Total Daily Grid Dimensions: 366 days × 10 latitudes × 9 longitudes = 32,940 pixel-days
```

### Physical Value Verification

1. **Daily Maximum Temperature ($T_{\max}$):**
   * **Valid Pixel-Days:** $32,850$ ($99.73\%$ valid over land).
   * **Missing Pixel-Days:** $90$ ($0.27\%$ missing, confined to extreme coastal grid boundary).
   * **Observed Minimum $T_{\max}$:** $+13.62^\circ\text{C}$ (High-altitude Simien Mountain winter ridges).
   * **Observed Maximum $T_{\max}$:** $+44.03^\circ\text{C}$ (Lowland western canyon floor in pre-Kiremt May).
   * **Spatial Basin Mean $T_{\max}$:** $+29.19^\circ\text{C}$.

2. **Daily Minimum Temperature ($T_{\min}$):**
   * **Valid Pixel-Days:** $32,850$ ($99.73\%$ valid over land).
   * **Missing Pixel-Days:** $90$ ($0.27\%$ missing).
   * **Observed Minimum $T_{\min}$:** $-12.97^\circ\text{C}$ (Severe winter night frost at $>4,000\text{ m}$ elevation).
   * **Observed Maximum $T_{\min}$:** $+36.65^\circ\text{C}$ (Lowland tropical night).
   * **Spatial Basin Mean $T_{\min}$:** $+17.08^\circ\text{C}$.

3. **Jensen's Inequality Impact on Hargreaves PET:**
   * Mean Daily Temperature Range: $\Delta T = T_{\max} - T_{\min} = 29.19 - 17.08 = 12.11^\circ\text{C}$.
   * By preserving daily extrema rather than monthly averages, Jensen's inequality guarantees that:
     $$\mathbb{E}[\sqrt{T_{\max,\text{daily}} - T_{\min,\text{daily}}}] \le \sqrt{\mathbb{E}[T_{\max,\text{daily}}] - \mathbb{E}[T_{\min,\text{daily}}]}$$
   * The daily calculation prevents overestimation of potential evapotranspiration during the critical 1984 drought year.

---

## 4. Dataset Provenance & Methodological Classification

### 4.1 Primary Temperature Source: ECMWF ERA5-Land Numerical Reanalysis
* **Data Provider:** European Centre for Medium-Range Weather Forecasts (ECMWF) via Copernicus Climate Data Store (CDS).
* **Native Resolution:** $0.1^\circ \times 0.1^\circ$ (~9 km), hourly temporal sampling.
* **Underlying Physics:** Numerical simulation of land-surface thermodynamics and water balance (HTESSEL model), driven by atmospheric atmospheric forcing from ERA5 with lapse-rate elevation correction.
* **Role in AI-DREWS:** **Primary Historical Temperature Reanalysis (1981–2024)**.
* **Acquisition Status:** Ingestion pipeline is scripted and locked ([`scripts/download_era5_land_tekeze_1981_2024.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/download_era5_land_tekeze_1981_2024.py)). Batch execution is scheduled pending Copernicus CDS API key configuration.

### 4.2 Independent Gridded Comparison: NOAA CPC Global Unified Daily Temperature
* **Data Provider:** NOAA Climate Prediction Center (CPC) / PSL.
* **Native Resolution:** $0.5^\circ \times 0.5^\circ$ (~55 km), daily temporal sampling ($T_{\max}$, $T_{\min}$).
* **Construction Methodology:** Objective interpolation of Global Telecommunication System (GTS) daily station observations using an enhanced Shepard distance-weighting algorithm, coupled with CRU elevation lapse-rate adjustment.
* **Scientific Classification:** **Independent Gridded Comparison Product** (NOT direct in-situ ground truth).
* **Scientific Reality Check:** In Northern Ethiopia and the Horn of Africa during the early 1980s, the GTS weather station network was sparse. Therefore, CPC represents an interpolated statistical product subject to smoothing and station reporting availability. It serves as an independent check on reanalysis lapse rates, not an infallible reference.

### 4.3 Timezone & Daily Extrema Grouping Boundaries

Calculating daily temperature extrema ($T_{\max, d}$, $T_{\min, d}$) from hourly reanalyses requires an explicit, documented diurnal window:
1. **ERA5-Land Diurnal Grouping (Primary Convention):**
   * ERA5-Land records hourly temperatures in Coordinated Universal Time (UTC).
   * Local civil time in Ethiopia is East Africa Time ($\text{EAT} = \text{UTC} + 3\text{h}$).
   * **Primary Standard (UTC Day):** Grouping hourly steps from $00:00\text{ UTC}$ to $23:00\text{ UTC}$ for each calendar date $d$.
     * In Tekezé ($36.3^\circ\text{E}–40.0^\circ\text{E}$), $00:00\text{ UTC}$ corresponds to $03:00\text{ EAT}$ (3 hours before sunrise), and $23:00\text{ UTC}$ corresponds to $02:00\text{ EAT}$ the following night.
     * In tropical highlands ($13^\circ\text{N}$), diurnal minimum universally occurs near astronomical sunrise ($\sim 06:00\text{ EAT} = 03:00\text{ UTC}$), and diurnal maximum occurs in early afternoon ($\sim 14:00\text{ EAT} = 11:00\text{ UTC}$). Both physical extrema fall cleanly within the $00:00–23:00\text{ UTC}$ window, avoiding split solar heating cycles.
   * **Sensitivity Standard (Local Civil Day):** Grouping from $21:00\text{ UTC}(d-1)$ to $20:00\text{ UTC}(d)$ corresponding to local midnight-to-midnight ($00:00–23:00\text{ EAT}$). The aggregation script supports this alternative for sensitivity analysis.
2. **NOAA CPC Observation Window:**
   * NOAA CPC Global Daily Temperature compiles GTS station reports over a 24-hour observation cycle (typically $12:00\text{ UTC} - 12:00\text{ UTC}$ or the local national 24-hour meteorological reporting cycle ending at 06:00 or 12:00 UTC).
   * **Cross-Product Nuance:** CPC and ERA5-Land daily extrema represent slightly shifted 24-hour observation windows. While daily diurnal ranges ($\Delta T = T_{\max} - T_{\min}$) and monthly aggregated means converge, daily time series cannot be assumed to be synchronized to the exact second.

---

## 5. Gate 1 Action Plan for Full Gate Certification

To advance Gate 1 from **PARTIAL** to **PASS**, the following sequential steps are executed:

1. **Configure Copernicus CDS API:**
   User configures `~/.cdsapirc` with personal Copernicus CDS API key (never committed to Git).
2. **Execute Full ERA5-Land Download:**
   ```bash
   python scripts/download_era5_land_tekeze_1981_2024.py --start-year 1981 --end-year 2024
   ```
3. **Execute Full NOAA CPC Ingestion:**
   ```bash
   python scripts/download_noaa_cpc_tekeze_1981_2024.py --start-year 1981 --end-year 2024
   ```
4. **Aggregate Daily Extrema to Monthly Table:**
   ```bash
   python scripts/process_temperature_daily_to_monthly.py --era5-dir data/raw/temperature/era5_land --cpc-dir data/raw/temperature/cpc
   ```
5. **Verify Complete 528-Month Manifest:**
   Compute SHA-256 hashes for all 44 annual NetCDF files and record them in [`data/processed/temperature_provenance_manifest.json`](file:///c:/Users/User/Desktop/AgriMinds/data/processed/temperature_provenance_manifest.json).
6. **Formally Certify Gate 1:**
   Update status in master plan and proceed to Gate 4 target reconstruction.
