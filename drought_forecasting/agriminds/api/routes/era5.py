"""
ERA5T API Routes (Requirement §17)
====================================
GET  /api/era5/status      — ERA5T ingestion status panel
GET  /api/era5/latest      — Latest available ERA5T date
GET  /api/era5/coverage    — Spatial and temporal coverage
GET  /api/era5/variables   — Available variables + units
POST /api/era5/ingest      — Trigger manual ingestion

NOTE: CDS API credentials (CDS_API_KEY) are only present on the server.
They are NEVER returned in any API response.
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agriminds.climate.sources.era5t import ERA5TSource, ERA5T_VARIABLE_METADATA
from agriminds.db.models import ERA5TIngestionLog, IngestionStatus, get_db
from agriminds.ingestion.scheduler import get_scheduler

router = APIRouter(prefix="/api/era5", tags=["ERA5T"])
_source = ERA5TSource()


# ────────────────────────────────────────────────────────────────────────────
# Schemas
# ────────────────────────────────────────────────────────────────────────────
class IngestRequest(BaseModel):
    target_date: date
    variables: Optional[list[str]] = None
    bbox: Optional[list[float]] = None  # [North, West, South, East]


# ────────────────────────────────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────────────────────────────────

@router.get("/status")
def era5t_status():
    """
    ERA5T status panel for the AI-DREWS dashboard.

    Returns ingestion health, latest date, variable list, and the latency note:
    'ERA5T is a near-real-time atmospheric reanalysis product with approximately
    a 5-day latency.'
    """
    status = _source.get_status()
    health = get_scheduler().get_health()
    return {**status, "ingestion_health": health}


@router.get("/latest")
def era5t_latest(db: Session = Depends(get_db)):
    """Return the latest date for which ERA5T data has been successfully ingested."""
    log = (
        db.query(ERA5TIngestionLog)
        .filter(ERA5TIngestionLog.status == IngestionStatus.COMPLETE)
        .order_by(ERA5TIngestionLog.target_date.desc())
        .first()
    )
    if not log:
        return {
            "latest_ingested_date": None,
            "message": "No ERA5T data has been ingested yet.",
        }
    return {
        "latest_ingested_date": log.target_date,
        "records": log.records_stored,
        "ingested_at": log.completed_at.isoformat() if log.completed_at else None,
    }


@router.get("/coverage")
def era5t_coverage(db: Session = Depends(get_db)):
    """
    Return the temporal and spatial coverage of ingested ERA5T data.
    """
    from agriminds.config import get_settings
    settings = get_settings()

    logs = (
        db.query(ERA5TIngestionLog)
        .filter(ERA5TIngestionLog.status == IngestionStatus.COMPLETE)
        .order_by(ERA5TIngestionLog.target_date)
        .all()
    )

    dates = [l.target_date for l in logs]
    return {
        "temporal_coverage": {
            "start": dates[0] if dates else None,
            "end": dates[-1] if dates else None,
            "total_days": len(dates),
            "dates": dates,
        },
        "spatial_coverage": {
            "region": "Ethiopia (National Grid)",
            "bbox": {
                "north": settings.era5_bbox_north,
                "south": settings.era5_bbox_south,
                "west": settings.era5_bbox_west,
                "east": settings.era5_bbox_east,
            },
            "coordinate_system": "WGS84 / EPSG:4326",
            "grid_resolution": "0.25° × 0.25° (~28 km)",
            "expansion_plan": "Ethiopia (National: Amhara, Tigray, Oromia, Somali, Afar, Sidama) → East Africa (IGAD/ICPAC)",
        },
    }


@router.get("/variables")
def era5t_variables():
    """
    Return all supported ERA5T variables with their units and descriptions.
    Units are documented for every variable (Requirement §18).
    """
    return {
        "variables": ERA5T_VARIABLE_METADATA,
        "total": len(ERA5T_VARIABLE_METADATA),
        "unit_note": (
            "Units are as provided by the Copernicus CDS API. "
            "Precipitation is in m/hour (accumulated). "
            "Temperatures are in Kelvin. "
            "Wind components are in m/s."
        ),
    }


@router.post("/ingest")
def trigger_ingest(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger a manual ERA5T ingestion for a specific date.
    The ingestion runs in the background and is idempotent.
    """
    if not _source.is_available():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "CDS API not configured.",
                "action": "Set CDS_API_URL and CDS_API_KEY in your .env file.",
            },
        )

    # Validate date (ERA5T ~5-day latency)
    latest_available = date.today() - timedelta(days=5)
    if request.target_date > latest_available:
        raise HTTPException(
            status_code=422,
            detail={
                "error": (
                    f"ERA5T data is not yet available for {request.target_date}. "
                    f"ERA5T has approximately a 5-day latency. "
                    f"Latest estimated available date: {latest_available}"
                )
            },
        )

    background_tasks.add_task(
        _source.ingest,
        request.target_date,
        request.variables,
        request.bbox,
    )

    return {
        "message": f"ERA5T ingestion queued for {request.target_date}.",
        "target_date": request.target_date.isoformat(),
        "status": "queued",
        "note": "Check /api/era5/status for progress.",
    }


@router.get("/ingestion-log")
def ingestion_log(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Return recent ERA5T ingestion log entries."""
    logs = (
        db.query(ERA5TIngestionLog)
        .order_by(ERA5TIngestionLog.started_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "count": len(logs),
        "log": [
            {
                "id": l.id,
                "date": l.target_date,
                "status": l.status.value if l.status else None,
                "records_stored": l.records_stored,
                "retry_count": l.retry_count,
                "error": l.error_message,
                "started_at": l.started_at.isoformat() if l.started_at else None,
                "completed_at": l.completed_at.isoformat() if l.completed_at else None,
            }
            for l in logs
        ],
    }
