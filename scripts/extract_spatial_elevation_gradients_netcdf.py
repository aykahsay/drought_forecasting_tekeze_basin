"""
Spatial Elevation Gradient Extraction from 2000-2023-soillayer.nc
Extracts soil moisture (swvl1, swvl2), temperature (t2m), and precipitation (tp)
across three distinct elevation regimes of the Tekeze River Basin:
1. Lowland Canyon Gorge (~1,100 m a.s.l.): High thermal stress, rapid desiccation
2. Mid-Altitude Escarpment (~1,500 m a.s.l.): Agricultural Vertisol cropping belt (Yechila Abergelle)
3. Highland Plateau (~2,000 m a.s.l.): Deep moisture storage, attenuated evaporative demand
"""

import sys
from pathlib import Path
import netCDF4 as nc
import numpy as np
import pandas as pd

def extract_elevation_gradients():
    nc_path = Path("2000-2023-soillayer.nc")
    if not nc_path.exists():
        print(f"Error: {nc_path} not found.")
        return

    print(f"Opening NetCDF archive: {nc_path}")
    ds = nc.Dataset(nc_path, mode="r")
    
    lats = ds.variables["latitude"][:]
    lons = ds.variables["longitude"][:]
    times_raw = ds.variables["time"][:]
    timestamps = pd.to_datetime(times_raw, unit="s")
    
    # Coordinates corresponding to elevation zones in the Tekeze River Basin
    # Canyon Gorge (~1,100 m): deeply incised Tekeze riverbed (high T2m, rapid desiccation)
    # Escarpment (~1,500 m): Yechila / Tanqua Abergelle agricultural plains
    # Highland Ridge (~2,000 m): Semien / Dogu'a Tembien high plateaus
    
    zones = {
        "Canyon Gorge (1,100 m)": {"lat": 13.00, "lon": 38.75, "desc": "Arid Deep Kolla gorge"},
        "Escarpment (1,500 m)":   {"lat": 13.50, "lon": 38.75, "desc": "Kolla Vertisol cropping zone"},
        "Highland (2,000 m)":    {"lat": 13.25, "lon": 38.25, "desc": "Woina Dega high plateau"}
    }
    
    results = []
    
    for zone_name, meta in zones.items():
        lat_idx = np.argmin(np.abs(lats - meta["lat"]))
        lon_idx = np.argmin(np.abs(lons - meta["lon"]))
        actual_lat = float(lats[lat_idx])
        actual_lon = float(lons[lon_idx])
        
        swvl1 = ds.variables["swvl1"][:, 0, lat_idx, lon_idx]
        swvl2 = ds.variables["swvl2"][:, 0, lat_idx, lon_idx]
        t2m_c = ds.variables["t2m"][:, 0, lat_idx, lon_idx] - 273.15
        tp_mm = ds.variables["tp"][:, 0, lat_idx, lon_idx] * 1000.0 # convert to mm
        
        df_zone = pd.DataFrame({
            "timestamp": timestamps,
            "swvl1": swvl1,
            "swvl2": swvl2,
            "t2m_C": t2m_c,
            "tp_mm": tp_mm
        })
        
        # Monthly resample
        df_monthly = df_zone.set_index("timestamp").resample("ME").agg({
            "swvl1": "mean",
            "swvl2": "mean",
            "t2m_C": "mean",
            "tp_mm": "sum"
        }).reset_index()
        
        df_monthly["zone"] = zone_name
        df_monthly["elevation_m"] = 1100 if "1,100" in zone_name else (1500 if "1,500" in zone_name else 2000)
        results.append(df_monthly)
        
        # Summary statistics
        mean_sm1 = df_zone["swvl1"].mean()
        mean_sm2 = df_zone["swvl2"].mean()
        min_sm2 = df_zone["swvl2"].min()
        max_sm2 = df_zone["swvl2"].max()
        mean_t = df_zone["t2m_C"].mean()
        wilting_pct = (df_zone["swvl2"] < 0.05).mean() * 100.0
        
        print(f"\n--- {zone_name} (Lat: {actual_lat:.2f}N, Lon: {actual_lon:.2f}E) ---")
        print(f"  Description:           {meta['desc']}")
        print(f"  Mean Air Temp (T2m):   {mean_t:.2f} °C")
        print(f"  Root-Zone SM (swvl2):  Mean={mean_sm2:.4f}, Min={min_sm2:.4f}, Max={max_sm2:.4f} m³/m³")
        print(f"  Surface SM (swvl1):   Mean={mean_sm1:.4f} m³/m³")
        print(f"  Time < Wilting (0.05): {wilting_pct:.1f}% of record")

    ds.close()
    
    df_all = pd.concat(results, ignore_index=True)
    out_csv = Path("data/processed/spatial_elevation_gradient_timeseries.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_csv(out_csv, index=False)
    print(f"\nSaved detailed spatial extraction timeseries to: {out_csv}")
    
    # Generate Climatological Summary Table
    summary = df_all.groupby("zone").agg(
        Mean_Elevation_m=("elevation_m", "first"),
        Mean_T2m_degC=("t2m_C", "mean"),
        Mean_RootZone_SM=("swvl2", "mean"),
        Min_RootZone_SM=("swvl2", "min"),
        Max_RootZone_SM=("swvl2", "max"),
        Total_Precip_mm=("tp_mm", "sum")
    ).reset_index()
    
    summary_path = Path("data/processed/elevation_gradient_climatology_summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"Saved climatology summary table to: {summary_path}")
    print("\nSummary Table:")
    print(summary.to_string(index=False))

if __name__ == "__main__":
    extract_elevation_gradients()
