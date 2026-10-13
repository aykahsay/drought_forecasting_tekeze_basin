"""
Geographic & Agro-Ecological Climate Zone Architecture for Ethiopia (§7, §15)
=============================================================================
Defines two orthogonal hierarchies:
  1. Administrative Spatial Hierarchy:
     Ethiopia
       └── Region (Tigray, Afar, Amhara, Oromia, Somali, Sidama, etc.)
            └── Zone (Borana, North Wollo, Eastern Tigray, Fafan, etc.)
                 └── Woreda (Hawzen, Yabelo, Gode, Delanta, Dubti, etc.)

  2. Climatological & Agro-Ecological Hierarchy (Top-Level Climate Zones):
     Overlaid on top of administrative units to capture homogeneous biophysical behavior:
       - Bereha      (Hot Arid Lowlands, < 500–800m, pastoral, severe water stress)
       - Kolla       (Warm Semi-Arid Lowlands, 500–1,500m, erratic rain, high evapotranspiration)
       - Weyna Dega  (Temperate Mid-Highlands, 1,500–2,300m, main cropping heartland)
       - Dega        (Cool Humid Highlands, 2,300–3,200m, barley/wheat, frost sensitive)
       - Wurch / Kur (Cold Alpine / Afro-Alpine, > 3,200m, extreme cold hazards)

  3. Climatological Rainfall Regimes (National Meteorological Institute Classification):
       - Regime A: Central & Northern Bimodal (Belg: Mar–May, Kiremt: Jun–Sep)
       - Regime B: Western Monomodal (Continuous summer: May–Oct)
       - Regime C: Southern & Southeastern Bimodal (Gu: Mar–May, Deyr: Oct–Dec — Heavily IOD/ENSO coupled)
"""
from typing import Any, List, Optional


# ────────────────────────────────────────────────────────────────────────────
# 1. Agro-Ecological Climate Zones (AEZs)
# ────────────────────────────────────────────────────────────────────────────
CLIMATE_ZONES: list[dict[str, Any]] = [
    {
        "climate_zone_id": "bereha",
        "name": "Bereha (Hot Arid Lowlands)",
        "local_name": "Bereha (በረሃ)",
        "elevation_range": "< 500 – 800m",
        "annual_rainfall_mm": "< 400 mm",
        "temperature_range_c": "> 28 °C",
        "primary_livelihood": "Pastoralist (Camels, Goats)",
        "drought_sensitivity": "Extreme (Hyper-Aridity, Acute Water Deficits)",
        "dominant_vegetation": "Acacia-Commiphora desert thorn scrub",
        "description": "Hot hyper-arid desert and semi-desert lowlands covering the Danakil Depression, Afar Triangle, and Lower Ogaden basin.",
        "vulnerability_profile": "Immediate flash drought vulnerability, borehole depletion, severe pasture collapse during failed rains.",
    },
    {
        "climate_zone_id": "kolla",
        "name": "Kolla (Warm Semi-Arid Lowlands)",
        "local_name": "Kolla (ቆላ)",
        "elevation_range": "500 – 1,500m",
        "annual_rainfall_mm": "400 – 800 mm",
        "temperature_range_c": "20 – 28 °C",
        "primary_livelihood": "Agro-Pastoralist (Sorghum, Millet, Sesame, Cattle)",
        "drought_sensitivity": "High (Erratic Rainfall, Long Mid-Season Dry Spells)",
        "dominant_vegetation": "Wooded savannah and dry acacia woodlands",
        "description": "Warm semi-arid lowlands and river valleys with erratic bimodal or monomodal precipitation and high evaporative demand.",
        "vulnerability_profile": "High seasonal coefficient of variation; mid-season dry spells cause complete wilt of long-cycle cereals.",
    },
    {
        "climate_zone_id": "weyna_dega",
        "name": "Weyna Dega (Temperate Mid-Highlands)",
        "local_name": "Weyna Dega (ወይና ደጋ)",
        "elevation_range": "1,500 – 2,300m",
        "annual_rainfall_mm": "800 – 1,200 mm",
        "temperature_range_c": "15 – 20 °C",
        "primary_livelihood": "Sedentary Rainfed Agriculture (Teff, Wheat, Maize, Pulses)",
        "drought_sensitivity": "Moderate to High (Belg/Kiremt Delay or Early Cessation)",
        "dominant_vegetation": "Cultivated farmland with highland evergreen trees",
        "description": "Temperate sub-humid mid-altitude plateau representing Ethiopia's agricultural heartland and highest rural population density.",
        "vulnerability_profile": "Reliant on bimodal or reliable summer rains; late onset or early cessation directly slashes national food security.",
    },
    {
        "climate_zone_id": "dega",
        "name": "Dega (Cool Humid Highlands)",
        "local_name": "Dega (ደጋ)",
        "elevation_range": "2,300 – 3,200m",
        "annual_rainfall_mm": "1,200 – 2,000 mm",
        "temperature_range_c": "10 – 15 °C",
        "primary_livelihood": "Highland Grain & Livestock (Barley, Wheat, Pulses, Sheep)",
        "drought_sensitivity": "Moderate (Belg Short-Rain Failure, Soil Erosion, Frost)",
        "dominant_vegetation": "Highland coniferous forest (Podocarpus, Juniperus) and moorland",
        "description": "Cool humid high-altitude plateau with reliable summer rains but high vulnerability to Belg season failure and cold temperature stress.",
        "vulnerability_profile": " Belg rains crucial for land preparation and short-cycle barley; failure triggers severe pre-harvest lean season.",
    },
    {
        "climate_zone_id": "wurch",
        "name": "Wurch / Kur (Afro-Alpine)",
        "local_name": "Wurch (ውርጭ / ቁር)",
        "elevation_range": "> 3,200m",
        "annual_rainfall_mm": "> 1,400 mm",
        "temperature_range_c": "< 10 °C",
        "primary_livelihood": "Afro-Alpine Pastoralism & High-Altitude Barley",
        "drought_sensitivity": "Low to Moderate (Frost & Extreme Wind Desiccation)",
        "dominant_vegetation": "Afro-alpine Ericaceous moorland, Giant Lobelia, tussock grass",
        "description": "Afro-alpine mountain summits (Semien, Bale) subject to nightly sub-zero frost and steep microclimatic gradients.",
        "vulnerability_profile": "Freeze-thaw cycles, winter soil desiccation, extreme weather shocks.",
    },
]


