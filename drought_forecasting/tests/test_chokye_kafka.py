"""
Tests for Apache Kafka Streaming, Choke Watershed PoC & Local Ground Truth Calibrator
"""

import pytest
from fastapi.testclient import TestClient

from agriminds.app import create_app
from agriminds.ingestion.kafka_stream import (
    get_stream_manager,
    TOPIC_KEBELE_REPORTS,
    TOPIC_WEATHER_TELEMETRY,
    TOPIC_HYDROLOGY_WATER_POINTS,
    TOPIC_WOREDA_ALERTS,
)
from agriminds.spatial.chokye_watershed import (
    CHOKYE_WATERSHED_METADATA,
    CHOKYE_WOREDAS,
    CHOKYE_VILLAGES,
    CHOKYE_WATER_POINTS,
    CHOKYE_WATER_BODIES,
    calculate_haversine_distance_m,
    calculate_walking_time_minutes,
    get_village_water_distance_matrix,
    get_chokye_watershed_summary,
)
from agriminds.climate.local_ground_truth import (
    get_ground_truth_calibrator,
    KebeleGroundReport,
)


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


# ────────────────────────────────────────────────────────────────────────────
# 1. Kafka Event Streaming Tests
# ────────────────────────────────────────────────────────────────────────────
class TestKafkaStreaming:
    def test_kafka_stream_manager_init(self):
        mgr = get_stream_manager()
        assert mgr is not None
        status = mgr.get_cluster_status()
        assert status["kafka_enabled"] is True
        assert len(status["topics_available"]) >= 4

    def test_publish_and_retrieve_event(self):
        mgr = get_stream_manager()
        payload = {"station_id": "TEST_STATION", "temp_c": 21.5, "rainfall_mm": 0.0}
        res = mgr.publish_event(
            topic=TOPIC_WEATHER_TELEMETRY,
            payload=payload,
            key="test_station_key",
        )
        assert res["status"] == "PUBLISHED"
        assert res["topic"] == TOPIC_WEATHER_TELEMETRY

        recent = mgr.get_topic_stream(TOPIC_WEATHER_TELEMETRY, limit=5)
        assert len(recent) >= 1
        assert recent[0]["payload"]["station_id"] == "TEST_STATION"

    def test_subscriber_callback(self):
        mgr = get_stream_manager()
        received = []

        def callback(msg):
            received.append(msg.payload)

        mgr.subscribe(TOPIC_WOREDA_ALERTS, callback)
        mgr.publish_event(
            topic=TOPIC_WOREDA_ALERTS,
            payload={"woreda_id": "sinan", "alert_level": "WARNING"},
        )
        assert len(received) >= 1
        assert received[-1]["woreda_id"] == "sinan"


# ────────────────────────────────────────────────────────────────────────────
# 2. Choke Watershed Spatial & Hydrology Tests
# ────────────────────────────────────────────────────────────────────────────
class TestChokyeWatershed:
    def test_watershed_metadata(self):
        assert CHOKYE_WATERSHED_METADATA["summit_peak_m"] == 4088
        assert "Blue Nile" in CHOKYE_WATERSHED_METADATA["basin"]
        assert len(CHOKYE_WOREDAS) == 6
        assert len(CHOKYE_VILLAGES) >= 10
        assert len(CHOKYE_WATER_POINTS) >= 10
        assert len(CHOKYE_WATER_BODIES) >= 4

    def test_haversine_distance_calculation(self):
        # Distance between Meketem village and Meketem cold spring
        v = CHOKYE_VILLAGES[0]
        wp = CHOKYE_WATER_POINTS[0]
        dist_m = calculate_haversine_distance_m(v["lat"], v["lon"], wp["lat"], wp["lon"])
        assert 100 < dist_m < 1500  # realistic local walking distance

    def test_topographic_walking_time(self):
        time_flat = calculate_walking_time_minutes(distance_m=700, elevation_diff_m=0)
        time_steep = calculate_walking_time_minutes(distance_m=700, elevation_diff_m=150)
        assert time_steep > time_flat
        assert time_flat >= 8

    def test_village_water_distance_matrix(self):
        matrix = get_village_water_distance_matrix("vil_meketem")
        assert "village" in matrix
        assert matrix["village"]["name"] == "Meketem Village"
        assert "water_security" in matrix
        assert matrix["water_security"]["nearest_spring"] is not None
        assert "all_water_points_by_distance" in matrix
        assert len(matrix["all_water_points_by_distance"]) == len(CHOKYE_WATER_POINTS)

        # Distances must be sorted ascending
        dists = [wp["distance_m"] for wp in matrix["all_water_points_by_distance"]]
        assert dists == sorted(dists)

    def test_chokye_watershed_summary(self):
        summary = get_chokye_watershed_summary()
        assert summary["statistics"]["total_population_monitored"] > 10000
        assert summary["statistics"]["perennial_springs_count"] >= 5


