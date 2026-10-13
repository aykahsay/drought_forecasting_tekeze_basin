"""
Unit and Integration Tests for Real-Time Kafka Data Acquisition Pipeline
========================================================================
Validates:
  1. Kafka Stream Manager topics and dual-mode broker status.
  2. NOAA Ocean teleconnections streaming and DB persistence.
  3. AWS weather station real-time telemetry streaming and quality validation.
  4. Agro-ecological crop-climate panel dataset streaming and CSV output.
  5. NetCDF archive verification and spatial tensor streaming.
  6. Hot tempo buffer (60-day) population.
  7. REST API endpoint `/api/kafka/run-ingestion`.
"""

import os
from pathlib import Path
import pytest
import pandas as pd
from fastapi.testclient import TestClient

from agriminds.app import create_app
from agriminds.ingestion.kafka_stream import (
    get_stream_manager,
    TOPIC_OCEAN_TELECONNECTIONS,
    TOPIC_WEATHER_TELEMETRY,
    TOPIC_CROP_CLIMATE,
    TOPIC_SPATIAL_NETCDF,
    TOPIC_SATELLITE_TILES,
    TOPIC_HYDROLOGY_WATER_POINTS,
    TOPIC_KEBELE_REPORTS,
    ALL_TOPICS,
)
from agriminds.ingestion.realtime_kafka_pipeline import RealtimeKafkaDataPipeline
from agriminds.db.models import OceanAtmosphereIndexRecord, ClimateObservationRecord, get_session


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


class TestRealtimeKafkaDataPipeline:
    def test_all_kafka_topics_registered(self):
        mgr = get_stream_manager()
        status = mgr.get_cluster_status()
        assert status["kafka_enabled"] is True
        for topic in [
            TOPIC_OCEAN_TELECONNECTIONS,
            TOPIC_WEATHER_TELEMETRY,
            TOPIC_CROP_CLIMATE,
            TOPIC_SPATIAL_NETCDF,
            TOPIC_SATELLITE_TILES,
            TOPIC_HYDROLOGY_WATER_POINTS,
            TOPIC_KEBELE_REPORTS,
        ]:
            assert topic in status["topics_available"]

    def test_stream_ocean_teleconnections(self):
        pipeline = RealtimeKafkaDataPipeline()
        res = pipeline.stream_ocean_teleconnections(throttle_ms=0)
        assert res["topic"] == TOPIC_OCEAN_TELECONNECTIONS
        assert res["published_count"] > 0
        assert res["throughput_msg_per_sec"] > 0

        # Verify database records
        db = get_session()
        try:
            nino_count = db.query(OceanAtmosphereIndexRecord).filter_by(index_name="Nino3.4").count()
            assert nino_count > 0
        finally:
            db.close()

    def test_stream_weather_telemetry(self):
        pipeline = RealtimeKafkaDataPipeline()
        res = pipeline.stream_weather_telemetry(days_history=3, throttle_ms=0)
        assert res["topic"] == TOPIC_WEATHER_TELEMETRY
        assert res["published_count"] >= 8 * 3  # stations * days

        recent = pipeline.mgr.get_topic_stream(TOPIC_WEATHER_TELEMETRY, limit=5)
        assert len(recent) > 0
        assert "station_id" in recent[0]["payload"]
        assert "temperature_c" in recent[0]["payload"]

    def test_stream_crop_climate_dataset(self):
        pipeline = RealtimeKafkaDataPipeline()
        res = pipeline.stream_crop_climate_dataset(throttle_ms=0)
        assert res["topic"] == TOPIC_CROP_CLIMATE
        assert res["published_count"] > 0

        clean_csv = Path("crop_ML/data/crop_climate_clean.csv")
        assert clean_csv.exists()
        df = pd.read_csv(clean_csv)
        assert len(df) >= 300
        for col in ["crop", "zone", "altitude_approx_m", "crop_yield_ton_ha", "enso_phase"]:
            assert col in df.columns

    def test_verify_and_stream_netcdf_archive(self):
        pipeline = RealtimeKafkaDataPipeline()
        res = pipeline.verify_and_stream_netcdf_archive(sample_frames=5)
        assert "file_path" in res
        assert res["time_slices"] >= 400
        assert "spatial_shape" in res["kafka_streaming"] or res["kafka_streaming"]["published_count"] > 0

    def test_populate_hot_tempo_buffer(self):
        pipeline = RealtimeKafkaDataPipeline()
        count = pipeline.populate_hot_tempo_buffer()
        assert count > 0

        import sqlite3
        conn = sqlite3.connect("data/tempo_buffer.db")
        cur = conn.cursor()
        actual = cur.execute("SELECT count(*) FROM recent_observations").fetchone()[0]
        conn.close()
        assert actual == count

    def test_run_full_pipeline(self):
        pipeline = RealtimeKafkaDataPipeline()
        summary = pipeline.run_full_pipeline()
        assert summary["status"] == "COMPLETED_SUCCESSFULLY"
        assert summary["total_events_published"] > 500
        assert summary["total_events_consumed"] > 500
        assert "noaa_teleconnections" in summary["datasets_ready_for_training"]
        assert "spatiotemporal_netcdf" in summary["datasets_ready_for_training"]
        assert "agro_ecological_crops" in summary["datasets_ready_for_training"]

    def test_api_kafka_run_ingestion(self, client):
        r = client.post("/api/kafka/run-ingestion")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "COMPLETED_SUCCESSFULLY"
        assert data["total_events_published"] > 100
        assert "datasets_ready_for_training" in data
