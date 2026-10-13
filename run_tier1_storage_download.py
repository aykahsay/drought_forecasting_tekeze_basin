"""
Tier 1 Storage-Aware Data Download & Real-Time Kafka Streaming Pipeline
======================================================================
Executes Tier 1 (~5 to 10 GB) acquisition based on 1.78 TB free storage:
  1. High-Resolution CHIRPS Satellite Rainfall (0.05° ~5 km, 250x300 grid)
  2. Copernicus Digital Elevation Model (DEM) & Slope/Aspect Rasters
  3. High-Capacity 6-Band Spatiotemporal Tensor Cubes for the 20 GB GPU
"""

import sys
import time
from pathlib import Path

# Add project root and drought_forecasting directory to Python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "drought_forecasting"))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agriminds.ingestion.storage_aware_downloader import StorageAwareDataDownloader
from agriminds.ingestion.kafka_stream import get_stream_manager


def main():
    print("=" * 80)
    print("[*] LAUNCHING TIER 1 STORAGE-AWARE DATA INGESTION & KAFKA STREAMING")
    print("=" * 80)

    downloader = StorageAwareDataDownloader()
    stats = downloader.get_storage_stats()
    print(f"Host Total Storage: {stats['total_gb']} GB")
    print(f"Host Free Storage:  {stats['free_gb']} GB ({stats['free_pct']}% available)")
    print(f"Target Budget:      Tier 1 (~5 to 10 GB)")
    print("-" * 80)

    t_start = time.time()

    # 1. Copernicus DEM Topography
    print("\n[1/3] Generating Copernicus High-Resolution Topographic Grid (250x300 pixels)...")
    dem_res = downloader.generate_copernicus_dem_topography(grid_shape=(250, 300))
    print(f"  [+] Saved: {dem_res['file_path']}")
    print(f"  [+] Elevation Range: {round(dem_res['elevation_min_m'])}m to {round(dem_res['elevation_max_m'])}m (Mean slope: {dem_res['mean_slope_deg']} deg)")

    # 2. 6-Band Spatiotemporal Tensor Cube for the 20 GB GPU
    print("\n[2/3] Constructing 6-Band Spatiotemporal Tensor Cube for 20 GB VRAM GPU...")
    print("      Channels: [swvl1, swvl2, t2m, tp, CHIRPS_precip, Copernicus_DEM]")
    cube_res = downloader.build_high_capacity_gpu_tensor_cube(seq_len=12, num_samples=1200)
    print(f"  [+] Saved: {cube_res['tensor_cube_file']} ({cube_res['size_mb']} MB)")
    print(f"  [+] Tensor Shape: {cube_res['shape']} (Samples x Seq_Len x Channels x Height x Width)")
    print(f"  [+] Kafka Event: {cube_res['kafka_published']}")

    # 3. High-Resolution CHIRPS African Satellite Precipitation
    print("\n[3/3] Downloading & Streaming High-Res CHIRPS Satellite Rainfall (2018 - 2024)...")
    print("      Resolution: 0.05 deg (~5 km), Ethiopia Bounding Box (250x300 grid)")
    
    def on_progress(cur, total, date_str):
        if cur % 12 == 0 or cur == total:
            print(f"      -> Streamed {cur}/{total} months (Latest: {date_str}) over Kafka...")

    chirps_res = downloader.download_and_stream_chirps_ethiopia(
        start_year=2018,
        end_year=2024,
        save_netcdf=True,
        throttle_ms=0,
        progress_cb=on_progress,
    )
    print(f"  [+] Downloaded & Streamed: {chirps_res['months_downloaded']} monthly high-res grids")
    print(f"  [+] NetCDF Archive:        {chirps_res['netcdf_archive']} ({chirps_res['archive_size_mb']} MB)")
    print(f"  [+] Kafka Events Streamed: {chirps_res['kafka_events_streamed']} tiles at {chirps_res['throughput_msg_sec']} msg/s")

    elapsed = round(time.time() - t_start, 2)
    final_stats = downloader.get_storage_stats()

    print("\n" + "=" * 80)
    print("[+] TIER 1 DATA INGESTION & KAFKA STREAMING COMPLETE")
    print("=" * 80)
    print(f"Total Duration:          {elapsed} seconds")
    print(f"Remaining Free Storage:  {final_stats['free_gb']} GB")
    print("-" * 80)
    print("ALL HIGH-RESOLUTION DATASETS READY FOR 20 GB GPU TRAINING:")
    print(f"  - CHIRPS 5km Rainfall:  {chirps_res['netcdf_archive']}")
    print(f"  - Copernicus DEM:       {dem_res['file_path']}")
    print(f"  - 6-Band Tensor Cube:   {cube_res['tensor_cube_file']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
