"""
Compatibility layer redirecting to Abergelle - Tekeze Basin Spatial Model.
All Choke watershed references have been permanently pivoted to Abergelle - Tekeze Basin.
"""

from agriminds.spatial.tekeze_abergelle_basin import (
    TEKEZE_ABERGELLE_METADATA as CHOKYE_WATERSHED_METADATA,
    TEKEZE_WOREDAS as CHOKYE_WOREDAS,
    TEKEZE_VILLAGES as CHOKYE_VILLAGES,
    TEKEZE_WATER_POINTS as CHOKYE_WATER_POINTS,
    TEKEZE_WATER_BODIES as CHOKYE_WATER_BODIES,
    TEKEZE_ABERGELLE_METADATA,
    TEKEZE_WOREDAS,
    TEKEZE_VILLAGES,
    TEKEZE_WATER_POINTS,
    TEKEZE_WATER_BODIES,
    get_tekeze_abergelle_summary as get_chokye_watershed_summary,
    get_tekeze_abergelle_summary,
    get_village_water_distance_matrix,
    get_village_by_id,
    get_water_point_by_id,
    calculate_haversine_distance_m,
    calculate_walking_time_minutes,
)

__all__ = [
    "CHOKYE_WATERSHED_METADATA",
    "CHOKYE_WOREDAS",
    "CHOKYE_VILLAGES",
    "CHOKYE_WATER_POINTS",
    "CHOKYE_WATER_BODIES",
    "TEKEZE_ABERGELLE_METADATA",
    "TEKEZE_WOREDAS",
    "TEKEZE_VILLAGES",
    "TEKEZE_WATER_POINTS",
    "TEKEZE_WATER_BODIES",
    "get_chokye_watershed_summary",
    "get_tekeze_abergelle_summary",
    "get_village_water_distance_matrix",
    "get_village_by_id",
    "get_water_point_by_id",
    "calculate_haversine_distance_m",
    "calculate_walking_time_minutes",
]
