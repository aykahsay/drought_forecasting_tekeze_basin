"""
AI-DREWS Test Suite
====================
Tests for:
  - ENSO dataset loading (elnino.xlsx integrity)
  - ERA5T data validation
  - Feature engineering
  - API endpoints
  - Data source distinction

Usage:
    pytest tests/ -v
"""
import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Database setup (in-memory SQLite for tests) ───────────────────────────
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    from agriminds.db.models import Base
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ════════════════════════════════════════════════════════════════════════════
# 1. ENSO Dataset Tests
# ════════════════════════════════════════════════════════════════════════════

class TestENSODataset:
    """elnino.xlsx must be preserved exactly and loaded correctly."""

    def test_elnino_file_exists(self):
        """elnino.xlsx must be present and untouched."""
        path = Path("elnino.xlsx")
        assert path.exists(), "elnino.xlsx not found. Dataset must not be deleted."

    def test_elnino_has_correct_columns(self):
        """All required columns must be present."""
        df = pd.read_excel("elnino.xlsx", engine="openpyxl")
        required = [
            "Year",
            "Nino3.4-DJF", "Nino3.4-MAM", "Nino3.4-JJA", "Nino3.4-SON", "Nino3.4-annual",
            "P-DJF (m)", "P-MAM (m)", "P-JJA (m)", "P-SON (m)", "P-c (mm/mon)",
            "T-DJF (K)", "T-MAM (K)", "T-JJA (K)", "T-SON (K)", "T-annual (0C)",
            "Sc-PDSI",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_elnino_year_range(self):
        """Dataset must cover 1990 through recent years."""
        df = pd.read_excel("elnino.xlsx", engine="openpyxl")
        years = df["Year"].dropna().astype(int)
        assert years.min() <= 1990, "Expected data from 1990"
        assert years.max() >= 2020, "Expected data through at least 2020"

    def test_elnino_row_count(self):
        """Must have at least 30 years of data."""
        df = pd.read_excel("elnino.xlsx", engine="openpyxl")
        assert len(df) >= 30

    def test_elnino_not_modified_by_era5t(self):
        """ERA5T integration must never add columns to elnino.xlsx."""
        df = pd.read_excel("elnino.xlsx", engine="openpyxl")
        era5t_indicators = [
            "total_precipitation", "2m_temperature", "ERA5",
            "era5", "volumetric_soil"
        ]
        for col in df.columns:
            for indicator in era5t_indicators:
                assert indicator.lower() not in col.lower(), (
                    f"ERA5T column '{col}' found in elnino.xlsx. "
                    "ERA5T must NEVER be merged into the existing dataset."
                )


# ════════════════════════════════════════════════════════════════════════════
# 2. ENSO Classification Tests
# ════════════════════════════════════════════════════════════════════════════

class TestENSOClassification:
    def test_el_nino_detection(self):
        from agriminds.climate.enso import classify_enso_phase
        assert classify_enso_phase(1.5) == "El Niño"
        assert classify_enso_phase(0.5) == "El Niño"

    def test_la_nina_detection(self):
        from agriminds.climate.enso import classify_enso_phase
        assert classify_enso_phase(-1.2) == "La Niña"
        assert classify_enso_phase(-0.5) == "La Niña"

    def test_neutral_detection(self):
        from agriminds.climate.enso import classify_enso_phase
        assert classify_enso_phase(0.0) == "Neutral"
        assert classify_enso_phase(0.3) == "Neutral"

    def test_none_input(self):
        from agriminds.climate.enso import classify_enso_phase
        assert classify_enso_phase(None) == "Unknown"


# ════════════════════════════════════════════════════════════════════════════
# 3. PDSI Classification Tests  (documented thresholds)
# ════════════════════════════════════════════════════════════════════════════

class TestPDSIClassification:
    def test_normal(self):
        from agriminds.climate.features.engineering import classify_pdsi
        assert classify_pdsi(0.5) == "Normal"
        assert classify_pdsi(-0.9) == "Normal"

    def test_moderate_drought(self):
        from agriminds.climate.features.engineering import classify_pdsi
        assert classify_pdsi(-1.5) == "Moderate Drought"

    def test_severe_drought(self):
        from agriminds.climate.features.engineering import classify_pdsi
        assert classify_pdsi(-2.5) == "Severe Drought"

    def test_extreme_drought(self):
        from agriminds.climate.features.engineering import classify_pdsi
        assert classify_pdsi(-3.5) == "Extreme Drought"
        assert classify_pdsi(-3.0) == "Extreme Drought"


# ════════════════════════════════════════════════════════════════════════════
# 4. ERA5T Validation Tests
# ════════════════════════════════════════════════════════════════════════════

class TestERA5TValidation:
    def _make_df(self, n=10):
        return pd.DataFrame({
            "timestamp_utc": [datetime(2024, 1, 1, h, tzinfo=timezone.utc) for h in range(n)],
            "date": ["2024-01-01"] * n,
            "latitude": [13.5] * n,
            "longitude": [38.5] * n,
            "variable": ["2m_temperature"] * n,
            "value": [300.0 + i for i in range(n)],
            "unit": ["K"] * n,
        })

    def test_valid_data_passes(self):
        from agriminds.climate.validation import ERA5TValidator
        df = self._make_df()
        result = ERA5TValidator().validate(df)
        assert "is_valid" in result.columns
        assert result["is_valid"].all()

    def test_missing_values_flagged(self):
        from agriminds.climate.validation import ERA5TValidator
        df = self._make_df()
        df.loc[0, "value"] = None
        result = ERA5TValidator().validate(df)
        assert not result.loc[0, "is_valid"]

    def test_negative_precipitation_flagged(self):
        from agriminds.climate.validation import ERA5TValidator
        df = pd.DataFrame({
            "timestamp_utc": [datetime(2024,1,1,0,tzinfo=timezone.utc)],
            "date": ["2024-01-01"],
            "latitude": [13.5],
            "longitude": [38.5],
            "variable": ["total_precipitation"],
            "value": [-0.001],  # Invalid — precipitation cannot be negative
            "unit": ["m"],
        })
        result = ERA5TValidator().validate(df)
        assert not result.loc[0, "is_valid"]

    def test_impossible_temperature_flagged(self):
        from agriminds.climate.validation import ERA5TValidator
        df = pd.DataFrame({
            "timestamp_utc": [datetime(2024,1,1,0,tzinfo=timezone.utc)],
            "date": ["2024-01-01"],
            "latitude": [13.5],
            "longitude": [38.5],
            "variable": ["2m_temperature"],
            "value": [1000.0],  # Impossible temperature
            "unit": ["K"],
        })
        result = ERA5TValidator().validate(df)
        assert not result.loc[0, "is_valid"]

    def test_invalid_coordinates_flagged(self):
        from agriminds.climate.validation import ERA5TValidator
        df = pd.DataFrame({
            "timestamp_utc": [datetime(2024,1,1,0,tzinfo=timezone.utc)],
            "date": ["2024-01-01"],
            "latitude": [999.0],   # Invalid latitude
            "longitude": [38.5],
            "variable": ["2m_temperature"],
            "value": [300.0],
            "unit": ["K"],
        })
        result = ERA5TValidator().validate(df)
        assert not result.loc[0, "is_valid"]

    def test_duplicates_removed(self):
        from agriminds.climate.validation import ERA5TValidator
        df = self._make_df(5)
        # Duplicate the first row
        df_dup = pd.concat([df, df.iloc[:1]], ignore_index=True)
        result = ERA5TValidator().validate(df_dup)
        assert len(result) == len(df)  # Duplicate removed


# ════════════════════════════════════════════════════════════════════════════
# 5. SPI Computation Tests
# ════════════════════════════════════════════════════════════════════════════

class TestSPIEngine:
    def test_spi_output_shape(self):
        from agriminds.climate.features.engineering import SPIEngine
        monthly = pd.Series(
            np.random.gamma(2, 50, 60),  # 60 months of random precipitation
            index=pd.date_range("2019-01", periods=60, freq="ME"),
        )
        spi_engine = SPIEngine()
        result = spi_engine.compute(monthly)
        assert "spi_3" in result.columns
        assert "spi_6" in result.columns
        assert len(result) == len(monthly)

    def test_spi_insufficient_data(self):
        from agriminds.climate.features.engineering import SPIEngine
        monthly = pd.Series(
            [10.0] * 5,  # Only 5 months — too few
            index=pd.date_range("2024-01", periods=5, freq="ME"),
        )
        spi_engine = SPIEngine()
        result = spi_engine.compute(monthly)
        # Should return NaN values for insufficient data — not crash
        assert result is not None


# ════════════════════════════════════════════════════════════════════════════
# 6. ML Model Tests (time-series validation)
# ════════════════════════════════════════════════════════════════════════════

class TestDroughtModel:
    def _make_feature_df(self):
        """Create a synthetic feature DataFrame for model testing."""
        years = range(1990, 2026)
        rng = np.random.default_rng(42)
        records = []
        for y in years:
            records.append({
                "date": f"{y}-06-01",
                "nino34": rng.normal(0, 0.8),
                "rainfall_30d": rng.gamma(2, 50),
                "rainfall_90d": rng.gamma(2, 150),
                "rainfall_anomaly": rng.normal(0, 20),
                "rainfall_percentile": rng.uniform(0, 100),
                "temperature_mean": rng.normal(25, 3),
                "temperature_anomaly": rng.normal(0, 1),
                "soil_moisture_layer1": rng.uniform(0.1, 0.5),
                "soil_moisture_anomaly": rng.normal(0, 0.05),
                "spi_3": rng.normal(0, 1),
                "spi_6": rng.normal(0, 1),
                "spei_3": rng.normal(0, 1),
                "spei_6": rng.normal(0, 1),
                "sc_pdsi": rng.normal(-1, 1.5),
            })
        return pd.DataFrame(records)

    def test_chronological_split(self):
        """Training/validation/test split must be chronological."""
        from agriminds.ml.models import DroughtModelTrainer
        df = self._make_feature_df()
        trainer = DroughtModelTrainer()
        train, val, test = trainer.chronological_split(df)

        # Verify chronological order
        assert pd.to_datetime(train["date"]).max().year <= trainer.TRAIN_END_YEAR
        assert pd.to_datetime(val["date"]).max().year <= trainer.VAL_END_YEAR
        if not test.empty:
            assert pd.to_datetime(test["date"]).min().year > trainer.VAL_END_YEAR

    def test_prediction_labeled_as_model_output(self):
        """Predictions must be explicitly labeled as MODEL_PREDICTION."""
        from agriminds.ml.models import DroughtModelTrainer
        df = self._make_feature_df()
        trainer = DroughtModelTrainer()
        trainer.train_all_baselines(df)
        result = trainer.predict(df.iloc[-1].to_dict())
        assert result.get("prediction_type") == "MODEL_PREDICTION"

    def test_models_dont_shuffle_data(self):
        """Verify training data maintains chronological order."""
        from agriminds.ml.models import DroughtModelTrainer
        df = self._make_feature_df()
        trainer = DroughtModelTrainer()
        train, val, test = trainer.chronological_split(df)

        train_dates = pd.to_datetime(train["date"])
        assert list(train_dates) == sorted(train_dates), "Training data must be chronologically ordered."


# ════════════════════════════════════════════════════════════════════════════
# 7. API Endpoint Tests
# ════════════════════════════════════════════════════════════════════════════

class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        from agriminds.app import create_app
        app = create_app()
        return TestClient(app, raise_server_exceptions=False)

    def test_root_endpoint(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "AI-DREWS" in data["name"]
        assert "5-day latency" in data["era5t"]

    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_era5t_variables_endpoint(self, client):
        r = client.get("/api/era5/variables")
        assert r.status_code == 200
        data = r.json()
        assert "variables" in data
        assert "total_precipitation" in data["variables"]
        assert "unit" in data["variables"]["total_precipitation"]

    def test_era5t_status_endpoint(self, client):
        r = client.get("/api/era5/status")
        assert r.status_code == 200
        data = r.json()
        assert "source" in data
        assert "latency_note" in data
        # Must state ~5-day latency
        assert "5-day" in data["latency_note"]

    def test_enso_historical_endpoint(self, client):
        r = client.get("/api/enso/historical")
        assert r.status_code == 200
        data = r.json()
        assert data["source"] == "elnino.xlsx"
        assert data["data_type"] == "HISTORICAL_CLIMATE_REFERENCE"

    def test_drought_risk_labels_prediction(self, client):
        r = client.get("/api/drought/risk")
        assert r.status_code == 200
        data = r.json()
        # Must explicitly label as prediction
        assert "prediction_type" in data or "message" in data


# ════════════════════════════════════════════════════════════════════════════
# 8. Data Source Distinction Tests  (Requirement §21)
# ════════════════════════════════════════════════════════════════════════════

class TestDataSourceDistinction:
    """
    Verify the system correctly distinguishes between:
      - ERA5T: reanalysis/observation-type
      - elnino.xlsx: historical climate reference
      - Derived indicators: SPI, SPEI, anomalies
      - Model outputs: predictions
    """

    def test_era5t_source_type(self):
        from agriminds.climate.sources.era5t import ERA5TSource
        source = ERA5TSource()
        assert source.source_type == "reanalysis"

    def test_era5t_description_contains_five_day_latency(self):
        from agriminds.climate.sources.era5t import ERA5TSource
        source = ERA5TSource()
        assert "5-day" in source.description.lower() or "5-day" in source.latency_note

    def test_era5t_not_called_real_time(self):
        """ERA5T must NEVER be described as 'real-time' without 'near'."""
        from agriminds.climate.sources.era5t import ERA5TSource
        source = ERA5TSource()
        desc = source.description.lower()
        # Must say near-real-time, not just real-time
        if "real-time" in desc:
            assert "near-real-time" in desc, (
                "ERA5T description must say 'near-real-time', not 'real-time'"
            )

    def test_historical_dataset_type_label(self):
        """elnino.xlsx records must be labeled as HISTORICAL_CLIMATE_REFERENCE."""
        from agriminds.app import create_app
        from fastapi.testclient import TestClient
        client = TestClient(create_app(), raise_server_exceptions=False)
        r = client.get("/api/enso/historical")
        data = r.json()
        assert data.get("data_type") == "HISTORICAL_CLIMATE_REFERENCE"

    def test_ml_prediction_not_observation(self):
        """Model predictions must include prediction_type = MODEL_PREDICTION."""
        from agriminds.ml.models import DroughtModelTrainer
        rng = np.random.default_rng(42)
        features = {
            "nino34": 1.2, "rainfall_30d": 45.0, "rainfall_90d": 130.0,
            "rainfall_anomaly": -15.0, "temperature_mean": 27.0,
            "soil_moisture_layer1": 0.2, "spi_3": -1.4, "spei_3": -1.6,
        }
        trainer = DroughtModelTrainer()
        result = trainer.predict(features, model_name="NonExistent")
        # Even failed predictions must include prediction_type
        assert result.get("prediction_type") == "MODEL_PREDICTION"
