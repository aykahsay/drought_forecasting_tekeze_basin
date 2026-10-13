"""
Tanqua Abergelle Woreda & Tekeze River Basin Spatial & Hydrological Model
========================================================================
Administrative Unit: Tanqua Abergelle Woreda, Central Tigray Zone, Tigray, Ethiopia.
Local Hydrology:     Tekeze River Basin, Tekeze Hydroelectric Dam Reservoir & Tanqua River.
Capital:             Yechila (13.250°N, 38.980°E)

Settlements mapped directly from official survey:
  - Yechila (Woreda administrative capital, eastern road corridor)
  - Ozentari (Western Tekeze Reservoir shore settlement)
  - Missadi (Western canyon plain)
  - Adeseb (Northwestern valley)
  - Hidmo (Northern foothills)
  - Fighisia (North-central ridge)
  - Adellet (Central plateau)
  - Gera (Northeastern approach)
  - Crustaba (South-central plain)
  - Shewat'a (Western approach to Yechila)
  - Agora (Northern road / Tanqua river corridor)
  - Bolda (Southern border corridor near Amhara/Wag Hemra boundary)
"""

from __future__ import annotations
import math
from typing import Any, Dict, List, Optional

# Metadata
TEKEZE_ABERGELLE_METADATA = {
    "watershed_id": "tanqua_abergelle_tekeze",
    "name": "Yechila Abergelle Woreda - Tekeze Basin",
    "name_local": "ወረዳ ጭላ ዓበርገለ - ተፋሰስ ተከዘ",
    "woreda": "Tanqua Abergelle",
    "capital": "Yechila",
    "zone": "Central Tigray",
    "region": "Tigray",
    "country": "Ethiopia",
    "basin": "Tekeze River Basin (Nile Basin)",
    "local_river": "Tekeze River (and Tekeze Hydroelectric Reservoir)",
    "tributary_river": "Tanqua River",
    "centroid_lat": 13.250,
    "centroid_lon": 38.980,
    "elevation_range_m": "1,080m (Tekeze canyon floor) to 1,650m (Eastern ridges)",
    "climate_zone": "Kolla (Arid & Semi-Arid Lowlands)",
    "soil_types": "Vertisols (cracking black clay), Chromic Cambisols, Lithic Leptosols",
    "mean_annual_rainfall_mm": "400 - 550 mm (highly erratic, unimodal Kiremt)",
    "primary_crops": ["Dryland Sorghum (Mashilla)", "Sesame (Selit)", "Lowland Teff"],
    "livestock": "Abergelle indigenous drought-hardy goats, cattle, donkeys",
    "description": (
        "Tanqua Abergelle is a drought-prone woreda in Central Tigray, Northern Ethiopia, bounded on the west "
        "by the massive Tekeze River and the Tekeze Hydroelectric Dam Reservoir, and on the south by the "
        "Amhara (Wag Hemra) border. The landscape is characterized by severe potential evapotranspiration, "
        "deeply incised river gorges, and reliance on alluvial groundwater and the Tekeze reservoir."
    ),
}

# Member administrative units
TEKEZE_WOREDAS = [
    {"woreda_id": "tanqua_abergelle", "name": "Tanqua Abergelle", "zone": "Central Tigray", "capital": "Yechila", "elevation_mean_m": 1380, "aez": "kolla"},
    {"woreda_id": "tekeze_gorge", "name": "Tekeze Reservoir Corridor", "zone": "Hydrological Buffer", "capital": "Ozentari", "elevation_mean_m": 1140, "aez": "deep_kolla"},
]

