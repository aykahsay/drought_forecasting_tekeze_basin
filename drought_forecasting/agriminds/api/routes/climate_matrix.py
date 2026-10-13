"""
Climate Matrix REST API Router.
Exposes the 4-Quadrant Regional Climate Intelligence Matrix (El Niño, Drought Index,
Precipitation, and Dual-Axis Multi-Year Time Series) for Amhara Region & Ethiopia.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query

from agriminds.spatial.amhara_basins import (
    AMHARA_BASINS,
    AMHARA_MONTHLY_AGGREGATE,
    LAKE_TANA_GEOMETRY,
)

matrix_router = APIRouter(prefix="/api/matrix", tags=["Regional Climate Matrix"])


@matrix_router.get("/amhara")
def get_amhara_climate_matrix(
    month: Optional[str] = Query(None, description="Optional month filter: jun, jul, aug, sep, oct, nov, dec")
) -> Dict[str, Any]:
    """
    Returns the complete 4-quadrant climate matrix for Amhara Region:
      1. El Niño Index 2026 spatial distribution
      2. Drought Index 2026 (SPI/SPEI) spatial distribution
      3. Cumulative Precipitation 2026 spatial distribution
      4. Monthly Mean Precipitation & Rain Days (2025 vs 2026) dual-axis series
    """
    basins_payload = []
    m_key = month.lower() if month else None

    for b in AMHARA_BASINS:
        basin_copy = dict(b)
        # If a specific month is requested, adjust the indices to reflect that month
        if m_key and m_key in b.get("monthly_data", {}):
            m_slice = b["monthly_data"][m_key]
            basin_copy["active_el_nino"] = m_slice["el_nino"]
            basin_copy["active_drought"] = m_slice["drought"]
            basin_copy["active_precip"] = m_slice["precip_2026"] * 25  # Monthly scaled mm
            basin_copy["active_rain_days"] = m_slice["rain_days_2026"]
        else:
            basin_copy["active_el_nino"] = b["el_nino_index_2026"]
            basin_copy["active_drought"] = b["drought_index_2026"]
            basin_copy["active_precip"] = b["precipitation_2026_mm"]
            basin_copy["active_rain_days"] = b["rain_days_2026"]

        basins_payload.append(basin_copy)

    return {
        "region_id": "amhara",
        "region_name": "Amhara Region",
        "target_year": 2026,
        "baseline_year": 2025,
        "selected_month": m_key or "annual_composite",
        "spatial_bounds": {
            "lat_min": 9.0,
            "lat_max": 14.0,
            "lon_min": 36.0,
            "lon_max": 40.0,
            "viewbox": "0 0 580 490",
        },
        "color_ramps": {
            "el_nino": {
                "title": "El Niño Index 2026",
                "unit": "SST Anomaly (°C)",
                "min": -2.0,
                "max": +2.0,
                "stops": [
                    {"val": -2.0, "color": "#002060", "label": "-2"},
                    {"val": -1.0, "color": "#3399ff", "label": "-1"},
                    {"val": 0.0, "color": "#c6e2ff", "label": "0"},
                    {"val": +1.0, "color": "#ff6600", "label": "+1"},
                    {"val": +2.0, "color": "#cc0000", "label": "+2"},
                ]
            },
            "drought": {
                "title": "Drought Index 2026 (SPI / SPEI)",
                "unit": "Standardized Index",
                "min": -2.0,
                "max": +2.0,
                "stops": [
                    {"val": -2.0, "color": "#5c2e00", "label": "-2"},
                    {"val": -1.0, "color": "#b35900", "label": "-1"},
                    {"val": 0.0, "color": "#ffffcc", "label": "0"},
                    {"val": +1.0, "color": "#99cc00", "label": "+1"},
                    {"val": +2.0, "color": "#006600", "label": "+2"},
                ]
            },
            "precipitation": {
                "title": "Precipitation 2026",
                "unit": "mm",
                "min": 100,
                "max": 1000,
                "stops": [
                    {"val": 100, "color": "#ffff66", "label": "100"},
                    {"val": 300, "color": "#ccff33", "label": "300"},
                    {"val": 500, "color": "#33cc33", "label": "500"},
                    {"val": 700, "color": "#009966", "label": "700"},
                    {"val": 900, "color": "#006699", "label": "900"},
                    {"val": 1000, "color": "#003366", "label": "1000"},
                ]
            }
        },
        "lake_tana": LAKE_TANA_GEOMETRY,
        "basins_count": len(basins_payload),
        "basins": basins_payload,
        "aggregate_timeseries": AMHARA_MONTHLY_AGGREGATE,
    }


@matrix_router.get("/amhara/basin/{basin_id}")
def get_amhara_basin_detail(basin_id: str) -> Dict[str, Any]:
    """Retrieves specific basin telemetry, polygon coordinates, and monthly profile."""
    for b in AMHARA_BASINS:
        if b["basin_id"] == basin_id.lower():
            return {
                "basin": b,
                "lake_tana_proximity": (
                    "Immediate adjacent littoral zone"
                    if basin_id in ["tana_basin", "north_gojam", "angereb"]
                    else "Upstream / Downstream Blue Nile Basin"
                ),
            }
    raise HTTPException(status_code=404, detail=f"Basin '{basin_id}' not found in Amhara Region")