# ────────────────────────────────────────────────────────────────────────────
# 3. Local Kebele Ground Truth & Calibration Tests
# ────────────────────────────────────────────────────────────────────────────
class TestLocalGroundTruthCalibrator:
    def test_prepopulated_reports_exist(self):
        calibrator = get_ground_truth_calibrator()
        reps = calibrator.get_all_reports()
        assert len(reps) >= 4

    def test_ground_truth_calibration_narrows_confidence_interval(self):
        calibrator = get_ground_truth_calibrator()
        synoptic_ci = (0.40, 0.76)  # width = 0.36
        calib = calibrator.calibrate_prediction(
            synoptic_probability=0.58,
            synoptic_ci=synoptic_ci,
            woreda_id="sinan",
        )
        assert calib["ground_reality_score_pct"] > 50.0
        assert calib["confidence_level"] == "VERY_HIGH_GROUND_VERIFIED"
        narrowed_ci = calib["calibrated_confidence_interval"]
        width_narrowed = narrowed_ci[1] - narrowed_ci[0]
        assert width_narrowed < (0.76 - 0.40)  # CI must narrow significantly!


# ────────────────────────────────────────────────────────────────────────────
# 4. REST API Endpoint Integration Tests
# ────────────────────────────────────────────────────────────────────────────
class TestChokyeAndKafkaAPI:
    def test_kafka_status_endpoint(self, client):
        r = client.get("/api/kafka/status")
        assert r.status_code == 200
        data = r.json()
        assert data["kafka_enabled"] is True
        assert "topics_available" in data

    def test_kafka_publish_endpoint(self, client):
        r = client.post(
            "/api/kafka/publish",
            json={
                "topic": TOPIC_WEATHER_TELEMETRY,
                "payload": {"rain_mm": 5.2, "location": "sinan"},
                "key": "sinan",
            },
        )
        assert r.status_code == 200
        assert r.json()["status"] == "PUBLISHED"

    def test_chokye_overview_endpoint(self, client):
        r = client.get("/api/chokye/overview")
        assert r.status_code == 200
        data = r.json()
        assert data["metadata"]["summit_peak_m"] == 4088
        assert len(data["water_points"]) >= 10

    def test_chokye_water_points_endpoint(self, client):
        r = client.get("/api/chokye/water-points?water_type=spring")
        assert r.status_code == 200
        data = r.json()
        assert all(wp["type"] == "spring" for wp in data["water_points"])

    def test_chokye_villages_endpoint(self, client):
        r = client.get("/api/chokye/villages")
        assert r.status_code == 200
        assert len(r.json()["villages"]) >= 10

    def test_village_water_distance_endpoint(self, client):
        r = client.get("/api/chokye/villages/vil_meketem/water-distance")
        assert r.status_code == 200
        data = r.json()
        assert data["village"]["village_id"] == "vil_meketem"
        assert len(data["all_water_points_by_distance"]) >= 10
        assert "nearest_spring" in data["water_security"]

    def test_submit_ground_report_endpoint(self, client):
        r = client.post(
            "/api/chokye/ground-report",
            json={
                "woreda_id": "sinan",
                "kebele_name": "Meketem Kebele",
                "reporter_name": "Tadesse Bekele",
                "crop_stage": "flowering",
                "crop_wilting_index": 0.40,
                "manual_rain_gauge_24h_mm": 0.0,
                "soil_surface_cracking": 2,
                "pasture_depletion_pct": 35.0,
                "livestock_body_score": 3.2,
                "grain_price_deviation_pct": 15.0,
                "notes": "Field inspection test.",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "RECORDED_AND_STREAMED"
        assert data["kafka_topic"] == TOPIC_KEBELE_REPORTS

    def test_calibrated_woreda_forecast_endpoint(self, client):
        r = client.get("/api/chokye/calibrated-forecast/sinan")
        assert r.status_code == 200
        data = r.json()
        assert "ground_truth_calibration" in data
        assert data["ground_truth_calibration"]["confidence_level"] == "VERY_HIGH_GROUND_VERIFIED"

    def test_map_heatmap_endpoint(self, client):
        r = client.get("/api/map/heatmap")
        assert r.status_code == 200
        data = r.json()
        assert len(data["heat_points"]) > 20
        assert "center" in data

    def test_satellite_layers_endpoint(self, client):
        r = client.get("/api/map/satellite-layers")
        assert r.status_code == 200
        data = r.json()
        assert "satellite_basemap" in data
        assert "arcgisonline" in data["satellite_basemap"]["tile_url"]
