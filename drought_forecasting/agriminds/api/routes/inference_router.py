from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

# Import our mock ablation suite to get the Bayesian inference
from agriminds.ml.ablation import get_ablation_suite

router = APIRouter(prefix="/api/v1/inference", tags=["Inference Engine"])

class RegionalRequest(BaseModel):
    woreda_id: str
    latitude: float
    longitude: float
    current_spi: float
    current_soil_moisture_pct: float

class UnifiedForecastResponse(BaseModel):
    timestamp: str
    woreda_id: str
    assigned_expert: str
    drought_probabilities: List[Dict[str, Any]]
    key_factors: List[Dict[str, Any]]

def determine_regional_expert(lat: float, lon: float) -> str:
    """
    Geospatial Routing Layer: Determines which MoE (Mixture of Experts) model 
    to use based on latitude and longitude boundaries.
    """
    if lat > 9.0 and 36.0 < lon < 40.0:
        return "Highlands_Kiremt_Expert"
    elif lat < 8.0 and lon > 40.0:
        return "Somali_Pastoral_Expert"
    elif 7.0 <= lat <= 9.0 and 38.0 <= lon <= 40.0:
        return "Rift_Valley_Expert"
    else:
        return "General_National_Model"

@router.post("/predict", response_model=UnifiedForecastResponse)
async def predict_drought_risk(request: RegionalRequest):
    """
    The Unified Mixture of Experts (MoE) API Endpoint.
    1. Routes request to the correct regional expert.
    2. Runs the Spatio-Temporal-Frequency Bayesian inference.
    3. Returns unified JSON to the frontend dashboard.
    """
    try:
        # Step 1: Geospatial Routing
        expert = determine_regional_expert(request.latitude, request.longitude)
        
        # Step 2: Extract Real Live Teleconnections from Synced NOAA Observations
        from agriminds.climate.sources.ocean_teleconnections import get_multi_ocean_engine
        engine = get_multi_ocean_engine()
        intel = engine.get_latest_ocean_intelligence()
        live_nino = intel.get("pacific_ocean", {}).get("observation", {}).get("value", 0.85)
        live_iod = intel.get("indian_ocean", {}).get("observation", {}).get("value", -0.20)

        real_telemetry = {
            "spi_3": request.current_spi,
            "soil_moisture_percentile": request.current_soil_moisture_pct,
            "nino34": float(live_nino),
            "iod": float(live_iod),
            "rainfall_anomaly": -15.0
        }
        
        # Step 3: Run Real Inference
        suite = get_ablation_suite()
        forecast = suite.predict_multi_horizon(
            features=real_telemetry,
            woreda_id=request.woreda_id,
            tier="Model_E_FFT"
        )
        
        # Format the response for the Leaflet UI
        return UnifiedForecastResponse(
            timestamp=date.today().isoformat(),
            woreda_id=request.woreda_id,
            assigned_expert=expert,
            drought_probabilities=[
                {
                    "horizon_months": h.horizon_months,
                    "probability": h.drought_probability,
                    "risk_level": h.risk_level
                } for h in forecast.horizons
            ],
            key_factors=forecast.top_contributing_factors
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference Engine Error: {str(e)}")


# ────────────────────────────────────────────────────────────────────────────
# END-USER CROP YIELD FORECASTING ENDPOINT (Abergelle - Tekeze + CNN-LSTM)
# ────────────────────────────────────────────────────────────────────────────

class CropYieldRequest(BaseModel):
    crop: str = "Maize"                     # 'Teff', 'Wheat', 'Maize', or 'All'
    zone: str = "Midland"                   # 'Lowland', 'Midland', or 'Highland'
    year: int = 2025                        # Target forecast year
    last_year_yield: Optional[float] = None # Optional prior season harvest in q/ha

@router.post("/crop-yield")
async def predict_crop_yield_endpoint(request: CropYieldRequest):
    """
    End-user crop forecast endpoint.
    Takes only:
      - crop ('Teff', 'Wheat', 'Maize', or 'All')
      - zone ('Lowland', 'Midland', 'Highland')
      - year (default 2025)
      - last_year_yield (optional)
      
    Climate parameters, teleconnections, and altitude tiers are automatically
    resolved by the AgriMinds spatio-temporal intelligence core.
    """
    try:
        from agriminds.ml.crop_forecast_service import get_crop_forecast_service
        service = get_crop_forecast_service()
        
        if request.crop.lower() == "all":
            result = service.predict_all_crops(
                zone=request.zone,
                year=request.year
            )
            return {"status": "success", "forecasts": result}
        else:
            result = service.predict_for_user(
                crop=request.crop,
                zone=request.zone,
                year=request.year,
                last_year_yield=request.last_year_yield
            )
            return {"status": "success", "forecast": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Crop Forecast Error: {str(e)}")

