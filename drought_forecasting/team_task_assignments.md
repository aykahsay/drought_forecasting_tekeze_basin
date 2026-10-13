# AI-DREWS Core Team: Recruitment & Task Assignments

To operationalize the AI-DREWS pipeline for national deployment, we need to transition from the prototyping phase to a robust, specialized team structure. 

## 1. The Climatologist & Earth Observation (EO) Lead
**Profile:** Expertise in African climatology, teleconnections (ENSO/IOD), and satellite raster processing (xarray, GDAL).
**Primary Tasks:**
*   **Data Pipeline Maintenance:** Ensure the Google Earth Engine / Copernicus API hooks are pulling ERA5, CHIRPS, and SMAP data without breaking during server updates.
*   **LULC Masking:** Continuously update the ESA WorldCover masks to ensure we are excluding urban and open-water expansions.
*   **Teleconnection Fine-Tuning:** Monitor NOAA's Niño 3.4 index and dynamically adjust the temporal lag periods in the model if global ocean currents shift.

## 2. The Machine Learning / Bayesian Engineer
**Profile:** Deep mathematical background in PyTorch (CNN/LSTM/Fourier Neural Operators) and Probabilistic Programming (Pyro/Stan) for Bayesian inference.
**Primary Tasks:**
*   **Fourier Layer Optimization:** Implement the actual FFT filtering logic in PyTorch to cleanly isolate the 3-to-7 year ENSO waves without distorting the underlying trend.
*   **Bi-Monthly CRON Retraining:** Oversee the automated retraining pipeline (Hot $\rightarrow$ Warm $\rightarrow$ Cold storage transitions) and ensure the weights don't suffer from catastrophic forgetting.
*   **Bayesian Prior Calibration:** Calibrate the Log-Odds inference engine. If the model starts producing too many false-alarms, mathematically stiffen the prior to anchor the predictions.

## 3. The Backend & Geospatial Data Engineer
**Profile:** Expertise in FastAPI, PostgreSQL/PostGIS, Apache Parquet, and scalable cloud architectures.
**Primary Tasks:**
*   **The Tempo Buffer:** Manage the real-time Hot Storage layer using Redis or fast-read databases so the inference engine never hangs.
*   **Cold Storage Archiving:** Efficiently compress historical climate data into partitioned Parquet files (by year and region) for cheap, massive storage.
*   **API Development:** Maintain the secure endpoints that the frontend dashboard polls for the daily probabilistic drought percentages.

## 4. The Frontend UX / GIS Developer
**Profile:** Expertise in React, Next.js, Leaflet/Mapbox, and data visualization (D3.js).
**Primary Tasks:**
*   **The 4-Tier Dashboard:** Maintain the cinematic, drill-down map navigation (National $\rightarrow$ Regional $\rightarrow$ Woreda $\rightarrow$ Kebele).
*   **Explainability UI:** Design the tooltip components that clearly show the "Factors Contributing to the Model Prediction" (e.g., showing a farmer *why* the alert was triggered based on soil moisture and IOD).
*   **Low-Bandwidth Optimization:** Ensure the dashboard loads quickly in rural Ethiopian regions with 3G/intermittent internet.