# ────────────────────────────────────────────────────────────────────────────
# 2. Climatological Rainfall Regimes
# ────────────────────────────────────────────────────────────────────────────
RAINFALL_REGIMES: dict[str, dict[str, Any]] = {
    "regime_a": {
        "regime_id": "regime_a",
        "name": "Regime A (Central & Northern Bimodal)",
        "description": "Bimodal rainfall: Belg (short rains: Mar–May) and Kiremt (main rains: Jun–Sep).",
        "regions": ["Tigray", "Amhara", "Central Oromia", "Afar Escarpment"],
        "enso_sensitivity": "El Niño suppresses Kiremt (severe drought risk); La Niña may enhance Kiremt but disrupt Belg.",
    },
    "regime_b": {
        "regime_id": "regime_b",
        "name": "Regime B (Western Monomodal)",
        "description": "Single continuous summer wet season extending from May through October.",
        "regions": ["Benishangul-Gumuz", "Gambella", "Western Oromia"],
        "enso_sensitivity": "Driven by Atlantic & Congo basin equatorial moisture influx; buffered against teleconnection extremes.",
    },
    "regime_c": {
        "regime_id": "regime_c",
        "name": "Regime C (Southern & Southeastern Bimodal)",
        "description": "Bimodal equatorial rains: Gu / Genna (Mar–May) and Deyr / Hageya (Oct–Dec). Dry during Jun–Aug.",
        "regions": ["Somali", "Southern Oromia (Borana, Guji)", "South Omo"],
        "enso_sensitivity": "Extreme teleconnection coupling: Negative IOD + La Niña produces catastrophic multi-season droughts (e.g. 2020–2023).",
    },
}


# ────────────────────────────────────────────────────────────────────────────
# 3. Administrative Regions of Ethiopia
# ────────────────────────────────────────────────────────────────────────────
ETHIOPIA_REGIONS: list[dict[str, Any]] = [
    {"region_id": "tigray", "name": "Tigray", "capital": "Mekelle", "centroid_lat": 14.032, "centroid_lon": 38.746, "area_km2": 50079},
    {"region_id": "afar", "name": "Afar", "capital": "Semera", "centroid_lat": 11.755, "centroid_lon": 40.958, "area_km2": 72053},
    {"region_id": "amhara", "name": "Amhara", "capital": "Bahir Dar", "centroid_lat": 11.600, "centroid_lon": 37.400, "area_km2": 154709},
    {"region_id": "oromia", "name": "Oromia", "capital": "Finfinnee / Adama", "centroid_lat": 8.000, "centroid_lon": 39.000, "area_km2": 284538},
    {"region_id": "somali", "name": "Somali", "capital": "Jigjiga", "centroid_lat": 6.661, "centroid_lon": 44.279, "area_km2": 279252},
    {"region_id": "sidama", "name": "Sidama", "capital": "Hawassa", "centroid_lat": 6.700, "centroid_lon": 38.450, "area_km2": 12000},
    {"region_id": "south_ethiopia", "name": "South Ethiopia", "capital": "Wolaita Sodo", "centroid_lat": 6.058, "centroid_lon": 36.726, "area_km2": 54000},
    {"region_id": "central_ethiopia", "name": "Central Ethiopia", "capital": "Hossana", "centroid_lat": 7.550, "centroid_lon": 37.850, "area_km2": 32000},
    {"region_id": "benishangul", "name": "Benishangul-Gumuz", "capital": "Assosa", "centroid_lat": 10.780, "centroid_lon": 35.565, "area_km2": 50699},
    {"region_id": "gambella", "name": "Gambella", "capital": "Gambella", "centroid_lat": 8.250, "centroid_lon": 34.580, "area_km2": 29783},
    {"region_id": "harari", "name": "Harari", "capital": "Harar", "centroid_lat": 9.310, "centroid_lon": 42.120, "area_km2": 334},
    {"region_id": "dire_dawa", "name": "Dire Dawa", "capital": "Dire Dawa", "centroid_lat": 9.593, "centroid_lon": 41.866, "area_km2": 1213},
    {"region_id": "addis_ababa", "name": "Addis Ababa", "capital": "Addis Ababa", "centroid_lat": 9.032, "centroid_lon": 38.746, "area_km2": 527},
]


