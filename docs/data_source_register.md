# AI-DREWS Data Source Register
## Provenance, Provider APIs, Licensing, and Verification Protocol

**Document ID:** `AI-DREWS-DOC-DSR-2026-10`  
**Reference Standard:** FAIR Data Principles / WMO-No. 100  
**Status:** **ACTIVE REGISTER**

---

### 1. Primary Precipitation Dataset: CHIRPS v2.0

* **Full Title:** Climate Hazards Center InfraRed Precipitation with Station data (CHIRPS) v2.0
* **Provider:** Climate Hazards Center, University of California, Santa Barbara (UCSB) / USGS
* **Native Resolution:** $0.05^\circ \times 0.05^\circ$ (~5.3 km at equator)
* **Temporal Coverage:** January 1, 1981 – present (Monthly and Daily archives)
* **Access Protocol:** HTTP download via `https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/`
* **Coordinate Origin:** Upper left corner $(40.0^\circ\text{N}, -20.0^\circ\text{E})$, pixel centers offset $+0.025^\circ$.
* **Units:** Millimetres per month ($\text{mm/month}$).
* **License:** Public Domain / Open Access
* **Storage Location:** `data/raw/chirps_monthly/`
* **Validation Status:** `VALIDATED` (Spatial alignment verified in [`test_gate3_chirps_grid_coordinate_alignment`](file:///c:/Users/User/Desktop/AgriMinds/drought_forecasting/tests/test_gate3_spatial_and_temporal_integrity.py)).

---

### 2. Primary Temperature Dataset: ECMWF ERA5-Land Reanalysis

* **Full Title:** ERA5-Land: Hourly reanalysis of land variables
* **Provider:** European Centre for Medium-Range Weather Forecasts (ECMWF) / Copernicus Climate Change Service (C3S)
* **Product Classification:** Numerical Land-Surface Model Reanalysis (HTESSEL land-surface model driven by ERA5 atmospheric forcing with surface observation assimilation); **not direct station measurements**.
* **Native Resolution:** $0.1^\circ \times 0.1^\circ$ (~9 km native Gaussian grid)
* **Temporal Coverage:** January 1950 – present (Hourly timesteps)
* **Target Variables:** `2m_temperature` (Parameter ID: `2t`, GRIB Code: `167`)
* **Source Units:** Kelvin ($\text{K}$); converted to Celsius ($^\circ\text{C} = \text{K} - 273.15$).
* **Access Protocol:** Copernicus CDS API client (`cdsapi`) with user authentication token configured in `~/.cdsapirc`.
* **Bounding Box:** Tekezé Catchment Buffer $[15.0^\circ\text{N}, 35.5^\circ\text{E}, 11.5^\circ\text{N}, 40.0^\circ\text{E}]$.
* **Downloader Script:** [`scripts/download_era5_land_tekeze_1981_2024.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/download_era5_land_tekeze_1981_2024.py)
* **Storage Location:** `data/raw/temperature/era5_land/`
* **Validation Status:** `NOT_ACQUIRED` (Downloader operational; batch execution pending CDS API token activation).

---

### 3. Independent Comparison Dataset: NOAA CPC Global Daily Temperature

* **Full Title:** NOAA CPC Global Daily Temperature (Version 1.0)
* **Provider:** NOAA Climate Prediction Center / Physical Sciences Laboratory (PSL)
* **Product Classification:** Gridded station analysis interpolating GTS station records via modified Shepard's algorithm with PRISM/CRU orographic adjustment; **independent gridded comparison product, not direct in-situ ground truth**.
* **Native Resolution:** $0.50^\circ \times 0.50^\circ$ (~55 km)
* **Temporal Coverage:** January 1, 1979 – present
* **Variables:** Daily maximum temperature (`tmax`), Daily minimum temperature (`tmin`)
* **Source Units:** Degrees Celsius ($^\circ\text{C}$)
* **Access Protocol:** Chunked Range requests from NOAA PSL THREDDS server: `https://psl.noaa.gov/thredds/fileServer/Datasets/cpc_global_temp/`
* **Downloader Script:** [`scripts/download_noaa_cpc_tekeze_1981_2024.py`](file:///c:/Users/User/Desktop/AgriMinds/scripts/download_noaa_cpc_tekeze_1981_2024.py)
* **Storage Location:** `data/raw/temperature/cpc/`
* **Benchmark Verified:** 1984 benchmark acquired, hashed (SHA-256), and audited.
* **Validation Status:** `PARTIALLY_AVAILABLE` (1984 benchmark acquired; 1981–2024 full series pending download).

---

### 4. Basin Boundary & Catchment Hydrography

* **Dataset:** HydroBASINS Africa Level 5, 6, and 7
* **Provider:** World Wildlife Fund (WWF) / USGS EROS (Lehner & Grill 2013)
* **Derived Polygon:** [`data/spatial/processed/tekeze_basin_hydrological_complete.geojson`](file:///c:/Users/User/Desktop/AgriMinds/data/spatial/processed/tekeze_basin_hydrological_complete.geojson)
* **Constituent Units:** `hybas_id` `1050648030` (Upper Tekezé/Simien), `1050692800` (Middle Tekezé/Tigray), `1050692900` (Lower Tekezé/Humera outlet).
* **Provisional Geodesic Area:** $67,135.4\text{ km}^2$ (WGS 84 ellipsoid).
* **Validation Status:** `VALIDATED` (Provisional audit complete).

---

### 5. Excluded & Retracted Legacy Files

* **`2000-2023-soillayer.nc`:** Formally **REJECTED & RETRACTED**. File timestamps were shifted forward into future dates (e.g. 2025 timestamps), violating historical authenticity. Excluded from all historical analyses.
* **Preliminary CNN-LSTM Checkpoints:** Formally **RETRACTED**. Checkpoints trained on corrupted timestamps were deleted from the repository.
