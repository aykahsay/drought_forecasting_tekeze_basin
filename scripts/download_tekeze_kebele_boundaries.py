#!/usr/bin/env python3
"""
download_tekeze_kebele_boundaries.py
------------------------------------
Downloads candidate Kebele (Admin Level 4) polygons for Tigray and Amhara
from the official Ethiopia Geoportal / ArcGIS FeatureServer:
https://services8.arcgis.com/oTalEaSXAuyNT7xf/arcgis/rest/services/Ethiopia_AdminBoundaries/FeatureServer/0

Features pagination (max 1000 per request) and saves to:
data/raw/tekeze_study_area_kebeles_candidate.geojson
"""

import os
import json
import time
import requests
from pathlib import Path

BASE = (
    "https://services8.arcgis.com/oTalEaSXAuyNT7xf/"
    "arcgis/rest/services/Ethiopia_AdminBoundaries/"
    "FeatureServer/0"
)
OUT = Path("data/raw/tekeze_study_area_kebeles_candidate.geojson")
OUT.parent.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers["User-Agent"] = "AI-DREWS-research/1.0"

def download_kebeles():
    print(f"Connecting to ArcGIS FeatureServer: {BASE}")
    where = "R_NAME IN ('Amhara', 'Tigray')"
    
    # 1. Obtain ObjectIDs
    print("Querying ObjectIDs for Amhara and Tigray...")
    resp = session.get(
        f"{BASE}/query",
        params={
            "where": where,
            "returnIdsOnly": "true",
            "f": "json",
        },
        timeout=60,
    )
    resp.raise_for_status()
    result = resp.json()
    if "error" in result:
        raise RuntimeError(result["error"])
        
    object_ids = result.get("objectIds", [])
    total_requested = len(object_ids)
    print(f"Total candidate ObjectIDs found: {total_requested}")

    # 2. Batch download in chunks of 100 features
    batch_size = 100
    all_features = []
    
    print(f"Downloading {total_requested} kebele polygons in batches of {batch_size}...")
    start_time = time.time()
    
    for i in range(0, total_requested, batch_size):
        chunk_ids = object_ids[i:i + batch_size]
        id_str = ",".join(map(str, chunk_ids))
        
        # Query GeoJSON format
        retries = 3
        for attempt in range(retries):
            try:
                resp_batch = session.get(
                    f"{BASE}/query",
                    params={
                        "objectIds": id_str,
                        "outFields": "*",
                        "returnGeometry": "true",
                        "outSR": "4326",
                        "f": "geojson",
                    },
                    timeout=60,
                )
                resp_batch.raise_for_status()
                geojson_data = resp_batch.json()
                if "error" in geojson_data:
                    raise RuntimeError(geojson_data["error"])
                
                features = geojson_data.get("features", [])
                all_features.extend(features)
                print(f"  Downloaded batch {i//batch_size + 1}/{(total_requested + batch_size - 1)//batch_size}: {len(features)} features (Total so far: {len(all_features)}/{total_requested})")
                break
            except Exception as e:
                if attempt == retries - 1:
                    print(f"  Error on batch starting at index {i}: {e}")
                    raise
                time.sleep(2)

    elapsed = time.time() - start_time
    print(f"\nDownload completed in {elapsed:.1f}s. Total features received: {len(all_features)}")

    # 3. Validation check
    if len(all_features) != total_requested:
        print(f"WARNING: Feature count mismatch! Requested {total_requested}, got {len(all_features)}")
    else:
        print(f"VERIFIED: Exactly {len(all_features)} features match the requested ObjectIDs.")

    # 4. Save GeoJSON
    out_fc = {
        "type": "FeatureCollection",
        "name": "Ethiopia_Tigray_Amhara_Kebeles_Candidate",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": all_features
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out_fc, f)
    
    file_size_mb = os.path.getsize(OUT) / (1024 * 1024)
    print(f"Saved candidate Kebeles to {OUT} ({file_size_mb:.2f} MB)")


if __name__ == "__main__":
    download_kebeles()
