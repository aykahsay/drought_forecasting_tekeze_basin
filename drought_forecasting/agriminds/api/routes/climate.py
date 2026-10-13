"""
Climate Features, Drought Indices, Drought Risk, and ENSO API Routes
(Requirement §17)

GET  /api/climate/features   — Feature engineering output
GET  /api/drought/indices    — SPI, SPEI, Sc-PDSI values
GET  /api/drought/risk       — ML drought risk prediction
GET  /api/enso/status        — Current ENSO conditions
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agriminds.climate.enso import classify_enso_phase, get_enso_dataframe
from agriminds.climate.features.engineering import (
    FeatureEngineeringPipeline,
    classify_pdsi,
)
from agriminds.db.models import ENSORecord, get_db
from agriminds.ml.models import DroughtModelTrainer

climate_router = APIRouter(prefix="/api/climate", tags=["Climate Features"])
drought_router = APIRouter(prefix="/api/drought", tags=["Drought"])
enso_router = APIRouter(prefix="/api/enso", tags=["ENSO"])

_feature_pipeline = FeatureEngineeringPipeline()


# ============================================================================
# Climate Features
# ============================================================================

@climate_router.get("/features")
def get_climate_features(
    start_date: date = Query(default=date.today() - timedelta(days=90)),
    end_date: date = Query(default=date.today()),
    location_id: str = Query(default="tigray"),
):
    """
    Return engineered climate features for the specified date range.

    Features include:
    - Precipitation rolling windows (7d, 30d, 60d, 90d, 180d)
    - Temperature statistics
    - Soil moisture by layer
    - Anomalies and percentile ranks

    DATA SOURCE ATTRIBUTION:
    - Precipitation/temperature/soil moisture: ERA5T reanalysis (near-real-time)
    - ENSO/Niño 3.4: elnino.xlsx historical reference dataset
    """
    try:
        features_df = _feature_pipeline.build_features(start_date, end_date, location_id)
        if features_df.empty:
            return {
                "message": "No ERA5T data available for the requested period.",
                "hint": "Trigger ingestion via POST /api/era5/ingest first.",
                "features": [],
            }

        # Convert to JSON-safe records
        features_df["date"] = features_df["date"].astype(str)
        records = features_df.where(features_df.notna(), None).to_dict(orient="records")

        return {
            "location_id": location_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "count": len(records),
            "data_source_attribution": {
                "ERA5T": "Near-real-time atmospheric reanalysis (~5-day latency)",
                "elnino_xlsx": "Historical ENSO/climate reference dataset",
                "derived": "SPI, SPEI, anomalies are derived indicators (not observations)",
            },
            "features": records,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# Drought Indices
# ============================================================================

@drought_router.get("/indices")
def get_drought_indices(
    start_date: date = Query(default=date.today() - timedelta(days=365)),
    end_date: date = Query(default=date.today()),
    location_id: str = Query(default="tigray"),
):
    """
    Return drought indices for the specified period.

    IMPORTANT: These are DERIVED indicators, not raw observations.
    SPI and SPEI are computed from ERA5T precipitation/temperature.
    Sc-PDSI comes from the historical elnino.xlsx dataset.
    """
    try:
        features_df = _feature_pipeline.build_features(start_date, end_date, location_id)
        if features_df.empty:
            return {"message": "No data available.", "indices": []}

        index_cols = [
            "date", "spi_1", "spi_3", "spi_6", "spi_12",
            "spei_1", "spei_3", "spei_6", "spei_12", "sc_pdsi",
        ]
        available = [c for c in index_cols if c in features_df.columns]
        indices_df = features_df[available].copy()
        indices_df["date"] = indices_df["date"].astype(str)

        # Add drought classification for Sc-PDSI
        if "sc_pdsi" in indices_df.columns:
            indices_df["pdsi_classification"] = indices_df["sc_pdsi"].apply(
                lambda x: classify_pdsi(x) if x is not None else None
            )

        return {
            "location_id": location_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "note": (
                "SPI and SPEI are derived from ERA5T reanalysis. "
                "Sc-PDSI sourced from elnino.xlsx historical dataset. "
                "These are DERIVED INDICATORS, not raw observations."
            ),
            "classification_thresholds": {
                "Normal":           "Sc-PDSI > -1.0",
                "Moderate Drought": "-2.0 < Sc-PDSI ≤ -1.0",
                "Severe Drought":   "-3.0 < Sc-PDSI ≤ -2.0",
                "Extreme Drought":  "Sc-PDSI ≤ -3.0",
            },
            "indices": indices_df.where(indices_df.notna(), None).to_dict(orient="records"),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@drought_router.get("/risk")
def get_drought_risk(
    location_id: str = Query(default="tigray"),
    forecast_months: int = Query(default=1, ge=1, le=3),
):
    """
    Return AI/ML drought risk prediction.

    SCIENTIFIC REQUIREMENT (§21):
    This is a MODEL PREDICTION, NOT an observation or reanalysis measurement.
    The response explicitly labels the output type to prevent misrepresentation.

    Drought thresholds (documented, §11):
        Normal          : Sc-PDSI > -1.0
        Moderate Drought: -2.0 < Sc-PDSI ≤ -1.0
        Severe Drought  : -3.0 < Sc-PDSI ≤ -2.0
        Extreme Drought : Sc-PDSI ≤ -3.0
    """
    # Get latest available features
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    try:
        features_df = _feature_pipeline.build_features(start_date, end_date, location_id)
        if features_df.empty:
            return {
                "prediction_type": "MODEL_PREDICTION",
                "message": "Insufficient data for drought risk prediction.",
                "drought_probability": None,
                "risk_level": None,
            }

        latest = features_df.sort_values("date").iloc[-1]
        feature_dict = latest.to_dict()

        trainer = DroughtModelTrainer(task="regression")
        trainer.train_all_baselines(features_df)
        prediction = trainer.predict(feature_dict)

        # Augment with current conditions (from latest features)
        enso_status = get_enso_dataframe()
        nino_val = None
        if not enso_status.empty and "year" in enso_status.columns:
            latest_year = date.today().year
            enso_row = enso_status[enso_status["year"] == latest_year]
            if enso_row.empty:
                max_yr = enso_status["year"].max()
                enso_row = enso_status[enso_status["year"] == max_yr]
            if not enso_row.empty and "nino34_annual" in enso_row.columns and enso_row["nino34_annual"].notna().any():
                nino_val = float(enso_row["nino34_annual"].dropna().iloc[0])

        return {
            **prediction,
            "location_id": location_id,
            "forecast_horizon_months": forecast_months,
            "based_on_date": str(latest.get("date", end_date)),
            "current_conditions": {
                "enso": {
                    "nino34_annual": nino_val,
                    "phase": classify_enso_phase(nino_val),
                    "source": "elnino.xlsx (historical reference)",
                },
                "spi_3": feature_dict.get("spi_3"),
                "spi_6": feature_dict.get("spi_6"),
                "spei_3": feature_dict.get("spei_3"),
                "rainfall_anomaly": feature_dict.get("rainfall_anomaly"),
                "soil_moisture_percentile": feature_dict.get("soil_moisture_percentile"),
            },
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# ENSO Status
# ============================================================================

@enso_router.get("/status")
def get_enso_status(db: Session = Depends(get_db)):
    """
    Return current and recent ENSO conditions from the elnino.xlsx dataset.
    """
    records = (
        db.query(ENSORecord)
        .order_by(ENSORecord.year.desc())
        .limit(5)
        .all()
    )

    if not records:
        return {"message": "ENSO historical dataset not loaded yet."}

    latest = records[0]
    current_phase = classify_enso_phase(latest.nino34_annual)

    return {
        "source": "elnino.xlsx (Historical ENSO reference dataset)",
        "data_type": "HISTORICAL_CLIMATE_REFERENCE",
        "latest_year": latest.year,
        "current_enso_phase": current_phase,
        "nino34": {
            "annual": latest.nino34_annual,
            "djf": latest.nino34_djf,
            "mam": latest.nino34_mam,
            "jja": latest.nino34_jja,
            "son": latest.nino34_son,
        },
        "sc_pdsi": latest.sc_pdsi,
        "pdsi_classification": classify_pdsi(latest.sc_pdsi) if latest.sc_pdsi else None,
        "recent_years": [
            {
                "year": r.year,
                "nino34_annual": r.nino34_annual,
                "enso_phase": classify_enso_phase(r.nino34_annual),
                "sc_pdsi": r.sc_pdsi,
            }
            for r in records
        ],
        "phase_thresholds": {
            "El Nino":  "Niño 3.4 ≥ +0.5",
            "La Nina":  "Niño 3.4 ≤ −0.5",
            "Neutral":  "−0.5 < Niño 3.4 < +0.5",
        },
    }


@enso_router.get("/historical")
def get_enso_historical(db: Session = Depends(get_db)):
    """Return full historical ENSO dataset (elnino.xlsx)."""
    records = db.query(ENSORecord).order_by(ENSORecord.year).all()
    return {
        "source": "elnino.xlsx",
        "data_type": "HISTORICAL_CLIMATE_REFERENCE",
        "years": len(records),
        "coverage": {
            "start": records[0].year if records else None,
            "end": records[-1].year if records else None,
        },
        "note": (
            "This dataset is the historical ENSO reference. "
            "It is NEVER overwritten or replaced by ERA5T data."
        ),
        "records": [
            {
                "year": r.year,
                "nino34_djf": r.nino34_djf,
                "nino34_mam": r.nino34_mam,
                "nino34_jja": r.nino34_jja,
                "nino34_son": r.nino34_son,
                "nino34_annual": r.nino34_annual,
                "p_djf_m": r.p_djf_m,
                "p_mam_m": r.p_mam_m,
                "p_jja_m": r.p_jja_m,
                "p_son_m": r.p_son_m,
                "p_c_mm_mon": r.p_c_mm_mon,
                "t_djf_k": r.t_djf_k,
                "t_mam_k": r.t_mam_k,
                "t_jja_k": r.t_jja_k,
                "t_son_k": r.t_son_k,
                "t_annual_c": r.t_annual_c,
                "sc_pdsi": r.sc_pdsi,
                "enso_phase": classify_enso_phase(r.nino34_annual),
                "pdsi_classification": classify_pdsi(r.sc_pdsi) if r.sc_pdsi is not None else None,
            }
            for r in records
        ],
    }