# ────────────────────────────────────────────────────────────────────────────
# 4. Administrative Zones of Ethiopia
# ────────────────────────────────────────────────────────────────────────────
ETHIOPIA_ZONES: list[dict[str, Any]] = [
    # Tigray
    {"zone_id": "eastern_tigray", "region_id": "tigray", "name": "Eastern (Misraqawi)"},
    {"zone_id": "central_tigray", "region_id": "tigray", "name": "Central (Mehakelegnaw)"},
    {"zone_id": "southern_tigray", "region_id": "tigray", "name": "Southern (Debubawi)"},
    {"zone_id": "southeastern_tigray", "region_id": "tigray", "name": "Southeastern (Debub Misraqawi)"},
    {"zone_id": "northwestern_tigray", "region_id": "tigray", "name": "Northwestern (Semien Mi'irabawi)"},
    {"zone_id": "western_tigray", "region_id": "tigray", "name": "Western (Mi'irabawi)"},
    {"zone_id": "mekelle_special", "region_id": "tigray", "name": "Mekelle Special Zone"},

    # Afar
    {"zone_id": "awsi_rasu_afar", "region_id": "afar", "name": "Awsi Rasu (Zone 1)"},
    {"zone_id": "kilbet_rasu_afar", "region_id": "afar", "name": "Kilbet Rasu (Zone 2)"},
    {"zone_id": "gabi_rasu_afar", "region_id": "afar", "name": "Gabi Rasu (Zone 3)"},

    # Amhara
    {"zone_id": "north_wollo_amhara", "region_id": "amhara", "name": "North Wollo (Semien Wollo)"},
    {"zone_id": "north_shewa_amhara", "region_id": "amhara", "name": "North Shewa (Semien Shewa)"},
    {"zone_id": "west_gondar_amhara", "region_id": "amhara", "name": "West Gondar"},
    {"zone_id": "west_gojjam_amhara", "region_id": "amhara", "name": "West Gojjam"},
    {"zone_id": "south_gondar_amhara", "region_id": "amhara", "name": "South Gondar"},

    # Oromia
    {"zone_id": "borana_oromia", "region_id": "oromia", "name": "Borana Zone"},
    {"zone_id": "east_hararghe_oromia", "region_id": "oromia", "name": "East Hararghe"},
    {"zone_id": "east_shewa_oromia", "region_id": "oromia", "name": "East Shewa"},
    {"zone_id": "bale_oromia", "region_id": "oromia", "name": "Bale Zone"},
    {"zone_id": "west_shewa_oromia", "region_id": "oromia", "name": "West Shewa"},
    {"zone_id": "east_wollega_oromia", "region_id": "oromia", "name": "East Wollega"},

    # Somali
    {"zone_id": "shabelle_somali", "region_id": "somali", "name": "Shabelle Zone"},
    {"zone_id": "korahe_somali", "region_id": "somali", "name": "Korahe Zone"},
    {"zone_id": "fafan_somali", "region_id": "somali", "name": "Fafan Zone"},
    {"zone_id": "liben_somali", "region_id": "somali", "name": "Liben Zone"},
    {"zone_id": "dollo_somali", "region_id": "somali", "name": "Dollo Zone"},
    {"zone_id": "jarar_somali", "region_id": "somali", "name": "Jarar Zone"},

    # Sidama & South Ethiopia
    {"zone_id": "sidama_zone", "region_id": "sidama", "name": "Sidama Central"},
    {"zone_id": "south_omo_zone", "region_id": "south_ethiopia", "name": "South Omo Zone"},
    {"zone_id": "konso_zone", "region_id": "south_ethiopia", "name": "Konso Special Zone"},

    # Benishangul & Gambella
    {"zone_id": "assosa_zone", "region_id": "benishangul", "name": "Assosa Zone"},
    {"zone_id": "anywaa_zone", "region_id": "gambella", "name": "Anywaa Zone"},
]

TIGRAY_ZONES = [z for z in ETHIOPIA_ZONES if z["region_id"] == "tigray"]


