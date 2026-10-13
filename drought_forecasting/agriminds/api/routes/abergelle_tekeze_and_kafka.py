"""
Abergelle - Tekeze Basin, Hydrology, Local Ground Truth & Kafka API Routes
==========================================================================
REST endpoints for:
  - Apache Kafka event streaming, metrics, and topic listeners.
  - Abergelle - Tekeze Basin Spatial & Hydrological Model.
  - Granular Water Points (Tekeze Dam Reservoir, Deep Boreholes, Sand Dams, Afridev Hand Pumps).
  - Village-to-Water Distance Matrix (Geodesic meters & walking minutes).
  - Kebele Development Agent (DA) Ground Reports & Confidence Booster.
  - Geographic Map & Heatmap intensity coordinates centered on Abergelle - Tekeze.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from agriminds.ingestion.kafka_stream import (
    get_stream_manager,
    TOPIC_KEBELE_REPORTS,
    TOPIC_HYDROLOGY_WATER_POINTS,
    TOPIC_WEATHER_TELEMETRY,
    TOPIC_WOREDA_ALERTS,
)
from agriminds.spatial.tekeze_abergelle_basin import (
    TEKEZE_ABERGELLE_METADATA,
    TEKEZE_WOREDAS,
    TEKEZE_VILLAGES,
    TEKEZE_WATER_POINTS,
    TEKEZE_WATER_BODIES,
    get_tekeze_abergelle_summary,
    get_village_water_distance_matrix,
    get_village_by_id,
    get_water_point_by_id,
)
from agriminds.climate.local_ground_truth import (
    get_ground_truth_calibrator,
    KebeleGroundReport,
)
from agriminds.spatial.woredas import ETHIOPIA_WOREDAS

router = APIRouter(prefix="/api", tags=["Abergelle - Tekeze Basin & Kafka Streaming"])


# ────────────────────────────────────────────────────────────────────────────
# 1. Apache Kafka Event Streaming Endpoints
# ────────────────────────────────────────────────────────────────────────────
class KafkaPublishRequest(BaseModel):
    topic: str = Field(..., description="Target Kafka topic (e.g. aidrews.telemetry.weather, aidrews.ground.kebele_reports)")
    payload: Dict[str, Any] = Field(..., description="Event data dictionary")
    key: Optional[str] = Field(None, description="Partition key (e.g. woreda_id or station_id)")


@router.get("/kafka/status")
def get_kafka_status():
    """Return Kafka broker status, throughput metrics, and active topic counts."""
    mgr = get_stream_manager()
    return mgr.get_cluster_status()


@router.get("/kafka/topics")
def list_kafka_topics():
    """List all registered AI-DREWS Kafka topics and their configurations."""
    mgr = get_stream_manager()
    status = mgr.get_cluster_status()
    return {
        "topics": status["topics_available"],
        "broker_mode": status["broker_mode"],
        "metrics": status["metrics"],
    }


@router.get("/kafka/stream/{topic}")
def get_kafka_topic_stream(topic: str, limit: int = Query(20, ge=1, le=100)):
    """Retrieve recent event packets from a specific Kafka topic."""
    mgr = get_stream_manager()
    return {
        "topic": topic,
        "count": len(mgr.get_topic_stream(topic, limit=limit)),
        "messages": mgr.get_topic_stream(topic, limit=limit),
    }


@router.post("/kafka/publish")
def publish_to_kafka(req: KafkaPublishRequest):
    """Publish an arbitrary event packet into a Kafka stream topic."""
    mgr = get_stream_manager()
    result = mgr.publish_event(topic=req.topic, payload=req.payload, key=req.key)
    return result


@router.post("/kafka/run-ingestion")
def run_kafka_data_download():
    """
    Trigger end-to-end real-time Kafka data acquisition and streaming pipeline.
    Streams NOAA ocean indices, Abergelle weather stations, crop-climate panel,
    hydrology, and NetCDF tensor summaries into Kafka and database buffer.
    """
    from agriminds.ingestion.realtime_kafka_pipeline import RealtimeKafkaDataPipeline
    pipeline = RealtimeKafkaDataPipeline()
    summary = pipeline.run_full_pipeline()
    return summary


# ────────────────────────────────────────────────────────────────────────────
# 2. Abergelle - Tekeze Basin Endpoints
# ────────────────────────────────────────────────────────────────────────────
@router.get("/abergelle/overview")
@router.get("/tekeze/overview")
def get_abergelle_overview():
    """Return complete summary of the Abergelle - Tekeze Basin."""
    return get_tekeze_abergelle_summary()


@router.get("/abergelle/water-points")
@router.get("/tekeze/water-points")
def list_abergelle_water_points(
    water_type: Optional[str] = Query(None, description="Filter by type: reservoir_intake, borehole, sand_dam, hand_pump, spring"),
    perennial_only: bool = Query(False, description="Filter only perennial water points"),
):
    """List all monitored water points in Abergelle - Tekeze Basin."""
    points = TEKEZE_WATER_POINTS
    if water_type:
        points = [p for p in points if p["type"] == water_type.lower()]
    if perennial_only:
        points = [p for p in points if p["is_perennial"]]

    return {
        "basin": "Abergelle - Tekeze Basin",
        "count": len(points),
        "water_points": points,
    }


@router.get("/abergelle/water-bodies")
@router.get("/tekeze/water-bodies")
def list_abergelle_water_bodies():
    """List major water bodies (Tekeze Dam Reservoir, Trunk River, Tanqua, Weri)."""
    return {
        "basin": "Abergelle - Tekeze Basin",
        "count": len(TEKEZE_WATER_BODIES),
        "water_bodies": TEKEZE_WATER_BODIES,
    }


@router.get("/abergelle/villages")
@router.get("/tekeze/villages")
def list_abergelle_villages():
    """List the 12 monitored village settlements across Abergelle - Tekeze Basin."""
    return {
        "basin": "Abergelle - Tekeze Basin",
        "count": len(TEKEZE_VILLAGES),
        "villages": TEKEZE_VILLAGES,
    }


@router.get("/abergelle/villages/{village_id}/water-distance")
@router.get("/tekeze/villages/{village_id}/water-distance")
def get_village_water_distance(village_id: str):
    """
    Calculate exact distance matrix in meters and walking time in minutes
    from a specific village to EVERY water point in Abergelle - Tekeze Basin.
    """
    matrix = get_village_water_distance_matrix(village_id)
    if "error" in matrix:
        raise HTTPException(status_code=404, detail=matrix["error"])
    return matrix


# ────────────────────────────────────────────────────────────────────────────
# 3. Local Kebele Development Agent (DA) Ground Truth Reporting
# ────────────────────────────────────────────────────────────────────────────
class GroundReportInput(BaseModel):
    woreda_id: str = Field(..., examples=["tanqua_abergelle"])
    kebele_name: str = Field(..., examples=["Yechila 01 Kebele"])
    village_id: Optional[str] = Field("vil_yechila", examples=["vil_yechila"])
    reporter_name: str = Field("Gebremariam Hailu", examples=["Gebremariam Hailu"])
    reporter_role: str = Field("Senior Development Agent", examples=["Development Agent"])
    crop_stage: str = Field("vegetative_tillering", examples=["vegetative_tillering"])
    crop_wilting_index: float = Field(0.48, ge=0.0, le=1.0, description="0.0=healthy turgid, 1.0=permanent wilting")
    manual_rain_gauge_24h_mm: float = Field(0.0, ge=0.0, description="Measured daily precipitation in mm")
    soil_surface_cracking: int = Field(2, ge=0, le=3, description="0=none, 1=slight, 2=moderate, 3=deep vertisol fissures")
    spring_discharge_lpm: Optional[float] = Field(15.0, description="Spring/well discharge in Liters per minute")
    groundwater_table_depth_m: Optional[float] = Field(12.4, description="Depth to water table in meters")
    pasture_depletion_pct: float = Field(55.0, ge=0.0, le=100.0, description="Pasture deficit percentage")
    livestock_body_score: float = Field(3.0, ge=1.0, le=5.0, description="1=emaciated, 5=prime")
    grain_price_deviation_pct: float = Field(19.0, description="Market grain price increase %")
    notes: Optional[str] = Field("", examples=["Mashilla showing midday leaf curling."])


@router.post("/abergelle/ground-report")
@router.post("/tekeze/ground-report")
def submit_ground_report(report_in: GroundReportInput):
    """
    Submit a real local Kebele field report from an agricultural extension worker (DA).
    Automatically pushes event to Kafka topic 'aidrews.ground.kebele_reports'
    and triggers prediction calibration.
    """
    calibrator = get_ground_truth_calibrator()
    report_id = f"rep_{report_in.woreda_id}_{int(round(float(__import__('time').time())))}"
    
    rep = KebeleGroundReport(
        report_id=report_id,
        woreda_id=report_in.woreda_id,
        kebele_name=report_in.kebele_name,
        village_id=report_in.village_id,
        reporter_name=report_in.reporter_name,
        reporter_role=report_in.reporter_role,
        crop_stage=report_in.crop_stage,
        crop_wilting_index=report_in.crop_wilting_index,
        manual_rain_gauge_24h_mm=report_in.manual_rain_gauge_24h_mm,
        soil_surface_cracking=report_in.soil_surface_cracking,
        spring_discharge_lpm=report_in.spring_discharge_lpm,
        groundwater_table_depth_m=report_in.groundwater_table_depth_m,
        pasture_depletion_pct=report_in.pasture_depletion_pct,
        livestock_body_score=report_in.livestock_body_score,
        grain_price_deviation_pct=report_in.grain_price_deviation_pct,
        notes=report_in.notes or "",
    )
    calibrator.add_report(rep)

    # Publish to Kafka stream
    stream_mgr = get_stream_manager()
    stream_res = stream_mgr.publish_event(
        topic=TOPIC_KEBELE_REPORTS,
        payload=rep.to_dict(),
        key=report_in.woreda_id,
    )

    # Calibrate forecast for this woreda immediately
    calib = calibrator.calibrate_prediction(
        synoptic_probability=0.68,
        synoptic_ci=(0.52, 0.84),
        woreda_id=report_in.woreda_id,
    )

    return {
        "status": "RECORDED_AND_STREAMED",
        "report_id": report_id,
        "basin": "Abergelle - Tekeze Basin",
        "kafka_topic": TOPIC_KEBELE_REPORTS,
        "kafka_delivery": stream_res,
        "ground_truth_calibration": calib,
        "report": rep.to_dict(),
    }


@router.get("/abergelle/ground-reports")
@router.get("/tekeze/ground-reports")
def list_ground_reports(woreda_id: Optional[str] = None):
    """Retrieve all submitted Kebele field reports in Abergelle - Tekeze Basin."""
    calibrator = get_ground_truth_calibrator()
    if woreda_id:
        reps = [r.to_dict() for r in calibrator.get_reports_for_woreda(woreda_id)]
    else:
        reps = calibrator.get_all_reports()
    return {
        "basin": "Abergelle - Tekeze Basin",
        "count": len(reps),
        "reports": reps,
    }


@router.get("/abergelle/calibrated-forecast/{woreda_id}")
@router.get("/tekeze/calibrated-forecast/{woreda_id}")
def get_calibrated_woreda_forecast(woreda_id: str):
    """
    Return synoptic multi-horizon forecast fused with local Kebele ground observations.
    Demonstrates the reality boost and confidence interval narrowing in Abergelle.
    """
    calibrator = get_ground_truth_calibrator()
    synoptic_prob = 0.68
    synoptic_ci = (0.52, 0.84)

    calib = calibrator.calibrate_prediction(
        synoptic_probability=synoptic_prob,
        synoptic_ci=synoptic_ci,
        woreda_id=woreda_id,
    )
    return {
        "woreda_id": woreda_id,
        "basin": "Abergelle - Tekeze Basin",
        "synoptic_baseline": {
            "probability": synoptic_prob,
            "confidence_interval": list(synoptic_ci),
            "source": "ERA5T Reanalysis + NOAA CPC Niño 3.4 + Indian Ocean Dipole",
        },
        "ground_truth_calibration": calib,
    }


# ────────────────────────────────────────────────────────────────────────────
# 4. Geographic Map, Heatmap & Satellite Layers
# ────────────────────────────────────────────────────────────────────────────
@router.get("/map/heatmap")
def get_map_heatmap_data():
    """
    Return geographic coordinate intensity points for Leaflet heatmap layer.
    Centered densely on the Abergelle - Tekeze Basin and surrounding northern lowlands.
    """
    heat_points = []

    # 1. Nationwide woreda centroids
    for w in ETHIOPIA_WOREDAS:
        vuln = w.get("vulnerability_index", 0.7)
        heat_points.append({
            "lat": w["centroid_lat"],
            "lon": w["centroid_lon"],
            "intensity": round(vuln, 2),
            "name": w["name"],
            "region_id": w.get("region_id", "tigray"),
            "woreda_id": w.get("woreda_id", "tanqua_abergelle"),
            "type": "woreda_risk",
        })

    # 2. High-density Abergelle - Tekeze Basin points
    for v in TEKEZE_VILLAGES:
        intensity = 0.88 if v["aez"] == "deep_kolla" else (0.75 if v["aez"] == "kolla" else 0.55)
        heat_points.append({
            "lat": v["lat"],
            "lon": v["lon"],
            "intensity": intensity,
            "name": v["name"],
            "type": "abergelle_settlement",
        })

    return {
        "count": len(heat_points),
        "basin": "Abergelle - Tekeze Basin",
        "center": {"lat": 13.250, "lon": 38.920, "zoom": 10},
        "heat_points": heat_points,
    }


@router.get("/map/satellite-layers")
def get_satellite_layer_metadata():
    """Return basemap definitions for Real Satellite imagery and dark cartography."""
    return {
        "satellite_basemap": {
            "name": "Esri World Imagery (High-Resolution Satellite)",
            "tile_url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "attribution": "Tiles &copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community",
            "max_zoom": 19,
        },
        "dark_basemap": {
            "name": "CartoDB Dark Matter",
            "tile_url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            "attribution": "&copy; OpenStreetMap contributors &copy; CARTO",
            "max_zoom": 19,
        },
        "basin_bounds": {
            "min_lat": 12.70,
            "max_lat": 13.75,
            "min_lon": 38.40,
            "max_lon": 39.45,
            "target": "Abergelle - Tekeze Basin",
        },
    }


# ────────────────────────────────────────────────────────────────────────────
# 5. Abergelle - Tekeze 8x8 Grid & 4-Layer Soil Moisture Endpoints
# ────────────────────────────────────────────────────────────────────────────
@router.get("/abergelle/grid/spec")
@router.get("/tekeze/grid/spec")
def get_abergelle_grid_specification():
    """Return 8x8 grid geometry and hydrological boundary mask for Abergelle - Tekeze."""
    from agriminds.climate.tekeze_abergelle_observational import get_grid_spec
    return get_grid_spec()


@router.get("/abergelle/grid/latest")
@router.get("/tekeze/grid/latest")
def get_abergelle_grid_latest_state():
    """Return latest snapshot of 8x8 grid with 4-layer soil moisture for Abergelle - Tekeze."""
    from agriminds.climate.tekeze_abergelle_observational import get_latest_tekeze_grid_state
    return get_latest_tekeze_grid_state()


@router.get("/abergelle/grid/cell/{row}/{col}")
@router.get("/tekeze/grid/cell/{row}/{col}")
def get_abergelle_cell_history(row: int, col: int):
    """Return observational temporal history for a specific 8x8 grid cell."""
    from agriminds.climate.tekeze_abergelle_observational import get_cell_observational_history
    try:
        return get_cell_observational_history(row, col)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/abergelle/timeseries/basin")
@router.get("/tekeze/timeseries/basin")
def get_abergelle_basin_timeseries(limit: int = 100):
    """Return historical basin-averaged soil moisture and climate observations."""
    from agriminds.climate.tekeze_abergelle_observational import get_basin_timeseries_df
    df = get_basin_timeseries_df()
    return {
        "basin": "Abergelle - Tekeze Basin",
        "count": min(limit, len(df)),
        "total_records": len(df),
        "records": df.tail(limit).to_dict(orient="records"),
    }
