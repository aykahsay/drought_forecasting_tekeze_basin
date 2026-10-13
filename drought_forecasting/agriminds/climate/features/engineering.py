"""
Climate Feature Engineering (Requirement §9)
=============================================
Derives features from ERA5T observations and the ENSO historical dataset.

IMPORTANT DATA-SOURCE DISTINCTION (Requirement §21):
  - ERA5T observations: reanalysis product
  - elnino.xlsx values: historical climate reference
  - Features computed here: DERIVED PRODUCTS — not observations
  - Model outputs: PREDICTIONS — not measurements

Feature categories:
  Precipitation  : rainfall_7d, 30d, 60d, 90d, 180d, anomaly, percentile
  Temperature    : mean, max, min, anomaly, percentile
  Soil moisture  : layers 1–4, anomaly, percentile
  Drought indices: SPI (1,3,6,12), SPEI (1,3,6,12), Sc-PDSI
  ENSO           : nino34, enso_phase
"""
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger
from scipy import stats

from agriminds.climate.enso import classify_enso_phase, get_enso_dataframe
from agriminds.climate.sources.era5t import ERA5TSource


# ---------------------------------------------------------------------------
# Drought classification thresholds (Sc-PDSI)  (Requirement §11)
# Documented explicitly — do NOT change without updating this docstring.
#
#   Normal       : Sc-PDSI  >  −1.0
#   Moderate     : −2.0  <  Sc-PDSI  ≤  −1.0
#   Severe       : −3.0  <  Sc-PDSI  ≤  −2.0
#   Extreme      : Sc-PDSI  ≤  −3.0
# ---------------------------------------------------------------------------
PDSI_THRESHOLDS = {
    "Normal": (-1.0, float("inf")),
    "Moderate Drought": (-2.0, -1.0),
    "Severe Drought": (-3.0, -2.0),
    "Extreme Drought": (float("-inf"), -3.0),
}


def classify_pdsi(pdsi_value: Optional[float]) -> Optional[str]:
    """Classify Sc-PDSI value into drought category."""
    if pdsi_value is None or (isinstance(pdsi_value, float) and np.isnan(pdsi_value)):
        return None
    for label, (lo, hi) in PDSI_THRESHOLDS.items():
        if lo < pdsi_value <= hi:
            return label
    return "Extreme Drought"


class PrecipitationFeatureEngine:
    """
    Computes rolling precipitation features from ERA5T daily data.

    Input units: m/hour (ERA5T total_precipitation)
    Output units: mm (converted for easier interpretation)
    """

    def compute(
        self, df: pd.DataFrame, location_id: str = "tigray"
    ) -> pd.DataFrame:
        """
        Args:
            df: ERA5T DataFrame filtered to total_precipitation,
                columns: date, value (m/hour)
            location_id: Identifier for the aggregated location.

        Returns:
            DataFrame with precipitation features indexed by date.
        """
        if df.empty:
            return pd.DataFrame()

        # Aggregate to daily totals (m) and convert to mm
        daily = (
            df.groupby("date")["value"]
            .sum()
            .reset_index()
            .rename(columns={"value": "precip_mm_day"})
        )
        daily["date"] = pd.to_datetime(daily["date"])
        daily = daily.sort_values("date").set_index("date")
        daily["precip_mm_day"] *= 1000.0  # m → mm

        features = pd.DataFrame(index=daily.index)
        for window in [7, 30, 60, 90, 180]:
            col = f"rainfall_{window}d"
            features[col] = daily["precip_mm_day"].rolling(window, min_periods=1).sum()

        # Anomaly: deviation from long-term daily mean [mm]
        clim_mean = daily["precip_mm_day"].mean()
        features["rainfall_anomaly"] = daily["precip_mm_day"] - clim_mean

        # Percentile rank (0–100)
        features["rainfall_percentile"] = (
            daily["precip_mm_day"].rank(pct=True) * 100
        )

        features["location_id"] = location_id
        return features.reset_index().rename(columns={"date": "date"})


