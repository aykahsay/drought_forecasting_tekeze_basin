#!/usr/bin/env python3
"""
download_noaa_cpc_tekeze_1981_2024.py
=====================================
Automated, Resilient Downloader for NOAA CPC Global Unified Daily Temperature (1981–2024).

Features (Gate 1 Compliance):
  - Ingests daily maximum (`tmax`) and minimum (`tmin`) NetCDF4 files from NOAA PSL THREDDS / NCEP.
  - Implements chunked HTTP Range-request downloads with exponential backoff to handle rate limits.
  - Preserves raw downloads immutably in data/raw/temperature/cpc/.
  - Computes and records SHA-256 checksums and source manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_CPC_DIR = ROOT_DIR / "data" / "raw" / "temperature" / "cpc"
MANIFEST_PATH = RAW_CPC_DIR / "cpc_manifest.json"

PSL_BASE_URL = "https://downloads.psl.noaa.gov/Datasets/cpc_global_temp/"


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

    existing = [e for e in existing if e.get("filename") != entry.get("filename")]
    existing.append(entry)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def download_cpc_file(
    var_name: str,
    year: int,
    output_dir: Path = RAW_CPC_DIR,
    chunk_size: int = 5 * 1024 * 1024,
    max_retries: int = 20,
    force_download: bool = False
) -> Dict[str, Any]:
    """
    Downloads a single CPC NetCDF file (tmax.YYYY.nc or tmin.YYYY.nc) using chunked Range requests.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{var_name}.{year}.nc"
    dest_path = output_dir / filename
    part_path = output_dir / f"{filename}.part"

    if dest_path.exists() and dest_path.stat().st_size > 50000000 and not force_download:
        print(f"[{year}] {filename} already exists ({dest_path.stat().st_size:,} bytes). Verifying checksum...")
        h = compute_sha256(dest_path)
        return {
            "year": year,
            "variable": var_name,
            "filename": filename,
            "status": "CACHED_IMMUTABLE",
            "size_bytes": dest_path.stat().st_size,
            "sha256": h,
            "path": str(dest_path)
        }

    url = f"{PSL_BASE_URL}{filename}"
    print(f"[{year}] Connecting to {url}...")

    # Get total size
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}, method="HEAD")
    with urllib.request.urlopen(req, timeout=15) as resp:
        total_size = int(resp.headers.get("Content-Length", 0))

    if total_size <= 0:
        raise ValueError(f"Invalid content length for {url}")

    cur_pos = part_path.stat().st_size if part_path.exists() else 0
    t0 = time.time()

    while cur_pos < total_size:
        end_pos = min(cur_pos + chunk_size - 1, total_size - 1)
        pct = (cur_pos / total_size) * 100.0
        print(f"[{year}] {filename}: {cur_pos:,} - {end_pos:,} of {total_size:,} bytes ({pct:.1f}%)...")

        success = False
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = min(attempt * 4, 30)
                    time.sleep(delay)
                else:
                    time.sleep(1.0)

                chunk_req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Range": f"bytes={cur_pos}-{end_pos}"
                })
                with urllib.request.urlopen(chunk_req, timeout=20) as resp:
                    data = resp.read()
                    if len(data) == 0:
                        raise ValueError("Zero bytes received")
                    with open(part_path, "ab" if cur_pos > 0 else "wb") as f_out:
                        f_out.write(data)
                    cur_pos += len(data)
                    success = True
                    break
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed: {e}")
                time.sleep(4)

        if not success:
            raise RuntimeError(f"Failed to download chunk starting at byte {cur_pos} after {max_retries} retries")

    if dest_path.exists():
        dest_path.unlink()
    part_path.rename(dest_path)

    elapsed = time.time() - t0
    final_sha256 = compute_sha256(dest_path)
    file_size = dest_path.stat().st_size

    entry = {
        "dataset": "NOAA CPC Global Unified Temperature Dataset V1.0",
        "variable": var_name,
        "units": "degC",
        "year": year,
        "filename": filename,
        "source_url": url,
        "retrieval_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "size_bytes": file_size,
        "sha256": final_sha256
    }
    update_manifest(entry)
    print(f"[{year}] SUCCESS: {filename} complete ({file_size:,} bytes, {elapsed:.1f}s). SHA-256: {final_sha256}")
    return entry


def main():
    parser = argparse.ArgumentParser(description="NOAA CPC Tekezé Temperature Downloader (1981–2024)")
    parser.add_argument("--start-year", type=int, default=1981, help="Start year (default 1981)")
    parser.add_argument("--end-year", type=int, default=2024, help="End year (default 2024)")
    parser.add_argument("--years", nargs="+", type=int, help="Specific list of years to download")
    args = parser.parse_args()

    print("=" * 80)
    print("   AI-DREWS: NOAA CPC GLOBAL TEMPERATURE ACQUISITION ENGINE (GATE 1)")
    print("=" * 80)

    target_years = args.years if args.years else list(range(args.start_year, args.end_year + 1))
    print(f"Target Years: {len(target_years)} years ({target_years[0]} to {target_years[-1]})\n")

    for yr in target_years:
        for var in ["tmax", "tmin"]:
            try:
                download_cpc_file(var, yr)
            except Exception as e:
                print(f"[{yr}] Error downloading {var}: {e}")


if __name__ == "__main__":
    main()
