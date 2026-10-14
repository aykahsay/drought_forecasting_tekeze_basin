# AI-DREWS Model Card
## Intended Use, Architecture Candidates, Operational Constraints, and Ethical Safeguards

**Document ID:** `AI-DREWS-DOC-MC-2026-10`  
**Standard:** Model Cards for Model Reporting (Mitchell et al. 2019)  
**Status:** **SPECIFICATION & ARCHITECTURE DESIGN (Training Strictly Paused Pending Gate 4 Certification)**

---

### 1. Model Details

* **Model Name:** AI-DREWS Seasonal Drought Forecasting Engine
* **Version:** 1.0-Candidate
* **Model Type:** Multi-Model Ensemble (Persistence, Dynamic Climatology, ARIMA, Recurrent LSTM, Spatial CNN-LSTM, Fourier Neural Operator)
* **Target Geographic Basin:** Tekezé River Basin Catchment ($67,135.4\text{ km}^2$ provisional, Northern Ethiopia)
* **Primary Prediction Task:** September-ending SPEI-3 (Kiremt core agricultural season) issued on June 1 (3-month lead).
* **Secondary Prediction Task:** May-ending SPEI-3 (Belg short-rains pastoral season) issued on February 1 (3-month lead).
* **Developers:** AgriMinds AI-DREWS Collaborative Research Group

---

### 2. Intended Use & Target Users

* **Intended Use:** Early warning guidance for agricultural extension services, disaster risk management commissions (EDRMC), and water resource managers in Tigray and Amhara.
* **Out-of-Scope Uses:**
  * Must NOT be used as a standalone automated trigger for humanitarian assistance without on-the-ground ground truthing.
  * Must NOT be interpreted as a direct measurement of famine or household food security.
  * Must NOT be downscaled to field-level micro-plots beyond the physical resolution of the underlying climate grids (0.05° CHIRPS / 0.1° ERA5-Land).

---

### 3. Chronological Training & Evaluation Data Partitions

* **Training Set:** 1981–2005 (25 years, 300 consecutive months).
* **Validation / Tuning Set:** 2006–2014 (9 years, 108 consecutive months).
* **Frozen Holdout Test Set:** 2015–2024 (10 years, 120 consecutive months).
* **Anti-Leakage Guarantees:** Zero future information leakage. All scalers, normalizers, and feature transformations are fit exclusively on the Training Set. Real-time teleconnection release latencies ($\ge 1\text{ month}$) are enforced.

---

### 4. Metrics & Benchmarking Requirements

* **Primary Evaluation Metric:** Brier Skill Score ($\text{BSS} > 0$) relative to dynamic climatology for categorical drought events ($\text{SPEI-3} \le -1.5$).
* **Continuous Metrics:** Continuous Ranked Probability Score (CRPS), Mean Absolute Error (MAE), Root Mean Square Error (RMSE), and Pearson correlation ($r$).
* **Uncertainty Quantification:** Evaluated as **80% and 95% predictive intervals**; must demonstrate nominal empirical coverage on the frozen test holdout set.

---

### 5. Ethical Considerations & Operational Limitations

* **False Alarms vs Missed Events:** False alarms can cause costly misallocation of emergency reserves, while missed droughts cause unmitigated crop loss and humanitarian distress. All forecast outputs must report empirical false alarm ratios and probability of detection.
* **Fail-Safe Mechanism:** When climate inputs are missing or fail quality gates, the model must **abstain** and output an explicit error banner rather than generating synthetic or uncalibrated predictions.
