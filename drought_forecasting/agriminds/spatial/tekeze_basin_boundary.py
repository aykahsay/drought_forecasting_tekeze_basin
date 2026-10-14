"""
tekeze_basin_boundary.py
------------------------
Verified Hydrological Delineation of the Tekeze River Basin for AI-DREWS.

Derived from WWF / HydroSHEDS HydroBASINS Level 5 (Africa v1c) Standard Product:
- Constituent Sub-basins:
    * 1050648030 (PFAF 17227): Middle & Lower Tekeze Basin (Tigray / Eritrea border) - 38,225.7 km²
    * 1050692800 (PFAF 17228): Eastern Upper Tekeze Headwaters (Wag Hemra / Maychew) - 7,592.7 km²
    * 1050692900 (PFAF 17229): Southern Upper Tekeze Headwaters (Lalibela / Simien / Guna) - 21,317.0 km²
- Total Hydrological Catchment Area: 67,135.4 km²
- Geographic Bounding Box: 35.8583°E to 39.7917°E, 11.6619°N to 14.7958°N
- Coordinate Reference System: EPSG:4326 (WGS 84)

Provenance Note:
----------------
Popular single-polygon downloads (such as the standard HDX 'Tekeze Basin' shapefile)
contain ONLY sub-basin 1050648030 (38,226 km²), truncating the southern 43.1% of the basin
at 13.13°N. This module provides the complete, topologically connected hydrological catchment.
"""

from __future__ import annotations
import json
import os
import hashlib
from typing import Any, Dict, List, Tuple
import numpy as np
from shapely.geometry import shape, Point
from shapely.geometry.base import BaseGeometry


_GEOJSON_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'data', 'spatial', 'processed', 'tekeze_basin_hydrological_complete.geojson'
)


def get_tekeze_geojson_path() -> str:
    """Return the absolute path to the verified Tekeze Basin GeoJSON."""
    return os.path.abspath(_GEOJSON_PATH)


def load_tekeze_basin_geojson() -> Dict[str, Any]:
    """Load the GeoJSON feature collection for the complete Tekeze catchment."""
    path = get_tekeze_geojson_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Tekeze Basin GeoJSON not found at: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_tekeze_basin_geometry() -> BaseGeometry:
    """Load the Shapely geometry for the complete Tekeze catchment."""
    fc = load_tekeze_basin_geojson()
    return shape(fc['features'][0]['geometry'])


def get_tekeze_metadata() -> Dict[str, Any]:
    """Retrieve metadata, constituent IDs, area, and bounding box."""
    fc = load_tekeze_basin_geojson()
    props = fc['features'][0]['properties']
    return {
        "name": props.get("name"),
        "source": props.get("source"),
        "source_url": props.get("source_url"),
        "constituent_hybas_ids": props.get("constituent_hybas_ids"),
        "constituent_pfaf_ids": props.get("constituent_pfaf_ids"),
        "total_area_km2": props.get("total_area_km2"),
        "bounds_wsen": props.get("bounds"),
        "crs": props.get("crs"),
        "drainage_system": props.get("drainage_system"),
    }


def compute_geojson_sha256() -> str:
    """Compute the SHA256 checksum of the GeoJSON file for reproducibility auditing."""
    path = get_tekeze_geojson_path()
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def is_coordinate_in_tekeze_basin(lon: float, lat: float) -> bool:
    """Test whether a given coordinate (lon, lat) falls within the complete Tekeze basin."""
    geom = load_tekeze_basin_geometry()
    return bool(geom.contains(Point(lon, lat)))


def create_spatial_grid_mask(
    lats: np.ndarray, lons: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Build a 2D boolean mask and cosine area weights for any 2D regular grid (e.g. CHIRPS or ERA5).
    
    Returns:
        mask (2D bool): True where grid cell center is inside the basin.
        weights (2D float): Cosine latitude area weights multiplied by mask.
        lat_slice (1D int): Subgrid indices for latitude.
        lon_slice (1D int): Subgrid indices for longitude.
    """
    geom = load_tekeze_basin_geometry()
    minx, miny, maxx, maxy = geom.bounds

    lat_idx = np.where((lats >= miny) & (lats <= maxy))[0]
    lon_idx = np.where((lons >= minx) & (lons <= maxx))[0]

    sub_lats = lats[lat_idx]
    sub_lons = lons[lon_idx]

    mask = np.zeros((len(sub_lats), len(sub_lons)), dtype=bool)
    for i, lat in enumerate(sub_lats):
        for j, lon in enumerate(sub_lons):
            if geom.contains(Point(lon, lat)):
                mask[i, j] = True

    # Area weighting: spherical grid cell area proportional to cos(latitude)
    cos_lat = np.cos(np.radians(sub_lats))[:, np.newaxis]
    weights = cos_lat * mask.astype(float)
    if weights.sum() > 0:
        weights /= weights.sum()

    return mask, weights, lat_idx, lon_idx


def compute_area_weighted_basin_mean(
    precip_grid_2d: np.ndarray,
    lats: np.ndarray,
    lons: np.ndarray
) -> float:
    """
    Compute the area-weighted basin average precipitation for a single 2D grid slice.
    """
    mask, weights, lat_idx, lon_idx = create_spatial_grid_mask(lats, lons)
    sub_grid = precip_grid_2d[np.ix_(lat_idx, lon_idx)]
    return float(np.sum(sub_grid * weights))