# ────────────────────────────────────────────────────────────────────────────
# 5. National Woredas Catalogue of Ethiopia (With Climate Zone Overlays)
# ────────────────────────────────────────────────────────────────────────────
ETHIOPIA_WOREDAS: list[dict[str, Any]] = [
    # ── TIGRAY REGION (17 Woredas) ──────────────────────────────────────────
    {
        "woreda_id": "hawzen",
        "name": "Hawzen",
        "zone_id": "eastern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 13.978,
        "centroid_lon": 39.432,
        "area_km2": 1892.4,
        "elevation_mean_m": 2100,
        "vulnerability_index": 0.78,
        "bbox": {"north": 14.15, "south": 13.82, "west": 39.25, "east": 39.60},
    },
    {
        "woreda_id": "kilte_awlaelo",
        "name": "Kilte Awlaelo",
        "zone_id": "eastern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 13.731,
        "centroid_lon": 39.598,
        "area_km2": 1010.5,
        "elevation_mean_m": 1980,
        "vulnerability_index": 0.72,
        "bbox": {"north": 13.88, "south": 13.58, "west": 39.42, "east": 39.75},
    },
    {
        "woreda_id": "atsbi_wonberta",
        "name": "Atsbi Wonberta",
        "zone_id": "eastern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 13.876,
        "centroid_lon": 39.739,
        "area_km2": 1223.1,
        "elevation_mean_m": 2650,
        "vulnerability_index": 0.81,
        "bbox": {"north": 14.05, "south": 13.70, "west": 39.60, "east": 39.90},
    },
    {
        "woreda_id": "saesi_tsaedaemba",
        "name": "Saesi Tsaedaemba",
        "zone_id": "eastern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 14.331,
        "centroid_lon": 39.548,
        "area_km2": 1145.0,
        "elevation_mean_m": 2240,
        "vulnerability_index": 0.69,
        "bbox": {"north": 14.48, "south": 14.18, "west": 39.38, "east": 39.70},
    },
    {
        "woreda_id": "adwa",
        "name": "Adwa",
        "zone_id": "central_tigray",
        "region_id": "tigray",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 14.164,
        "centroid_lon": 38.895,
        "area_km2": 1248.6,
        "elevation_mean_m": 1900,
        "vulnerability_index": 0.65,
        "bbox": {"north": 14.32, "south": 14.00, "west": 38.75, "east": 39.05},
    },
    {
        "woreda_id": "axum",
        "name": "Axum",
        "zone_id": "central_tigray",
        "region_id": "tigray",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 14.123,
        "centroid_lon": 38.724,
        "area_km2": 320.0,
        "elevation_mean_m": 2130,
        "vulnerability_index": 0.58,
        "bbox": {"north": 14.22, "south": 14.05, "west": 38.65, "east": 38.80},
    },
    {
        "woreda_id": "tahtay_maychew",
        "name": "Tahtay Maychew",
        "zone_id": "central_tigray",
        "region_id": "tigray",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_a",
        "centroid_lat": 14.280,
        "centroid_lon": 38.650,
        "area_km2": 1540.0,
        "elevation_mean_m": 1450,
        "vulnerability_index": 0.74,
        "bbox": {"north": 14.45, "south": 14.12, "west": 38.48, "east": 38.82},
    },
    {
        "woreda_id": "naeder",
        "name": "Naeder",
        "zone_id": "central_tigray",
        "region_id": "tigray",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 14.050,
        "centroid_lon": 38.850,
        "area_km2": 980.0,
        "elevation_mean_m": 1820,
        "vulnerability_index": 0.71,
        "bbox": {"north": 14.18, "south": 13.92, "west": 38.72, "east": 38.98},
    },
    {
        "woreda_id": "raya_azebo",
        "name": "Raya Azebo",
        "zone_id": "southern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_a",
        "centroid_lat": 12.721,
        "centroid_lon": 39.645,
        "area_km2": 2045.0,
        "elevation_mean_m": 1480,
        "vulnerability_index": 0.83,
        "bbox": {"north": 12.92, "south": 12.52, "west": 39.48, "east": 39.82},
    },
    {
        "woreda_id": "raya_alamata",
        "name": "Raya Alamata",
        "zone_id": "southern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_a",
        "centroid_lat": 12.420,
        "centroid_lon": 39.560,
        "area_km2": 1650.0,
        "elevation_mean_m": 1520,
        "vulnerability_index": 0.80,
        "bbox": {"north": 12.60, "south": 12.25, "west": 39.40, "east": 39.75},
    },
    {
        "woreda_id": "ofla",
        "name": "Ofla",
        "zone_id": "southern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 12.580,
        "centroid_lon": 39.480,
        "area_km2": 1320.0,
        "elevation_mean_m": 2450,
        "vulnerability_index": 0.67,
        "bbox": {"north": 12.75, "south": 12.40, "west": 39.35, "east": 39.60},
    },
    {
        "woreda_id": "endamehoni",
        "name": "Endamehoni",
        "zone_id": "southern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 12.780,
        "centroid_lon": 39.520,
        "area_km2": 1180.0,
        "elevation_mean_m": 2400,
        "vulnerability_index": 0.64,
        "bbox": {"north": 12.92, "south": 12.65, "west": 39.40, "east": 39.65},
    },
    {
        "woreda_id": "degua_tembien",
        "name": "Degua Tembien",
        "zone_id": "southeastern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 13.628,
        "centroid_lon": 39.182,
        "area_km2": 1115.0,
        "elevation_mean_m": 2200,
        "vulnerability_index": 0.76,
        "bbox": {"north": 13.78, "south": 13.48, "west": 39.05, "east": 39.32},
    },
    {
        "woreda_id": "shire",
        "name": "Shire (Inda Selassie)",
        "zone_id": "northwestern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 14.105,
        "centroid_lon": 38.283,
        "area_km2": 850.0,
        "elevation_mean_m": 1900,
        "vulnerability_index": 0.66,
        "bbox": {"north": 14.28, "south": 13.92, "west": 38.10, "east": 38.45},
    },
    {
        "woreda_id": "asgede_tsimbla",
        "name": "Asgede Tsimbla",
        "zone_id": "northwestern_tigray",
        "region_id": "tigray",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_a",
        "centroid_lat": 13.950,
        "centroid_lon": 38.050,
        "area_km2": 2810.0,
        "elevation_mean_m": 1450,
        "vulnerability_index": 0.86,
        "bbox": {"north": 14.15, "south": 13.75, "west": 37.85, "east": 38.25},
    },
    {
        "woreda_id": "kafta_humera",
        "name": "Kafta Humera",
        "zone_id": "western_tigray",
        "region_id": "tigray",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_a",
        "centroid_lat": 13.980,
        "centroid_lon": 36.950,
        "area_km2": 4560.0,
        "elevation_mean_m": 680,
        "vulnerability_index": 0.79,
        "bbox": {"north": 14.30, "south": 13.65, "west": 36.60, "east": 37.30},
    },
    {
        "woreda_id": "mekelle",
        "name": "Mekelle City",
        "zone_id": "mekelle_special",
        "region_id": "tigray",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 13.497,
        "centroid_lon": 39.475,
        "area_km2": 110.0,
        "elevation_mean_m": 2080,
        "vulnerability_index": 0.45,
        "bbox": {"north": 13.56, "south": 13.44, "west": 39.42, "east": 39.53},
    },

    # ── AFAR REGION (6 Woredas — Arid Lowlands) ─────────────────────────────
    {
        "woreda_id": "dubti",
        "name": "Dubti",
        "zone_id": "awsi_rasu_afar",
        "region_id": "afar",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_a",
        "centroid_lat": 11.733,
        "centroid_lon": 41.083,
        "area_km2": 3850.0,
        "elevation_mean_m": 378,
        "vulnerability_index": 0.92,
        "bbox": {"north": 11.95, "south": 11.50, "west": 40.85, "east": 41.35},
    },
    {
        "woreda_id": "berhale",
        "name": "Berhale",
        "zone_id": "kilbet_rasu_afar",
        "region_id": "afar",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_a",
        "centroid_lat": 13.864,
        "centroid_lon": 40.021,
        "area_km2": 2680.0,
        "elevation_mean_m": 639,
        "vulnerability_index": 0.89,
        "bbox": {"north": 14.10, "south": 13.65, "west": 39.80, "east": 40.25},
    },
    {
        "woreda_id": "elidar",
        "name": "Elidar",
        "zone_id": "awsi_rasu_afar",
        "region_id": "afar",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_a",
        "centroid_lat": 12.050,
        "centroid_lon": 41.810,
        "area_km2": 4520.0,
        "elevation_mean_m": 390,
        "vulnerability_index": 0.94,
        "bbox": {"north": 12.35, "south": 11.75, "west": 41.50, "east": 42.10},
    },
    {
        "woreda_id": "awash_fentale",
        "name": "Awash Fentale",
        "zone_id": "gabi_rasu_afar",
        "region_id": "afar",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_a",
        "centroid_lat": 9.167,
        "centroid_lon": 40.033,
        "area_km2": 1940.0,
        "elevation_mean_m": 960,
        "vulnerability_index": 0.75,
        "bbox": {"north": 9.35, "south": 8.98, "west": 39.85, "east": 40.25},
    },
    {
        "woreda_id": "gewane",
        "name": "Gewane",
        "zone_id": "gabi_rasu_afar",
        "region_id": "afar",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_a",
        "centroid_lat": 10.160,
        "centroid_lon": 40.650,
        "area_km2": 3210.0,
        "elevation_mean_m": 618,
        "vulnerability_index": 0.87,
        "bbox": {"north": 10.40, "south": 9.90, "west": 40.40, "east": 40.90},
    },
    {
        "woreda_id": "mille",
        "name": "Mille",
        "zone_id": "awsi_rasu_afar",
        "region_id": "afar",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_a",
        "centroid_lat": 11.410,
        "centroid_lon": 40.760,
        "area_km2": 2890.0,
        "elevation_mean_m": 530,
        "vulnerability_index": 0.88,
        "bbox": {"north": 11.65, "south": 11.18, "west": 40.55, "east": 41.00},
    },

    # ── AMHARA REGION (7 Woredas — Highlands & Marginal Lowlands) ───────────
    {
        "woreda_id": "delanta",
        "name": "Delanta",
        "zone_id": "north_wollo_amhara",
        "region_id": "amhara",
        "climate_zone_id": "dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 11.530,
        "centroid_lon": 39.230,
        "area_km2": 1180.0,
        "elevation_mean_m": 2600,
        "vulnerability_index": 0.82,
        "bbox": {"north": 11.72, "south": 11.35, "west": 39.08, "east": 39.38},
    },
    {
        "woreda_id": "guba_lafto",
        "name": "Guba Lafto",
        "zone_id": "north_wollo_amhara",
        "region_id": "amhara",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 11.830,
        "centroid_lon": 39.600,
        "area_km2": 1450.0,
        "elevation_mean_m": 1850,
        "vulnerability_index": 0.77,
        "bbox": {"north": 12.02, "south": 11.65, "west": 39.42, "east": 39.78},
    },
    {
        "woreda_id": "kobo",
        "name": "Raya Kobo",
        "zone_id": "north_wollo_amhara",
        "region_id": "amhara",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_a",
        "centroid_lat": 12.150,
        "centroid_lon": 39.630,
        "area_km2": 1890.0,
        "elevation_mean_m": 1470,
        "vulnerability_index": 0.79,
        "bbox": {"north": 12.35, "south": 11.95, "west": 39.45, "east": 39.82},
    },
    {
        "woreda_id": "basona_werana",
        "name": "Basona Werana (Debre Berhan)",
        "zone_id": "north_shewa_amhara",
        "region_id": "amhara",
        "climate_zone_id": "dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 9.680,
        "centroid_lon": 39.530,
        "area_km2": 1210.0,
        "elevation_mean_m": 2840,
        "vulnerability_index": 0.58,
        "bbox": {"north": 9.88, "south": 9.48, "west": 39.35, "east": 39.72},
    },
    {
        "woreda_id": "metema",
        "name": "Metema",
        "zone_id": "west_gondar_amhara",
        "region_id": "amhara",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_b",
        "centroid_lat": 12.960,
        "centroid_lon": 36.150,
        "area_km2": 3980.0,
        "elevation_mean_m": 750,
        "vulnerability_index": 0.68,
        "bbox": {"north": 13.25, "south": 12.65, "west": 35.85, "east": 36.45},
    },
    {
        "woreda_id": "bahir_dar_zuria",
        "name": "Bahir Dar Zuria",
        "zone_id": "west_gojjam_amhara",
        "region_id": "amhara",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 11.600,
        "centroid_lon": 37.380,
        "area_km2": 1520.0,
        "elevation_mean_m": 1800,
        "vulnerability_index": 0.52,
        "bbox": {"north": 11.82, "south": 11.38, "west": 37.18, "east": 37.58},
    },
    {
        "woreda_id": "debre_tabor",
        "name": "Debre Tabor",
        "zone_id": "south_gondar_amhara",
        "region_id": "amhara",
        "climate_zone_id": "dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 11.850,
        "centroid_lon": 38.020,
        "area_km2": 580.0,
        "elevation_mean_m": 2700,
        "vulnerability_index": 0.55,
        "bbox": {"north": 11.98, "south": 11.72, "west": 37.90, "east": 38.15},
    },

    # ── OROMIA REGION (8 Woredas — Pastoral South to Breadbasket) ───────────
    {
        "woreda_id": "yabelo",
        "name": "Yabelo",
        "zone_id": "borana_oromia",
        "region_id": "oromia",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_c",
        "centroid_lat": 4.883,
        "centroid_lon": 38.083,
        "area_km2": 5420.0,
        "elevation_mean_m": 1600,
        "vulnerability_index": 0.88,
        "bbox": {"north": 5.25, "south": 4.50, "west": 37.75, "east": 38.45},
    },
    {
        "woreda_id": "moyale_oromia",
        "name": "Moyale",
        "zone_id": "borana_oromia",
        "region_id": "oromia",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_c",
        "centroid_lat": 3.530,
        "centroid_lon": 39.050,
        "area_km2": 4810.0,
        "elevation_mean_m": 1100,
        "vulnerability_index": 0.91,
        "bbox": {"north": 3.90, "south": 3.20, "west": 38.70, "east": 39.40},
    },
    {
        "woreda_id": "dhas",
        "name": "Dhas",
        "zone_id": "borana_oromia",
        "region_id": "oromia",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_c",
        "centroid_lat": 4.350,
        "centroid_lon": 38.250,
        "area_km2": 3890.0,
        "elevation_mean_m": 1050,
        "vulnerability_index": 0.93,
        "bbox": {"north": 4.65, "south": 4.05, "west": 37.95, "east": 38.55},
    },
    {
        "woreda_id": "babilie_oromia",
        "name": "Babilie",
        "zone_id": "east_hararghe_oromia",
        "region_id": "oromia",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_c",
        "centroid_lat": 9.220,
        "centroid_lon": 42.330,
        "area_km2": 3120.0,
        "elevation_mean_m": 1450,
        "vulnerability_index": 0.84,
        "bbox": {"north": 9.50, "south": 8.95, "west": 42.05, "east": 42.60},
    },
    {
        "woreda_id": "adaa_bishoftu",
        "name": "Ada'a (Bishoftu)",
        "zone_id": "east_shewa_oromia",
        "region_id": "oromia",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 8.750,
        "centroid_lon": 38.980,
        "area_km2": 1150.0,
        "elevation_mean_m": 1920,
        "vulnerability_index": 0.42,
        "bbox": {"north": 8.95, "south": 8.55, "west": 38.80, "east": 39.18},
    },
    {
        "woreda_id": "dinsho",
        "name": "Dinsho (Bale)",
        "zone_id": "bale_oromia",
        "region_id": "oromia",
        "climate_zone_id": "wurch",
        "rainfall_regime": "regime_a",
        "centroid_lat": 7.100,
        "centroid_lon": 39.780,
        "area_km2": 1280.0,
        "elevation_mean_m": 3050,
        "vulnerability_index": 0.54,
        "bbox": {"north": 7.30, "south": 6.90, "west": 39.58, "east": 39.98},
    },
    {
        "woreda_id": "ambo",
        "name": "Ambo Zuria",
        "zone_id": "west_shewa_oromia",
        "region_id": "oromia",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 8.980,
        "centroid_lon": 37.850,
        "area_km2": 1410.0,
        "elevation_mean_m": 2100,
        "vulnerability_index": 0.48,
        "bbox": {"north": 9.18, "south": 8.78, "west": 37.65, "east": 38.05},
    },
    {
        "woreda_id": "jimma_arjo",
        "name": "Jimma Arjo",
        "zone_id": "east_wollega_oromia",
        "region_id": "oromia",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_b",
        "centroid_lat": 8.750,
        "centroid_lon": 36.500,
        "area_km2": 1290.0,
        "elevation_mean_m": 2100,
        "vulnerability_index": 0.44,
        "bbox": {"north": 8.95, "south": 8.55, "west": 36.30, "east": 36.70},
    },

    # ── SOMALI REGION (6 Woredas — High Teleconnection Coupling) ────────────
    {
        "woreda_id": "gode",
        "name": "Gode",
        "zone_id": "shabelle_somali",
        "region_id": "somali",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_c",
        "centroid_lat": 5.950,
        "centroid_lon": 43.550,
        "area_km2": 6250.0,
        "elevation_mean_m": 290,
        "vulnerability_index": 0.95,
        "bbox": {"north": 6.35, "south": 5.55, "west": 43.15, "east": 43.95},
    },
    {
        "woreda_id": "kebri_dehar",
        "name": "Kebri Dehar",
        "zone_id": "korahe_somali",
        "region_id": "somali",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_c",
        "centroid_lat": 6.733,
        "centroid_lon": 44.283,
        "area_km2": 5890.0,
        "elevation_mean_m": 530,
        "vulnerability_index": 0.92,
        "bbox": {"north": 7.10, "south": 6.35, "west": 43.90, "east": 44.65},
    },
    {
        "woreda_id": "jigjiga",
        "name": "Jigjiga City",
        "zone_id": "fafan_somali",
        "region_id": "somali",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_c",
        "centroid_lat": 9.350,
        "centroid_lon": 42.800,
        "area_km2": 1380.0,
        "elevation_mean_m": 1609,
        "vulnerability_index": 0.70,
        "bbox": {"north": 9.55, "south": 9.15, "west": 42.60, "east": 43.00},
    },
    {
        "woreda_id": "dollo_ado",
        "name": "Dollo Ado",
        "zone_id": "liben_somali",
        "region_id": "somali",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_c",
        "centroid_lat": 4.180,
        "centroid_lon": 42.050,
        "area_km2": 4920.0,
        "elevation_mean_m": 210,
        "vulnerability_index": 0.96,
        "bbox": {"north": 4.55, "south": 3.80, "west": 41.70, "east": 42.40},
    },
    {
        "woreda_id": "warder",
        "name": "Warder",
        "zone_id": "dollo_somali",
        "region_id": "somali",
        "climate_zone_id": "bereha",
        "rainfall_regime": "regime_c",
        "centroid_lat": 6.970,
        "centroid_lon": 45.330,
        "area_km2": 6120.0,
        "elevation_mean_m": 545,
        "vulnerability_index": 0.94,
        "bbox": {"north": 7.35, "south": 6.60, "west": 44.95, "east": 45.70},
    },
    {
        "woreda_id": "degehabur",
        "name": "Degehabur",
        "zone_id": "jarar_somali",
        "region_id": "somali",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_c",
        "centroid_lat": 8.220,
        "centroid_lon": 43.560,
        "area_km2": 4870.0,
        "elevation_mean_m": 1040,
        "vulnerability_index": 0.89,
        "bbox": {"north": 8.55, "south": 7.90, "west": 43.20, "east": 43.90},
    },

    # ── SIDAMA & SOUTH ETHIOPIA (4 Woredas) ──────────────────────────────────
    {
        "woreda_id": "hawassa_zuria",
        "name": "Hawassa Zuria",
        "zone_id": "sidama_zone",
        "region_id": "sidama",
        "climate_zone_id": "weyna_dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 7.050,
        "centroid_lon": 38.480,
        "area_km2": 820.0,
        "elevation_mean_m": 1700,
        "vulnerability_index": 0.49,
        "bbox": {"north": 7.22, "south": 6.88, "west": 38.35, "east": 38.62},
    },
    {
        "woreda_id": "aleta_wendo",
        "name": "Aleta Wendo",
        "zone_id": "sidama_zone",
        "region_id": "sidama",
        "climate_zone_id": "dega",
        "rainfall_regime": "regime_a",
        "centroid_lat": 6.600,
        "centroid_lon": 38.420,
        "area_km2": 590.0,
        "elevation_mean_m": 2000,
        "vulnerability_index": 0.53,
        "bbox": {"north": 6.75, "south": 6.45, "west": 38.30, "east": 38.55},
    },
    {
        "woreda_id": "hamer",
        "name": "Hamer",
        "zone_id": "south_omo_zone",
        "region_id": "south_ethiopia",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_c",
        "centroid_lat": 5.080,
        "centroid_lon": 36.550,
        "area_km2": 5780.0,
        "elevation_mean_m": 850,
        "vulnerability_index": 0.89,
        "bbox": {"north": 5.45, "south": 4.70, "west": 36.20, "east": 36.90},
    },
    {
        "woreda_id": "konso",
        "name": "Konso",
        "zone_id": "konso_zone",
        "region_id": "south_ethiopia",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_c",
        "centroid_lat": 5.340,
        "centroid_lon": 37.430,
        "area_km2": 2350.0,
        "elevation_mean_m": 1450,
        "vulnerability_index": 0.81,
        "bbox": {"north": 5.60, "south": 5.10, "west": 37.20, "east": 37.65},
    },

    # ── BENISHANGUL-GUMUZ & GAMBELLA (Western Monomodal, 2 Woredas) ─────────
    {
        "woreda_id": "assosa",
        "name": "Assosa",
        "zone_id": "assosa_zone",
        "region_id": "benishangul",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_b",
        "centroid_lat": 10.070,
        "centroid_lon": 34.530,
        "area_km2": 2980.0,
        "elevation_mean_m": 1570,
        "vulnerability_index": 0.59,
        "bbox": {"north": 10.35, "south": 9.80, "west": 34.25, "east": 34.80},
    },
    {
        "woreda_id": "gambella_zuria",
        "name": "Gambella Zuria",
        "zone_id": "anywaa_zone",
        "region_id": "gambella",
        "climate_zone_id": "kolla",
        "rainfall_regime": "regime_b",
        "centroid_lat": 8.250,
        "centroid_lon": 34.580,
        "area_km2": 3120.0,
        "elevation_mean_m": 520,
        "vulnerability_index": 0.62,
        "bbox": {"north": 8.50, "south": 8.00, "west": 34.30, "east": 34.85},
    },
]

