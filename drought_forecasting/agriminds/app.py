"""
FastAPI Application Factory
============================
Creates and configures the AI-DREWS backend application.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from agriminds.api.routes.climate import (
    climate_router,
    drought_router,
    enso_router,
)
from agriminds.api.routes.dashboard_api import router as system_router
from agriminds.api.routes.abergelle_tekeze_and_kafka import router as abergelle_kafka_router
from agriminds.api.routes.era5 import router as era5_router
from agriminds.api.routes.noaa_api import router as noaa_router
from agriminds.api.routes.climate_matrix import matrix_router
from agriminds.api.routes.hierarchy_api import hierarchy_router
from agriminds.api.routes.ocean_api import router as ocean_router
from agriminds.api.routes.inference_router import router as inference_router
from agriminds.climate.enso import load_elnino_dataset
from agriminds.config import get_settings
from agriminds.db.models import init_db
from agriminds.ingestion.scheduler import get_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    logger.info(f"Starting AI-DREWS ({settings.app_env})")

    # 1. Initialise database tables (idempotent)
    init_db()
    logger.info("Database tables initialised.")

    try:
        from agriminds.db.seed import seed_database
        seed_database()
        logger.info("Database reference tables seeded.")
    except Exception as exc:
        logger.warning(f"Database seed notice: {exc}")

    # 2. Load historical ENSO dataset (idempotent — does not overwrite)
    if settings.elnino_dataset_path.exists():
        n = load_elnino_dataset()
        logger.info(f"ENSO dataset: {n} records loaded.")
    else:
        logger.warning(
            f"El Niño dataset not found at {settings.elnino_dataset_path}. "
            "Place elnino.xlsx in the project root."
        )

    # 3. Start ERA5T ingestion scheduler
    scheduler = get_scheduler()
    scheduler.start()

    yield  # Application is running

    # 4. Graceful shutdown
    scheduler.stop()
    logger.info("AI-DREWS shutdown complete.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Ethiopia Drought Early Warning System (AI-DREWS)",
        description=(
            "National Drought Early Warning System for Ethiopia across all federal regional states "
            "(Amhara, Tigray, Oromia, Somali, Afar, Sidama) and agro-ecological climate zones (AEZs).\n\n"
            "Integrates ERA5T near-real-time atmospheric reanalysis data (~5-day latency), "
            "NOAA operational feeds (RFE 2.0, ONI, STAR VHI), and the historical El Niño/ENSO reference dataset "
            "for nationwide agricultural drought monitoring and probabilistic prediction.\n\n"
            "**Data source distinction:**\n"
            "- `ERA5T`: Near-real-time atmospheric reanalysis (observation-type)\n"
            "- `NOAA`: Satellite precipitation (RFE 2.0), Oceanic Niño Index (ONI), and 4km Vegetation Health Index (VHI)\n"
            "- `elnino.xlsx`: Historical ENSO/climate reference dataset\n"
            "- `Derived`: Standardized precipitation (SPI), evaporative stress (SPEI), Sc-PDSI\n"
            "- `Model output`: Drought probability and risk ranking (probabilistic predictions — not observations)\n"
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(era5_router)
    app.include_router(climate_router)
    app.include_router(drought_router)
    app.include_router(enso_router)
    app.include_router(system_router)
    app.include_router(abergelle_kafka_router)
    app.include_router(noaa_router)
    app.include_router(matrix_router)
    app.include_router(hierarchy_router)
    app.include_router(ocean_router)
    app.include_router(inference_router)

    # Mount dashboard UI and data artifacts
    from pathlib import Path
    dashboard_dir = Path(__file__).resolve().parent.parent / "dashboard"
    data_dir = Path(__file__).resolve().parent.parent / "data"
    from fastapi.staticfiles import StaticFiles
    if dashboard_dir.exists():
        app.mount("/dashboard", StaticFiles(directory=str(dashboard_dir), html=True), name="dashboard")
    if data_dir.exists():
        app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

    @app.get("/")
    def root():
        return {
            "name": "Ethiopia Drought Early Warning System (AI-DREWS)",
            "acronym": "AI-DREWS",
            "country": "Ethiopia",
            "version": "1.0.0",
            "description": "National Multi-Source Climate Intelligence & Probabilistic Drought Early Warning System for Ethiopia",
            "era5t": (
                "Near-real-time atmospheric reanalysis data "
                "with approximately a 5-day latency."
            ),
            "endpoints": {
                "overview_ethiopia": "/api/overview/ethiopia",
                "regions": "/api/regions",
                "region_detail": "/api/regions/{region_id}",
                "climate_matrix_amhara": "/api/matrix/amhara",
                "woredas": "/api/woredas",
                "woreda_detail": "/api/woredas/{woreda_id}",
                "woreda_forecast": "/api/woredas/{woreda_id}/forecast",
                "causal_story": "/api/teleconnections/story",
                "ablation_experiment": "/api/experiments/ablation",
                "sources_registry": "/api/sources/registry",
                "era5_status": "/api/era5/status",
                "era5_latest": "/api/era5/latest",
                "era5_coverage": "/api/era5/coverage",
                "era5_variables": "/api/era5/variables",
                "era5_ingest": "POST /api/era5/ingest",
                "climate_features": "/api/climate/features",
                "drought_indices": "/api/drought/indices",
                "drought_risk": "/api/drought/risk",
                "enso_status": "/api/enso/status",
                "enso_historical": "/api/enso/historical",
                "docs": "/docs",
            },
        }

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
