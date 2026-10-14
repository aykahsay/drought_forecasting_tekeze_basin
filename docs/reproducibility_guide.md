# AI-DREWS Reproducibility Guide
## Step-by-Step Instructions to Reproduce Audits, Data Pipelines, and Test Suites

**Document ID:** `AI-DREWS-DOC-RG-2026-10`  
**Standard:** FAIR Computational Reproducibility Standards  
**Status:** **ACTIVE REPRODUCIBILITY GUIDE**

---

### 1. Environment Configuration

#### 1.1 Python Version & Virtual Environment
The pipeline is verified on Python 3.12.10 (Windows 64-bit / Linux):

```bash
# Clone the repository
git clone https://github.com/aykahsay/drought_forecasting_tekeze_basin.git
cd drought_forecasting_tekeze_basin

# Switch to the verified research branch
git switch research/verified-tekeze-drought-pipeline

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux

# Install locked dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### 1.2 Copernicus CDS API Credentials (Required for ERA5-Land)
Create the file `~/.cdsapirc` (in your user home directory) containing:

```ini
url: https://cds.climate.copernicus.eu/api
key: <YOUR-PERSONAL-CDS-API-KEY>
```

> [!WARNING]
> Never commit `~/.cdsapirc` or paste API keys into code or conversation. The downloader automatically detects this file locally.

---

### 2. Executing Automated Test Suites

The pipeline provides 23 automated regression and benchmark tests across Gates 1, 2, and 3:

```bash
# Run all verified Gate tests
python -m pytest drought_forecasting/tests/test_climate_reconstruction_and_spei.py \
                 drought_forecasting/tests/test_gate2_mathematical_benchmarks.py \
                 drought_forecasting/tests/test_gate3_spatial_and_temporal_integrity.py -v
```

Expected output: `23 passed in < 3.0s`.

---

### 3. Reproducing Data Ingestion & Gate 1 Audits

#### 3.1 NOAA CPC Download & Extraction
```bash
# Download 1984 benchmark or target years (saves immutably to data/raw/temperature/cpc/)
python scripts/download_noaa_cpc_tekeze_1981_2024.py --start-year 1984 --end-year 1984

# Run daily-to-monthly aggregation engine
python scripts/process_temperature_daily_to_monthly.py --cpc-dir data/raw/temperature/cpc
```

This generates:
* `data/processed/tekeze_monthly_temperature_audit_1981_2024.csv`
* `data/processed/temperature_provenance_manifest.json`

#### 3.2 ERA5-Land Hourly Ingestion
```bash
# Downloads hourly 2m temperature for Tekezé catchment buffer
python scripts/download_era5_land_tekeze_1981_2024.py --start-year 1984 --end-year 1984
```

---

### 4. Reproducing Gate 3 Spatial Masking & CHIRPS Alignment

```bash
# Runs the full verified spatial and temporal reconstruction pipeline
python scripts/build_verified_tekeze_monthly_climate_1981_2024.py --help
```

Pipeline arguments:
* `--start-year 1981 --end-year 2024`
* `--min-coverage 0.95` (Enforces 95% spatial coverage quality gate)
* `--allow-synthetic False` (Strictly enforces real observational NetCDFs)

---

### 5. Repository Checksum Manifest Verification

To verify that local raw files match the SHA-256 hashes recorded in the provenance manifest:

```python
import hashlib
import json
from pathlib import Path

manifest_path = Path("data/processed/temperature_provenance_manifest.json")
# Inspect manifest entries and compute local file hashes
```