# Settlements mapped directly from the woreda map
TEKEZE_VILLAGES = [
    {
        "village_id": "vil_yechila",
        "name": "Yechila Town",
        "name_local": "የጭላ ከተማ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Yechila 01",
        "lat": 13.250,
        "lon": 38.980,
        "elevation_m": 1450,
        "households": 720,
        "population": 3950,
        "primary_crops": ["Dryland Sorghum", "Sesame", "Lowland Teff"],
        "aez": "kolla",
        "role": "Woreda administrative capital, market hub",
    },
    {
        "village_id": "vil_ozentari",
        "name": "Ozentari",
        "name_local": "ኦዘንታሪ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Ozentari",
        "lat": 13.230,
        "lon": 38.720,
        "elevation_m": 1150,
        "households": 310,
        "population": 1680,
        "primary_crops": ["Recessional Sorghum", "Sesame", "Melon"],
        "aez": "deep_kolla",
        "role": "Tekeze Reservoir lakeside fishing and watering settlement",
    },
    {
        "village_id": "vil_missadi",
        "name": "Missadi",
        "name_local": "ሚሳዲ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Missadi",
        "lat": 13.240,
        "lon": 38.780,
        "elevation_m": 1260,
        "households": 380,
        "population": 2050,
        "primary_crops": ["Sorghum (Mashilla)", "Sesame"],
        "aez": "kolla",
        "role": "Lowland pastoral grazing hamlet",
    },
    {
        "village_id": "vil_adeseb",
        "name": "Adeseb",
        "name_local": "አደሰብ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Adeseb",
        "lat": 13.290,
        "lon": 38.830,
        "elevation_m": 1310,
        "households": 420,
        "population": 2280,
        "primary_crops": ["Sorghum", "Cowpea", "Sesame"],
        "aez": "kolla",
        "role": "Northwestern agricultural valley",
    },
    {
        "village_id": "vil_hidmo",
        "name": "Hidmo",
        "name_local": "ሕድሞ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Hidmo",
        "lat": 13.340,
        "lon": 38.850,
        "elevation_m": 1360,
        "households": 360,
        "population": 1940,
        "primary_crops": ["Sorghum", "Lowland Teff"],
        "aez": "kolla",
        "role": "Terraced foothill village",
    },
    {
        "village_id": "vil_fighisia",
        "name": "Fighisia",
        "name_local": "ፍጊሲያ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Fighisia",
        "lat": 13.380,
        "lon": 38.870,
        "elevation_m": 1410,
        "households": 290,
        "population": 1580,
        "primary_crops": ["Dryland Sorghum", "Millet"],
        "aez": "kolla",
        "role": "Northern ridge settlement",
    },
    {
        "village_id": "vil_adellet",
        "name": "Adellet",
        "name_local": "አደለት",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Adellet",
        "lat": 13.280,
        "lon": 38.920,
        "elevation_m": 1390,
        "households": 460,
        "population": 2490,
        "primary_crops": ["Sorghum", "Sesame", "Teff"],
        "aez": "kolla",
        "role": "Central plateau agricultural pocket",
    },
    {
        "village_id": "vil_gera",
        "name": "Gera",
        "name_local": "ገራ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Gera",
        "lat": 13.320,
        "lon": 38.960,
        "elevation_m": 1430,
        "households": 390,
        "population": 2110,
        "primary_crops": ["Lowland Teff", "Sorghum"],
        "aez": "kolla",
        "role": "Northeastern valley settlement",
    },
    {
        "village_id": "vil_crustaba",
        "name": "Crustaba",
        "name_local": "ክሩስታባ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Crustaba",
        "lat": 13.200,
        "lon": 38.920,
        "elevation_m": 1350,
        "households": 410,
        "population": 2240,
        "primary_crops": ["Sesame", "Sorghum", "Chickpea"],
        "aez": "kolla",
        "role": "South-central grazing zone",
    },
    {
        "village_id": "vil_shewata",
        "name": "Shewat'a",
        "name_local": "ሸዋዕታ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Shewat'a",
        "lat": 13.220,
        "lon": 38.950,
        "elevation_m": 1400,
        "households": 480,
        "population": 2620,
        "primary_crops": ["Dryland Sorghum", "Sesame", "Teff"],
        "aez": "kolla",
        "role": "Western gateway community to Yechila",
    },
    {
        "village_id": "vil_agora",
        "name": "Agora",
        "name_local": "ኣጎራ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Agora",
        "lat": 13.300,
        "lon": 39.000,
        "elevation_m": 1440,
        "households": 350,
        "population": 1890,
        "primary_crops": ["Sorghum", "Teff", "Vegetables"],
        "aez": "kolla",
        "role": "Northern road corridor along Tanqua River stream",
    },
    {
        "village_id": "vil_bolda",
        "name": "Bolda",
        "name_local": "ቦልዳ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Bolda",
        "lat": 13.160,
        "lon": 38.980,
        "elevation_m": 1420,
        "households": 440,
        "population": 2370,
        "primary_crops": ["Sorghum", "Sesame", "Cowpea"],
        "aez": "kolla",
        "role": "Southern frontier village near Amhara (Wag Hemra) border",
    },
    {
        "village_id": "vil_jijike",
        "name": "Jijike",
        "name_local": "ጂጂኬ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Jijike",
        "lat": 13.440,
        "lon": 38.860,
        "elevation_m": 1470,
        "households": 280,
        "population": 1520,
        "primary_crops": ["Sorghum", "Millet", "Teff"],
        "aez": "kolla",
        "role": "Northern highlands approach village",
    },
    {
        "village_id": "vil_adi_buda",
        "name": "Adi Buda",
        "name_local": "ዓዲ ቡዳ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Adi Buda",
        "lat": 13.410,
        "lon": 38.900,
        "elevation_m": 1450,
        "households": 310,
        "population": 1690,
        "primary_crops": ["Sorghum", "Sesame"],
        "aez": "kolla",
        "role": "North-central valley agricultural settlement",
    },
    {
        "village_id": "vil_adi_bula",
        "name": "Adi Bula",
        "name_local": "ዓዲ ቡላ",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Adi Bula",
        "lat": 13.390,
        "lon": 38.970,
        "elevation_m": 1460,
        "households": 340,
        "population": 1840,
        "primary_crops": ["Lowland Teff", "Sorghum"],
        "aez": "kolla",
        "role": "Northeastern plateau settlement",
    },
]

