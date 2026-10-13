# AI-DREWS Architectural View

This diagram illustrates how raw climate telemetry flows through the system, gets processed by the Hot-Warm-Cold data pipeline, infers probabilities via Bayesian updates, and triggers geospatial early warnings.

```mermaid
graph TD
    %% Define External Actors
    subgraph "External Actors & Sensors"
        ERA5[ECMWF ERA5 Satellite]
        CHIRPS[CHIRPS Rainfall Grids]
        NOAA[NOAA Ocean Teleconnections]
        GovOfficial[Government / WFP Decision Maker]
    end

    %% Define Core Backend
    subgraph "AI-DREWS Core Engine (Python/FastAPI)"
        Ingest[Data Ingestion API]
        
        subgraph "Storage Tiers"
            TempoBuffer[Hot Tempo Buffer]
            ColdDB[(Cold Parquet Climatology)]
        end
        
        subgraph "AI & Modeling"
            CNNLSTM[CNN-LSTM Feature Extractor]
            Bayesian[Bayesian Log-Odds Engine]
        end

        Cron[CRON Scheduler]
        
        subgraph "Presentation Layer"
            GeoServer[Leaflet Geospatial Server]
            AlertSvc[Early Warning Dispatcher]
        end
    end
    
    %% Define Future Expansion
    subgraph "Prescriptive Interventions"
        RLAgent[Reinforcement Learning Agent]
    end

    %% Data Flow - The Request
    ERA5 -- "1. Push 2m Temp/Moisture" --> Ingest
    CHIRPS -- "2. Push Rainfall Deficits" --> Ingest
    NOAA -- "3. Push Nino 3.4 / DMI" --> Ingest
    
    %% Data Flow - Storage & Preprocessing
    Ingest -- "4. Stage Live Data" --> TempoBuffer
    Ingest -- "5. Archive History" --> ColdDB
    
    %% Data Flow - Modeling
    TempoBuffer -- "6. Feed 60-day Sequence" --> CNNLSTM
    CNNLSTM -- "7. Output Spatial Vectors" --> Bayesian
    Bayesian -- "8. Update Probability %" --> GeoServer
    
    %% Data Flow - Notifications
    Bayesian -- "9. Threshold Exceeded" --> AlertSvc
    GeoServer -- "10. Render Map" --> GovOfficial
    AlertSvc -- "11. Dispatch Alert" --> GovOfficial
    
    %% Data Flow - Background Clearing
    Cron -- "12. Bi-Monthly Wakeup" --> ColdDB
    Cron -- "13. Retrain Weights" --> CNNLSTM
    
    %% Future State
    Bayesian -. "Future State Variables" .-> RLAgent
    RLAgent -. "Optimal Intervention" .-> GovOfficial
```

### Architectural Highlights

1. **Hot/Cold Segregation:** 
   The flow from the data ingestion down to the Bayesian engine (Steps 1 through 8) happens dynamically in the `Hot Tempo Buffer` to ensure decision-makers see real-time updates. The heavy historical Parquet storage is explicitly kept out of the live prediction path to ensure low latency.

2. **The Bayesian Chokepoint:**
   By forcing all deep learning vectors to pass through the `Bayesian Log-Odds Engine` (Step 7), we guarantee that opaque neural network outputs are translated into calibrated, mathematically explainable probability percentages before they ever reach the UI.

3. **Bi-Monthly Retraining Disconnect:**
   Notice that the `CRON Scheduler` (Steps 12-13) sits entirely separate from the live user forecast flow. It wakes up every two months, sweeps the `Cold Parquet Climatology` for all new verified ground-truth data, and fine-tunes the CNN-LSTM weights to prevent concept drift.
