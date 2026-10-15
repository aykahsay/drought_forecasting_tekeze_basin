"""
download_and_process_cpc_continuous.py
======================================
Automated background worker that systematically downloads NOAA CPC Global Daily
Temperature NetCDF files (1981–2024) from the high-speed NOAA PSL mirror and
immediately extracts exact spatial area-weighted daily extrema (Tmax, Tmin, DTR,
and Jensen's inequality square-root correction) for Abregelle and Tekezé Basin.

Strictly Zero Synthetic Data Rule:
  - 100% real daily observations from NOAA CPC V1.0.
  - Zero synthetic backfills or artificial noise.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.download_noaa_cpc_tekeze_1981_2024 import download_cpc_file, RAW_CPC_DIR
from scripts.process_temperature_daily_to_monthly import (
    build_cpc_spatial_weights,
    process_cpc_year,
    load_basin_polygon,
    OUT_CSV_PATH,
    OUT_MANIFEST_PATH,
)
import pandas as pd


def run_continuous_ingestion(start_year: int = 1981, end_year: int = 2024):
    print("=" * 80)
    print("AI-DREWS: CONTINUOUS NOAA CPC DAILY TEMPERATURE INGESTION & PROCESSING")
    print("=" * 80)

    # 1. Load basin geometry and build grid weights
    basin_poly = load_basin_polygon()
    sample_nc = list(RAW_CPC_DIR.glob("tmax.*.nc"))
    if not sample_nc:
        print("Downloading initial sample file tmax.1983.nc to initialize grid weights...")
        download_cpc_file("tmax", 1983)
        sample_nc = list(RAW_CPC_DIR.glob("tmax.*.nc"))

    norm_w, sub_lats, sub_lons, lat_slice, lon_slice = build_cpc_spatial_weights(basin_poly, sample_nc[0])
    print(f"Active CPC cells intersecting Tekezé Basin: {int((norm_w > 0).sum())} cells")

    # Priority order: critical historical drought benchmark years first, then remaining
    benchmark_order = [1985, 1982, 1981, 2002, 2015, 2021]
    all_years = benchmark_order + [y for y in range(start_year, end_year + 1) if y not in benchmark_order]

    for yr in all_years:
        print(f"\n--- Checking / Ingesting Year: {yr} ---")
        try:
            # 1. Download Tmax and Tmin
            download_cpc_file("tmax", yr)
            download_cpc_file("tmin", yr)

            # 2. Extract daily to monthly statistics
            yearly_records = process_cpc_year(yr, norm_w, lat_slice, lon_slice)
            if not yearly_records:
                print(f"[{yr}] No records extracted.")
                continue

            # 3. Append / Update processed CSV
            if OUT_CSV_PATH.exists():
                df_existing = pd.read_csv(OUT_CSV_PATH)
                # Filter out old records for this year
                df_existing = df_existing[df_existing["year"] != yr]
                df_new = pd.DataFrame(yearly_records)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_combined = pd.DataFrame(yearly_records)

            df_combined = df_combined.sort_values(["year", "month"]).reset_index(drop=True)
            df_combined.to_csv(str(OUT_CSV_PATH), index=False)
            print(f"[{yr}] Successfully extracted and updated {len(yearly_records)} months in {OUT_CSV_PATH.name} (Total: {len(df_combined)} months).")

        except Exception as e:
            print(f"[{yr}] Ingestion warning: {e}")
            time.sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=1981)
    parser.add_argument("--end-year", type=int, default=2024)
    args = parser.parse_args()

    run_continuous_ingestion(args.start_year, args.end_year)
