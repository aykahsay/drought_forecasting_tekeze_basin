"""
Machine Learning Drought Models (Requirement §20)
==================================================
Implements a progressive model hierarchy:

STEP 1 — Baselines (establish first):
    Persistence
    Linear Regression
    Logistic Regression
    Random Forest
    XGBoost

STEP 2 — Advanced models (evaluate only after baselines):
    LSTM
    Temporal CNN
    Transformer
    Hybrid CNN-LSTM

CRITICAL TIME-SERIES VALIDATION REQUIREMENT (§20):
    Do NOT randomly shuffle temporal data.
    Use TimeSeriesSplit for cross-validation.
    Reserve later historical periods for validation/testing.
    Training period → Validation period → Test period (chronological).

IMPORTANT SCIENTIFIC REQUIREMENT (§21):
    Model outputs are PREDICTIONS.
    They must NEVER be presented as observations or reanalysis data.
    The dashboard must clearly distinguish predictions from measurements.

TARGET VARIABLE (§11, §14):
    Default target: Sc-PDSI
    Classification thresholds (documented):
        Normal          : Sc-PDSI > -1.0
        Moderate Drought: -2.0 < Sc-PDSI ≤ -1.0
        Severe Drought  : -3.0 < Sc-PDSI ≤ -2.0
        Extreme Drought : Sc-PDSI ≤ -3.0
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder, StandardScaler

# XGBoost is optional
try:
    from xgboost import XGBClassifier, XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("xgboost not installed. XGBoost models will be skipped.")


# ---------------------------------------------------------------------------
# Drought classification thresholds (Sc-PDSI)
# These must be documented here and in any dashboard that displays them.
# ---------------------------------------------------------------------------
PDSI_CLASSIFICATION = {
    "Normal":           lambda v: v > -1.0,
    "Moderate Drought": lambda v: -2.0 < v <= -1.0,
    "Severe Drought":   lambda v: -3.0 < v <= -2.0,
    "Extreme Drought":  lambda v: v <= -3.0,
}
PDSI_CLASSES = ["Normal", "Moderate Drought", "Severe Drought", "Extreme Drought"]

# Default features used for model training
DEFAULT_FEATURES = [
    "nino34",
    "rainfall_30d",
    "rainfall_90d",
    "rainfall_anomaly",
    "rainfall_percentile",
    "temperature_mean",
    "temperature_anomaly",
    "soil_moisture_layer1",
    "soil_moisture_anomaly",
    "spi_3",
    "spi_6",
    "spei_3",
    "spei_6",
]


def classify_pdsi(pdsi: float) -> str:
    """Classify Sc-PDSI into drought category using documented thresholds."""
    for label, condition in PDSI_CLASSIFICATION.items():
        if condition(pdsi):
            return label
    return "Extreme Drought"


@dataclass
class ModelEvaluationResult:
    model_name: str
    model_type: str              # "regression" | "classification"
    train_period: tuple          # (start_date, end_date)
    test_period: tuple           # (start_date, end_date)
    metrics: dict[str, float]
    feature_importance: Optional[dict] = None
    notes: str = ""
    trained_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PersistenceBaseline:
    """
    Persistence model: predict next period = current period.
    Used as the simplest possible baseline (should be beaten by all real models).
    """

    def __init__(self, target_col: str = "sc_pdsi"):
        self.target_col = target_col
        self.name = "Persistence"

    def evaluate(self, df: pd.DataFrame) -> ModelEvaluationResult:
        if self.target_col not in df.columns or df.empty:
            return ModelEvaluationResult(
                model_name="Persistence",
                model_type="regression",
                train_period=("N/A", "N/A"),
                test_period=("N/A", "N/A"),
                metrics={"mae": 0.0, "rmse": 0.0, "r2": 0.0},
                notes="Target column not available in dataset",
            )
        df = df.dropna(subset=[self.target_col]).sort_values("date")
        if len(df) < 2:
            return ModelEvaluationResult(
                model_name="Persistence",
                model_type="regression",
                train_period=("N/A", "N/A"),
                test_period=("N/A", "N/A"),
                metrics={"mae": 0.0, "rmse": 0.0, "r2": 0.0},
                notes="Insufficient rows for persistence evaluation",
            )
        y_actual = df[self.target_col].values[1:]
        y_pred = df[self.target_col].values[:-1]  # Lag-1 prediction

        mae = mean_absolute_error(y_actual, y_pred)
        rmse = np.sqrt(mean_squared_error(y_actual, y_pred))
        r2 = r2_score(y_actual, y_pred)

        return ModelEvaluationResult(
            model_name="Persistence",
            model_type="regression",
            train_period=(str(df["date"].iloc[0]), str(df["date"].iloc[-2])),
            test_period=(str(df["date"].iloc[1]), str(df["date"].iloc[-1])),
            metrics={"mae": mae, "rmse": rmse, "r2": r2},
            notes="Baseline: predict y(t) = y(t-1)",
        )


class DroughtModelTrainer:
    """
    Trains and evaluates drought prediction models.

    VALIDATION PROTOCOL (requirement §20):
    ┌─────────────────────────────────────────────────┐
    │  Chronological split — NO random shuffling      │
    │  1990–2010: Training                            │
    │  2011–2018: Validation                          │
    │  2019–2026: Test (held out until final eval)    │
    └─────────────────────────────────────────────────┘
    """

    TRAIN_END_YEAR = 2010
    VAL_END_YEAR = 2018

    def __init__(
        self,
        target_col: str = "sc_pdsi",
        task: str = "regression",  # "regression" | "classification"
        feature_cols: Optional[list[str]] = None,
    ):
        self.target_col = target_col
        self.task = task
        self.feature_cols = feature_cols or DEFAULT_FEATURES
        self.scaler = StandardScaler()
        self._trained_models: dict[str, Any] = {}
        self._results: list[ModelEvaluationResult] = []

    def prepare_dataset(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """
        Prepare feature matrix and target vector.
        Uses only columns present in the DataFrame.
        """
        available = [c for c in self.feature_cols if c in df.columns]
        missing = set(self.feature_cols) - set(available)
        if missing:
            logger.warning(f"Features not available in dataset: {missing}")

        if self.target_col not in df.columns or df.empty:
            return pd.DataFrame(), pd.Series(dtype=float)

        df = df.dropna(subset=[self.target_col]).sort_values("date")
        if df.empty:
            return pd.DataFrame(), pd.Series(dtype=float)

        X = df[available].fillna(df[available].median() if not df[available].empty else 0)
        y = df[self.target_col]

        if self.task == "classification":
            y = y.apply(classify_pdsi)

        return X, y

    def chronological_split(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split dataset into train / validation / test using chronological order.
        NEVER shuffles data (time-series requirement).
        """
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        train = df[df["date"].dt.year <= self.TRAIN_END_YEAR]
        val = df[
            (df["date"].dt.year > self.TRAIN_END_YEAR)
            & (df["date"].dt.year <= self.VAL_END_YEAR)
        ]
        test = df[df["date"].dt.year > self.VAL_END_YEAR]

        logger.info(
            f"Chronological split: train={len(train)}, val={len(val)}, test={len(test)}"
        )
        return train, val, test

    def train_all_baselines(self, df: pd.DataFrame) -> list[ModelEvaluationResult]:
        """
        Train and evaluate all baseline models in chronological order.
        Results are sorted by primary metric.
        """
        results = []

        # 0. Persistence baseline
        persistence = PersistenceBaseline(self.target_col)
        results.append(persistence.evaluate(df))

        train, val, test = self.chronological_split(df)
        if train.empty or val.empty:
            logger.warning("Insufficient data for model training.")
            return results

        X_train, y_train = self.prepare_dataset(train)
        X_val, y_val = self.prepare_dataset(val)

        if X_train.empty:
            return results

        X_train_sc = self.scaler.fit_transform(X_train)
        X_val_sc = self.scaler.transform(X_val)

        models = self._get_baseline_models()
        for name, model in models.items():
            try:
                model.fit(X_train_sc, y_train)
                y_pred = model.predict(X_val_sc)
                metrics = self._compute_metrics(y_val, y_pred)
                importance = self._get_feature_importance(model, X_train.columns.tolist())

                result = ModelEvaluationResult(
                    model_name=name,
                    model_type=self.task,
                    train_period=(str(train["date"].iloc[0]), str(train["date"].iloc[-1])),
                    test_period=(str(val["date"].iloc[0]), str(val["date"].iloc[-1])),
                    metrics=metrics,
                    feature_importance=importance,
                    notes=(
                        "Chronological split | Train: ≤2010 | Val: 2011–2018 | "
                        "Test: >2018 (held out)"
                    ),
                )
                results.append(result)
                self._trained_models[name] = model
                logger.info(f"{name}: {metrics}")
            except Exception as exc:
                logger.error(f"Model {name} failed: {exc}")

        self._results = results
        return results

    def predict(
        self,
        features: dict[str, float],
        model_name: str = "RandomForest",
    ) -> dict:
        """
        Generate a drought risk prediction from a feature dict.

        Returns a dict with:
            model_name, drought_probability, risk_level,
            prediction_type = "MODEL_PREDICTION" (NOT an observation)
        """
        if model_name not in self._trained_models:
            spi3 = features.get("spi_3")
            spi3_val = float(spi3) if spi3 is not None and not pd.isna(spi3) else 0.0
            sm_pct = features.get("soil_moisture_percentile")
            sm_val = float(sm_pct) if sm_pct is not None and not pd.isna(sm_pct) else 50.0

            prob = float(np.clip(0.5 - (spi3_val * 0.25) - ((sm_val - 50.0) * 0.005), 0.05, 0.95))
            pred_pdsi = float(spi3_val * 1.5)
            risk = classify_pdsi(pred_pdsi)

            return {
                "model_name": f"{model_name} (Baseline Fallback)",
                "prediction_type": "MODEL_PREDICTION",
                "message": "Heuristic model prediction based on current climate indicators.",
                "scientific_note": (
                    "This is a model prediction, NOT an observed climate measurement."
                ),
                "drought_probability": round(prob, 2),
                "predicted_pdsi": round(pred_pdsi, 2),
                "risk_level": risk,
                "classification_scheme": "SC-PDSI-Palmer",
                "drought_thresholds": {
                    "Normal":           "Sc-PDSI > -1.0",
                    "Moderate Drought": "-2.0 < Sc-PDSI ≤ -1.0",
                    "Severe Drought":   "-3.0 < Sc-PDSI ≤ -2.0",
                    "Extreme Drought":  "Sc-PDSI ≤ -3.0",
                },
            }

        model = self._trained_models[model_name]
        available = [c for c in self.feature_cols if c in features]
        X = pd.DataFrame([{k: features.get(k, np.nan) for k in available}])
        X = X.fillna(0)
        X_sc = self.scaler.transform(X)

        result = {
            "model_name": model_name,
            "prediction_type": "MODEL_PREDICTION",
            "scientific_note": (
                "This is a model prediction, NOT an observed climate measurement."
            ),
            "classification_scheme": "SC-PDSI-Palmer",
            "drought_thresholds": {
                "Normal":           "Sc-PDSI > -1.0",
                "Moderate Drought": "-2.0 < Sc-PDSI ≤ -1.0",
                "Severe Drought":   "-3.0 < Sc-PDSI ≤ -2.0",
                "Extreme Drought":  "Sc-PDSI ≤ -3.0",
            },
        }

        if self.task == "regression":
            pred_value = float(model.predict(X_sc)[0])
            result["predicted_pdsi"] = pred_value
            result["risk_level"] = classify_pdsi(pred_value)
            # Normalise to 0–1 probability: lower PDSI = higher drought probability
            result["drought_probability"] = float(np.clip((pred_value * -1 + 3) / 6, 0, 1))

        elif self.task == "classification":
            pred_class = model.predict(X_sc)[0]
            result["risk_level"] = pred_class
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(X_sc)[0]
                classes = model.classes_
                proba_map = dict(zip(classes, proba))
                result["class_probabilities"] = proba_map
                drought_classes = [
                    c for c in classes if c != "Normal"
                ]
                result["drought_probability"] = float(
                    sum(proba_map.get(c, 0) for c in drought_classes)
                )

        return result

    def _get_baseline_models(self) -> dict[str, Any]:
        models = {}
        if self.task == "regression":
            models["LinearRegression"] = LinearRegression()
            models["RandomForest"] = RandomForestRegressor(
                n_estimators=100, random_state=42
            )
            if XGBOOST_AVAILABLE:
                models["XGBoost"] = XGBRegressor(
                    n_estimators=100, random_state=42, verbosity=0
                )
        elif self.task == "classification":
            models["LogisticRegression"] = LogisticRegression(max_iter=1000)
            models["RandomForest"] = RandomForestClassifier(
                n_estimators=100, random_state=42
            )
            if XGBOOST_AVAILABLE:
                models["XGBoost"] = XGBClassifier(
                    n_estimators=100, random_state=42, verbosity=0
                )
        return models

    def _compute_metrics(self, y_true, y_pred) -> dict[str, float]:
        if self.task == "regression":
            return {
                "mae": float(mean_absolute_error(y_true, y_pred)),
                "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
                "r2": float(r2_score(y_true, y_pred)),
            }
        return {"accuracy": float(accuracy_score(y_true, y_pred))}

    def _get_feature_importance(self, model, feature_names: list) -> Optional[dict]:
        if hasattr(model, "feature_importances_"):
            return dict(zip(feature_names, model.feature_importances_.tolist()))
        if hasattr(model, "coef_"):
            coef = model.coef_.flatten() if model.coef_.ndim > 1 else model.coef_
            return dict(zip(feature_names, coef.tolist()))
        return None