class TemperatureFeatureEngine:
    """
    Computes temperature features from ERA5T 2m_temperature data.

    Input units: K (Kelvin)
    Output units: °C (converted for usability)
    """

    def compute(
        self, df: pd.DataFrame, location_id: str = "tigray"
    ) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        # K → °C
        df = df.copy()
        df["value_c"] = df["value"] - 273.15

        daily = df.groupby("date")["value_c"].agg(["mean", "max", "min"])
        daily.columns = ["temperature_mean", "temperature_max", "temperature_min"]
        daily.index = pd.to_datetime(daily.index)
        daily = daily.sort_index()

        clim_mean = daily["temperature_mean"].mean()
        daily["temperature_anomaly"] = daily["temperature_mean"] - clim_mean
        daily["temperature_percentile"] = (
            daily["temperature_mean"].rank(pct=True) * 100
        )

        daily["location_id"] = location_id
        return daily.reset_index().rename(columns={"index": "date"})


class SoilMoistureFeatureEngine:
    """
    Computes soil moisture features from ERA5T volumetric soil water layers.

    Input/Output units: m³/m³ (volumetric fraction)
    """

    LAYER_VARS = {
        "volumetric_soil_water_layer_1": "soil_moisture_layer1",
        "volumetric_soil_water_layer_2": "soil_moisture_layer2",
        "volumetric_soil_water_layer_3": "soil_moisture_layer3",
        "volumetric_soil_water_layer_4": "soil_moisture_layer4",
    }

    def compute(
        self, df: pd.DataFrame, location_id: str = "tigray"
    ) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        result = pd.DataFrame()
        for var_name, feature_name in self.LAYER_VARS.items():
            layer_df = df[df["variable"] == var_name]
            if layer_df.empty:
                continue
            daily = layer_df.groupby("date")["value"].mean()
            daily.index = pd.to_datetime(daily.index)
            result[feature_name] = daily

        if result.empty:
            return pd.DataFrame()

        result = result.sort_index()

        # Use layer 1 (surface) for anomaly/percentile
        if "soil_moisture_layer1" in result.columns:
            sm1 = result["soil_moisture_layer1"]
            result["soil_moisture_anomaly"] = sm1 - sm1.mean()
            result["soil_moisture_percentile"] = sm1.rank(pct=True) * 100

        result["location_id"] = location_id
        return result.reset_index().rename(columns={"index": "date"})


class SPIEngine:
    """
    Standardized Precipitation Index (SPI) computation.

    SPI is computed by fitting a Gamma distribution to the precipitation
    accumulation series and transforming to standard normal deviates.

    Timescales: 1, 3, 6, 12 months.

    Reference: McKee et al. (1993), NOAA SPI guidelines.

    IMPORTANT: SPI values are DERIVED indicators, not observations.
    """

    def compute(
        self, monthly_precip: pd.Series, timescales: list[int] = [1, 3, 6, 12]
    ) -> pd.DataFrame:
        """
        Args:
            monthly_precip: Monthly precipitation totals (mm), DatetimeIndex.
            timescales:     SPI timescales in months.

        Returns:
            DataFrame with columns spi_1, spi_3, spi_6, spi_12.
        """
        result = pd.DataFrame(index=monthly_precip.index)

        for k in timescales:
            rolling = monthly_precip.rolling(k, min_periods=k).sum()
            spi = self._fit_gamma_spi(rolling)
            result[f"spi_{k}"] = spi

        return result

    def _fit_gamma_spi(self, series: pd.Series) -> pd.Series:
        """Fit Gamma distribution and return SPI values."""
        valid = series.dropna()
        if len(valid) < 10:
            return pd.Series(np.nan, index=series.index)

        # Add small offset to handle zero precipitation
        valid_pos = valid[valid > 0]
        if len(valid_pos) < 5:
            return pd.Series(np.nan, index=series.index)

        try:
            shape, loc, scale = stats.gamma.fit(valid_pos, floc=0)
            prob_zero = (valid == 0).sum() / len(valid)

            spi_values = pd.Series(np.nan, index=series.index)
            non_zero = series > 0
            if non_zero.any():
                cdf = stats.gamma.cdf(series[non_zero], shape, loc=loc, scale=scale)
                adj_cdf = prob_zero + (1 - prob_zero) * cdf
                adj_cdf = np.clip(adj_cdf, 1e-6, 1 - 1e-6)
                spi_values[non_zero] = stats.norm.ppf(adj_cdf)

            # Zero-precip months
            zero_prob_cdf = prob_zero / 2
            if zero_prob_cdf > 1e-6:
                spi_zero = stats.norm.ppf(zero_prob_cdf)
                spi_values[series == 0] = spi_zero

            return spi_values
        except Exception as exc:
            logger.warning(f"SPI gamma fit failed: {exc}")
            return pd.Series(np.nan, index=series.index)