# Transboundary reference points shown on the southern border of the user map (Amhara / Wag Hemra border)
TEKEZE_SOUTHERN_BORDER_POINTS = [
    {
        "point_id": "pt_guftamlo",
        "name": "Guftamlo",
        "name_local": "ጉፍታምሎ",
        "region": "Amhara (Wag Hemra boundary)",
        "lat": 13.110,
        "lon": 38.860,
        "role": "Southern transboundary reference point south of Tigray/Amhara border line",
    },
    {
        "point_id": "pt_digula",
        "name": "Digula",
        "name_local": "ዲጉላ",
        "region": "Amhara (Wag Hemra boundary)",
        "lat": 13.110,
        "lon": 38.970,
        "role": "Southeastern transboundary reference point south of Tigray/Amhara border line",
    },
]

# Real local water bodies directly from the map
TEKEZE_WATER_BODIES = [
    {
        "water_body_id": "wb_tekeze_reservoir",
        "name": "Tekeze Hydroelectric Dam Reservoir (Western Border)",
        "name_local": "የተከዘ ግድብ ሃይቅ",
        "type": "mega_reservoir",
        "lat": 13.230,
        "lon": 38.710,
        "elevation_m": 1140,
        "surface_area_ha": 10500.0,
        "estimated_storage_m3": 9300000000,
        "is_perennial": True,
        "description": "The massive reservoir seen on the west of the map bordering Ozentari; critical bulk water and fish source.",
    },
    {
        "water_body_id": "wb_tekeze_trunk_river",
        "name": "Tekeze River Canyon Trunk Channel",
        "name_local": "ተከዘ ወንዝ ዋና ፈሳሽ",
        "type": "perennial_river",
        "lat": 13.250,
        "lon": 38.715,
        "elevation_m": 1110,
        "surface_area_ha": 420.0,
        "estimated_storage_m3": 45000000,
        "is_perennial": True,
        "description": "The main river channel flowing through the deep gorge forming the western boundary of the woreda.",
    },
    {
        "water_body_id": "wb_tanqua_river_corridor",
        "name": "Tanqua River Seasonal Corridor",
        "name_local": "ታንቋ ወንዝ",
        "type": "tributary_river",
        "lat": 13.280,
        "lon": 38.990,
        "elevation_m": 1420,
        "surface_area_ha": 55.0,
        "estimated_storage_m3": 850000,
        "is_perennial": False,
        "description": "Seasonal tributary running down near Agora and Yechila providing sub-surface sand dam storage.",
    },
]

