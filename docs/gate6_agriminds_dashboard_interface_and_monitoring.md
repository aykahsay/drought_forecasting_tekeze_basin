# AI-DREWS Gate 6: AgriMinds Operational Interface & Monitoring Specification
## Data Contract, Uncertainty Transparency, Visual Layer Separation, and Fail-Safe Telemetry

**Document ID:** `AI-DREWS-GATE6-SPEC-2026-10`  
**Standard:** Open Geospatial Consortium (OGC); WMO Early Warning Standards; Streamlit / FastAPI Architecture  
**Status:** **SPECIFIED & ARCHITECTED**  
**Integration Points:** AgriMinds Streamlit Dashboard, Data Ingestion APIs, Operational Storage Cache

---

### 1. Versioned Data Contract & Schema Architecture

To prevent silent schema drifts or serialization bugs, the interface between the climate forecasting pipeline and the AgriMinds front-end dashboard is governed by an explicit JSON schema / Parquet contract:

#### 1.1 Schema Definition: Monthly Historical Observation Record
```json
{
  "type": "object",
  "properties": {
    "date": {"type": "string", "format": "date", "example": "2024-09-01"},
    "year": {"type": "integer", "example": 2024},
    "month": {"type": "integer", "example": 9},
    "spatial_scope": {"type": "string", "enum": ["TEKEZE_BASIN_WHOLE", "WOREDA_SUBBASIN"]},
    "precip_chirps_mm": {"type": "number", "minimum": 0.0},
    "temp_mean_c": {"type": "number", "minimum": -10.0, "maximum": 55.0},
    "pet_hargreaves_mm": {"type": "number", "minimum": 0.0},
    "spei_3": {"type": "number", "minimum": -5.0, "maximum": 5.0},
    "spi_3": {"type": "number", "minimum": -5.0, "maximum": 5.0},
    "data_quality_status": {"type": "string", "enum": ["CERTIFIED_OBSERVATION", "PROVISIONAL_OBSERVATION", "MISSING_DATA"]},
    "provenance_hash": {"type": "string", "example": "sha256:7b9c..."}
  },
  "required": ["date", "year", "month", "spei_3", "data_quality_status"]
}
```

#### 1.2 Schema Definition: Probabilistic Early Warning Forecast
```json
{
  "type": "object",
  "properties": {
    "issue_date": {"type": "string", "format": "date", "example": "2024-06-01"},
    "valid_target_date": {"type": "string", "format": "date", "example": "2024-09-01"},
    "target_season": {"type": "string", "enum": ["KIREMT_SEPTEMBER_SPEI3", "BELG_MAY_SPEI3"]},
    "lead_time_months": {"type": "integer", "enum": [1, 3, 6]},
    "model_version": {"type": "string", "example": "AI-DREWS-v1.0-FNO"},
    "forecast_median": {"type": "number"},
    "confidence_interval_80": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
    "confidence_interval_95": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
    "drought_probabilities": {
      "type": "object",
      "properties": {
        "p_mild_drought": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "p_moderate_drought": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "p_severe_drought": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "p_extreme_drought": {"type": "number", "minimum": 0.0, "maximum": 1.0}
      }
    },
    "benchmark_comparison": {
      "climatology_median": {"type": "number"},
      "persistence_median": {"type": "number"},
      "brier_skill_score": {"type": "number"}
    }
  },
  "required": ["issue_date", "valid_target_date", "lead_time_months", "forecast_median", "confidence_interval_80"]
}
```

---

### 2. Operational UI Standards & Visual Layer Separation

#### 2.1 Distinct Visual Layers: Observations vs Forecasts
* **Strict UI Rule:** The dashboard must visually and conceptually separate **observed historical climate records** from **probabilistic model forecasts**.
* **Visual Encoding:**
  * Observed records: Solid line (historical ground-truth).
  * Forecasts: Dashed/dotted line with shaded 80% and 95% uncertainty intervals (prediction cone).
  * An explicit legend badge must designate `"OBSERVED HISTORICAL RECORD (CHIRPS / ERA5-LAND)"` vs `"PROBABILISTIC FORECAST (MODEL ISSUED)"`.

#### 2.2 Spatial Claims & Resolution Transparency
* **Basin-Wide View ($67,135.4\text{ km}^2$):** Certified. Supported by 2,488 CHIRPS cells (0.05°) and 782 ERA5-Land cells (0.10°).
* **Woreda / Kebele Views:**
  * Displayed **only** when high-resolution downscaled products are certified.
  * The UI must display an explicit spatial disclaimer:
    > *"Note: Sub-basin and woreda views reflect aggregated spatial extractions from 0.05° precipitation grids. Micro-topographical rain shadow effects may not be fully resolved."*

---

### 3. Fail-Safe Telemetry, Data Refresh & Health Monitoring

#### 3.1 Automated Data-Refresh Checks
The dashboard ingestion daemon executes daily health checks:
1. **Source Availability:** Pings UCSB CHIRPS THREDDS, ECMWF CDS API, and NOAA PSL THREDDS.
2. **Checksum Verification:** Verifies SHA-256 hashes against `temperature_provenance_manifest.json`.
3. **Freshness Latency:** Alerts administrators if new monthly data is delayed beyond operational publication windows (>15 days past month end).

#### 3.2 Failure States & Anti-Fabrication Safeguards
* **Zero Synthetic Fallbacks in Production:** If raw climate observations or model input tensors are missing or corrupted, the system **strictly halts execution and displays a clear warning banner**:
  > ⚠️ **Data Feed Paused:** Climate observational records for the requested period are pending verification. Early warning alerts are suppressed to prevent fabricated drought notifications.
* **Prohibition:** Under no circumstances may missing observational feeds produce fabricated forecasts or deceptive alerts.

---

### 4. Operational Model Card Specification

When Gate 5 models are trained and deployed to Gate 6:
* **Model Name:** AI-DREWS Tekezé Basin Drought Early Warning Engine
* **Version:** v1.0-Audited
* **Intended Use:** Seasonal drought early warning for agricultural stakeholders and regional disaster risk management commissions in Northern Ethiopia.
* **Limitations:** Predicts meteorological water balance ($\text{SPEI-3}$); does not model political famine, market access, or pest infestations.
* **Ethical Constraints:** Forecasts must always include uncertainty bounds; decision-makers are informed that false alarm risk is quantified.

---

### 5. Multi-Gate Integration Architecture

The 6-gate system forms a unified, end-to-end scientific pipeline:

```
[Gate 1: Climate Ingestion] ──▶ [Gate 2: Math Cross-Validation] ──▶ [Gate 3: Spatial & Temporal Integrity]
                                                                                │
                                                                                ▼
[Gate 6: AgriMinds Dashboard] ◀── [Gate 5: Predictive Models] ◀── [Gate 4: Target Reconstruction]
```