class SPEIEngine:
    """
    Standardized Precipitation Evapotranspiration Index (SPEI).

    SPEI extends SPI by incorporating potential evapotranspiration (PET).
    PET is estimated from temperature using the Thornthwaite method.

    Input: monthly precipitation (mm), monthly mean temperature (°C).
    Output: SPEI values (dimensionless standard deviates).

    IMPORTANT: SPEI is a derived drought indicator, not an observation.
    """

    def compute(
        self,
        monthly_precip: pd.Series,
        monthly_temp_c: pd.Series,
        timescales: list[int] = [1, 3, 6, 12],
    ) -> pd.DataFrame:
        pet = self._thornthwaite_pet(monthly_temp_c)
        water_balance = monthly_precip - pet

        spi_engine = SPIEngine()
        # Use SPI engine on water balance as SPEI approximation
        result = pd.DataFrame(index=monthly_precip.index)
        for k in timescales:
            rolling_wb = water_balance.rolling(k, min_periods=k).sum()
            spei = spi_engine._fit_gamma_spi(
                rolling_wb - rolling_wb.min() + 0.001  # shift to positive
            )
            result[f"spei_{k}"] = spei

        return result

    def _thornthwaite_pet(self, temp_c: pd.Series) -> pd.Series:
        """
        Thornthwaite PET estimation.
        Returns PET in mm/month.
        Only valid for monthly mean temperatures > 0°C.
        """
        temp_positive = temp_c.clip(lower=0)
        I = (temp_positive / 5.0) ** 1.514  # Heat index
        I_annual = I.rolling(12, min_periods=12).sum()
        a = 6.75e-7 * I_annual**3 - 7.71e-5 * I_annual**2 + 1.792e-2 * I_annual + 0.49239
        pet = 16 * (10 * temp_positive / I_annual.replace(0, np.nan)) ** a
        return pet.fillna(0)


class ENSOFeatureEngine:
    """
    Builds ENSO-related features from the historical elnino.xlsx dataset.
    These features link the historical ENSO signal to current conditions.
    """

    def get_seasonal_enso(self, year: int, season: str) -> Optional[float]:
        """
        Retrieve Niño 3.4 value for a specific year and season.

        Args:
            year:   Year (e.g. 2024)
            season: One of 'DJF', 'MAM', 'JJA', 'SON', 'annual'

        Returns:
            Niño 3.4 value or None if not available.
        """
        df = get_enso_dataframe()
        if df.empty or "year" not in df.columns:
            return None
        row = df[df["year"] == year]
        if row.empty:
            return None
        col = f"nino34_{season.lower()}"
        if col not in row.columns:
            return None
        val = row[col].values[0]
        return float(val) if pd.notna(val) else None

    def build_enso_feature_series(self, dates: pd.DatetimeIndex) -> pd.DataFrame:
        """
        For each date, look up the corresponding Niño 3.4 value and ENSO phase.

        Returns DataFrame with columns: date, nino34, enso_phase.
        """
        df = get_enso_dataframe()
        year_to_annual = dict(zip(df["year"], df["nino34_annual"])) if not df.empty and "year" in df.columns else {}

        records = []
        for d in dates:
            nino34 = year_to_annual.get(d.year)
            phase = classify_enso_phase(nino34)
            records.append({"date": d, "nino34": nino34, "enso_phase": phase})

        return pd.DataFrame(records)


