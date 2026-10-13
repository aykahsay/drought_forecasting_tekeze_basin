# AI-DREWS Full System Architecture

```mermaid
flowchart TD
    %% Define Styles
    classDef dataBox fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0f172a
    classDef storageBox fill:#f1f5f9,stroke:#64748b,stroke-width:2px,stroke-dasharray: 5 5,color:#0f172a
    classDef modelBox fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#0f172a
    classDef uiBox fill:#fef08a,stroke:#ca8a04,stroke-width:2px,color:#0f172a
    classDef rlBox fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#0f172a

    %% Data Sources Layer
    subgraph Data Sources
        direction LR
        L1[Local Data:\nERA5 Temp, Soil Moisture, CHIRPS]:::dataBox
        G1[Global Data:\nENSO Nino 3.4, IOD DMI]:::dataBox
    end

    %% Storage Layer
    subgraph Hot-Warm-Cold Storage Pipeline
        direction TB
        C1[(Cold Storage:\nHistorical Parquet)]:::storageBox
        W1[(Warm Storage:\n2-Month Training Staging)]:::storageBox
        H1[(Hot Storage:\nLive Tempo Buffer)]:::storageBox
        
        C1 --> W1
        H1 --> W1
    end

    %% Modeling Layer
    subgraph AI Inference Engine
        direction TB
        DL[CNN-LSTM Network:\nExtract Spatial/Temporal Features]:::modelBox
        BAYES[Bayesian Log-Odds Updater:\nCalculate Probabilistic Threat]:::modelBox
        
        DL --> BAYES
    end

    %% UI Layer
    subgraph 4-Tier Geospatial Dashboard
        direction TB
        UI1[Level 1: National Alert Map]:::uiBox
        UI2[Level 2: Regional View]:::uiBox
        UI3[Level 3: Woreda Risk Zone]:::uiBox
        UI4[Level 4: Kebele Satellite]:::uiBox
        
        UI1 --> UI2 --> UI3 --> UI4
    end

    %% Reinforcement Learning Layer
    subgraph Prescriptive Engine (Future)
        direction TB
        RL[RL Agent:\nPolicy Network]:::rlBox
        ACT[Action Space:\n- Issue Early Warning\n- Seed Distribution\n- Financial Payout]:::rlBox
        REW[Reward Function:\nMinimize Loss vs. Budget]:::rlBox
        
        RL --> ACT
        ACT -. Feedback Loop .-> REW
        REW -. Tune Policy .-> RL
    end

    %% Connections
    L1 --> H1
    G1 --> H1
    
    W1 -- Trigger Retraining\n(CRON Job) --> DL
    H1 -- Live Observations --> BAYES
    
    BAYES -- Probabilistic Outputs --> UI1
    BAYES -- State Representation --> RL
```