# Real water infrastructure in Tanqua Abergelle
TEKEZE_WATER_POINTS = [
    {
        "water_point_id": "wp_tekeze_ozentari_intake",
        "name": "Tekeze Reservoir Intake at Ozentari",
        "name_local": "የተከዘ ግድብ ኦዘንታሪ መቅጃ",
        "type": "reservoir_intake",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Ozentari",
        "lat": 13.232,
        "lon": 38.721,
        "elevation_m": 1145,
        "discharge_lpm": 2500.0,
        "is_perennial": True,
        "status": "functional",
        "water_quality": "surface_bulk",
        "description": "Direct intake from Tekeze reservoir for community and livestock watering.",
    },
    {
        "water_point_id": "wp_yechila_deep_borehole",
        "name": "Yechila Town Motorized Deep Well #1",
        "name_local": "የጭላ ከተማ ጥልቅ ጉድጓድ ፩",
        "type": "borehole",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Yechila 01",
        "lat": 13.252,
        "lon": 38.982,
        "elevation_m": 1445,
        "discharge_lpm": 185.0,
        "is_perennial": True,
        "status": "functional",
        "water_quality": "potable",
        "description": "120m deep motorized well supplying drinking water to Yechila township.",
    },
    {
        "water_point_id": "wp_bolda_sand_dam",
        "name": "Bolda Sub-Surface Sand Dam",
        "name_local": "ቦልዳ የአሸዋ ግድብ",
        "type": "sand_dam",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Bolda",
        "lat": 13.162,
        "lon": 38.978,
        "elevation_m": 1415,
        "discharge_lpm": 55.0,
        "is_perennial": True,
        "status": "functional",
        "water_quality": "potable_subsurface",
        "description": "Engineered sand storage dam storing floodwater under dry riverbed sand.",
    },
    {
        "water_point_id": "wp_agora_riverbed_scoop",
        "name": "Agora Tanqua Riverbed Shallow Well",
        "name_local": "ኣጎራ የወንዝ ዳርቻ ጉድጓድ",
        "type": "shallow_well",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Agora",
        "lat": 13.298,
        "lon": 38.998,
        "elevation_m": 1435,
        "discharge_lpm": 30.0,
        "is_perennial": True,
        "status": "functional",
        "water_quality": "potable",
        "description": "Concrete lined shallow well in Tanqua alluvial riverbed.",
    },
    {
        "water_point_id": "wp_missadi_water_point",
        "name": "Missadi Community Hand Pump",
        "name_local": "ሚሳዲ ማህበረሰብ እጅ ፓምፕ",
        "type": "hand_pump",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Missadi",
        "lat": 13.242,
        "lon": 38.782,
        "elevation_m": 1265,
        "discharge_lpm": 22.0,
        "is_perennial": True,
        "status": "functional",
        "water_quality": "potable",
        "description": "Afridev hand pump installed on fractured basalt aquifer in western lowlands.",
    },
    {
        "water_point_id": "wp_crustaba_pond",
        "name": "Crustaba Livestock Retention Pond",
        "name_local": "ክሩስታባ የከብት ማጠጫ ኩሬ",
        "type": "micro_dam",
        "woreda_id": "tanqua_abergelle",
        "kebele": "Crustaba",
        "lat": 13.202,
        "lon": 38.922,
        "elevation_m": 1352,
        "discharge_lpm": 0.0,
        "is_perennial": False,
        "status": "reduced_yield",
        "water_quality": "livestock_only",
        "description": "Seasonal earthen pond storing runoff for goat herds during post-rainy season.",
    },
]


def calculate_haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate geodesic distance between two points in meters using Haversine formula."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def calculate_walking_time_minutes(distance_m: float, elevation_diff_m: float) -> int:
    """Calculate walking time over arid Kolla terrain (base 70 m/min + elevation penalty)."""
    base_minutes = distance_m / 70.0
    climb_penalty = max(0.0, elevation_diff_m) / 10.0
    descent_penalty = max(0.0, -elevation_diff_m) / 30.0
    return max(1, round(base_minutes + climb_penalty + descent_penalty))


def get_village_by_id(village_id: str) -> Optional[Dict[str, Any]]:
    return next((v for v in TEKEZE_VILLAGES if v["village_id"] == village_id), None)