class FeatureEngineeringPipeline:
    """
    Orchestrates all feature engineering steps.

    Combines:
      1. ERA5T observations (precipitation, temperature, soil moisture)
      2. Historical ENSO data (elnino.xlsx)
      3. Computed drought indices (SPI, SPEI)

    The result is a model-ready feature table (Requirement §11).
    """

    def __init__(self):
        self.era5t = ERA5TSource()
        self.precip_engine = PrecipitationFeatureEngine()
        self.temp_engine = TemperatureFeatureEngine()
        self.sm_engine = SoilMoistureFeatureEngine()
        self.spi_engine = SPIEngine()
        self.spei_engine = SPEIEngine()
        self.enso_engine = ENSOFeatureEngine()

    def build_features(
        self,
        start_date: date,
        end_date: date,
        location_id: str = "tigray",
    ) -> pd.DataFrame:
        """
        Build a complete feature table for the given date range and location.

        Returns a DataFrame with all features merged on 'date'.
        Data sources are explicitly tracked in 'data_sources' column.
        """
        logger.info(
            f"Building climate features: {start_date} to {end_date} | {location_id}"
        )
        data_sources = []

        # ── Precipitation features (ERA5T) ─────────────────────────────────
        precip_df = self.era5t.get_data(
            start_date, end_date, variables=["total_precipitation"]
        )
        precip_features = pd.DataFrame()
        if not precip_df.empty:
            precip_features = self.precip_engine.compute(precip_df, location_id)
            data_sources.append("ERA5T:total_precipitation")

        # ── Temperature features (ERA5T) ───────────────────────────────────
        temp_df = self.era5t.get_data(
            start_date, end_date, variables=["2m_temperature"]
        )
        temp_features = pd.DataFrame()
        if not temp_df.empty:
            temp_features = self.temp_engine.compute(temp_df, location_id)
            data_sources.append("ERA5T:2m_temperature")

        # ── Soil moisture features (ERA5T) ─────────────────────────────────
        sm_vars = [
            "volumetric_soil_water_layer_1",
            "volumetric_soil_water_layer_2",
            "volumetric_soil_water_layer_3",
            "volumetric_soil_water_layer_4",
        ]
        sm_df = self.era5t.get_data(start_date, end_date, variables=sm_vars)
        sm_features = pd.DataFrame()
        if not sm_df.empty:
            sm_features = self.sm_engine.compute(sm_df, location_id)
            data_sources.append("ERA5T:soil_moisture")

        # ── ENSO features (elnino.xlsx) ────────────────────────────────────
        all_dates = pd.date_range(start=start_date, end=end_date, freq="D")
        enso_features = self.enso_engine.build_enso_feature_series(all_dates)
        if not enso_features.empty:
            data_sources.append("elnino.xlsx:ENSO")

        # ── Merge all features on date ─────────────────────────────────────
        merged = self._merge_features(
            precip_features, temp_features, sm_features, enso_features
        )

        # ── SPI / SPEI (Drought indices — derived) ─────────────────────────
        if not merged.empty and "rainfall_30d" in merged.columns:
            merged = self._add_drought_indices(merged)
            data_sources.append("derived:SPI+SPEI")

        # ── Add ENSO-historical Sc-PDSI where available ───────────────────
        merged = self._add_historical_pdsi(merged)

        merged["data_sources"] = "; ".join(data_sources)
        logger.info(f"Feature table built: {len(merged)} rows, {len(merged.columns)} columns.")
        return merged

    def _merge_features(self, *dfs: pd.DataFrame) -> pd.DataFrame:
        """Left-join all feature DataFrames on the 'date' column."""
        result = None
        for df in dfs:
            if df is None or df.empty:
                continue
            df = df.copy()
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            if result is None:
                result = df
            else:
                on_cols = ["date"]
                if "location_id" in df.columns and "location_id" in result.columns:
                    on_cols.append("location_id")
                result = result.merge(df, on=on_cols, how="outer")

        return result if result is not None else pd.DataFrame()

    def _add_drought_indices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute SPI and SPEI from monthly-aggregated precipitation."""
        if "date" not in df.columns:
            return df

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        # Monthly totals needed for SPI/SPEI
        if "rainfall_30d" in df.columns:
            monthly = df.set_index("date")["rainfall_30d"].resample("ME").mean()

            spi_df = self.spi_engine.compute(monthly)
            spi_df.index.name = "date"
            spi_df = spi_df.reset_index()
            spi_df["date"] = pd.to_datetime(spi_df["date"])

            df = df.merge(spi_df, on="date", how="left")

            if "temperature_mean" in df.columns:
                temp_monthly = df.set_index("date")["temperature_mean"].resample("ME").mean()
                precip_monthly = df.set_index("date")["rainfall_30d"].resample("ME").mean()
                spei_df = self.spei_engine.compute(precip_monthly, temp_monthly)
                spei_df.index.name = "date"
                spei_df = spei_df.reset_index()
                df = df.merge(spei_df, on="date", how="left")

        return df

    def _add_historical_pdsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge Sc-PDSI from the historical elnino.xlsx dataset.
        This is the target variable for historical model training.
        """
        enso_df = get_enso_dataframe()
        if enso_df.empty or df.empty or "year" not in enso_df.columns:
            return df

        pdsi_map = dict(zip(enso_df["year"], enso_df.get("sc_pdsi", [])))

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            if "sc_pdsi" not in df.columns:
                df["sc_pdsi"] = df["date"].dt.year.map(pdsi_map)

        return df
