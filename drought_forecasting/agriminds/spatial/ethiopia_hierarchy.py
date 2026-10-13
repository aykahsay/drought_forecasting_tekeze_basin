"""
Ethiopia Multi-Tier Spatial & Climate Hierarchy
================================================
Defines the complete 4-tier administrative and climate hierarchy of Ethiopia:
  Tier 1: National (All 13 Regional States & Chartered Cities)
  Tier 2: Zonal Tier (Administrative Zones within each Region)
  Tier 3: Woreda Tier (Woredas within each Zone, with AEZ overlays)
  Tier 4: Kebele Tier (Local Kebeles, Ground Truth, Water Points & Village Distances)

Enables full drill-down exploration across:
  - El Niño Teleconnection SST Anomaly (-2 to +2 °C)
  - Drought Severity Index (SPI / SPEI / VHI: -2 to +2)
  - Precipitation Accumulation & Anomaly (100 to 1000 mm)
  - Monthly Mean Precipitation & Rain Days (2025 vs 2026 Timeseries)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

# ────────────────────────────────────────────────────────────────────────────
# 1. TIER 1: NATIONAL LEVEL — ALL REGIONS OF ETHIOPIA
# ────────────────────────────────────────────────────────────────────────────
# Canvas space for National Map: viewBox="0 0 650 520"
# Real Ethiopia bounds: 3.0°N to 15.0°N, 33.0°E to 48.0°E

ETHIOPIA_NATIONAL_REGIONS: List[Dict[str, Any]] = [
    {
        "region_id": "amhara",
        "name": "Amhara Region",
        "name_local": "አማራ ክልል",
        "capital": "Bahir Dar",
        "centroid_lat": 11.60,
        "centroid_lon": 37.80,
        "area_km2": 154709,
        "zones_count": 11,
        "woredas_count": 180,
        "primary_livelihood": "Crop Agriculture (Teff, Wheat, Barley) & Agro-Pastoral",
        "el_nino_index_2026": 1.75,
        "drought_index_2026": -1.35,
        "precipitation_2026_mm": 520,
        "precipitation_2025_mm": 670,
        "rain_days_2026": 42,
        "rain_days_2025": 58,
        # Normalized SVG polygon representing Amhara within national frame
        "svg_path": "M 180,105 L 235,90 L 285,120 L 305,175 L 295,225 L 245,250 L 195,235 L 165,180 L 160,135 Z",
        "label_x": 230,
        "label_y": 165,
        "monthly_data": {
            "jun": {"precip_2026": 17.8, "precip_2025": 11.5, "rain_days_2026": 7.5, "rain_days_2025": 13.5, "el_nino": 1.5, "drought": -1.1},
            "jul": {"precip_2026": 14.3, "precip_2025": 9.5, "rain_days_2026": 5.5, "rain_days_2025": 10.8, "el_nino": 1.6, "drought": -1.3},
            "aug": {"precip_2026": 11.2, "precip_2025": 10.2, "rain_days_2026": 4.5, "rain_days_2025": 9.2, "el_nino": 1.7, "drought": -1.5},
            "sep": {"precip_2026": 14.5, "precip_2025": 16.8, "rain_days_2026": 6.5, "rain_days_2025": 12.2, "el_nino": 1.8, "drought": -1.4},
            "oct": {"precip_2026": 12.0, "precip_2025": 15.0, "rain_days_2026": 5.5, "rain_days_2025": 10.5, "el_nino": 1.8, "drought": -1.4},
            "nov": {"precip_2026": 10.0, "precip_2025": 11.5, "rain_days_2026": 4.5, "rain_days_2025": 13.0, "el_nino": 1.7, "drought": -1.3},
            "dec": {"precip_2026": 9.2, "precip_2025": 12.0, "rain_days_2026": 4.5, "rain_days_2025": 14.8, "el_nino": 1.7, "drought": -1.3},
        }
    },
    {
        "region_id": "tigray",
        "name": "Tigray Region",
        "name_local": "ትግራይ ክልል",
        "capital": "Mekelle",
        "centroid_lat": 14.03,
        "centroid_lon": 38.75,
        "area_km2": 50079,
        "zones_count": 7,
        "woredas_count": 52,
        "primary_livelihood": "Highland Cereal Farming & Semi-Arid Lowlands",
        "el_nino_index_2026": 1.60,
        "drought_index_2026": -1.42,
        "precipitation_2026_mm": 410,
        "precipitation_2025_mm": 570,
        "rain_days_2026": 34,
        "rain_days_2025": 52,
        "svg_path": "M 190,45 L 260,35 L 290,75 L 280,115 L 225,95 L 180,95 L 165,65 Z",
        "label_x": 230,
        "label_y": 70,
        "monthly_data": {
            "jun": {"precip_2026": 15.0, "precip_2025": 9.5, "rain_days_2026": 6.0, "rain_days_2025": 11.5, "el_nino": 1.4, "drought": -1.2},
            "jul": {"precip_2026": 12.5, "precip_2025": 8.0, "rain_days_2026": 5.0, "rain_days_2025": 9.5, "el_nino": 1.5, "drought": -1.4},
            "aug": {"precip_2026": 9.8, "precip_2025": 8.5, "rain_days_2026": 4.0, "rain_days_2025": 8.0, "el_nino": 1.6, "drought": -1.6},
            "sep": {"precip_2026": 12.0, "precip_2025": 14.5, "rain_days_2026": 5.0, "rain_days_2025": 10.5, "el_nino": 1.7, "drought": -1.5},
            "oct": {"precip_2026": 9.5, "precip_2025": 13.0, "rain_days_2026": 4.0, "rain_days_2025": 9.0, "el_nino": 1.7, "drought": -1.4},
            "nov": {"precip_2026": 7.5, "precip_2025": 9.5, "rain_days_2026": 3.5, "rain_days_2025": 11.0, "el_nino": 1.6, "drought": -1.3},
            "dec": {"precip_2026": 6.8, "precip_2025": 10.0, "rain_days_2026": 3.5, "rain_days_2025": 12.5, "el_nino": 1.6, "drought": -1.3},
        }
    },
    {
        "region_id": "afar",
        "name": "Afar Region",
        "name_local": "አፋር ክልል",
        "capital": "Semera",
        "centroid_lat": 11.75,
        "centroid_lon": 40.95,
        "area_km2": 72053,
        "zones_count": 5,
        "woredas_count": 32,
        "primary_livelihood": "Pastoralist (Camels, Goats) & Irrigated Agro-Pastoral",
        "el_nino_index_2026": 1.88,
        "drought_index_2026": -1.68,
        "precipitation_2026_mm": 210,
        "precipitation_2025_mm": 320,
        "rain_days_2026": 18,
        "rain_days_2025": 29,
        "svg_path": "M 285,55 L 340,90 L 375,150 L 350,220 L 305,215 L 290,140 L 285,90 Z",
        "label_x": 330,
        "label_y": 140,
        "monthly_data": {
            "jun": {"precip_2026": 8.0, "precip_2025": 6.0, "rain_days_2026": 3.0, "rain_days_2025": 5.0, "el_nino": 1.6, "drought": -1.4},
            "jul": {"precip_2026": 11.0, "precip_2025": 8.0, "rain_days_2026": 4.0, "rain_days_2025": 6.5, "el_nino": 1.7, "drought": -1.6},
            "aug": {"precip_2026": 9.5, "precip_2025": 9.0, "rain_days_2026": 3.5, "rain_days_2025": 5.5, "el_nino": 1.8, "drought": -1.7},
            "sep": {"precip_2026": 6.5, "precip_2025": 8.5, "rain_days_2026": 2.5, "rain_days_2025": 4.5, "el_nino": 1.9, "drought": -1.8},
            "oct": {"precip_2026": 4.0, "precip_2025": 6.0, "rain_days_2026": 1.5, "rain_days_2025": 3.5, "el_nino": 1.8, "drought": -1.6},
            "nov": {"precip_2026": 3.5, "precip_2025": 4.5, "rain_days_2026": 1.5, "rain_days_2025": 3.0, "el_nino": 1.7, "drought": -1.5},
            "dec": {"precip_2026": 3.0, "precip_2025": 4.0, "rain_days_2026": 1.0, "rain_days_2025": 2.5, "el_nino": 1.7, "drought": -1.5},
        }
    },
    {
        "region_id": "oromia",
        "name": "Oromia Region",
        "name_local": "ኦሮሚያ ክልል",
        "capital": "Finfinnee / Adama",
        "centroid_lat": 8.00,
        "centroid_lon": 39.00,
        "area_km2": 284538,
        "zones_count": 21,
        "woredas_count": 330,
        "primary_livelihood": "Breadbasket Agriculture (Cereals, Coffee) & Pastoral South (Borana)",
        "el_nino_index_2026": 1.45,
        "drought_index_2026": -1.15,
        "precipitation_2026_mm": 680,
        "precipitation_2025_mm": 790,
        "rain_days_2026": 55,
        "rain_days_2025": 72,
        "svg_path": "M 150,220 L 225,235 L 290,230 L 340,240 L 400,280 L 420,340 L 380,410 L 310,440 L 250,420 L 210,340 L 150,280 Z",
        "label_x": 280,
        "label_y": 320,
        "monthly_data": {
            "jun": {"precip_2026": 21.0, "precip_2025": 14.5, "rain_days_2026": 9.0, "rain_days_2025": 16.0, "el_nino": 1.3, "drought": -0.9},
            "jul": {"precip_2026": 18.5, "precip_2025": 12.0, "rain_days_2026": 8.0, "rain_days_2025": 14.0, "el_nino": 1.4, "drought": -1.1},
            "aug": {"precip_2026": 15.0, "precip_2025": 13.5, "rain_days_2026": 6.5, "rain_days_2025": 12.5, "el_nino": 1.5, "drought": -1.2},
            "sep": {"precip_2026": 18.0, "precip_2025": 20.5, "rain_days_2026": 8.0, "rain_days_2025": 15.0, "el_nino": 1.6, "drought": -1.2},
            "oct": {"precip_2026": 14.5, "precip_2025": 18.0, "rain_days_2026": 6.5, "rain_days_2025": 13.0, "el_nino": 1.5, "drought": -1.1},
            "nov": {"precip_2026": 11.5, "precip_2025": 13.5, "rain_days_2026": 5.0, "rain_days_2025": 15.5, "el_nino": 1.4, "drought": -1.0},
            "dec": {"precip_2026": 10.2, "precip_2025": 14.0, "rain_days_2026": 4.5, "rain_days_2025": 16.5, "el_nino": 1.4, "drought": -1.0},
        }
    },
    {
        "region_id": "somali",
        "name": "Somali Region",
        "name_local": "ሶማሌ ክልል",
        "capital": "Jigjiga",
        "centroid_lat": 6.66,
        "centroid_lon": 44.28,
        "area_km2": 279252,
        "zones_count": 11,
        "woredas_count": 93,
        "primary_livelihood": "Nomadic Pastoralism (Camels, Sheep, Goats) & Riverine Farming",
        "el_nino_index_2026": 1.95,
        "drought_index_2026": -1.92,
        "precipitation_2026_mm": 180,
        "precipitation_2025_mm": 310,
        "rain_days_2026": 14,
        "rain_days_2025": 26,
        "svg_path": "M 390,210 L 470,225 L 590,270 L 610,340 L 540,410 L 450,420 L 410,350 L 380,270 Z",
        "label_x": 490,
        "label_y": 310,
        "monthly_data": {
            "jun": {"precip_2026": 4.0, "precip_2025": 3.0, "rain_days_2026": 1.5, "rain_days_2025": 2.5, "el_nino": 1.7, "drought": -1.7},
            "jul": {"precip_2026": 3.0, "precip_2025": 2.5, "rain_days_2026": 1.0, "rain_days_2025": 2.0, "el_nino": 1.8, "drought": -1.8},
            "aug": {"precip_2026": 3.5, "precip_2025": 3.0, "rain_days_2026": 1.0, "rain_days_2025": 2.5, "el_nino": 1.9, "drought": -1.9},
            "sep": {"precip_2026": 5.0, "precip_2025": 7.0, "rain_days_2026": 2.0, "rain_days_2025": 4.0, "el_nino": 2.0, "drought": -2.0},
            "oct": {"precip_2026": 8.5, "precip_2025": 14.0, "rain_days_2026": 3.5, "rain_days_2025": 7.5, "el_nino": 1.9, "drought": -1.9},
            "nov": {"precip_2026": 6.0, "precip_2025": 11.0, "rain_days_2026": 2.5, "rain_days_2025": 6.0, "el_nino": 1.8, "drought": -1.8},
            "dec": {"precip_2026": 3.5, "precip_2025": 6.5, "rain_days_2026": 1.5, "rain_days_2025": 3.5, "el_nino": 1.8, "drought": -1.8},
        }
    },
    {
        "region_id": "sidama",
        "name": "Sidama Region",
        "name_local": "ሲዳማ ክልል",
        "capital": "Hawassa",
        "centroid_lat": 6.70,
        "centroid_lon": 38.45,
        "area_km2": 12000,
        "zones_count": 4,
        "woredas_count": 30,
        "primary_livelihood": "Highland Agroforestry (Coffee, Enset, Avocado)",
        "el_nino_index_2026": 1.10,
        "drought_index_2026": -0.45,
        "precipitation_2026_mm": 920,
        "precipitation_2025_mm": 980,
        "rain_days_2026": 68,
        "rain_days_2025": 78,
        "svg_path": "M 255,340 L 290,345 L 285,380 L 250,375 Z",
        "label_x": 270,
        "label_y": 360,
        "monthly_data": {
            "jun": {"precip_2026": 24.0, "precip_2025": 18.0, "rain_days_2026": 11.0, "rain_days_2025": 16.0, "el_nino": 1.0, "drought": -0.3},
            "jul": {"precip_2026": 21.0, "precip_2025": 16.0, "rain_days_2026": 9.5, "rain_days_2025": 14.0, "el_nino": 1.1, "drought": -0.4},
            "aug": {"precip_2026": 18.5, "precip_2025": 17.0, "rain_days_2026": 8.0, "rain_days_2025": 13.0, "el_nino": 1.2, "drought": -0.5},
            "sep": {"precip_2026": 22.0, "precip_2025": 23.0, "rain_days_2026": 10.0, "rain_days_2025": 15.5, "el_nino": 1.2, "drought": -0.5},
            "oct": {"precip_2026": 18.0, "precip_2025": 20.0, "rain_days_2026": 8.5, "rain_days_2025": 13.5, "el_nino": 1.1, "drought": -0.4},
            "nov": {"precip_2026": 14.0, "precip_2025": 15.0, "rain_days_2026": 6.5, "rain_days_2025": 14.0, "el_nino": 1.0, "drought": -0.4},
            "dec": {"precip_2026": 12.0, "precip_2025": 14.0, "rain_days_2026": 5.5, "rain_days_2025": 15.0, "el_nino": 1.0, "drought": -0.4},
        }
    },
    {
        "region_id": "south_ethiopia",
        "name": "South Ethiopia Region",
        "name_local": "ደቡብ ኢትዮጵያ ክልል",
        "capital": "Wolaita Sodo",
        "centroid_lat": 6.05,
        "centroid_lon": 36.72,
        "area_km2": 54000,
        "zones_count": 6,
        "woredas_count": 55,
        "primary_livelihood": "Mixed Highlands & Lower Omo Pastoralism",
        "el_nino_index_2026": 1.30,
        "drought_index_2026": -0.85,
        "precipitation_2026_mm": 740,
        "precipitation_2025_mm": 830,
        "rain_days_2026": 58,
        "rain_days_2025": 70,
        "svg_path": "M 195,360 L 250,375 L 240,440 L 180,410 Z",
        "label_x": 215,
        "label_y": 400,
        "monthly_data": {
            "jun": {"precip_2026": 20.0, "precip_2025": 15.0, "rain_days_2026": 8.5, "rain_days_2025": 14.5, "el_nino": 1.2, "drought": -0.7},
            "jul": {"precip_2026": 17.0, "precip_2025": 13.0, "rain_days_2026": 7.5, "rain_days_2025": 12.5, "el_nino": 1.3, "drought": -0.8},
            "aug": {"precip_2026": 15.5, "precip_2025": 14.5, "rain_days_2026": 7.0, "rain_days_2025": 11.5, "el_nino": 1.3, "drought": -0.9},
            "sep": {"precip_2026": 18.5, "precip_2025": 20.0, "rain_days_2026": 8.5, "rain_days_2025": 14.0, "el_nino": 1.4, "drought": -0.9},
            "oct": {"precip_2026": 15.0, "precip_2025": 17.5, "rain_days_2026": 7.0, "rain_days_2025": 12.0, "el_nino": 1.3, "drought": -0.8},
            "nov": {"precip_2026": 12.0, "precip_2025": 13.5, "rain_days_2026": 5.5, "rain_days_2025": 13.0, "el_nino": 1.2, "drought": -0.8},
            "dec": {"precip_2026": 10.5, "precip_2025": 12.5, "rain_days_2026": 5.0, "rain_days_2025": 14.0, "el_nino": 1.2, "drought": -0.8},
        }
    },
    {
        "region_id": "benishangul",
        "name": "Benishangul-Gumuz",
        "name_local": "ቤንሻንጉል ጉሙዝ ክልል",
        "capital": "Assosa",
        "centroid_lat": 10.78,
        "centroid_lon": 35.56,
        "area_km2": 50699,
        "zones_count": 3,
        "woredas_count": 22,
        "primary_livelihood": "Lowland Agriculture, Bamboo Agroforestry & Gold Mining",
        "el_nino_index_2026": 1.05,
        "drought_index_2026": -0.30,
        "precipitation_2026_mm": 890,
        "precipitation_2025_mm": 930,
        "rain_days_2026": 64,
        "rain_days_2025": 74,
        "svg_path": "M 110,140 L 165,135 L 170,215 L 115,225 Z",
        "label_x": 135,
        "label_y": 180,
        "monthly_data": {
            "jun": {"precip_2026": 23.0, "precip_2025": 16.0, "rain_days_2026": 10.5, "rain_days_2025": 15.0, "el_nino": 1.0, "drought": -0.2},
            "jul": {"precip_2026": 20.0, "precip_2025": 15.0, "rain_days_2026": 9.0, "rain_days_2025": 13.5, "el_nino": 1.0, "drought": -0.3},
            "aug": {"precip_2026": 17.5, "precip_2025": 16.0, "rain_days_2026": 8.0, "rain_days_2025": 12.0, "el_nino": 1.1, "drought": -0.3},
            "sep": {"precip_2026": 21.0, "precip_2025": 22.0, "rain_days_2026": 9.5, "rain_days_2025": 14.5, "el_nino": 1.1, "drought": -0.3},
            "oct": {"precip_2026": 17.0, "precip_2025": 19.0, "rain_days_2026": 8.0, "rain_days_2025": 13.0, "el_nino": 1.0, "drought": -0.3},
            "nov": {"precip_2026": 13.0, "precip_2025": 14.0, "rain_days_2026": 6.0, "rain_days_2025": 13.5, "el_nino": 1.0, "drought": -0.2},
            "dec": {"precip_2026": 11.0, "precip_2025": 12.5, "rain_days_2026": 5.0, "rain_days_2025": 14.0, "el_nino": 1.0, "drought": -0.2},
        }
    },
    {
        "region_id": "gambella",
        "name": "Gambella Region",
        "name_local": "ጋምቤላ ክልል",
        "capital": "Gambella",
        "centroid_lat": 8.25,
        "centroid_lon": 34.58,
        "area_km2": 29783,
        "zones_count": 3,
        "woredas_count": 14,
        "primary_livelihood": "Riverine Agriculture, Fishery & Agro-Pastoralism",
        "el_nino_index_2026": 0.95,
        "drought_index_2026": -0.20,
        "precipitation_2026_mm": 980,
        "precipitation_2025_mm": 1020,
        "rain_days_2026": 72,
        "rain_days_2025": 80,
        "svg_path": "M 85,235 L 140,240 L 155,295 L 95,290 Z",
        "label_x": 115,
        "label_y": 265,
        "monthly_data": {
            "jun": {"precip_2026": 25.0, "precip_2025": 19.0, "rain_days_2026": 11.5, "rain_days_2025": 16.5, "el_nino": 0.9, "drought": -0.1},
            "jul": {"precip_2026": 22.0, "precip_2025": 17.0, "rain_days_2026": 10.0, "rain_days_2025": 15.0, "el_nino": 0.9, "drought": -0.2},
            "aug": {"precip_2026": 19.0, "precip_2025": 17.5, "rain_days_2026": 8.5, "rain_days_2025": 13.0, "el_nino": 1.0, "drought": -0.2},
            "sep": {"precip_2026": 23.0, "precip_2025": 24.0, "rain_days_2026": 10.5, "rain_days_2025": 15.5, "el_nino": 1.0, "drought": -0.2},
            "oct": {"precip_2026": 19.0, "precip_2025": 21.0, "rain_days_2026": 9.0, "rain_days_2025": 14.0, "el_nino": 0.9, "drought": -0.2},
            "nov": {"precip_2026": 15.0, "precip_2025": 16.0, "rain_days_2026": 7.0, "rain_days_2025": 14.5, "el_nino": 0.9, "drought": -0.1},
            "dec": {"precip_2026": 13.0, "precip_2025": 14.0, "rain_days_2026": 6.0, "rain_days_2025": 15.0, "el_nino": 0.9, "drought": -0.1},
        }
    },
    {
        "region_id": "central_ethiopia",
        "name": "Central Ethiopia",
        "name_local": "ማዕከላዊ ኢትዮጵያ ክልል",
        "capital": "Hossana",
        "centroid_lat": 7.55,
        "centroid_lon": 37.85,
        "area_km2": 32000,
        "zones_count": 5,
        "woredas_count": 48,
        "primary_livelihood": "Highland Enset/Wheat Agroforestry (Gurage, Hadiya, Silte)",
        "el_nino_index_2026": 1.25,
        "drought_index_2026": -0.65,
        "precipitation_2026_mm": 810,
        "precipitation_2025_mm": 890,
        "rain_days_2026": 60,
        "rain_days_2025": 71,
        "svg_path": "M 225,275 L 265,280 L 255,335 L 210,325 Z",
        "label_x": 238,
        "label_y": 305,
        "monthly_data": {
            "jun": {"precip_2026": 21.5, "precip_2025": 15.5, "rain_days_2026": 9.0, "rain_days_2025": 15.0, "el_nino": 1.1, "drought": -0.5},
            "jul": {"precip_2026": 18.0, "precip_2025": 13.5, "rain_days_2026": 8.0, "rain_days_2025": 13.0, "el_nino": 1.2, "drought": -0.6},
            "aug": {"precip_2026": 16.0, "precip_2025": 15.0, "rain_days_2026": 7.5, "rain_days_2025": 12.0, "el_nino": 1.3, "drought": -0.7},
            "sep": {"precip_2026": 19.5, "precip_2025": 21.0, "rain_days_2026": 9.0, "rain_days_2025": 14.5, "el_nino": 1.3, "drought": -0.7},
            "oct": {"precip_2026": 16.0, "precip_2025": 18.5, "rain_days_2026": 7.5, "rain_days_2025": 12.5, "el_nino": 1.2, "drought": -0.6},
            "nov": {"precip_2026": 12.5, "precip_2025": 14.0, "rain_days_2026": 6.0, "rain_days_2025": 13.5, "el_nino": 1.1, "drought": -0.5},
            "dec": {"precip_2026": 11.0, "precip_2025": 13.0, "rain_days_2026": 5.0, "rain_days_2025": 14.5, "el_nino": 1.1, "drought": -0.5},
        }
    },
    {
        "region_id": "harari",
        "name": "Harari Region",
        "name_local": "ሐረሪ ክልል",
        "capital": "Harar",
        "centroid_lat": 9.31,
        "centroid_lon": 42.12,
        "area_km2": 334,
        "zones_count": 1,
        "woredas_count": 9,
        "primary_livelihood": "Urban, Chat Cash Cropping & Agro-Commerce",
        "el_nino_index_2026": 1.62,
        "drought_index_2026": -1.25,
        "precipitation_2026_mm": 510,
        "precipitation_2025_mm": 620,
        "rain_days_2026": 38,
        "rain_days_2025": 50,
        "svg_path": "M 370,225 L 390,220 L 395,240 L 375,245 Z",
        "label_x": 382,
        "label_y": 232,
        "monthly_data": {
            "jun": {"precip_2026": 14.5, "precip_2025": 10.5, "rain_days_2026": 6.0, "rain_days_2025": 11.5, "el_nino": 1.5, "drought": -1.1},
            "jul": {"precip_2026": 12.5, "precip_2025": 9.0, "rain_days_2026": 5.0, "rain_days_2025": 9.5, "el_nino": 1.6, "drought": -1.2},
            "aug": {"precip_2026": 10.5, "precip_2025": 9.5, "rain_days_2026": 4.5, "rain_days_2025": 8.5, "el_nino": 1.7, "drought": -1.3},
            "sep": {"precip_2026": 13.5, "precip_2025": 15.5, "rain_days_2026": 6.5, "rain_days_2025": 12.0, "el_nino": 1.7, "drought": -1.3},
            "oct": {"precip_2026": 11.5, "precip_2025": 14.5, "rain_days_2026": 5.5, "rain_days_2025": 10.5, "el_nino": 1.6, "drought": -1.2},
            "nov": {"precip_2026": 9.0, "precip_2025": 11.0, "rain_days_2026": 4.5, "rain_days_2025": 12.5, "el_nino": 1.5, "drought": -1.1},
            "dec": {"precip_2026": 8.0, "precip_2025": 10.5, "rain_days_2026": 4.0, "rain_days_2025": 13.5, "el_nino": 1.5, "drought": -1.1},
        }
    },
    {
        "region_id": "dire_dawa",
        "name": "Dire Dawa",
        "name_local": "ድሬዳዋ አስተዳደር",
        "capital": "Dire Dawa",
        "centroid_lat": 9.59,
        "centroid_lon": 41.86,
        "area_km2": 1213,
        "zones_count": 1,
        "woredas_count": 9,
        "primary_livelihood": "Industrial City & Lowland Agro-Pastoral",
        "el_nino_index_2026": 1.70,
        "drought_index_2026": -1.35,
        "precipitation_2026_mm": 450,
        "precipitation_2025_mm": 560,
        "rain_days_2026": 34,
        "rain_days_2025": 48,
        "svg_path": "M 355,205 L 380,200 L 385,220 L 360,225 Z",
        "label_x": 370,
        "label_y": 212,
        "monthly_data": {
            "jun": {"precip_2026": 13.5, "precip_2025": 9.5, "rain_days_2026": 5.0, "rain_days_2025": 10.5, "el_nino": 1.5, "drought": -1.2},
            "jul": {"precip_2026": 11.5, "precip_2025": 8.0, "rain_days_2026": 4.0, "rain_days_2025": 8.5, "el_nino": 1.6, "drought": -1.3},
            "aug": {"precip_2026": 9.5, "precip_2025": 8.5, "rain_days_2026": 3.5, "rain_days_2025": 7.5, "el_nino": 1.7, "drought": -1.4},
            "sep": {"precip_2026": 12.5, "precip_2025": 14.5, "rain_days_2026": 5.5, "rain_days_2025": 11.0, "el_nino": 1.7, "drought": -1.4},
            "oct": {"precip_2026": 10.5, "precip_2025": 13.5, "rain_days_2026": 4.5, "rain_days_2025": 9.5, "el_nino": 1.6, "drought": -1.3},
            "nov": {"precip_2026": 8.0, "precip_2025": 10.0, "rain_days_2026": 3.5, "rain_days_2025": 11.5, "el_nino": 1.5, "drought": -1.2},
            "dec": {"precip_2026": 7.0, "precip_2025": 9.5, "rain_days_2026": 3.0, "rain_days_2025": 12.5, "el_nino": 1.5, "drought": -1.2},
        }
    },
    {
        "region_id": "addis_ababa",
        "name": "Addis Ababa",
        "name_local": "አዲስ አበባ",
        "capital": "Addis Ababa",
        "centroid_lat": 9.03,
        "centroid_lon": 38.75,
        "area_km2": 527,
        "zones_count": 1,
        "woredas_count": 11,
        "primary_livelihood": "National Capital & Urban Agro-Commerce",
        "el_nino_index_2026": 1.40,
        "drought_index_2026": -0.80,
        "precipitation_2026_mm": 840,
        "precipitation_2025_mm": 920,
        "rain_days_2026": 62,
        "rain_days_2025": 73,
        "svg_path": "M 270,240 L 290,240 L 290,260 L 270,260 Z",
        "label_x": 280,
        "label_y": 252,
        "monthly_data": {
            "jun": {"precip_2026": 22.0, "precip_2025": 16.0, "rain_days_2026": 9.5, "rain_days_2025": 15.5, "el_nino": 1.2, "drought": -0.6},
            "jul": {"precip_2026": 19.0, "precip_2025": 14.0, "rain_days_2026": 8.5, "rain_days_2025": 13.5, "el_nino": 1.3, "drought": -0.7},
            "aug": {"precip_2026": 16.5, "precip_2025": 15.5, "rain_days_2026": 7.5, "rain_days_2025": 12.5, "el_nino": 1.4, "drought": -0.8},
            "sep": {"precip_2026": 20.0, "precip_2025": 22.0, "rain_days_2026": 9.0, "rain_days_2025": 15.0, "el_nino": 1.4, "drought": -0.8},
            "oct": {"precip_2026": 16.5, "precip_2025": 19.0, "rain_days_2026": 8.0, "rain_days_2025": 13.0, "el_nino": 1.3, "drought": -0.7},
            "nov": {"precip_2026": 13.0, "precip_2025": 14.5, "rain_days_2026": 6.5, "rain_days_2025": 14.0, "el_nino": 1.2, "drought": -0.6},
            "dec": {"precip_2026": 11.5, "precip_2025": 13.5, "rain_days_2026": 5.5, "rain_days_2025": 15.0, "el_nino": 1.2, "drought": -0.6},
        }
    }
]


# ────────────────────────────────────────────────────────────────────────────
# 2. TIER 2: ZONAL LEVEL — ADMINISTRATIVE ZONES BY REGION
# ────────────────────────────────────────────────────────────────────────────
# Canvas space for Regional Map: viewBox="0 0 600 500"

ETHIOPIA_HIERARCHY_ZONES: Dict[str, List[Dict[str, Any]]] = {
    "amhara": [
        {
            "zone_id": "west_gojjam",
            "name": "West Gojjam",
            "name_local": "ምዕራብ ጎጃም",
            "capital": "Finote Selam",
            "area_km2": 13312,
            "woredas_count": 15,
            "el_nino_index_2026": 1.68,
            "drought_index_2026": -1.30,
            "precipitation_2026_mm": 510,
            "precipitation_2025_mm": 640,
            "rain_days_2026": 40,
            "rain_days_2025": 56,
            "svg_path": "M 160,250 L 240,240 L 255,320 L 195,350 L 140,310 Z",
            "label_x": 195,
            "label_y": 290,
        },
        {
            "zone_id": "east_gojjam",
            "name": "East Gojjam",
            "name_local": "ምሥራቅ ጎጃም (ጮቄ)",
            "capital": "Debre Markos",
            "area_km2": 14004,
            "woredas_count": 18,
            "el_nino_index_2026": 1.72,
            "drought_index_2026": -1.38,
            "precipitation_2026_mm": 485,
            "precipitation_2025_mm": 615,
            "rain_days_2026": 38,
            "rain_days_2025": 54,
            "svg_path": "M 240,240 L 320,250 L 330,340 L 255,360 L 255,320 Z",
            "label_x": 285,
            "label_y": 300,
        },
        {
            "zone_id": "north_wollo",
            "name": "North Wollo",
            "name_local": "ሰሜን ወሎ",
            "capital": "Woldiya",
            "area_km2": 12172,
            "woredas_count": 14,
            "el_nino_index_2026": 1.82,
            "drought_index_2026": -1.55,
            "precipitation_2026_mm": 390,
            "precipitation_2025_mm": 530,
            "rain_days_2026": 31,
            "rain_days_2025": 47,
            "svg_path": "M 320,130 L 410,140 L 420,210 L 350,220 L 320,180 Z",
            "label_x": 370,
            "label_y": 175,
        },
        {
            "zone_id": "south_wollo",
            "name": "South Wollo",
            "name_local": "ደቡብ ወሎ",
            "capital": "Dessie",
            "area_km2": 17059,
            "woredas_count": 21,
            "el_nino_index_2026": 1.78,
            "drought_index_2026": -1.48,
            "precipitation_2026_mm": 440,
            "precipitation_2025_mm": 580,
            "rain_days_2026": 36,
            "rain_days_2025": 51,
            "svg_path": "M 330,220 L 420,210 L 430,290 L 360,310 L 320,250 Z",
            "label_x": 375,
            "label_y": 260,
        },
        {
            "zone_id": "south_gondar",
            "name": "South Gondar",
            "name_local": "ደቡብ ጎንደር",
            "capital": "Debre Tabor",
            "area_km2": 14095,
            "woredas_count": 13,
            "el_nino_index_2026": 1.75,
            "drought_index_2026": -1.40,
            "precipitation_2026_mm": 470,
            "precipitation_2025_mm": 600,
            "rain_days_2026": 37,
            "rain_days_2025": 53,
            "svg_path": "M 230,160 L 320,150 L 330,230 L 240,240 Z",
            "label_x": 280,
            "label_y": 195,
        },
        {
            "zone_id": "central_gondar",
            "name": "Central Gondar",
            "name_local": "ማዕከላዊ ጎንደር",
            "capital": "Gondar",
            "area_km2": 18200,
            "woredas_count": 15,
            "el_nino_index_2026": 1.70,
            "drought_index_2026": -1.35,
            "precipitation_2026_mm": 460,
            "precipitation_2025_mm": 590,
            "rain_days_2026": 35,
            "rain_days_2025": 52,
            "svg_path": "M 180,90 L 290,80 L 290,155 L 210,165 Z",
            "label_x": 240,
            "label_y": 120,
        },
        {
            "zone_id": "west_gondar",
            "name": "West Gondar",
            "name_local": "ምዕራብ ጎንደር (መተማ)",
            "capital": "Genda Wuha",
            "area_km2": 15800,
            "woredas_count": 8,
            "el_nino_index_2026": 1.60,
            "drought_index_2026": -1.50,
            "precipitation_2026_mm": 360,
            "precipitation_2025_mm": 490,
            "rain_days_2026": 28,
            "rain_days_2025": 42,
            "svg_path": "M 90,100 L 180,90 L 180,210 L 100,220 Z",
            "label_x": 135,
            "label_y": 155,
        },
        {
            "zone_id": "north_shewa_amhara",
            "name": "North Shewa",
            "name_local": "ሰሜን ሸዋ (ደብረ ብርሃን)",
            "capital": "Debre Berhan",
            "area_km2": 15936,
            "woredas_count": 24,
            "el_nino_index_2026": 1.65,
            "drought_index_2026": -1.25,
            "precipitation_2026_mm": 560,
            "precipitation_2025_mm": 700,
            "rain_days_2026": 45,
            "rain_days_2025": 61,
            "svg_path": "M 320,310 L 410,300 L 420,390 L 340,410 Z",
            "label_x": 370,
            "label_y": 355,
        },
        {
            "zone_id": "awi",
            "name": "Awi Zone",
            "name_local": "አዊ ዞን",
            "capital": "Injibara",
            "area_km2": 9148,
            "woredas_count": 9,
            "el_nino_index_2026": 1.55,
            "drought_index_2026": -1.10,
            "precipitation_2026_mm": 670,
            "precipitation_2025_mm": 790,
            "rain_days_2026": 52,
            "rain_days_2025": 68,
            "svg_path": "M 110,230 L 170,225 L 185,320 L 120,330 Z",
            "label_x": 145,
            "label_y": 275,
        },
        {
            "zone_id": "wag_hemra",
            "name": "Wag Hemra",
            "name_local": "ዋግ ኽምራ",
            "capital": "Sekota",
            "area_km2": 9039,
            "woredas_count": 7,
            "el_nino_index_2026": 1.85,
            "drought_index_2026": -1.65,
            "precipitation_2026_mm": 320,
            "precipitation_2025_mm": 460,
            "rain_days_2026": 26,
            "rain_days_2025": 39,
            "svg_path": "M 280,60 L 360,50 L 370,120 L 290,130 Z",
            "label_x": 325,
            "label_y": 90,
        },
        {
            "zone_id": "oromia_special_zone",
            "name": "Oromia Special Zone",
            "name_local": "የኦሮሚያ ልዩ ዞን",
            "capital": "Kemise",
            "area_km2": 3740,
            "woredas_count": 6,
            "el_nino_index_2026": 1.80,
            "drought_index_2026": -1.50,
            "precipitation_2026_mm": 410,
            "precipitation_2025_mm": 540,
            "rain_days_2026": 32,
            "rain_days_2025": 46,
            "svg_path": "M 410,250 L 460,245 L 465,310 L 415,315 Z",
            "label_x": 435,
            "label_y": 280,
        }
    ],
    "tigray": [
        {
            "zone_id": "eastern_tigray",
            "name": "Eastern Zone",
            "name_local": "ምስራቃዊ ዞን (ሐውዜን)",
            "capital": "Adigrat",
            "area_km2": 6000,
            "woredas_count": 9,
            "el_nino_index_2026": 1.65,
            "drought_index_2026": -1.45,
            "precipitation_2026_mm": 390,
            "precipitation_2025_mm": 540,
            "rain_days_2026": 32,
            "rain_days_2025": 49,
            "svg_path": "M 320,100 L 440,90 L 450,220 L 330,230 Z",
            "label_x": 385,
            "label_y": 160,
        },
        {
            "zone_id": "central_tigray",
            "name": "Central Zone",
            "name_local": "ማእከላይ ዞን (ዓድዋ)",
            "capital": "Axum",
            "area_km2": 9741,
            "woredas_count": 12,
            "el_nino_index_2026": 1.58,
            "drought_index_2026": -1.38,
            "precipitation_2026_mm": 430,
            "precipitation_2025_mm": 590,
            "rain_days_2026": 36,
            "rain_days_2025": 54,
            "svg_path": "M 200,90 L 320,100 L 330,230 L 210,220 Z",
            "label_x": 265,
            "label_y": 160,
        },
        {
            "zone_id": "northwestern_tigray",
            "name": "Northwestern Zone",
            "name_local": "ሰሜን ምዕራብ ዞን (ሽሬ)",
            "capital": "Shire",
            "area_km2": 10400,
            "woredas_count": 8,
            "el_nino_index_2026": 1.52,
            "drought_index_2026": -1.30,
            "precipitation_2026_mm": 470,
            "precipitation_2025_mm": 620,
            "rain_days_2026": 38,
            "rain_days_2025": 55,
            "svg_path": "M 90,80 L 200,90 L 210,220 L 100,210 Z",
            "label_x": 150,
            "label_y": 150,
        },
        {
            "zone_id": "western_tigray",
            "name": "Western Zone",
            "name_local": "ምዕራባዊ ዞን (ሁመራ)",
            "capital": "Humera",
            "area_km2": 14000,
            "woredas_count": 5,
            "el_nino_index_2026": 1.48,
            "drought_index_2026": -1.35,
            "precipitation_2026_mm": 440,
            "precipitation_2025_mm": 580,
            "rain_days_2026": 30,
            "rain_days_2025": 46,
            "svg_path": "M 20,100 L 90,80 L 100,280 L 30,290 Z",
            "label_x": 60,
            "label_y": 190,
        },
        {
            "zone_id": "southern_tigray",
            "name": "Southern Zone",
            "name_local": "ደቡባዊ ዞን (ማይጨው)",
            "capital": "Maychew",
            "area_km2": 9300,
            "woredas_count": 8,
            "el_nino_index_2026": 1.62,
            "drought_index_2026": -1.40,
            "precipitation_2026_mm": 420,
            "precipitation_2025_mm": 560,
            "rain_days_2026": 35,
            "rain_days_2025": 51,
            "svg_path": "M 310,230 L 430,220 L 420,360 L 300,350 Z",
            "label_x": 365,
            "label_y": 290,
        },
        {
            "zone_id": "southeastern_tigray",
            "name": "Southeastern Zone",
            "name_local": "ደቡብ ምብራቕ ዞን",
            "capital": "Adigudom",
            "area_km2": 4500,
            "woredas_count": 5,
            "el_nino_index_2026": 1.60,
            "drought_index_2026": -1.38,
            "precipitation_2026_mm": 410,
            "precipitation_2025_mm": 550,
            "rain_days_2026": 33,
            "rain_days_2025": 50,
            "svg_path": "M 220,230 L 310,230 L 300,350 L 210,340 Z",
            "label_x": 260,
            "label_y": 285,
        },
        {
            "zone_id": "mekelle_special",
            "name": "Mekelle Special Zone",
            "name_local": "መቐለ ፍሉይ ዞን",
            "capital": "Mekelle",
            "area_km2": 110,
            "woredas_count": 1,
            "el_nino_index_2026": 1.55,
            "drought_index_2026": -1.25,
            "precipitation_2026_mm": 450,
            "precipitation_2025_mm": 580,
            "rain_days_2026": 37,
            "rain_days_2025": 53,
            "svg_path": "M 285,210 L 315,210 L 315,240 L 285,240 Z",
            "label_x": 300,
            "label_y": 225,
        }
    ],
    "oromia": [
        {
            "zone_id": "borana_oromia",
            "name": "Borana Zone",
            "name_local": "ቦረና ዞን (ያቤሎ)",
            "capital": "Yabelo",
            "area_km2": 45000,
            "woredas_count": 13,
            "el_nino_index_2026": 1.90,
            "drought_index_2026": -1.85,
            "precipitation_2026_mm": 240,
            "precipitation_2025_mm": 390,
            "rain_days_2026": 20,
            "rain_days_2025": 35,
            "svg_path": "M 200,330 L 350,320 L 340,460 L 190,440 Z",
            "label_x": 270,
            "label_y": 390,
        },
        {
            "zone_id": "bale_oromia",
            "name": "Bale Zone",
            "name_local": "ባሌ ዞን",
            "capital": "Robe",
            "area_km2": 43691,
            "woredas_count": 18,
            "el_nino_index_2026": 1.40,
            "drought_index_2026": -1.05,
            "precipitation_2026_mm": 610,
            "precipitation_2025_mm": 740,
            "rain_days_2026": 50,
            "rain_days_2025": 66,
            "svg_path": "M 320,200 L 450,210 L 440,340 L 310,330 Z",
            "label_x": 380,
            "label_y": 270,
        },
        {
            "zone_id": "east_shewa_oromia",
            "name": "East Shewa",
            "name_local": "ምሥራቅ ሸዋ (አዳማ)",
            "capital": "Adama",
            "area_km2": 8370,
            "woredas_count": 12,
            "el_nino_index_2026": 1.50,
            "drought_index_2026": -1.15,
            "precipitation_2026_mm": 590,
            "precipitation_2025_mm": 710,
            "rain_days_2026": 48,
            "rain_days_2025": 64,
            "svg_path": "M 240,140 L 330,130 L 330,220 L 240,210 Z",
            "label_x": 285,
            "label_y": 175,
        },
        {
            "zone_id": "west_shewa_oromia",
            "name": "West Shewa",
            "name_local": "ምዕራብ ሸዋ (አምቦ)",
            "capital": "Ambo",
            "area_km2": 14788,
            "woredas_count": 22,
            "el_nino_index_2026": 1.35,
            "drought_index_2026": -0.85,
            "precipitation_2026_mm": 780,
            "precipitation_2025_mm": 890,
            "rain_days_2026": 62,
            "rain_days_2025": 76,
            "svg_path": "M 140,130 L 240,140 L 240,220 L 130,210 Z",
            "label_x": 185,
            "label_y": 175,
        }
    ],
    "somali": [
        {
            "zone_id": "shabelle_somali",
            "name": "Shabelle Zone",
            "name_local": "ሻበሌ ዞን (ጎዴ)",
            "capital": "Gode",
            "area_km2": 39000,
            "woredas_count": 10,
            "el_nino_index_2026": 1.98,
            "drought_index_2026": -1.95,
            "precipitation_2026_mm": 160,
            "precipitation_2025_mm": 290,
            "rain_days_2026": 12,
            "rain_days_2025": 24,
            "svg_path": "M 240,230 L 380,240 L 370,390 L 230,370 Z",
            "label_x": 305,
            "label_y": 310,
        },
        {
            "zone_id": "fafan_somali",
            "name": "Fafan Zone",
            "name_local": "ፋፋን ዞን (ጅግጅጋ)",
            "capital": "Jigjiga",
            "area_km2": 10000,
            "woredas_count": 9,
            "el_nino_index_2026": 1.85,
            "drought_index_2026": -1.75,
            "precipitation_2026_mm": 280,
            "precipitation_2025_mm": 420,
            "rain_days_2026": 22,
            "rain_days_2025": 36,
            "svg_path": "M 200,80 L 350,90 L 360,230 L 210,220 Z",
            "label_x": 280,
            "label_y": 155,
        }
    ],
    "afar": [
        {
            "zone_id": "awsi_rasu_afar",
            "name": "Awsi Rasu (Zone 1)",
            "name_local": "አውሲ ረሱ (ዱብቲ/ሰመራ)",
            "capital": "Asayita / Semera",
            "area_km2": 30000,
            "woredas_count": 8,
            "el_nino_index_2026": 1.92,
            "drought_index_2026": -1.75,
            "precipitation_2026_mm": 190,
            "precipitation_2025_mm": 300,
            "rain_days_2026": 16,
            "rain_days_2025": 27,
            "svg_path": "M 210,180 L 380,170 L 370,330 L 200,320 Z",
            "label_x": 290,
            "label_y": 250,
        },
        {
            "zone_id": "kilbet_rasu_afar",
            "name": "Kilbet Rasu (Zone 2)",
            "name_local": "ኪልበት ረሱ (ዳሎል/በርሃሌ)",
            "capital": "Abala",
            "area_km2": 18000,
            "woredas_count": 7,
            "el_nino_index_2026": 1.85,
            "drought_index_2026": -1.65,
            "precipitation_2026_mm": 170,
            "precipitation_2025_mm": 270,
            "rain_days_2026": 14,
            "rain_days_2025": 24,
            "svg_path": "M 180,50 L 340,60 L 350,180 L 190,170 Z",
            "label_x": 265,
            "label_y": 115,
        }
    ]
}


# ────────────────────────────────────────────────────────────────────────────
# 3. TIER 3: WOREDA LEVEL — WOREDAS WITHIN EACH ZONE
# ────────────────────────────────────────────────────────────────────────────
ETHIOPIA_HIERARCHY_WOREDAS: Dict[str, List[Dict[str, Any]]] = {
    "east_gojjam": [
        {
            "woreda_id": "sinan",
            "name": "Sinan Woreda",
            "name_local": "ሲናን ወረዳ (ጮቄ)",
            "capital": "Rebu Gebeya",
            "elevation_m": 3150,
            "aez": "Dega / Wurch",
            "kebeles_count": 18,
            "spi_3": -1.45,
            "el_nino_index": 1.74,
            "precipitation_2026_mm": 470,
            "precipitation_2025_mm": 610,
            "prob_1m": 0.58,
            "prob_2m": 0.69,
            "prob_3m": 0.76,
            "risk_level": "High Risk",
            "svg_path": "M 200,140 L 310,130 L 320,240 L 210,250 Z",
            "label_x": 260,
            "label_y": 190,
        },
        {
            "woreda_id": "machakel",
            "name": "Machakel Woreda",
            "name_local": "ማቻከል ወረዳ",
            "capital": "Amanuel",
            "elevation_m": 2240,
            "aez": "Weyna Dega",
            "kebeles_count": 22,
            "spi_3": -1.35,
            "el_nino_index": 1.70,
            "precipitation_2026_mm": 510,
            "precipitation_2025_mm": 630,
            "prob_1m": 0.52,
            "prob_2m": 0.64,
            "prob_3m": 0.71,
            "risk_level": "High Risk",
            "svg_path": "M 100,160 L 200,140 L 210,250 L 110,260 Z",
            "label_x": 155,
            "label_y": 205,
        },
        {
            "woreda_id": "gozamin",
            "name": "Gozamin Woreda",
            "name_local": "ጎዛምን ወረዳ (ደብረ ማርቆስ)",
            "capital": "Debre Markos Area",
            "elevation_m": 2400,
            "aez": "Weyna Dega",
            "kebeles_count": 25,
            "spi_3": -1.30,
            "el_nino_index": 1.68,
            "precipitation_2026_mm": 530,
            "precipitation_2025_mm": 650,
            "prob_1m": 0.48,
            "prob_2m": 0.59,
            "prob_3m": 0.67,
            "risk_level": "Moderate Risk",
            "svg_path": "M 210,250 L 320,240 L 330,350 L 220,360 Z",
            "label_x": 270,
            "label_y": 300,
        },
        {
            "woreda_id": "bibugn",
            "name": "Bibugn Woreda",
            "name_local": "ቢቡኝ ወረዳ",
            "capital": "Digotsion",
            "elevation_m": 2680,
            "aez": "Dega",
            "kebeles_count": 16,
            "spi_3": -1.40,
            "el_nino_index": 1.72,
            "precipitation_2026_mm": 480,
            "precipitation_2025_mm": 615,
            "prob_1m": 0.54,
            "prob_2m": 0.65,
            "prob_3m": 0.73,
            "risk_level": "High Risk",
            "svg_path": "M 310,130 L 420,120 L 430,230 L 320,240 Z",
            "label_x": 370,
            "label_y": 180,
        }
    ],
    "eastern_tigray": [
        {
            "woreda_id": "hawzen",
            "name": "Hawzen Woreda",
            "name_local": "ሓውዜን ወረዳ",
            "capital": "Hawzen",
            "elevation_m": 2100,
            "aez": "Weyna Dega",
            "kebeles_count": 19,
            "spi_3": -1.48,
            "el_nino_index": 1.68,
            "precipitation_2026_mm": 370,
            "precipitation_2025_mm": 520,
            "prob_1m": 0.61,
            "prob_2m": 0.72,
            "prob_3m": 0.81,
            "risk_level": "Severe Risk",
            "svg_path": "M 180,120 L 300,110 L 310,240 L 190,250 Z",
            "label_x": 245,
            "label_y": 180,
        },
        {
            "woreda_id": "kilte_awlaelo",
            "name": "Kilte Awlaelo Woreda",
            "name_local": "ኪልተ ኣውላዕሎ ወረዳ (ዉቅሮ)",
            "capital": "Wukro",
            "elevation_m": 1980,
            "aez": "Weyna Dega",
            "kebeles_count": 17,
            "spi_3": -1.42,
            "el_nino_index": 1.64,
            "precipitation_2026_mm": 395,
            "precipitation_2025_mm": 545,
            "prob_1m": 0.56,
            "prob_2m": 0.68,
            "prob_3m": 0.77,
            "risk_level": "High Risk",
            "svg_path": "M 190,250 L 310,240 L 320,360 L 200,370 Z",
            "label_x": 255,
            "label_y": 305,
        },
        {
            "woreda_id": "atsbi_wonberta",
            "name": "Atsbi Wonberta Woreda",
            "name_local": "ዓጽቢ ወንበርታ ወረዳ",
            "capital": "Atsbi",
            "elevation_m": 2650,
            "aez": "Dega",
            "kebeles_count": 18,
            "spi_3": -1.52,
            "el_nino_index": 1.70,
            "precipitation_2026_mm": 350,
            "precipitation_2025_mm": 500,
            "prob_1m": 0.64,
            "prob_2m": 0.75,
            "prob_3m": 0.84,
            "risk_level": "Severe Risk",
            "svg_path": "M 300,110 L 420,100 L 430,230 L 310,240 Z",
            "label_x": 365,
            "label_y": 170,
        }
    ],
    "borana_oromia": [
        {
            "woreda_id": "yabelo",
            "name": "Yabelo Woreda",
            "name_local": "ያቤሎ ወረዳ",
            "capital": "Yabelo",
            "elevation_m": 1600,
            "aez": "Kolla Lowlands",
            "kebeles_count": 23,
            "spi_3": -1.82,
            "el_nino_index": 1.88,
            "precipitation_2026_mm": 260,
            "precipitation_2025_mm": 410,
            "prob_1m": 0.72,
            "prob_2m": 0.82,
            "prob_3m": 0.89,
            "risk_level": "Extreme Risk",
            "svg_path": "M 160,140 L 320,130 L 330,280 L 170,290 Z",
            "label_x": 245,
            "label_y": 210,
        },
        {
            "woreda_id": "dhas",
            "name": "Dhas Woreda",
            "name_local": "ዳስ ወረዳ",
            "capital": "Dhas",
            "elevation_m": 1050,
            "aez": "Bereha Hyper-Arid",
            "kebeles_count": 14,
            "spi_3": -1.95,
            "el_nino_index": 1.94,
            "precipitation_2026_mm": 210,
            "precipitation_2025_mm": 360,
            "prob_1m": 0.78,
            "prob_2m": 0.87,
            "prob_3m": 0.93,
            "risk_level": "Extreme Risk",
            "svg_path": "M 170,290 L 330,280 L 340,420 L 180,430 Z",
            "label_x": 255,
            "label_y": 355,
        }
    ]
}


# ────────────────────────────────────────────────────────────────────────────
# 4. TIER 4: KEBELE LEVEL — LOCAL GROUND TRUTH, WATER POINTS & VILLAGES
# ────────────────────────────────────────────────────────────────────────────
    "tanqua_abergelle": [
        {
            "kebele_id": "yechila_center",
            "name": "Yechila 01 Kebele",
            "name_local": "የጭላ ፩ ቀበሌ (ዓበርገለ ተከዘ ተፋሰስ)",
            "village_center": "Yechila Town / Agro-Pastoral Belt",
            "elevation_m": 1450,
            "households": 680,
            "primary_crop": "Dryland Sorghum (ማሽላ) & Sesame (ሰሊጥ)",
            "crop_stage": "Vegetative Tillering Stage",
            "crop_wilting_status": "Midday leaf rolling and moisture deficit (48%)",
            "soil_cracking_depth_cm": 4.2,
            "nearest_water_point": {
                "name": "Yechila Motorized Deep Well #1 (የጭላ ጥልቅ ጉድጓድ ፩)",
                "type": "deep_borehole",
                "distance_m": 350,
                "walking_time_mins": 7,
                "status": "Functional 120m Deep Borehole (185 L/min)",
                "discharge_lpm": 185.0,
                "water_quality": "High Clarity Potable Ground Water"
            },
            "da_field_report": {
                "da_name": "Gebremariam H. (Abergelle Agronomy & Soil DA)",
                "verification_status": "VERIFIED_ON_GROUND",
                "confidence_score": 0.99,
                "urgency_alert": "HEAT_WAVE_WATER_MONITORING",
                "notes": "Tanqua Abergelle dryland belt experiencing elevated Kolla evapotranspiration. Deep borehole operating normally. Livestock herds relying on Tanqua sand storage."
            },
            "spi_3": -1.68,
            "precip_2026_mm": 280,
            "precip_2025_mm": 390,
            "prob_1m": 0.68,
            "prob_2m": 0.79,
            "prob_3m": 0.88,
            "svg_path": "M 280,220 L 410,210 L 420,340 L 290,350 Z",
            "label_x": 350,
            "label_y": 280,
        },
    ],
    "sinan": [
        {
            "kebele_id": "sinan_robit",
            "name": "Robit Kebele",
            "name_local": "ሮቢት ቀበሌ",
            "village_center": "Robit Amba Village",
            "elevation_m": 3280,
            "households": 840,
            "primary_crop": "Highland Barley (ገብስ) & Potato",
            "crop_stage": "Vegetative Tillering Stage",
            "crop_wilting_status": "Severe Leaf Rolling & Moisture Deficit (44%)",
            "soil_cracking_depth_cm": 3.2,
            "nearest_water_point": {
                "name": "Robit Mountain Gravity Spring (ምንጭ)",
                "type": "natural_spring",
                "distance_m": 420,
                "walking_time_mins": 9,
                "status": "Reduced Yield (-35% seasonal discharge)",
                "discharge_lpm": 8.5,
                "water_quality": "Potable"
            },
            "da_field_report": {
                "da_name": "Mulugeta T. (Development Agent)",
                "verification_status": "VERIFIED_ON_GROUND",
                "confidence_score": 0.94,
                "urgency_alert": "HIGH_DROUGHT_STRESS",
                "notes": "Belg harvest completely failed; Kiremt sowing delayed by 18 days due to delayed moisture onset."
            },
            "spi_3": -1.52,
            "precip_2026_mm": 440,
            "precip_2025_mm": 590,
            "prob_1m": 0.58,
            "prob_2m": 0.71,
            "prob_3m": 0.82,
            "svg_path": "M 150,110 L 270,100 L 280,210 L 160,220 Z",
            "label_x": 215,
            "label_y": 160,
        },
        {
            "kebele_id": "sinan_gedeb",
            "name": "Gedeb Kebele",
            "name_local": "ገደብ ቀበሌ",
            "village_center": "Gedeb Mikael Village",
            "elevation_m": 3120,
            "households": 720,
            "primary_crop": "Wheat & Barley",
            "crop_stage": "Stem Elongation",
            "crop_wilting_status": "Moderate Wilting (32% Moisture Deficit)",
            "soil_cracking_depth_cm": 2.1,
            "nearest_water_point": {
                "name": "Gedeb Stream Community Shallow Well",
                "type": "shallow_well",
                "distance_m": 610,
                "walking_time_mins": 14,
                "status": "Functional (Water Table dropped 1.8m)",
                "discharge_lpm": 18.0,
                "water_quality": "Potable"
            },
            "da_field_report": {
                "da_name": "Tigist A. (Crop Extension Officer)",
                "verification_status": "VERIFIED_ON_GROUND",
                "confidence_score": 0.91,
                "urgency_alert": "MODERATE_STRESS",
                "notes": "Stream baseflow sustaining supplemental bucket irrigation; pasture drying rapidly."
            },
            "spi_3": -1.38,
            "precip_2026_mm": 480,
            "precip_2025_mm": 620,
            "prob_1m": 0.50,
            "prob_2m": 0.62,
            "prob_3m": 0.71,
            "svg_path": "M 270,100 L 400,90 L 410,210 L 280,220 Z",
            "label_x": 340,
            "label_y": 150,
        },
        {
            "kebele_id": "sinan_dangule",
            "name": "Dangule Kebele",
            "name_local": "ዳንጉሌ ቀበሌ (የጮቄ እግር)",
            "village_center": "Dangule Upper Village",
            "elevation_m": 3410,
            "households": 510,
            "primary_crop": "Highland Barley & Livestock Pasture",
            "crop_stage": "Early Vegetative",
            "crop_wilting_status": "High Moisture Stress & Cold Hazard Interaction",
            "soil_cracking_depth_cm": 1.8,
            "nearest_water_point": {
                "name": "Dangule Summit Protected Spring (ምንጭ)",
                "type": "natural_spring",
                "distance_m": 310,
                "walking_time_mins": 7,
                "status": "Functional (Perennial Afro-Alpine Bog Source)",
                "discharge_lpm": 12.0,
                "water_quality": "High Quality Spring Water"
            },
            "da_field_report": {
                "da_name": "Alemu W. (Natural Resources DA)",
                "verification_status": "VERIFIED_ON_GROUND",
                "confidence_score": 0.96,
                "urgency_alert": "ELEVATED_VULNERABILITY",
                "notes": "Water sponge wetlands intact; community water security stable but cereal crops stunted."
            },
            "spi_3": -1.45,
            "precip_2026_mm": 490,
            "precip_2025_mm": 630,
            "prob_1m": 0.52,
            "prob_2m": 0.65,
            "prob_3m": 0.75,
            "svg_path": "M 160,220 L 280,210 L 290,340 L 170,350 Z",
            "label_x": 225,
            "label_y": 280,
        }
    ],
    "hawzen": [
        {
            "kebele_id": "hawzen_megab",
            "name": "Megab Kebele",
            "name_local": "መጋብ ቀበሌ (ጌራልታ)",
            "village_center": "Megab Gheralta Settlement",
            "elevation_m": 2040,
            "households": 680,
            "primary_crop": "Teff & Wheat",
            "crop_stage": "Emergence / Vegetative",
            "crop_wilting_status": "Extreme Wilting (52% Moisture Deficit, Leaf Necrosis)",
            "soil_cracking_depth_cm": 4.5,
            "nearest_water_point": {
                "name": "Megab Rock Cistern & Borehole",
                "type": "motorized_borehole",
                "distance_m": 850,
                "walking_time_mins": 19,
                "status": "Critical Load (Borehole running 18 hrs/day)",
                "discharge_lpm": 45.0,
                "water_quality": "Potable"
            },
            "da_field_report": {
                "da_name": "Berhane G. (Agronomist)",
                "verification_status": "CRITICAL_GROUND_TRUTH",
                "confidence_score": 0.98,
                "urgency_alert": "SEVERE_DROUGHT_EMERGENCY",
                "notes": "Rainwater harvesting cisterns dry since May; water trucking request submitted to woreda bureau."
            },
            "spi_3": -1.62,
            "precip_2026_mm": 330,
            "precip_2025_mm": 490,
            "svg_path": "M 150,130 L 290,120 L 300,250 L 160,260 Z",
            "label_x": 225,
            "label_y": 190,
        },
        {
            "kebele_id": "hawzen_debre_tsion",
            "name": "Debre Tsion Kebele",
            "name_local": "ደብረ ጽዮን ቀበሌ",
            "village_center": "Debre Tsion Village",
            "elevation_m": 2180,
            "households": 540,
            "primary_crop": "Barley & Pulses",
            "crop_stage": "Early Vegetative",
            "crop_wilting_status": "Severe Wilting (48% Moisture Deficit)",
            "soil_cracking_depth_cm": 3.8,
            "nearest_water_point": {
                "name": "Debre Tsion Valley Hand Pump",
                "type": "hand_pump",
                "distance_m": 530,
                "walking_time_mins": 12,
                "status": "Reduced Yield (Yield down 42%)",
                "discharge_lpm": 14.0,
                "water_quality": "Potable"
            },
            "da_field_report": {
                "da_name": "Hagos K. (Field Officer)",
                "verification_status": "VERIFIED_ON_GROUND",
                "confidence_score": 0.95,
                "urgency_alert": "HIGH_DROUGHT_STRESS",
                "notes": "Pastoral fodder exhausted; farmers traveling 6km to valley bottom for cattle watering."
            },
            "spi_3": -1.55,
            "precip_2026_mm": 350,
            "precip_2025_mm": 510,
            "svg_path": "M 290,120 L 430,110 L 440,240 L 300,250 Z",
            "label_x": 365,
            "label_y": 180,
        }
    ],
    "yabelo": [
        {
            "kebele_id": "yabelo_dharito",
            "name": "Dharito Kebele",
            "name_local": "ዳሪቶ ቀበሌ (ቦረና)",
            "village_center": "Dharito Pastoral Community",
            "elevation_m": 1540,
            "households": 920,
            "primary_crop": "Pastoral Pasture & Dryland Sorghum",
            "crop_stage": "Pasture Rangeland Desiccation",
            "crop_wilting_status": "Extreme Pasture Die-Off (65% Biomass Deficit)",
            "soil_cracking_depth_cm": 5.2,
            "nearest_water_point": {
                "name": "Dharito Traditional Deep Well (Ellaa)",
                "type": "ella_traditional_deep_well",
                "distance_m": 1200,
                "walking_time_mins": 26,
                "status": "Extreme Queue (Human & livestock congestion)",
                "discharge_lpm": 35.0,
                "water_quality": "Livestock & Household"
            },
            "da_field_report": {
                "da_name": "Galgalo B. (Pastoral DA)",
                "verification_status": "EMERGENCY_FIELD_AUDIT",
                "confidence_score": 0.99,
                "urgency_alert": "CRITICAL_LIVESTOCK_MORTALITY_RISK",
                "notes": "Ellaa water drawing ladder teams operating 24 hours; livestock body condition score 1.5/5."
            },
            "spi_3": -1.95,
            "precip_2026_mm": 210,
            "precip_2025_mm": 370,
            "svg_path": "M 160,140 L 320,130 L 330,280 L 170,290 Z",
            "label_x": 245,
            "label_y": 210,
        }
    ]
}


# ────────────────────────────────────────────────────────────────────────────
# 5. PUBLIC HIERARCHICAL QUERY FUNCTIONS
# ────────────────────────────────────────────────────────────────────────────

def get_national_tier_matrix(month: Optional[str] = None) -> Dict[str, Any]:
    """Returns the National Tier (13 regions of Ethiopia) with 4-quadrant metrics."""
    regions = []
    m_key = month.lower() if month and month.lower() in ["jun", "jul", "aug", "sep", "oct", "nov", "dec"] else None

    for r in ETHIOPIA_NATIONAL_REGIONS:
        r_copy = dict(r)
        if m_key and m_key in r["monthly_data"]:
            m_val = r["monthly_data"][m_key]
            r_copy["active_el_nino"] = m_val["el_nino"]
            r_copy["active_drought"] = m_val["drought"]
            # Scale monthly precipitation into realistic seasonal mm (e.g. 100-750mm dynamic range)
            r_copy["active_precip"] = round(m_val["precip_2026"] * 24.0, 1)
            r_copy["active_rain_days"] = m_val["rain_days_2026"]
        else:
            r_copy["active_el_nino"] = r["el_nino_index_2026"]
            r_copy["active_drought"] = r["drought_index_2026"]
            r_copy["active_precip"] = r["precipitation_2026_mm"]
            r_copy["active_rain_days"] = r["rain_days_2026"]
        regions.append(r_copy)

    # Compute National Aggregate Timeseries
    months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m_keys = ["jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    p26 = [round(sum(r["monthly_data"][m]["precip_2026"] for r in ETHIOPIA_NATIONAL_REGIONS) / len(ETHIOPIA_NATIONAL_REGIONS), 1) for m in m_keys]
    p25 = [round(sum(r["monthly_data"][m]["precip_2025"] for r in ETHIOPIA_NATIONAL_REGIONS) / len(ETHIOPIA_NATIONAL_REGIONS), 1) for m in m_keys]
    rd26 = [round(sum(r["monthly_data"][m]["rain_days_2026"] for r in ETHIOPIA_NATIONAL_REGIONS) / len(ETHIOPIA_NATIONAL_REGIONS), 1) for m in m_keys]
    rd25 = [round(sum(r["monthly_data"][m]["rain_days_2025"] for r in ETHIOPIA_NATIONAL_REGIONS) / len(ETHIOPIA_NATIONAL_REGIONS), 1) for m in m_keys]

    return {
        "tier": "national",
        "title": "Ethiopia National Drought & Climate Matrix (2026)",
        "subtitle": "All 13 Regional States & Chartered Cities of the Federal Democratic Republic of Ethiopia",
        "breadcrumb": [{"tier": "national", "id": "ethiopia", "name": "Ethiopia (National)"}],
        "current_level": "Level 1: National (All Regions)",
        "items_count": len(regions),
        "items": regions,
        "active_month": m_key or "annual",
        "aggregate_timeseries": {
            "months": months,
            "series": {
                "precipitation_2026": p26,
                "precipitation_2025": p25,
                "rain_days_2026": rd26,
                "rain_days_2025": rd25,
            }
        }
    }


def get_regional_tier_matrix(region_id: str, month: Optional[str] = None) -> Dict[str, Any]:
    """Returns Tier 2 (Zonal Level) for any selected Ethiopian region."""
    reg = next((r for r in ETHIOPIA_NATIONAL_REGIONS if r["region_id"] == region_id.lower()), None)
    if not reg:
        # Fallback to Amhara if unknown
        reg = ETHIOPIA_NATIONAL_REGIONS[0]
        region_id = reg["region_id"]

    zones = ETHIOPIA_HIERARCHY_ZONES.get(region_id, ETHIOPIA_HIERARCHY_ZONES["amhara"])
    m_key = month.lower() if month and month.lower() in ["jun", "jul", "aug", "sep", "oct", "nov", "dec"] else None

    items = []
    for z in zones:
        z_copy = dict(z)
        if m_key and m_key in reg["monthly_data"]:
            m_val = reg["monthly_data"][m_key]
            z_copy["active_el_nino"] = round(z["el_nino_index_2026"] * (m_val["el_nino"] / max(0.1, reg["el_nino_index_2026"])), 2)
            z_copy["active_drought"] = round(z["drought_index_2026"] * (m_val["drought"] / min(-0.1, reg["drought_index_2026"])), 2)
            z_copy["active_precip"] = round(z["precipitation_2026_mm"] * (m_val["precip_2026"] / 16.0), 1)
            z_copy["active_rain_days"] = max(1, round(z["rain_days_2026"] * (m_val["rain_days_2026"] / 6.0)))
        else:
            z_copy["active_el_nino"] = z["el_nino_index_2026"]
            z_copy["active_drought"] = z["drought_index_2026"]
            z_copy["active_precip"] = z["precipitation_2026_mm"]
            z_copy["active_rain_days"] = z["rain_days_2026"]
        items.append(z_copy)

    months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m_keys = ["jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    p26 = [reg["monthly_data"][m]["precip_2026"] for m in m_keys]
    p25 = [reg["monthly_data"][m]["precip_2025"] for m in m_keys]
    rd26 = [reg["monthly_data"][m]["rain_days_2026"] for m in m_keys]
    rd25 = [reg["monthly_data"][m]["rain_days_2025"] for m in m_keys]

    return {
        "tier": "zone",
        "parent_tier": "national",
        "parent_id": region_id,
        "parent_name": reg["name"],
        "title": f"{reg['name']} &ndash; Zonal Drought & Climate Matrix (2026)",
        "subtitle": f"Administrative Zones of {reg['name']} ({len(items)} Zones Monitored)",
        "breadcrumb": [
            {"tier": "national", "id": "ethiopia", "name": "Ethiopia"},
            {"tier": "region", "id": region_id, "name": reg["name"]},
        ],
        "current_level": f"Level 2: Zonal Tier ({reg['name']})",
        "items_count": len(items),
        "items": items,
        "active_month": m_key or "annual",
        "aggregate_timeseries": {
            "months": months,
            "series": {
                "precipitation_2026": p26,
                "precipitation_2025": p25,
                "rain_days_2026": rd26,
                "rain_days_2025": rd25,
            }
        }
    }


def get_zonal_tier_matrix(zone_id: str, month: Optional[str] = None) -> Dict[str, Any]:
    """Returns Tier 3 (Woreda Level) for any selected Ethiopian zone."""
    # Find parent region and zone
    parent_reg = None
    target_zone = None
    for r_id, z_list in ETHIOPIA_HIERARCHY_ZONES.items():
        found = next((z for z in z_list if z["zone_id"] == zone_id.lower()), None)
        if found:
            target_zone = found
            parent_reg = next((r for r in ETHIOPIA_NATIONAL_REGIONS if r["region_id"] == r_id), None)
            break

    if not target_zone:
        # Default to East Gojjam
        target_zone = ETHIOPIA_HIERARCHY_ZONES["amhara"][1]
        zone_id = target_zone["zone_id"]
        parent_reg = ETHIOPIA_NATIONAL_REGIONS[0]

    woredas = ETHIOPIA_HIERARCHY_WOREDAS.get(zone_id, ETHIOPIA_HIERARCHY_WOREDAS["east_gojjam"])
    m_key = month.lower() if month and month.lower() in ["jun", "jul", "aug", "sep", "oct", "nov", "dec"] else None

    items = []
    for w in woredas:
        w_copy = dict(w)
        if m_key and parent_reg and m_key in parent_reg["monthly_data"]:
            m_val = parent_reg["monthly_data"][m_key]
            w_copy["active_el_nino"] = round(w["el_nino_index"] * (m_val["el_nino"] / max(0.1, parent_reg["el_nino_index_2026"])), 2)
            w_copy["active_drought"] = round(w["spi_3"] * (m_val["drought"] / min(-0.1, parent_reg["drought_index_2026"])), 2)
            w_copy["active_precip"] = round(w["precipitation_2026_mm"] * (m_val["precip_2026"] / 16.0), 1)
            w_copy["active_rain_days"] = max(1, round(38 * (m_val["rain_days_2026"] / 6.0)))
        else:
            w_copy["active_el_nino"] = w["el_nino_index"]
            w_copy["active_drought"] = w["spi_3"]
            w_copy["active_precip"] = w["precipitation_2026_mm"]
            w_copy["active_rain_days"] = 38
        items.append(w_copy)

    months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m_keys = ["jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    p26 = [parent_reg["monthly_data"][m]["precip_2026"] for m in m_keys]
    p25 = [parent_reg["monthly_data"][m]["precip_2025"] for m in m_keys]
    rd26 = [parent_reg["monthly_data"][m]["rain_days_2026"] for m in m_keys]
    rd25 = [parent_reg["monthly_data"][m]["rain_days_2025"] for m in m_keys]

    return {
        "tier": "woreda",
        "parent_tier": "zone",
        "parent_id": zone_id,
        "parent_name": target_zone["name"],
        "region_id": parent_reg["region_id"],
        "region_name": parent_reg["name"],
        "title": f"{target_zone['name']} &ndash; Woreda Risk Matrix (2026)",
        "subtitle": f"Woredas of {target_zone['name']}, {parent_reg['name']} with Probabilistic Predictions",
        "breadcrumb": [
            {"tier": "national", "id": "ethiopia", "name": "Ethiopia"},
            {"tier": "region", "id": parent_reg["region_id"], "name": parent_reg["name"]},
            {"tier": "zone", "id": zone_id, "name": target_zone["name"]},
        ],
        "current_level": f"Level 3: Woreda Tier ({target_zone['name']})",
        "items_count": len(items),
        "items": items,
        "active_month": m_key or "annual",
        "aggregate_timeseries": {
            "months": months,
            "series": {
                "precipitation_2026": p26,
                "precipitation_2025": p25,
                "rain_days_2026": rd26,
                "rain_days_2025": rd25,
            }
        }
    }


def get_woreda_tier_matrix(woreda_id: str, month: Optional[str] = None) -> Dict[str, Any]:
    """Returns Tier 4 (Kebele Level) for any selected Ethiopian woreda."""
    # Find parent zone and woreda
    target_woreda = None
    parent_zone_id = None
    for z_id, w_list in ETHIOPIA_HIERARCHY_WOREDAS.items():
        found = next((w for w in w_list if w["woreda_id"] == woreda_id.lower()), None)
        if found:
            target_woreda = found
            parent_zone_id = z_id
            break

    if not target_woreda:
        target_woreda = ETHIOPIA_HIERARCHY_WOREDAS["east_gojjam"][0]
        woreda_id = target_woreda["woreda_id"]
        parent_zone_id = "east_gojjam"

    # Find parent region
    parent_reg = None
    parent_zone = None
    for r_id, z_list in ETHIOPIA_HIERARCHY_ZONES.items():
        found_z = next((z for z in z_list if z["zone_id"] == parent_zone_id), None)
        if found_z:
            parent_zone = found_z
            parent_reg = next((r for r in ETHIOPIA_NATIONAL_REGIONS if r["region_id"] == r_id), None)
            break

    kebeles = ETHIOPIA_HIERARCHY_KEBELES.get(woreda_id, ETHIOPIA_HIERARCHY_KEBELES["sinan"])
    m_key = month.lower() if month and month.lower() in ["jun", "jul", "aug", "sep", "oct", "nov", "dec"] else None

    items = []
    for k in kebeles:
        k_copy = dict(k)
        if m_key and parent_reg and m_key in parent_reg["monthly_data"]:
            m_val = parent_reg["monthly_data"][m_key]
            k_copy["active_el_nino"] = round(1.72 * (m_val["el_nino"] / max(0.1, parent_reg["el_nino_index_2026"])), 2)
            k_copy["active_drought"] = round(k["spi_3"] * (m_val["drought"] / min(-0.1, parent_reg["drought_index_2026"])), 2)
            k_copy["active_precip"] = round(k["precip_2026_mm"] * (m_val["precip_2026"] / 16.0), 1)
            k_copy["active_rain_days"] = max(1, round(38 * (m_val["rain_days_2026"] / 6.0)))
        else:
            k_copy["active_el_nino"] = 1.72
            k_copy["active_drought"] = k["spi_3"]
            k_copy["active_precip"] = k["precip_2026_mm"]
            k_copy["active_rain_days"] = 38
        items.append(k_copy)

    months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    m_keys = ["jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    p26 = [parent_reg["monthly_data"][m]["precip_2026"] for m in m_keys]
    p25 = [parent_reg["monthly_data"][m]["precip_2025"] for m in m_keys]
    rd26 = [parent_reg["monthly_data"][m]["rain_days_2026"] for m in m_keys]
    rd25 = [parent_reg["monthly_data"][m]["rain_days_2025"] for m in m_keys]

    return {
        "tier": "kebele",
        "parent_tier": "woreda",
        "parent_id": woreda_id,
        "parent_name": target_woreda["name"],
        "zone_id": parent_zone_id,
        "zone_name": parent_zone["name"] if parent_zone else "Zone",
        "region_id": parent_reg["region_id"] if parent_reg else "amhara",
        "region_name": parent_reg["name"] if parent_reg else "Amhara",
        "title": f"{target_woreda['name']} &ndash; Kebele Ground Truth &amp; Village Water Matrix",
        "subtitle": f"Local Communities, Springs/Minch Yields &amp; Crop Wilting ({len(items)} Kebeles)",
        "breadcrumb": [
            {"tier": "national", "id": "ethiopia", "name": "Ethiopia"},
            {"tier": "region", "id": parent_reg["region_id"] if parent_reg else "amhara", "name": parent_reg["name"] if parent_reg else "Amhara"},
            {"tier": "zone", "id": parent_zone_id, "name": parent_zone["name"] if parent_zone else "Zone"},
            {"tier": "woreda", "id": woreda_id, "name": target_woreda["name"]},
        ],
        "current_level": f"Level 4: Kebele Tier ({target_woreda['name']})",
        "items_count": len(items),
        "items": items,
        "active_month": m_key or "annual",
        "aggregate_timeseries": {
            "months": months,
            "series": {
                "precipitation_2026": p26,
                "precipitation_2025": p25,
                "rain_days_2026": rd26,
                "rain_days_2025": rd25,
            }
        }
    }

