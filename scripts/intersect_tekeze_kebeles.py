#!/usr/bin/env python3
"""
intersect_tekeze_kebeles.py
---------------------------
Performs rigorous spatial intersection between the candidate Kebele polygons
(3,874 from Tigray & Amhara) and the verified HydroBASINS Tekeze complete catchment
(67,135.4 km²).

Categorizes each kebele:
  - FULLY_CONTAINED: >= 90% area inside basin
  - PARTIALLY_CONTAINED: 5% - 90% area inside basin
  - PERIPHERAL_TOUCH: < 5% area inside basin

Saves intersected results to:
  data/spatial/processed/tekeze_basin_kebeles_intersected.geojson
"""

import json
import os
import time
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

def run_intersection():
    tekeze_basin_path = 'data/spatial/processed/tekeze_basin_hydrological_complete.geojson'
    kebeles_path = 'data/raw/tekeze_study_area_kebeles_candidate.geojson'
    out_path = 'data/spatial/processed/tekeze_basin_kebeles_intersected.geojson'

    print("Loading verified Tekeze Basin geometry...")
    with open(tekeze_basin_path, 'r', encoding='utf-8') as f:
        basin_fc = json.load(f)
    basin_geom = shape(basin_fc['features'][0]['geometry'])
    basin_bbox = basin_geom.bounds
    print(f"Basin loaded. Bounding Box: {basin_bbox}, Area: ~{basin_fc['features'][0]['properties']['total_area_km2']} km2")

    print(f"Loading candidate kebeles from {kebeles_path}...")
    with open(kebeles_path, 'r', encoding='utf-8') as f:
        kebeles_fc = json.load(f)
    total_kebeles = len(kebeles_fc['features'])
    print(f"Loaded {total_kebeles} candidate kebele features.")

    print("\nFiltering and intersecting candidate kebeles against Tekeze basin...")
    start_time = time.time()
    
    intersected_features = []
    category_counts = {'FULLY_CONTAINED': 0, 'PARTIALLY_CONTAINED': 0, 'PERIPHERAL_TOUCH': 0}
    regional_counts = {}
    woreda_summary = {}

    for idx, feat in enumerate(kebeles_fc['features']):
        props = feat['properties']
        geom_json = feat['geometry']
        if not geom_json or not geom_json.get('coordinates'):
            continue
        
        k_geom = shape(geom_json)
        if not k_geom.is_valid:
            k_geom = k_geom.buffer(0)

        # Bounding box quick check
        k_bounds = k_geom.bounds
        if (k_bounds[2] < basin_bbox[0] or k_bounds[0] > basin_bbox[2] or
            k_bounds[3] < basin_bbox[1] or k_bounds[1] > basin_bbox[3]):
            continue

        # Spatial intersection
        if k_geom.intersects(basin_geom):
            inter_geom = k_geom.intersection(basin_geom)
            k_area = k_geom.area
            inter_area = inter_geom.area
            ratio = inter_area / k_area if k_area > 0 else 0.0

            if ratio >= 0.90:
                cat = 'FULLY_CONTAINED'
            elif ratio >= 0.05:
                cat = 'PARTIALLY_CONTAINED'
            else:
                cat = 'PERIPHERAL_TOUCH'

            category_counts[cat] += 1
            r_name = props.get('R_NAME', 'Unknown')
            z_name = props.get('Z_NAME', 'Unknown')
            w_name = props.get('W_NAME', 'Unknown')
            # In Tigray RK_NAME is populated; in Amhara RK_NAME or KK_NAME
            kebele_name = (props.get('RK_NAME') or props.get('KK_NAME') or '').strip()

            regional_counts[r_name] = regional_counts.get(r_name, 0) + 1
            w_key = (r_name, z_name, w_name)
            if w_key not in woreda_summary:
                woreda_summary[w_key] = {'count': 0, 'kebeles': []}
            woreda_summary[w_key]['count'] += 1
            woreda_summary[w_key]['kebeles'].append(kebele_name)

            # Store properties with intersection metadata
            out_props = dict(props)
            out_props['basin_containment_category'] = cat
            out_props['basin_intersection_ratio'] = round(ratio, 4)
            out_props['kebele_centroid_lon'] = round(k_geom.centroid.x, 4)
            out_props['kebele_centroid_lat'] = round(k_geom.centroid.y, 4)
            out_props['centroid_inside_basin'] = basin_geom.contains(k_geom.centroid)

            intersected_features.append({
                'type': 'Feature',
                'properties': out_props,
                'geometry': mapping(k_geom)  # keep full kebele polygon
            })

    elapsed = time.time() - start_time
    print(f"Intersection complete in {elapsed:.1f}s.")
    print(f"Total Intersecting Kebeles: {len(intersected_features)}")
    print(f"  - FULLY_CONTAINED (>= 90% in basin): {category_counts['FULLY_CONTAINED']}")
    print(f"  - PARTIALLY_CONTAINED (5% - 90% in basin): {category_counts['PARTIALLY_CONTAINED']}")
    print(f"  - PERIPHERAL_TOUCH (< 5% in basin): {category_counts['PERIPHERAL_TOUCH']}")
    print(f"\nBreakdown by Region:")
    for r, cnt in regional_counts.items():
        print(f"  - {r}: {cnt} kebeles")

    print(f"\nTotal Woredas represented: {len(woreda_summary)}")
    # Print Tanqua Abergele specifically
    for (r, z, w), info in woreda_summary.items():
        if 'aber' in w.lower() or 'tanq' in w.lower():
            print(f"\n>>> TARGET WOREDA: {r} / {z} / {w} ({info['count']} kebeles)")
            print(f"    Kebeles: {info['kebeles']}")

    # Save output
    out_fc = {
        'type': 'FeatureCollection',
        'name': 'Tekeze_Basin_Intersected_Kebeles',
        'crs': {
            'type': 'name',
            'properties': {'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'}
        },
        'properties': {
            'description': 'Kebeles intersecting the HydroBASINS complete Tekeze Catchment (67,135.4 km2)',
            'total_features': len(intersected_features),
            'fully_contained': category_counts['FULLY_CONTAINED'],
            'partially_contained': category_counts['PARTIALLY_CONTAINED'],
            'peripheral_touch': category_counts['PERIPHERAL_TOUCH']
        },
        'features': intersected_features
    }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out_fc, f)

    file_size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"\nSaved intersected kebeles to {out_path} ({file_size_mb:.2f} MB)")


if __name__ == '__main__':
    run_intersection()
