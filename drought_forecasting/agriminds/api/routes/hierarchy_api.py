"""
Ethiopia Multi-Tier Hierarchy REST API Router
=============================================
Provides seamless 4-tier drill-down endpoints across Ethiopia:
  1. National: /api/hierarchy/national
  2. Region:   /api/hierarchy/region/{region_id}
  3. Zone:     /api/hierarchy/zone/{zone_id}
  4. Woreda:   /api/hierarchy/woreda/{woreda_id}
  5. Kebele:   /api/hierarchy/kebele/{kebele_id}
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query

from agriminds.spatial.ethiopia_hierarchy import (
    ETHIOPIA_NATIONAL_REGIONS,
    ETHIOPIA_HIERARCHY_ZONES,
    ETHIOPIA_HIERARCHY_WOREDAS,
    ETHIOPIA_HIERARCHY_KEBELES,
    get_national_tier_matrix,
    get_regional_tier_matrix,
    get_zonal_tier_matrix,
    get_woreda_tier_matrix,
)

hierarchy_router = APIRouter(prefix="/api/hierarchy", tags=["Ethiopia National Hierarchy"])


@hierarchy_router.get("/overview")
def get_hierarchy_overview() -> Dict[str, Any]:
    """Returns total count and administrative scope of the 4-tier hierarchy."""
    total_zones = sum(len(z) for z in ETHIOPIA_HIERARCHY_ZONES.values())
    total_woredas = sum(len(w) for w in ETHIOPIA_HIERARCHY_WOREDAS.values())
    total_kebeles = sum(len(k) for k in ETHIOPIA_HIERARCHY_KEBELES.values())
    return {
        "status": "active",
        "country": "Ethiopia",
        "federal_system": "Federal Democratic Republic of Ethiopia",
        "tiers": {
            "tier_1_national": {"name": "National (Regions)", "count": len(ETHIOPIA_NATIONAL_REGIONS)},
            "tier_2_zones": {"name": "Administrative Zones", "count": total_zones},
            "tier_3_woredas": {"name": "Administrative Woredas", "count": total_woredas},
            "tier_4_kebeles": {"name": "Community Kebeles & Villages", "count": total_kebeles},
        },
        "supported_months": ["jun", "jul", "aug", "sep", "oct", "nov", "dec", "annual"],
    }


@hierarchy_router.get("/national")
def get_national_level(month: Optional[str] = Query(None, description="Temporal filter: jun..dec or annual")) -> Dict[str, Any]:
    """Level 1: National Ethiopia (All 13 Regions with 4-quadrant spatial & temporal metrics)."""
    return get_national_tier_matrix(month)


@hierarchy_router.get("/region/{region_id}")
def get_region_level(region_id: str, month: Optional[str] = Query(None, description="Temporal filter: jun..dec or annual")) -> Dict[str, Any]:
    """Level 2: Regional State (All Zones within the region)."""
    return get_regional_tier_matrix(region_id, month)


@hierarchy_router.get("/zone/{zone_id}")
def get_zone_level(zone_id: str, month: Optional[str] = Query(None, description="Temporal filter: jun..dec or annual")) -> Dict[str, Any]:
    """Level 3: Zonal Tier (All Woredas within the zone)."""
    return get_zonal_tier_matrix(zone_id, month)


@hierarchy_router.get("/woreda/{woreda_id}")
def get_woreda_level(woreda_id: str, month: Optional[str] = Query(None, description="Temporal filter: jun..dec or annual")) -> Dict[str, Any]:
    """Level 4: Woreda Tier (All Kebeles, Water Points, Springs, and Local Crop Wilting Ground Truth)."""
    return get_woreda_tier_matrix(woreda_id, month)


@hierarchy_router.get("/kebele/{kebele_id}")
def get_kebele_detail(kebele_id: str) -> Dict[str, Any]:
    """Kebele-specific ground truth inspection and water point telemetry."""
    for w_id, k_list in ETHIOPIA_HIERARCHY_KEBELES.items():
        found = next((k for k in k_list if k["kebele_id"] == kebele_id.lower()), None)
        if found:
            return {
                "kebele": found,
                "woreda_id": w_id,
                "status": "success"
            }
    raise HTTPException(status_code=404, detail=f"Kebele '{kebele_id}' not found")