# Backwards compatibility alias for Tigray-specific code & test fixtures
TIGRAY_WOREDAS = [w for w in ETHIOPIA_WOREDAS if w["region_id"] == "tigray"]


# ────────────────────────────────────────────────────────────────────────────
# 6. Query and Helper Functions
# ────────────────────────────────────────────────────────────────────────────
def get_all_woredas(
    region_id: Optional[str] = None,
    climate_zone_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Returns woredas across all of Ethiopia, with optional filtering
    by administrative region or top-level climate zone.
    """
    woredas = ETHIOPIA_WOREDAS
    if region_id:
        woredas = [w for w in woredas if w["region_id"].lower() == region_id.lower()]
    if climate_zone_id:
        woredas = [w for w in woredas if w.get("climate_zone_id", "").lower() == climate_zone_id.lower()]
    return woredas


def get_woreda_by_id(woreda_id: str) -> Optional[dict[str, Any]]:
    """Find woreda by ID or case-insensitive name across all Ethiopia."""
    for w in ETHIOPIA_WOREDAS:
        if w["woreda_id"].lower() == woreda_id.lower() or w["name"].lower() == woreda_id.lower():
            return w
    return None


def get_climate_zones() -> list[dict[str, Any]]:
    """Return all 5 Ethiopian Agro-Ecological Climate Zones."""
    return CLIMATE_ZONES


def get_climate_zone_by_id(zone_id: str) -> Optional[dict[str, Any]]:
    """Lookup specific Agro-Ecological Climate Zone."""
    for cz in CLIMATE_ZONES:
        if cz["climate_zone_id"].lower() == zone_id.lower():
            return cz
    return None


def get_all_regions() -> list[dict[str, Any]]:
    """Return all administrative regions of Ethiopia."""
    return ETHIOPIA_REGIONS


def get_all_zones(region_id: Optional[str] = None) -> list[dict[str, Any]]:
    """Return administrative zones, optionally filtered by region."""
    if region_id:
        return [z for z in ETHIOPIA_ZONES if z["region_id"].lower() == region_id.lower()]
    return ETHIOPIA_ZONES
