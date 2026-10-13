"""
Multi-Ocean Teleconnection API Routes
======================================
REST endpoints exposing real observational intelligence from the Pacific,
Indian, and Atlantic Oceans, and their coupled impacts on Ethiopia's rainfall regimes.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from agriminds.climate.sources.ocean_teleconnections import get_multi_ocean_engine

router = APIRouter(prefix="/api/teleconnections", tags=["Multi-Ocean Teleconnections"])


@router.get("/oceans")
def get_multi_ocean_overview():
    """
    Comprehensive real observational state across Pacific, Indian, and Atlantic oceans.
    Includes current index values, phases, and coupled drought risk assessment.
    """
    engine = get_multi_ocean_engine()
    return engine.get_latest_ocean_intelligence()


@router.get("/indian")
def get_indian_ocean_intelligence():
    """
    Real-time Indian Ocean Dipole (DMI) observations and Belg/Gu moisture impact.
    Positive IOD enhances East African rains; Negative IOD suppresses precipitation.
    """
    engine = get_multi_ocean_engine()
    intel = engine.get_latest_ocean_intelligence()
    return {
        "ocean": "Indian Ocean",
        "data": intel["indian_ocean"],
        "regime_c_impact": intel["coupled_multi_ocean_assessment"]["regime_c_status"],
    }


@router.get("/atlantic")
def get_atlantic_ocean_intelligence():
    """
    Real-time Tropical Atlantic SST Gradient (TNA - TSA), AMO, and Kiremt monsoon moisture flow.
    Governs the low-level westerly monsoon transport from the Congo Basin into Northern Ethiopia & Abergelle - Tekeze Basin.
    """
    engine = get_multi_ocean_engine()
    intel = engine.get_latest_ocean_intelligence()
    return {
        "ocean": "Atlantic Ocean",
        "data": intel["atlantic_ocean"],
        "regime_a_impact": intel["coupled_multi_ocean_assessment"]["regime_a_status"],
    }


@router.get("/coupled-regimes")
def get_coupled_regimes_assessment():
    """
    Coupled multi-ocean early-warning synthesis across Ethiopia's 3 rainfall regimes:
      Regime A: Northern Highlands & Tekeze Lowlands (Abergelle, Wag Hemra, Tigray)
      Regime B: Western Escarpment (Gambella, Metekel)
      Regime C: Southern/Eastern Lowlands (Somali, Borena)
    """
    engine = get_multi_ocean_engine()
    intel = engine.get_latest_ocean_intelligence()
    return intel["coupled_multi_ocean_assessment"]


@router.post("/sync")
def sync_ocean_data(background_tasks: BackgroundTasks):
    """Trigger live background synchronization from NOAA PSL and CPC endpoints."""
    engine = get_multi_ocean_engine()
    background_tasks.add_task(engine.sync_all_oceans)
    return {
        "status": "ACCEPTED",
        "message": "Initiated live synchronization from NOAA PSL (DMI, TNA, TSA, AMO) and CPC (ONI).",
    }
