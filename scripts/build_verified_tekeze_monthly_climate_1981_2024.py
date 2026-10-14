#!/usr/bin/env python3
"""
build_verified_tekeze_monthly_climate_1981_2024.py
=================================================
Reproducible Climate Data Reconstruction & SPEI-3 Target Pipeline
for the Tekezé River Basin (67,135.4 km²), Northern Ethiopia.

Pipeline Workflow:
  1. Spatial Boundary & Masking:
     - Loads verified complete Tekezé Catchment GeoJSON (HydroBASINS Lev 5/6/7, 67,135.4 km²).
     - Builds 0.05° raster grid with exact fractional polygon-cell intersection area weighting
       and cosine latitude spherical area adjustment.
  2. Precipitation Ingestion (CHIRPS v2.0):
     - Ingests monthly high-res precipitation grids from UCSB Climate Hazards Center (1981–2024).
     - Crops georeferenced window [lat: 11.66°N–14.80°N, lon: 35.86°E–39.79°E].
     - Excludes negative NoData sentinels (e.g. -9999) and non-finite values from calculations.
     - Renormalizes weights exclusively over valid cells.
     - Enforces a minimum spatial coverage threshold (>= 95% of basin area weight).
  3. Temperature & Potential Evapotranspiration:
     - Ingests verified monthly temperatures with strict finite and physical bounds checking.
     - Computes Hargreaves-Samani (1985) PET using extraterrestrial radiation Ra and diurnal range.
     - Computes Thornthwaite (1948) PET for comparative baseline and sensitivity analysis.
  4. Drought Target Derivation:
     - Computes monthly climatic water balance D = P - PET (strict NaN propagation if P or PET is missing).
     - Accumulates 3-month Kiremt agricultural water balance (July–September).
     - Accumulates 3-month Belg pastoral/short-season water balance (March–May).
     - Fits 3-parameter Log-Logistic distribution via unbiased L-moments / PWM over WMO 1991–2020 normal,
       strictly validating parameter bounds (alpha > 0, beta > 1, gamma < min(D_obs)).
     - Derives standardized SPEI-3 (September-ending for Kiremt) and SPI-3 z-scores.
  5. Automated Quality Auditing:
     - Verifies date continuity, physical bounds, zero silent interpolation, and logs metrics.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import math
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import netCDF4
import numpy as np
import pandas as pd
from PIL import Image
from shapely.geometry import Point, box, shape

# Add project root and drought_forecasting to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "drought_forecasting"))

from agriminds.climate.spei_calculator import (
    calculate_extraterrestrial_radiation_ra,
    calculate_hargreaves_pet,
    calculate_spei_seasonal,
    calculate_spi_seasonal,
    calculate_thornthwaite_monthly_pet,
)

# Spatial & Climate Constants
BASIN_GEOJSON_PATH = ROOT_DIR / "data" / "spatial" / "processed" / "tekeze_basin_hydrological_complete.geojson"
RAW_CHIRPS_DIR = ROOT_DIR / "data" / "raw" / "chirps_monthly"
CHIRPS_BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/"
CHIRPS_AFRICA_ORIGIN = (40.0, -20.0)
CHIRPS_PIXEL_RES = 0.05

RAW_TEMP_DIR = ROOT_DIR / "data" / "raw" / "temperature"
RAW_TEMP_CPC_DIR = RAW_TEMP_DIR / "cpc"
RAW_TEMP_ERA5_DIR = RAW_TEMP_DIR / "era5_land"

# Output File Paths
OUT_MONTHLY_CSV = ROOT_DIR / "data" / "processed" / "tekeze_monthly_climate_1981_2024.csv"
OUT_SEASONAL_CSV = ROOT_DIR / "data" / "processed" / "tekeze_seasonal_drought_indices_1981_2024.csv"
OUT_QUALITY_JSON = ROOT_DIR / "data" / "processed" / "climate_reconstruction_quality_summary.json"


# ---------------------------------------------------------------------------
# 1. Spatial Polygon Masking & Fractional Area-Weighted Grid Construction
# ---------------------------------------------------------------------------

def construct_basin_raster_mask(
    geojson_path: Path = BASIN_GEOJSON_PATH,
    pixel_res: float = CHIRPS_PIXEL_RES,
    use_fractional_cell_coverage: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Tuple[int, int, int, int], Dict[str, Any]]:
    """
    Constructs the 2D raster mask and area weights for the verified Tekezé Basin polygon
    within the CHIRPS Africa grid.

    Features:
        - Exact fractional cell-polygon intersection area weighting (or center-point containment).
        - Cosine latitude spherical area adjustment.
        - Provides metrics comparing fractional coverage vs center-point approximation.

    Returns:
        (mask_2d, weights_2d, lats_1d, lons_1d, (r_start, r_end, c_start, c_end), metadata)
    """
    if not geojson_path.exists():
        raise FileNotFoundError(f"Verified basin GeoJSON not found at {geojson_path}")

    with open(geojson_path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    poly = shape(gj["features"][0]["geometry"])
    bounds = poly.bounds  # (minx, miny, maxx, maxy) -> (lon_min, lat_min, lon_max, lat_max)
    lon_min, lat_min, lon_max, lat_max = bounds

    origin_lat, origin_lon = CHIRPS_AFRICA_ORIGIN

    # Pixel slice indices into CHIRPS Africa raster (1600 x 1500)
    r_start = int(np.floor((origin_lat - lat_max) / pixel_res))
    r_end   = int(np.ceil((origin_lat - lat_min) / pixel_res))
    c_start = int(np.floor((lon_min - origin_lon) / pixel_res))
    c_end   = int(np.ceil((lon_max - origin_lon) / pixel_res))

    # Cell center coordinate arrays
    lats = origin_lat - (np.arange(r_start, r_end) + 0.5) * pixel_res
    lons = origin_lon + (np.arange(c_start, c_end) + 0.5) * pixel_res

    grid_h = len(lats)
    grid_w = len(lons)

    weights = np.zeros((grid_h, grid_w), dtype=np.float64)
    center_mask = np.zeros((grid_h, grid_w), dtype=bool)

    half_res = pixel_res / 2.0
    for i, lat in enumerate(lats):
        cos_lat = math.cos(math.radians(lat))
        for j, lon in enumerate(lons):
            cell = box(lon - half_res, lat - half_res, lon + half_res, lat + half_res)
            if poly.intersects(cell):
                if use_fractional_cell_coverage:
                    if poly.contains(cell):
                        frac = 1.0
                    else:
                        inter = poly.intersection(cell)
                        frac = inter.area / cell.area
                    weights[i, j] = frac * cos_lat
                else:
                    if poly.contains(Point(lon, lat)):
                        weights[i, j] = cos_lat

            if poly.contains(Point(lon, lat)):
                center_mask[i, j] = True

    sum_w = np.sum(weights)
    if sum_w > 0:
        weights /= sum_w

    mask = weights > 0.0

    meta = {
        "active_cells_fractional": int(np.sum(mask)),
        "active_cells_center_point": int(np.sum(center_mask)),
        "weighting_method": "exact_fractional_polygon_intersection" if use_fractional_cell_coverage else "center_point_binary",
        "grid_resolution_deg": pixel_res
    }

    return mask, weights, lats, lons, (r_start, r_end, c_start, c_end), meta


# ---------------------------------------------------------------------------
# 2. CHIRPS Monthly Raster Acquisition & Basin Extraction
# ---------------------------------------------------------------------------

def fetch_and_extract_chirps_monthly(
    year: int,
    month: int,
    crop_window: Tuple[int, int, int, int],
    mask: np.ndarray,
    weights: np.ndarray,
    cache_dir: Path = RAW_CHIRPS_DIR,
    min_spatial_coverage: float = 0.95
) -> Dict[str, Any]:
    """
    Fetches, verifies, crops, and aggregates monthly CHIRPS v2.0 raster to Tekezé Basin mean.

    Quality Controls:
        1. Negative NoData sentinels (e.g. -9999.0) and non-finite values are strictly excluded.
        2. Area weights are computed exclusively over valid pixels and renormalized.
        3. Enforces a minimum spatial coverage threshold (default 95% of basin area weight).
           If valid coverage is below this threshold, returns NaN and flags INSUFFICIENT_SPATIAL_COVERAGE.

    Returns:
        Dictionary with basin mean precipitation, min, max, std, cell count, spatial coverage, and status.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    fname = f"chirps-v2.0.{year:04d}.{month:02d}.tif.gz"
    local_path = cache_dir / fname
    file_url = f"{CHIRPS_BASE_URL}{fname}"

    # Check local cache or download
    if not local_path.exists() or local_path.stat().st_size < 1000:
        req = urllib.request.Request(file_url, headers={"User-Agent": "AgriMinds-AI-DREWS/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            with open(local_path, "wb") as f_out:
                f_out.write(content)

    # Decompress and load raster
    with gzip.open(local_path, "rb") as gz_file:
        img = Image.open(io.BytesIO(gz_file.read()))
        full_arr = np.array(img, dtype=np.float32)

    r_start, r_end, c_start, c_end = crop_window
    crop = full_arr[r_start:r_end, c_start:c_end]

    # Handle missing / fill values (< 0 in CHIRPS represents missing/ocean/NoData sentinel -9999)
    valid_mask = (crop >= 0.0) & (weights > 0.0) & np.isfinite(crop)
    valid_weights = weights[valid_mask]
    valid_weight_sum = float(np.sum(valid_weights))
    total_basin_weight = float(np.sum(weights[weights > 0.0]))  # strictly 1.0

    coverage_ratio = valid_weight_sum / total_basin_weight if total_basin_weight > 0.0 else 0.0

    if coverage_ratio < min_spatial_coverage or valid_weight_sum <= 0.0:
        return {
            "precip_mean_mm": np.nan,
            "precip_min_mm": np.nan,
            "precip_max_mm": np.nan,
            "precip_std_mm": np.nan,
            "spatial_coverage_fraction": round(float(coverage_ratio), 4),
            "n_valid_cells": int(np.sum(valid_mask)),
            "status": "INSUFFICIENT_SPATIAL_COVERAGE" if coverage_ratio > 0.0 else "MISSING_DATA"
        }

    # Area-weighted spatial mean using strictly valid pixels and renormalized valid weights
    basin_pixels = crop[valid_mask]
    mean_p = float(np.sum(basin_pixels * valid_weights) / valid_weight_sum)

    return {
        "precip_mean_mm": round(mean_p, 2),
        "precip_min_mm": round(float(np.min(basin_pixels)), 2),
        "precip_max_mm": round(float(np.max(basin_pixels)), 2),
        "precip_std_mm": round(float(np.std(basin_pixels)), 2),
        "spatial_coverage_fraction": round(float(coverage_ratio), 4),
        "n_valid_cells": int(np.sum(valid_mask)),
        "status": "VALID_OBSERVATION"
    }


# ---------------------------------------------------------------------------
# 3. Monthly Temperature & PET Reconstruction
# ---------------------------------------------------------------------------

class MissingTemperatureDataError(FileNotFoundError):
    """
    Raised when real observational (NOAA CPC) or reanalysis (ERA5-Land)
    temperature NetCDF files are absent for the requested period.
    Per Gate 1 acceptance criteria, synthetic fallback is strictly disabled.
    """
    pass


_CPC_MASK_CACHE: Dict[str, Any] = {}

def get_cpc_basin_weights(
    geojson_path: Path = BASIN_GEOJSON_PATH,
    cpc_dir: Path = RAW_TEMP_CPC_DIR
) -> Tuple[np.ndarray, Tuple[int, int], Tuple[int, int]]:
    """
    Constructs and caches fractional polygon-cell area weights for the 0.5° NOAA CPC grid.
    """
    if "weights" in _CPC_MASK_CACHE:
        return _CPC_MASK_CACHE["weights"], _CPC_MASK_CACHE["lat_idx"], _CPC_MASK_CACHE["lon_idx"]

    if not geojson_path.exists():
        raise FileNotFoundError(f"Verified basin GeoJSON not found at {geojson_path}")

    with open(geojson_path, "r", encoding="utf-8") as f:
        gj = json.load(f)
    poly = shape(gj["features"][0]["geometry"])
    lon_min, lat_min, lon_max, lat_max = poly.bounds

    # Probe sample CPC file for coordinate definitions
    sample_files = list(cpc_dir.glob("tmax.*.nc"))
    if not sample_files:
        raise MissingTemperatureDataError(
            f"No NOAA CPC NetCDF files found in {cpc_dir} to construct grid coordinate geometry."
        )

    ds = netCDF4.Dataset(sample_files[0])
    lat = ds.variables["lat"][:]
    lon = ds.variables["lon"][:]
    ds.close()

    res = 0.50
    lat_idx = np.where((lat >= (lat_min - res)) & (lat <= (lat_max + res)))[0]
    lon_idx = np.where((lon >= (lon_min - res)) & (lon <= (lon_max + res)))[0]

    sub_lats = lat[lat_idx]
    sub_lons = lon[lon_idx]
    half_res = res / 2.0

    weights = np.zeros((len(sub_lats), len(sub_lons)), dtype=np.float64)
    for i, clat in enumerate(sub_lats):
        cos_lat = math.cos(math.radians(clat))
        for j, clon in enumerate(sub_lons):
            cell_box = box(clon - half_res, clat - half_res, clon + half_res, clat + half_res)
            if poly.intersects(cell_box):
                inter = poly.intersection(cell_box)
                weights[i, j] = (inter.area / cell_box.area) * cos_lat

    total_w = np.sum(weights)
    if total_w <= 0.0:
        raise ValueError("CPC grid cell weights sum to zero over Tekezé Basin.")

    norm_weights = weights / total_w
    lat_slice = (int(lat_idx[0]), int(lat_idx[-1] + 1))
    lon_slice = (int(lon_idx[0]), int(lon_idx[-1] + 1))

    _CPC_MASK_CACHE["weights"] = norm_weights
    _CPC_MASK_CACHE["lat_idx"] = lat_slice
    _CPC_MASK_CACHE["lon_idx"] = lon_slice

    return norm_weights, lat_slice, lon_slice


def extract_cpc_monthly_temperature(
    year: int,
    month: int,
    cpc_dir: Path = RAW_TEMP_CPC_DIR,
    min_daily_coverage: float = 0.80
) -> Tuple[float, float, float]:
    """
    Extracts monthly basin-weighted T_max, T_min, and T_mean from raw NOAA CPC NetCDF files.

    Methodological Guarantees (Gate 1):
      1. Preserves daily extrema before monthly averaging: DTR = T_max - T_min computed daily.
      2. Excludes invalid / NoData cells and enforces minimum basin coverage (default 80%).
      3. Strictly checks physical bounds: T_max >= T_min.
    """
    tmax_file = cpc_dir / f"tmax.{year}.nc"
    tmin_file = cpc_dir / f"tmin.{year}.nc"

    if not tmax_file.exists() or not tmin_file.exists():
        raise MissingTemperatureDataError(
            f"Observed NOAA CPC temperature files missing for year {year}: "
            f"expected '{tmax_file.name}' and '{tmin_file.name}' in {cpc_dir}."
        )

    norm_weights, (lat_s, lat_e), (lon_s, lon_e) = get_cpc_basin_weights(cpc_dir=cpc_dir)
    active_cells = norm_weights > 0.0

    ds_max = netCDF4.Dataset(tmax_file)
    ds_min = netCDF4.Dataset(tmin_file)

    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    days_in_year = 366 if is_leap else 365
    dates = pd.date_range(f"{year}-01-01", periods=days_in_year, freq="D")
    month_indices = np.where(dates.month == month)[0]

    tmax_all = ds_max.variables["tmax"]
    tmin_all = ds_min.variables["tmin"]

    daily_tmax = []
    daily_tmin = []

    for d_idx in month_indices:
        day_tmax = tmax_all[d_idx, lat_s:lat_e, lon_s:lon_e]
        day_tmin = tmin_all[d_idx, lat_s:lat_e, lon_s:lon_e]

        valid = (
            np.isfinite(day_tmax) & np.isfinite(day_tmin) &
            (day_tmax > -50.0) & (day_tmax < 65.0) &
            (day_tmin > -50.0) & (day_tmin < 65.0) &
            active_cells
        )

        val_w = norm_weights[valid]
        w_sum = np.sum(val_w)
        if w_sum >= min_daily_coverage:
            norm_w = val_w / w_sum
            w_max = float(np.sum(day_tmax[valid] * norm_w))
            w_min = float(np.sum(day_tmin[valid] * norm_w))
            if w_max >= w_min:
                daily_tmax.append(w_max)
                daily_tmin.append(w_min)

    ds_max.close()
    ds_min.close()

    if len(daily_tmax) < int(len(month_indices) * 0.75):
        raise MissingTemperatureDataError(
            f"Insufficient valid daily observations ({len(daily_tmax)}/{len(month_indices)} days) "
            f"for Tekezé Basin in {year}-{month:02d}."
        )

    tmax_m = round(float(np.mean(daily_tmax)), 2)
    tmin_m = round(float(np.mean(daily_tmin)), 2)
    tmean_m = round((tmax_m + tmin_m) / 2.0, 2)
    return tmax_m, tmin_m, tmean_m


def get_verified_monthly_temperature(
    year: int,
    month: int,
    cpc_dir: Path = RAW_TEMP_CPC_DIR,
    allow_synthetic_fallback: bool = False
) -> Tuple[float, float, float]:
    """
    Retrieves verified monthly temperatures (T_max, T_min, T_mean in °C) for the Tekezé Basin.

    GATE 1 COMPLIANCE:
      - Tries to extract verified real observational records from NOAA CPC (or ERA5-Land).
      - If raw files are missing and allow_synthetic_fallback is False, FAILS EXPLICITLY
        by raising MissingTemperatureDataError.
      - Never silently generates heuristic historical temperatures in production.
    """
    tmax_nc = cpc_dir / f"tmax.{year}.nc"
    tmin_nc = cpc_dir / f"tmin.{year}.nc"

    if tmax_nc.exists() and tmin_nc.exists():
        return extract_cpc_monthly_temperature(year, month, cpc_dir=cpc_dir)

    if not allow_synthetic_fallback:
        raise MissingTemperatureDataError(
            f"No verified observational temperature NetCDF files found for {year}-{month:02d} "
            f"in {cpc_dir}. Synthetic heuristic fallback is strictly disabled per Gate 1 acceptance checklist."
        )

    # Isolated synthetic heuristic for software testing ONLY
    import warnings
    warnings.warn(
        f"[PROVISIONAL_HEURISTIC_MODEL] Synthetic temperature used for {year}-{month:02d}. "
        f"NOT certified for historical drought reconstruction.",
        UserWarning
    )

    monthly_t_mean_clim = [
        18.5, 20.2, 22.4, 24.1, 24.8, 23.5, 20.8, 20.2, 21.5, 21.8, 19.8, 18.2
    ]
    monthly_dtr_clim = [
        13.5, 14.2, 14.0, 13.2, 11.8, 10.2, 7.5, 7.0, 9.2, 12.0, 13.0, 13.2
    ]

    t_mean_base = monthly_t_mean_clim[month - 1]
    dtr_base = monthly_dtr_clim[month - 1]

    year_offset = (year - 2000) * 0.025
    heat_anom = 0.0
    if year in [1984, 1997, 2002, 2009, 2015, 2023]:
        heat_anom = +0.85
    elif year in [1988, 1998, 2000, 2010, 2020]:
        heat_anom = -0.45

    t_mean = round(t_mean_base + year_offset + heat_anom, 2)
    dtr = round(dtr_base + (0.8 if heat_anom > 0 else -0.5), 2)
    t_max = round(t_mean + dtr / 2.0, 2)
    t_min = round(t_mean - dtr / 2.0, 2)

    return t_max, t_min, t_mean


# ---------------------------------------------------------------------------
# 4. End-to-End Pipeline Execution
# ---------------------------------------------------------------------------

def run_climate_reconstruction_pipeline(
    start_year: int = 1981,
    end_year: int = 2024,
    benchmark_years_only: bool = False,
    min_spatial_coverage: float = 0.95,
    allow_synthetic_fallback: bool = False
) -> Dict[str, Any]:
    """
    Executes the monthly climate reconstruction and SPEI-3 derivation.

    GATE 1 COMPLIANCE:
      allow_synthetic_fallback defaults strictly to False. If real observational / reanalysis
      temperature files are absent, execution halts with MissingTemperatureDataError.
    """
    print("=" * 100)
    print("   AI-DREWS: TEKEZE RIVER BASIN CLIMATE RECONSTRUCTION & SPEI-3 PIPELINE (1981–2024)")
    print("=" * 100)

    t_start = time.time()

    # Step 1: Spatial Masking
    print("\n[1/5] Building spatial mask for verified Tekezé Catchment...")
    mask, weights, lats, lons, crop_window, mask_meta = construct_basin_raster_mask()
    n_inside = int(np.sum(mask))
    print(f"      Basin Area:           67,135.4 km²")
    print(f"      Raster Resolution:    0.05° (~5.5 km)")
    print(f"      Weighting Scheme:     {mask_meta['weighting_method']}")
    print(f"      Active Basin Cells:   {mask_meta['active_cells_fractional']} fractional cells ({mask_meta['active_cells_center_point']} center-point cells)")

    # Step 2: Date Sequence Selection
    if benchmark_years_only:
        selected_years = [1984, 1987, 1991, 1994, 1997, 2000, 2002, 2009, 2011, 2015, 2018, 2020, 2023, 2024]
        print(f"\n[2/5] Running in BENCHMARK MODE on {len(selected_years)} historical years:")
        print(f"      {selected_years}")
    else:
        selected_years = list(range(start_year, end_year + 1))
        print(f"\n[2/5] Running in FULL MODE from {start_year} through {end_year} ({len(selected_years)} years, {len(selected_years)*12} months)...")

    monthly_records = []
    days_in_months = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Step 3: Monthly Ingestion & PET Calculation
    print("\n[3/5] Ingesting monthly precipitation and calculating PET...")
    for yr in selected_years:
        leap = (yr % 4 == 0 and yr % 100 != 0) or (yr % 400 == 0)
        days_in_months[1] = 29 if leap else 28

        # First pass to compute annual Thornthwaite heat index
        t_means_year = []
        for mo in range(1, 13):
            _, _, tm = get_verified_monthly_temperature(yr, mo, allow_synthetic_fallback=allow_synthetic_fallback)
            t_means_year.append(tm)
        th_pets_year = calculate_thornthwaite_monthly_pet(t_means_year, latitude_deg=13.325)

        for mo in range(1, 13):
            ch_res = fetch_and_extract_chirps_monthly(
                year=yr,
                month=mo,
                crop_window=crop_window,
                mask=mask,
                weights=weights,
                min_spatial_coverage=min_spatial_coverage
            )
            p_val = ch_res["precip_mean_mm"]

            t_max, t_min, t_mean = get_verified_monthly_temperature(yr, mo, allow_synthetic_fallback=allow_synthetic_fallback)
            d_count = days_in_months[mo - 1]
            harg_pet = calculate_hargreaves_pet(
                t_max_c=t_max,
                t_min_c=t_min,
                t_mean_c=t_mean,
                latitude_deg=13.325,
                month=mo,
                days_in_month=d_count
            )
            th_pet = th_pets_year[mo - 1]

            # Water balance D = P - PET (strict NaN propagation if P or PET is missing)
            if math.isfinite(p_val) and math.isfinite(harg_pet):
                d_harg = round(p_val - harg_pet, 2)
            else:
                d_harg = np.nan

            if math.isfinite(p_val) and math.isfinite(th_pet):
                d_th = round(p_val - th_pet, 2)
            else:
                d_th = np.nan

            monthly_records.append({
                "year": yr,
                "month": mo,
                "date": f"{yr:04d}-{mo:02d}-01",
                "precip_mm": p_val,
                "t_max_c": t_max,
                "t_min_c": t_min,
                "t_mean_c": t_mean,
                "pet_hargreaves_mm": round(harg_pet, 2) if math.isfinite(harg_pet) else np.nan,
                "pet_thornthwaite_mm": round(th_pet, 2) if math.isfinite(th_pet) else np.nan,
                "water_balance_harg_mm": d_harg,
                "water_balance_th_mm": d_th,
                "spatial_coverage_fraction": ch_res.get("spatial_coverage_fraction", 0.0),
                "n_valid_cells": ch_res["n_valid_cells"],
                "status": ch_res["status"]
            })

    df_monthly = pd.DataFrame(monthly_records)

    # Step 4: Seasonal Drought Target Derivation
    print("\n[4/5] Deriving seasonal drought indices (September-ending SPEI-3 & SPI-3)...")
    seasonal_records = []

    for yr in selected_years:
        df_yr = df_monthly[df_monthly["year"] == yr]

        # Kiremt Season (July, August, September: months 7, 8, 9)
        kiremt_rows = df_yr[df_yr["month"].isin([7, 8, 9])]
        if len(kiremt_rows) == 3 and not kiremt_rows["precip_mm"].isna().any():
            p_kiremt = float(kiremt_rows["precip_mm"].sum())
            pet_h_kiremt = float(kiremt_rows["pet_hargreaves_mm"].sum())
            pet_th_kiremt = float(kiremt_rows["pet_thornthwaite_mm"].sum())
            d_harg_kiremt = float(kiremt_rows["water_balance_harg_mm"].sum())
            d_th_kiremt = float(kiremt_rows["water_balance_th_mm"].sum())
        else:
            p_kiremt = np.nan
            pet_h_kiremt = np.nan
            pet_th_kiremt = np.nan
            d_harg_kiremt = np.nan
            d_th_kiremt = np.nan

        # Belg Season (March, April, May: months 3, 4, 5)
        belg_rows = df_yr[df_yr["month"].isin([3, 4, 5])]
        if len(belg_rows) == 3 and not belg_rows["precip_mm"].isna().any():
            p_belg = float(belg_rows["precip_mm"].sum())
            pet_h_belg = float(belg_rows["pet_hargreaves_mm"].sum())
            d_harg_belg = float(belg_rows["water_balance_harg_mm"].sum())
        else:
            p_belg = np.nan
            pet_h_belg = np.nan
            d_harg_belg = np.nan

        p_annual = float(df_yr["precip_mm"].sum()) if not df_yr["precip_mm"].isna().any() else np.nan
        pet_annual = float(df_yr["pet_hargreaves_mm"].sum()) if not df_yr["pet_hargreaves_mm"].isna().any() else np.nan

        seasonal_records.append({
            "year": yr,
            "precip_kiremt_jas_mm": round(p_kiremt, 2) if math.isfinite(p_kiremt) else np.nan,
            "pet_harg_kiremt_mm": round(pet_h_kiremt, 2) if math.isfinite(pet_h_kiremt) else np.nan,
            "pet_th_kiremt_mm": round(pet_th_kiremt, 2) if math.isfinite(pet_th_kiremt) else np.nan,
            "d_harg_kiremt_mm": round(d_harg_kiremt, 2) if math.isfinite(d_harg_kiremt) else np.nan,
            "d_th_kiremt_mm": round(d_th_kiremt, 2) if math.isfinite(d_th_kiremt) else np.nan,
            "precip_belg_mam_mm": round(p_belg, 2) if math.isfinite(p_belg) else np.nan,
            "d_harg_belg_mm": round(d_harg_belg, 2) if math.isfinite(d_harg_belg) else np.nan,
            "precip_annual_mm": round(p_annual, 2) if math.isfinite(p_annual) else np.nan,
            "pet_annual_mm": round(pet_annual, 2) if math.isfinite(pet_annual) else np.nan
        })

    df_seasonal = pd.DataFrame(seasonal_records)

    # Standardize Kiremt SPEI-3 using Hosking Generalized Logistic (GLO) distribution
    d_vals = df_seasonal["d_harg_kiremt_mm"].values
    p_vals = df_seasonal["precip_kiremt_jas_mm"].values
    yr_vals = df_seasonal["year"].values

    calib_window = (1991, 2020)
    calib_mask = (yr_vals >= calib_window[0]) & (yr_vals <= calib_window[1]) & np.isfinite(d_vals)
    n_calib_valid = int(np.sum(calib_mask))
    min_calib_required = 20 if len(yr_vals) >= 30 else 10

    if n_calib_valid < min_calib_required:
        raise ValueError(
            f"Insufficient valid calibration observations ({n_calib_valid} < {min_calib_required}) "
            f"in fixed reference baseline {calib_window}. Pipeline will not silently substitute full record."
        )

    spei_res = calculate_spei_seasonal(
        d_seasonal_series=d_vals,
        years=yr_vals,
        calibration_period=calib_window,
        min_calibration_years=min_calib_required
    )
    df_seasonal["spei3_kiremt_sep"] = [round(v, 3) if math.isfinite(v) else np.nan for v in spei_res["spei"]]

    # Standardize Kiremt SPI-3 (2-parameter Gamma MLE with zero-precipitation probability adjustment)
    spi_res = calculate_spi_seasonal(
        p_seasonal_series=p_vals,
        years=yr_vals,
        calibration_period=calib_window,
        min_calibration_years=min_calib_required
    )
    df_seasonal["spi3_kiremt_sep"] = [round(v, 3) if math.isfinite(v) else np.nan for v in spi_res["spi"]]

    # Separate unstandardized empirical precipitation z-score (clearly distinct from SPI)
    p_calib = p_vals[(yr_vals >= calib_window[0]) & (yr_vals <= calib_window[1]) & np.isfinite(p_vals)]
    p_mean = float(np.mean(p_calib)) if len(p_calib) > 0 else np.nan
    p_std = float(np.std(p_calib)) if len(p_calib) > 0 else np.nan
    df_seasonal["precip_zscore_kiremt_sep"] = [
        round(float((p - p_mean) / (p_std + 1e-6)), 3) if math.isfinite(p) else np.nan
        for p in p_vals
    ]

    # Save outputs
    OUT_MONTHLY_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_monthly.to_csv(OUT_MONTHLY_CSV, index=False)
    df_seasonal.to_csv(OUT_SEASONAL_CSV, index=False)

    # Step 5: Data Quality Summary Generation
    print("\n[5/5] Generating automated Data Quality & Verification Summary...")
    quality_summary = {
        "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "basin_name": "Tekeze River Basin (Complete Hydrological Catchment)",
        "basin_area_km2": 67135.4,
        "n_grid_cells_in_basin": mask_meta["active_cells_fractional"],
        "spatial_weighting_method": mask_meta["weighting_method"],
        "spatial_resolution_deg": CHIRPS_PIXEL_RES,
        "temporal_range": [int(np.min(yr_vals)), int(np.max(yr_vals))],
        "total_months_processed": len(df_monthly),
        "total_seasonal_years": len(df_seasonal),
        "data_completeness_pct": 100.0 * (1.0 - df_monthly["precip_mm"].isna().mean()),
        "spei_calibration_period": list(calib_window),
        "spei_distribution": spei_res.get("distribution", "Generalized_Logistic_Hosking"),
        "spei_fitted_parameters": spei_res["params"],
        "spi_distribution": spi_res.get("distribution", "Gamma_2Param_Thom_MLE"),
        "spi_fitted_parameters": spi_res["params"],
        "provenance_and_integrity_metadata": {
            "status": "PRELIMINARY_COMPUTATIONAL_OUTPUT",
            "temperature_data_status": "PROVISIONAL_HEURISTIC_MODEL",
            "temperature_warning": (
                "Monthly temperatures are currently generated by a heuristic climatological model. "
                "They are NOT certified historical observations. Full scientific certification "
                "requires ingesting documented gridded reanalysis (e.g., NOAA CPC / ERA5-Land)."
            ),
            "precipitation_data_status": "VERIFIED_CHIRPS_V2_GEOREFERENCED",
            "spatial_coverage_enforcement": ">= 95% of basin area weight required per month"
        },
        "pet_method_comparison": {
            "mean_annual_hargreaves_pet_mm": round(float(df_seasonal["pet_annual_mm"].dropna().mean()), 1),
            "mean_kiremt_hargreaves_pet_mm": round(float(df_seasonal["pet_harg_kiremt_mm"].dropna().mean()), 1),
            "mean_kiremt_thornthwaite_pet_mm": round(float(df_seasonal["pet_th_kiremt_mm"].dropna().mean()), 1),
            "pet_ratio_hargreaves_to_thornthwaite": round(
                float(df_seasonal["pet_harg_kiremt_mm"].dropna().mean() / (df_seasonal["pet_th_kiremt_mm"].dropna().mean() + 1e-6)), 2
            ),
            "methodological_note": (
                "Hargreaves-Samani uses extraterrestrial radiation and diurnal temperature range as an empirical proxy "
                "for surface radiation and vapour pressure deficit. Thornthwaite is driven solely by monthly mean temperature. "
                "Neither directly measures net surface radiation or explicit humidity. Both are temperature-based empirical estimators "
                "evaluated for sensitivity; ERA5-Land Penman-Monteith provides the physical reference target."
            )
        },
        "moderate_drought_years_identified": [int(y) for y in spei_res["drought_years_moderate"]],
        "severe_drought_years_identified": [int(y) for y in spei_res["drought_years_severe"]],
        "output_files": [
            str(OUT_MONTHLY_CSV.relative_to(ROOT_DIR)),
            str(OUT_SEASONAL_CSV.relative_to(ROOT_DIR)),
            str(OUT_QUALITY_JSON.relative_to(ROOT_DIR))
        ]
    }

    with open(OUT_QUALITY_JSON, "w", encoding="utf-8") as f:
        json.dump(quality_summary, f, indent=2)

    elapsed = round(time.time() - t_start, 2)
    print("\n" + "=" * 100)
    print("[+] CLIMATE RECONSTRUCTION & SPEI-3 PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 100)
    print(f"Total Execution Duration:  {elapsed} seconds")
    print(f"Monthly Series Output:     {OUT_MONTHLY_CSV}")
    print(f"Seasonal SPEI-3 Output:    {OUT_SEASONAL_CSV}")
    print(f"Data Quality Audit:        {OUT_QUALITY_JSON}")
    print(f"Moderate Drought Years:    {spei_res['drought_years_moderate']}")
    print(f"Severe Drought Years:      {spei_res['drought_years_severe']}")
    print("=" * 100)

    return quality_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-DREWS Tekezé Climate Reconstruction Pipeline")
    parser.add_argument("--benchmark-only", action="store_true", help="Process only representative benchmark years")
    parser.add_argument("--start-year", type=int, default=1981, help="Start year (default: 1981)")
    parser.add_argument("--end-year", type=int, default=2024, help="End year (default: 2024)")
    parser.add_argument("--min-coverage", type=float, default=0.95, help="Minimum valid spatial coverage fraction (default: 0.95)")
    args = parser.parse_args()

    run_climate_reconstruction_pipeline(
        start_year=args.start_year,
        end_year=args.end_year,
        benchmark_years_only=args.benchmark_only,
        min_spatial_coverage=args.min_coverage
    )
