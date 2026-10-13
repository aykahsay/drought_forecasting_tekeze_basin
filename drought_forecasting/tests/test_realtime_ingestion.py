"""
Tests for AI-DREWS Real-Time Telemetry & Stream Ingestion Engine
================================================================
Verifies:
  1. Sub-hourly AWS station packet ingestion & validation
  2. Legitimate zero-rainfall preservation in streaming data
  3. Rejection of unphysical sensor readings (thermodynamic bounds)
  4. Hot-cache buffer updates for sub-10ms UI queries
  5. GPM IMERG Early Run (~4h latency) quick-look ingestion
  6. Stream-to-reanalysis reconciliation when ERA5T arrives
  7. Real-time REST API endpoints
"""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from agriminds.app import create_app
from agriminds.climate.sources.realtime import (
    RealtimeStationIngestor,
    SatelliteQuickLookIngestor,
    StationTelemetryPacket,
    StreamToReanalysisReconciliation,
    get_realtime_station_ingestor,
    get_reconciliation_engine,
)
from agriminds.db.models import ClimateObservationRecord, get_session


@pytest.fixture
def test_client():
    app = create_app()
    return TestClient(app)


class TestRealtimeStationIngestion:

    def test_valid_station_packet_ingested(self):
        ingestor = RealtimeStationIngestor()
        packet = StationTelemetryPacket(
            station_id="STAT_MEKELLE_01",
            timestamp_utc=datetime.now(timezone.utc),
            latitude=13.468,
            longitude=39.533,
            elevation_m=2257.0,
            temperature_c=24.5,
            precipitation_mm=0.0,  # Legitimate zero during dry period
            relative_humidity_pct=42.0,
            wind_speed_ms=3.2,
            soil_moisture_pct=18.5,
            battery_volts=12.6,
        )

        res = ingestor.ingest_packet(packet)
        assert res["status"] == "INGESTED"
        assert res["observation_status"] == "PROVISIONAL_REALTIME"
        assert res["station_id"] == "STAT_MEKELLE_01"
        assert res["records_persisted"] >= 2  # temperature, precip, soil moisture

        # Verify hot cache updated
        cache = ingestor.get_latest_station_readings()
        assert any(s["station_id"] == "STAT_MEKELLE_01" for s in cache)

    def test_zero_rainfall_preserved_in_realtime_stream(self):
        """Rainfall = 0.0 mm must NOT be discarded or treated as NULL/missing."""
        ingestor = RealtimeStationIngestor()
        packet = StationTelemetryPacket(
            station_id="STAT_AXUM_01",
            timestamp_utc=datetime.now(timezone.utc),
            latitude=14.148,
            longitude=38.775,
            temperature_c=26.0,
            precipitation_mm=0.0,
        )
        res = ingestor.ingest_packet(packet)
        assert res["status"] == "INGESTED"

        # Check DB record
        db = get_session()
        try:
            obs = (
                db.query(ClimateObservationRecord)
                .filter(
                    ClimateObservationRecord.source_id == "ETH_STATIONS_REALTIME",
                    ClimateObservationRecord.variable_id == "station_precipitation",
                    ClimateObservationRecord.quality_note.like("%STAT_AXUM_01%"),
                )
                .first()
            )
            assert obs is not None
            assert obs.value == 0.0
            assert obs.quality_flag == "GOOD"
        finally:
            db.close()

    def test_unphysical_sensor_reading_rejected(self):
        """Temperature = 85.0°C violates thermodynamic limits for Tigray highlands."""
        ingestor = RealtimeStationIngestor()
        packet = StationTelemetryPacket(
            station_id="STAT_SHIRE_FAULTY",
            timestamp_utc=datetime.now(timezone.utc),
            latitude=14.103,
            longitude=38.283,
            temperature_c=85.0,  # Physically impossible
        )
        res = ingestor.ingest_packet(packet)
        assert res["status"] == "REJECTED"
        assert "physical bounds" in res["reason"]

    def test_stream_metrics_tracking(self):
        ingestor = RealtimeStationIngestor()
        metrics = ingestor.get_stream_metrics()
        assert "total_packets_received" in metrics
        assert "active_station_count" in metrics
        assert "stream_protocol" in metrics


class TestSatelliteQuickLook:

    def test_gpm_imerg_quicklook_pipeline(self):
        source = SatelliteQuickLookIngestor()
        assert source.source_name == "GPM_IMERG_EARLY"
        assert source.source_type == "satellite_quicklook"
        assert "4-hour" in source.temporal_resolution

        from datetime import date
        result = source.ingest(target_date=date.today())
        assert result.success is True
        assert result.records_stored > 0


class TestStreamToReanalysisReconciliation:

    def test_reconciliation_workflow(self):
        # 1. Ingest provisional station packet
        ingestor = get_realtime_station_ingestor()
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        packet = StationTelemetryPacket(
            station_id="STAT_ALAMATA_01",
            timestamp_utc=now,
            latitude=12.420,
            longitude=39.560,
            temperature_c=27.5,
            precipitation_mm=1.2,
        )
        ingestor.ingest_packet(packet)

        # 2. Run reconciliation engine
        reconciler = get_reconciliation_engine()
        res = reconciler.reconcile_date(date_str)
        assert res["status"] == "RECONCILED"
        assert res["provisional_records_reconciled"] >= 1
        assert "mean_bias_precipitation_mm" in res


class TestRealtimeAPIEndpoints:

    def test_realtime_station_ingest_endpoint(self, test_client):
        payload = {
            "station_id": "STAT_HAWZEN_MET",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "latitude": 13.980,
            "longitude": 39.430,
            "elevation_m": 2100.0,
            "temperature_c": 22.8,
            "precipitation_mm": 0.0,
            "relative_humidity_pct": 35.0,
            "soil_moisture_pct": 14.2,
            "battery_volts": 12.8,
        }
        response = test_client.post("/api/ingest/realtime/station", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "INGESTED"
        assert data["station_id"] == "STAT_HAWZEN_MET"

    def test_realtime_status_endpoint(self, test_client):
        response = test_client.get("/api/ingest/realtime/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "HEALTHY_STREAMING"
        assert "metrics" in data

    def test_realtime_stations_list_endpoint(self, test_client):
        response = test_client.get("/api/ingest/realtime/stations")
        assert response.status_code == 200
        data = response.json()
        assert "active_stations" in data

    def test_reconciliation_run_endpoint(self, test_client):
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        response = test_client.post(f"/api/ingest/reconciliation/run?target_date={today_str}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RECONCILED"
