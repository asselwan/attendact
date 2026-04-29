from __future__ import annotations

"""Fixed UAE location coordinates for deterministic distance computation.

Clinic coordinates are the actual hospital locations.
Patient area coordinates are approximate centroids of each region.
"""

from math import atan2, cos, pi, sin, sqrt


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine great-circle distance in km."""
    R = 6371
    d_lat = (lat2 - lat1) * pi / 180
    d_lng = (lng2 - lng1) * pi / 180
    a = (
        sin(d_lat / 2) ** 2
        + cos(lat1 * pi / 180) * cos(lat2 * pi / 180) * sin(d_lng / 2) ** 2
    )
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# Hospital coordinates (lat, lng)
CLINIC_COORDS: dict[str, tuple[float, float]] = {
    "SSMC": (24.4295, 54.4350),
    "CCAD": (24.5340, 54.4340),
    "TAWAM": (24.2200, 55.7400),
    "MAFRAQ": (24.4700, 54.3800),
    "ALAIN": (24.2140, 55.7560),
    "CORNICHE": (24.4860, 54.3560),
    "HEALTHPOINT": (24.4980, 54.6100),
    "NMC": (24.4530, 54.3710),
    "BURJEEL_AD": (24.4270, 54.4770),
    "BURJEEL_DXB": (25.1850, 55.2560),
    "MEDICLINIC": (24.4540, 54.3880),
    "DANAT": (24.4260, 54.4350),
    "RASHID": (25.2330, 55.3170),
    "DUBAI_HOSP": (25.2540, 55.3120),
    "AMERICAN_DXB": (25.2310, 55.2700),
    "ASTER": (25.1860, 55.2610),
    "ALZAHRA": (25.3420, 55.3870),
    "UHS": (25.3040, 55.4560),
}

# Patient area centroids (lat, lng)
AREA_COORDS: dict[str, tuple[float, float]] = {
    # Abu Dhabi City
    "al_maryah_island": (24.5020, 54.3940),
    "al_reem_island": (24.4980, 54.4020),
    "saadiyat_island": (24.5400, 54.4400),
    "yas_island": (24.4900, 54.6100),
    "al_bateen": (24.4610, 54.3540),
    "corniche": (24.4790, 54.3550),
    "al_nahyan": (24.4680, 54.3730),
    "al_mushrif": (24.4560, 54.3850),
    "al_karamah": (24.4510, 54.3710),
    "al_muroor": (24.4480, 54.3920),
    "al_rawdah": (24.4570, 54.4050),
    "tourist_club": (24.4920, 54.3770),
    "between_bridges": (24.4630, 54.4030),
    # Abu Dhabi Suburbs
    "khalifa_city": (24.4130, 54.5750),
    "mbz_city": (24.3500, 54.5500),
    "mussafah": (24.3500, 54.4800),
    "al_shamkha": (24.3700, 54.6100),
    "al_reef": (24.3200, 54.7000),
    "baniyas": (24.3100, 54.6400),
    "al_wathba": (24.2500, 54.6000),
    "shahama": (24.5800, 54.6800),
    "al_rahba": (24.5700, 54.7300),
    "al_falah": (24.3400, 54.5200),
    # Al Ain
    "al_ain_centre": (24.2100, 55.7450),
    "al_jimi": (24.2300, 55.7300),
    "al_muwaiji": (24.2000, 55.7200),
    "al_khabisi": (24.2150, 55.7700),
    "hili": (24.2800, 55.7700),
    "zakher": (24.1700, 55.7500),
    # Dubai
    "bur_dubai": (25.2530, 55.2970),
    "deira": (25.2700, 55.3300),
    "downtown_dubai": (25.1970, 55.2740),
    "dubai_marina": (25.0800, 55.1400),
    "jumeirah": (25.2120, 55.2550),
    "al_barsha": (25.1130, 55.2000),
    "international_city": (25.1650, 55.4050),
    "silicon_oasis": (25.1180, 55.3780),
    # Sharjah
    "al_majaz": (25.3350, 55.3890),
    "al_nahda_shj": (25.3100, 55.3700),
    "al_taawun": (25.3280, 55.3780),
    "al_khan": (25.3280, 55.3550),
    # Northern Emirates
    "ajman": (25.4100, 55.4350),
    "rak": (25.7900, 55.9500),
    "fujairah": (25.1200, 56.3400),
    "uaq": (25.5650, 55.5560),
}


def compute_distance(clinic_code: str | None, area_code: str | None) -> float | None:
    """Compute distance in km between a clinic and patient area.

    Returns None if either code is unknown.
    """
    if not clinic_code or not area_code:
        return None

    clinic = CLINIC_COORDS.get(clinic_code)
    area = AREA_COORDS.get(area_code)

    if not clinic or not area:
        return None

    return round(haversine_km(area[0], area[1], clinic[0], clinic[1]), 1)