def get_water_point_by_id(water_point_id: str) -> Optional[Dict[str, Any]]:
    return next((wp for wp in TEKEZE_WATER_POINTS if wp["water_point_id"] == water_point_id), None)


def get_village_water_distance_matrix(village_id: str) -> Dict[str, Any]:
    village = get_village_by_id(village_id)
    if not village:
        return {"error": f"Village '{village_id}' not found in Tanqua Abergelle Woreda"}

    v_lat, v_lon, v_elev = village["lat"], village["lon"], village["elevation_m"]

    wp_distances = []
    for wp in TEKEZE_WATER_POINTS:
        dist_m = calculate_haversine_distance_m(v_lat, v_lon, wp["lat"], wp["lon"])
        elev_diff = wp["elevation_m"] - v_elev
        walk_min = calculate_walking_time_minutes(dist_m, elev_diff)
        wp_distances.append({
            "water_point_id": wp["water_point_id"],
            "name": wp["name"],
            "type": wp["type"],
            "status": wp["status"],
            "is_perennial": wp["is_perennial"],
            "distance_m": round(dist_m),
            "distance_km": round(dist_m / 1000.0, 2),
            "walking_time_minutes": walk_min,
            "coordinates": {"lat": wp["lat"], "lon": wp["lon"]},
        })
    wp_distances.sort(key=lambda x: x["distance_m"])

    wb_distances = []
    for wb in TEKEZE_WATER_BODIES:
        dist_m = calculate_haversine_distance_m(v_lat, v_lon, wb["lat"], wb["lon"])
        wb_distances.append({
            "water_body_id": wb["water_body_id"],
            "name": wb["name"],
            "type": wb["type"],
            "distance_m": round(dist_m),
            "distance_km": round(dist_m / 1000.0, 2),
            "coordinates": {"lat": wb["lat"], "lon": wb["lon"]},
        })
    wb_distances.sort(key=lambda x: x["distance_m"])

    nearest_wp = wp_distances[0] if wp_distances else None
    nearest_wb = wb_distances[0] if wb_distances else None

    # Water security in arid Kolla context
    dist_to_primary = nearest_wp["distance_m"] if nearest_wp else 99999
    if dist_to_primary <= 1000:
        sec_status = "WATER_SECURE_LOCAL"
        sec_desc = "Protected community water source within 1.0 km."
    elif dist_to_primary <= 3000:
        sec_status = "MODERATE_ACCESS"
        sec_desc = "Water point within 1.0 - 3.0 km walking distance."
    else:
        sec_status = "ACUTE_WATER_DEFICIT"
        sec_desc = "Households travel > 3.0 km across rugged terrain to reach water."

    return {
        "village": village,
        "water_security": {
            "status": sec_status,
            "description": sec_desc,
            "nearest_water_point": nearest_wp,
            "nearest_water_body": nearest_wb,
        },
        "all_water_points_by_distance": wp_distances,
        "water_bodies_by_distance": wb_distances,
    }


def get_tekeze_abergelle_summary() -> Dict[str, Any]:
    total_pop = sum(v["population"] for v in TEKEZE_VILLAGES)
    total_hh = sum(v["households"] for v in TEKEZE_VILLAGES)
    perennial_pts = sum(1 for wp in TEKEZE_WATER_POINTS if wp["is_perennial"])

    return {
        "metadata": TEKEZE_ABERGELLE_METADATA,
        "statistics": {
            "woreda": "Tanqua Abergelle",
            "capital": "Yechila",
            "region": "Tigray",
            "basin": "Tekeze River Basin",
            "villages_mapped": len(TEKEZE_VILLAGES),
            "total_population": total_pop,
            "total_households": total_hh,
            "water_points_monitored": len(TEKEZE_WATER_POINTS),
            "perennial_points": perennial_pts,
            "water_bodies": len(TEKEZE_WATER_BODIES),
        },
        "woredas": TEKEZE_WOREDAS,
        "villages": TEKEZE_VILLAGES,
        "water_points": TEKEZE_WATER_POINTS,
        "water_bodies": TEKEZE_WATER_BODIES,
    }
