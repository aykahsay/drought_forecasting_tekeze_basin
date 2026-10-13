"""
NOAA Climate Intelligence API Endpoints (§17)
==============================================
Provides REST endpoints for NOAA CPC, STAR, and CFSv2 operational feeds:
- RFE 2.0 precipitation estimates & cross-validation against ERA5T
- ONI & weekly Niño 3.4 SST teleconnection stream
- STAR Vegetation Health Index (VHI/VCI/TCI)
- CFSv2 dynamical seasonal ensemble guidance
"""
from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agriminds.climate.sources.noaa import (
    NOAACFSv2SeasonalSource,
    NOAACPCRainfallSource,
    NOAAONISource,
    NOAAVegetationHealthSource,
    get_noaa_suite,
)

router = APIRouter(prefix="/api/noaa", tags=["NOAA Climate Data"])


@router.get("/overview")
def get_noaa_overview():
    """
    Returns consolidated operational intelligence across all 4 NOAA climate feeds:
    - NOAA CPC Africa Rainfall Estimation (RFE 2.0)
    - NOAA CPC Oceanic Niño Index (ONI) & Weekly Niño 3.4 SST
    - NOAA STAR Vegetation Health Products (VHI/VCI/TCI)
    - NOAA NCEP CFSv2 Seasonal Dynamical Ensemble
    """
    suite = get_noaa_suite()
    return suite.get_full_overview()


@router.get("/rfe/latest")
def get_latest_rfe(
    target_date: Optional[str] = Query(None, description="ISO Date (YYYY-MM-DD)")
):
    """
    Retrieve latest NOAA CPC Africa Rainfall Estimation (RFE 2.0) daily observations.
    """
    suite = get_noaa_suite()
    dt = date.fromisoformat(target_date) if target_date else suite.rfe_source.get_latest_available_date()
    df = suite.rfe_source.extract(dt)
    return {
        "source": "NOAA_CPC_RFE",
        "target_date": dt.isoformat(),
        "resolution_deg": suite.rfe_source.spatial_resolution_deg,
        "records_count": len(df),
        "observations": df.to_dict(orient="records"),
    }


@router.get("/rfe/cross-validation/{woreda_id}")
def get_rfe_cross_validation(woreda_id: str):
    """
    Cross-validate NOAA RFE 2.0 satellite-gauge blended rainfall against
    ERA5T atmospheric reanalysis and CHIRPS for a specific woreda.
    Quantifies multi-source observational consistency.
    """
    suite = get_noaa_suite()
    return suite.rfe_source.get_comparison_with_era5t(woreda_id)


@router.get("/oni/stream")
def get_oni_stream():
    """
    Retrieve near-real-time NOAA CPC Oceanic Niño Index (ONI) and weekly Niño 3.4 SST.
    Bridges historical elnino.xlsx reference dataset to current conditions.
    """
    suite = get_noaa_suite()
    return suite.oni_source.get_live_teleconnection_state()


@router.get("/vhi/woreda/{woreda_id}")
def get_woreda_vhi(woreda_id: str):
    """
    Retrieve NOAA STAR Vegetation Health Index (VHI), Vegetation Condition Index (VCI),
    and Thermal Condition Index (TCI) at 4 km resolution for a specific woreda.
    """
    suite = get_noaa_suite()
    return suite.vhi_source.get_woreda_vegetation_health(woreda_id)


@router.get("/cfsv2/outlook")
def get_cfsv2_outlook():
    """
    Retrieve NOAA Climate Forecast System (CFSv2) sub-seasonal to seasonal ensemble outlook.
    Provides physical dynamical precipitation and temperature anomaly guidance for 1–3 months.
    """
    suite = get_noaa_suite()
    return suite.cfsv2_source.get_multi_horizon_guidance()


@router.post("/ingest/{source_id}")
def trigger_noaa_ingestion(source_id: str):
    """
    Trigger on-demand ingestion run for a specific NOAA source.
    Allowed sources: NOAA_CPC_RFE, NOAA_CPC_ONI, NOAA_STAR_VHI, NOAA_CFSv2_OUTLOOK.
    """
    suite = get_noaa_suite()
    src_map = {
        "NOAA_CPC_RFE": suite.rfe_source,
        "NOAA_CPC_ONI": suite.oni_source,
        "NOAA_STAR_VHI": suite.vhi_source,
        "NOAA_CFSv2_OUTLOOK": suite.cfsv2_source,
    }
    src = src_map.get(source_id.upper())
    if not src:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown NOAA source: {source_id}. Allowed: {list(src_map.keys())}",
        )

    res = src.ingest()
    return {
        "status": "SUCCESS" if res.success else "FAILED",
        "source_name": res.source_name,
        "target_date": res.target_date.isoformat(),
        "records_stored": res.records_stored,
        "duration_seconds": res.duration_seconds,
    }
