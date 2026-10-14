#!/usr/bin/env python3
"""
download_era5_land_tekeze_1981_2024.py
======================================
Reproducible Downloader for ECMWF ERA5-Land Reanalysis via Copernicus Climate Data Store (CDS) API.

Security & Integrity Guarantees (Gate 1):
  - Never logs, prints, or exposes CDS API credentials.
  - Ingests credentials from ~/.cdsapirc or CDS_API_KEY / CDS_API_URL environment variables.
  - Spatial domain: Tekezé Basin Bounding Box [North: 15.0°N, West: 35.5°E, South: 11.5°N, East: 40.0°E].
  - Variables: Hourly 2 m temperature (`2m_temperature`) for daily extrema derivation.
  - Output: Preserves raw downloads immutably in data/raw/temperature/era5_land/hourly/.
  - Provenance: Logs retrieval timestamps, dataset version, and SHA-256 checksums.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_ERA5_DIR = ROOT_DIR / "data" / "raw" / "temperature" / "era5_land"
RAW_ERA5_HOURLY_DIR = RAW_ERA5_DIR / "hourly"
RAW_ERA5_MONTHLY_DIR = RAW_ERA5_DIR / "monthly"
MANIFEST_PATH = RAW_ERA5_DIR / "era5_land_manifest.json"

TEKEZE_BBOX_NORTH = 15.0
TEKEZE_BBOX_WEST = 35.5
TEKEZE_BBOX_SOUTH = 11.5
TEKEZE_BBOX_EAST = 40.0


def check_cds_configuration() -> Tuple[bool, str]:
    """
    Checks whether CDS API is configured locally without revealing sensitive keys.
    Looks for ~/.cdsapirc or environment variable CDS_API_KEY.
    """
    home_rc = Path.home() / ".cdsapirc"
    if home_rc.exists() and home_rc.stat().st_size > 10:
        return True, "Configured via ~/.cdsapirc"

    env_key = os.environ.get("CDS_API_KEY")
    if env_key and len(env_key.strip()) > 10:
        return True, "Configured via CDS_API_KEY environment variable"

    return False, (
        "CDS API not configured. To enable ERA5-Land automated downloads, please register at "
        "https://cds.climate.copernicus.eu/ and create ~/.cdsapirc with your user key."
    )


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 checksum for immutable provenance tracking."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def update_manifest(entry: Dict[str, Any], manifest_path: Path = MANIFEST_PATH):
    """Updates the JSON provenance manifest."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    existing: List[Dict[str, Any]] = []
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    # Update or append
    existing = [e for e in existing if e.get("filename") != entry.get("filename")]
    existing.append(entry)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def download_era5_land_hourly_year(
    year: int,
    output_dir: Path = RAW_ERA5_HOURLY_DIR,
    force_download: bool = False
) -> Dict[str, Any]:
    """
    Downloads ERA5-Land hourly 2m temperature for a given year over the Tekezé bounding box.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_filename = f"era5_land_2m_temp_hourly_{year}.nc"
    out_path = output_dir / out_filename

    if out_path.exists() and out_path.stat().st_size > 1000000 and not force_download:
        print(f"[{year}] ERA5-Land hourly file already exists ({out_path.stat().st_size:,} bytes). Calculating checksum...")
        h = compute_sha256(out_path)
        return {
            "year": year,
            "filename": out_filename,
            "status": "CACHED_IMMUTABLE",
            "size_bytes": out_path.stat().st_size,
            "sha256": h,
            "path": str(out_path)
        }

    is_configured, status_msg = check_cds_configuration()
    if not is_configured:
        raise RuntimeError(
            f"Cannot download ERA5-Land for year {year}: {status_msg}"
        )

    try:
        import cdsapi
    except ImportError:
        raise ImportError("Package 'cdsapi' is not installed. Install via: pip install cdsapi")

    c = cdsapi.Client()

    print(f"[{year}] Requesting ERA5-Land hourly 2m temperature from Copernicus CDS...")
    t0 = time.time()

    request_payload = {
        "format": "netcdf",
        "variable": ["2m_temperature"],
        "year": str(year),
        "month": [f"{m:02d}" for m in range(1, 13)],
        "day": [f"{d:02d}" for d in range(1, 32)],
        "time": [f"{h:02d}:00" for h in range(24)],
        "area": [
            TEKEZE_BBOX_NORTH,
            TEKEZE_BBOX_WEST,
            TEKEZE_BBOX_SOUTH,
            TEKEZE_BBOX_EAST,
        ],
    }

    part_path = output_dir / f"{out_filename}.part"
    c.retrieve("reanalysis-era5-land", request_payload, str(part_path))

    if out_path.exists():
        out_path.unlink()
    part_path.rename(out_path)

    elapsed = time.time() - t0
    file_size = out_path.stat().st_size
    file_sha256 = compute_sha256(out_path)

    manifest_entry = {
        "dataset": "ECMWF ERA5-Land Hourly Reanalysis",
        "product_id": "reanalysis-era5-land",
        "variable": "2m_temperature",
        "units": "K",
        "spatial_bbox": [TEKEZE_BBOX_NORTH, TEKEZE_BBOX_WEST, TEKEZE_BBOX_SOUTH, TEKEZE_BBOX_EAST],
        "grid_resolution_deg": 0.1,
        "year": year,
        "filename": out_filename,
        "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "size_bytes": file_size,
        "sha256": file_sha256
    }
    update_manifest(manifest_entry)

    print(f"[{year}] SUCCESS: {out_filename} downloaded ({file_size:,} bytes, {elapsed:.1f}s). SHA-256: {file_sha256}")
    return manifest_entry


def main():
    parser = argparse.ArgumentParser(description="ERA5-Land Tekezé Basin Downloader (1981–2024)")
    parser.add_argument("--start-year", type=int, default=1981, help="Start year (default 1981)")
    parser.add_argument("--end-year", type=int, default=2024, help="End year (default 2024)")
    parser.add_argument("--check-only", action="store_true", help="Check CDS credentials and configuration without downloading")
    args = parser.parse_args()

    print("=" * 80)
    print("   AI-DREWS: ECMWF ERA5-LAND TEMPERATURE ACQUISITION ENGINE (GATE 1)")
    print("=" * 80)

    is_cfg, msg = check_cds_configuration()
    print(f"\nCDS Configuration Status: {msg}")

    if args.check_only:
        sys.exit(0 if is_cfg else 1)

    if not is_cfg:
        print("\nERROR: Please configure CDS API credentials to proceed with automated ERA5-Land downloads.")
        print("See documentation in docs/AI_DREWS_MASTER_SCIENTIFIC_WORKFLOW_AND_VALIDATION_PLAN.md")
        sys.exit(1)

    print(f"\nStarting acquisition from {args.start_year} through {args.end_year}...")
    for y in range(args.start_year, args.end_year + 1):
        try:
            download_era5_land_hourly_year(y)
        except Exception as e:
            print(f"[{y}] Download failed: {e}")


if __name__ == "__main__":
    main()
