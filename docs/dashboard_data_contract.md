# AI-DREWS Dashboard Data Contract
## Front-End API Interface, JSON Schema, Visual Separation, and Fail-Safe Telemetry

**Document ID:** `AI-DREWS-DOC-DDC-2026-10`  
**Standard:** OpenAPI 3.0 / JSON Schema Draft 7 / OGC Standards  
**Status:** **ACTIVE CONTRACT SPECIFICATION**

---

### 1. Interface Objectives & Design Principles

The AgriMinds Dashboard connects to the verified AI-DREWS data pipeline through an explicit, versioned data contract designed to eliminate silent failures, data fabrication, and visual ambiguity:

1. **Visual Layer Separation:** Observed historical climate records and probabilistic model forecasts are served through distinct endpoints and rendered on separate visual layers.
2. **Predictive Intervals:** Forecast uncertainty must be labeled as **80% and 95% predictive intervals**, never conflated with confidence intervals.
3. **Telemetry & Observation Cutoff:** Every response explicitly includes the observation cutoff date, forecast issue date, model version, and spatial resolution disclaimer.
4. **Zero Synthetic Failover:** Missing or unverified data must trigger an explicit failure banner, never a fabricated forecast.

---

### 2. Historical Observations Endpoint Schema (`/api/v1/historical/observations`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "HistoricalObservationsResponse",
  "type": "object",
  "properties": {
    "basin_id": {"type": "string", "enum": ["TEKEZE_BASIN_WHOLE"]},
    "start_date": {"type": "string", "format": "date"},
    "end_date": {"type": "string", "format": "date"},
    "records": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "date": {"type": "string", "format": "date"},
          "year": {"type": "integer"},
          "month": {"type": "integer"},
          "precip_mm": {"type": ["number", "null"]},
          "tmax_c": {"type": ["number", "null"]},
          "tmin_c": {"type": ["number", "null"]},
          "tmean_c": {"type": ["number", "null"]},
          "pet_hargreaves_mm": {"type": ["number", "null"]},
          "water_balance_mm": {"type": ["number", "null"]},
          "spei_3": {"type": ["number", "null"]},
          "spi_3": {"type": ["number", "null"]},
          "qc_status": {
            "type": "string",
            "enum": ["CERTIFIED_OBSERVATION", "PROVISIONAL_OBSERVATION", "INSUFFICIENT_COVERAGE", "MISSING_DATA"]
          }
        },
        "required": ["date", "year", "month", "qc_status"]
      }
    }
  },
  "required": ["basin_id", "records"]
}
```

---

### 3. Seasonal Forecast Endpoint Schema (`/api/v1/forecast/seasonal`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SeasonalForecastResponse",
  "type": "object",
  "properties": {
    "basin_id": {"type": "string", "enum": ["TEKEZE_BASIN_WHOLE"]},
    "issue_date": {"type": "string", "format": "date"},
    "observation_cutoff_date": {"type": "string", "format": "date"},
    "valid_target_date": {"type": "string", "format": "date"},
    "target_season": {"type": "string", "enum": ["KIREMT_SEPTEMBER_SPEI3", "BELG_MAY_SPEI3"]},
    "lead_time_months": {"type": "integer"},
    "model_version": {"type": "string"},
    "forecast_median": {"type": "number"},
    "predictive_interval_80": {
      "type": "array",
      "items": {"type": "number"},
      "minItems": 2,
      "maxItems": 2
    },
    "predictive_interval_95": {
      "type": "array",
      "items": {"type": "number"},
      "minItems": 2,
      "maxItems": 2
    },
    "categorical_probabilities": {
      "type": "object",
      "properties": {
        "p_mild_drought": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "p_moderate_drought": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "p_severe_drought": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "p_extreme_drought": {"type": "number", "minimum": 0.0, "maximum": 1.0}
      },
      "required": ["p_moderate_drought", "p_severe_drought", "p_extreme_drought"]
    },
    "benchmark_comparison": {
      "climatology_median": {"type": "number"},
      "persistence_median": {"type": "number"},
      "brier_skill_score": {"type": "number"}
    },
    "data_quality_status": {
      "type": "string",
      "enum": ["VALIDATED_FORECAST", "PROVISIONAL_FORECAST", "DATA_FEED_PAUSED"]
    }
  },
  "required": [
    "basin_id",
    "issue_date",
    "observation_cutoff_date",
    "valid_target_date",
    "forecast_median",
    "predictive_interval_80",
    "data_quality_status"
  ]
}
```

---

### 4. Front-End Failure States & Warnings

1. **`DATA_FEED_PAUSED`:** Rendered when input observational NetCDFs are missing:
   > ⚠️ **Data Feed Paused:** Climate observational records for the requested period are pending verification. Early warning alerts are suppressed to prevent fabricated drought notifications.
2. **Spatial Disclaimer:** Displayed across all sub-basin and woreda views:
   > *"Spatial Disclaimer: Sub-basin and woreda extractions reflect aggregated cell intersections from 0.05° (CHIRPS) and 0.1° (ERA5-Land) grids. Micro-topographical rain-shadow effects may not be fully resolved."*
