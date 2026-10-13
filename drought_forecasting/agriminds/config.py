"""
Application configuration using pydantic-settings.
All sensitive values come from environment variables / .env file.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # ── Database ────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./agriminds.db"

    # ── CDS API (ERA5T) ─────────────────────────────────────────────────────
    # Credentials are NEVER exposed in frontend code or committed to Git.
    cds_api_url: str = "https://cds.climate.copernicus.eu/api/v2"
    cds_api_key: Optional[str] = None  # Set in .env — never hard-coded

    # ── Spatial bounding box (Ethiopia — National Grid) ────────────────────
    # Designed to expand: Ethiopia (National Grid) → East Africa (IGAD/ICPAC)
    era5_bbox_north: float = 15.0
    era5_bbox_south: float = 12.0
    era5_bbox_west: float = 36.5
    era5_bbox_east: float = 40.0

    # ── Scheduler ───────────────────────────────────────────────────────────
    ingestion_cron: str = "0 6 * * *"  # Daily at 06:00 UTC

    # ── Paths ────────────────────────────────────────────────────────────────
    data_dir: Path = Path("data")
    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")
    elnino_dataset_path: Path = Path("elnino.xlsx")

    @field_validator("raw_data_dir", "processed_data_dir", "data_dir", mode="before")
    @classmethod
    def make_dirs(cls, v):
        p = Path(v)
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ── ERA5T variables ─────────────────────────────────────────────────────
    # Configurable list — add variables without code changes
    era5_variables: list[str] = [
        "total_precipitation",
        "2m_temperature",
        "2m_dewpoint_temperature",
        "surface_pressure",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "surface_solar_radiation_downwards",
        "volumetric_soil_water_layer_1",
        "volumetric_soil_water_layer_2",
        "volumetric_soil_water_layer_3",
        "volumetric_soil_water_layer_4",
    ]

    @property
    def era5_bbox(self) -> list[float]:
        """[North, West, South, East] — CDS API format."""
        return [
            self.era5_bbox_north,
            self.era5_bbox_west,
            self.era5_bbox_south,
            self.era5_bbox_east,
        ]

    @property
    def cds_configured(self) -> bool:
        """True only when a real API key has been provided."""
        return bool(self.cds_api_key and self.cds_api_key != "your-cds-api-key-here")


@lru_cache
def get_settings() -> Settings:
    return Settings()
