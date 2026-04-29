"""Geocoding and autocomplete routes. Ported from FuelQ location assets."""

import os
from math import atan2, cos, pi, sin, sqrt

import httpx
from fastapi import APIRouter

router = APIRouter()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


@router.get("/autocomplete")
async def autocomplete(q: str = ""):
    """Google Places Autocomplete for area search."""
    if len(q.strip()) < 2:
        return {"predictions": []}

    if not GOOGLE_API_KEY:
        return {"predictions": [], "status": "NO_API_KEY"}

    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {"input": q, "key": GOOGLE_API_KEY}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    return {"predictions": data.get("predictions", []), "status": data.get("status")}


async def geocode_area(area: str) -> tuple[float, float] | None:
    """Geocode an area name to (lat, lng). Returns None on failure."""
    if not area or not GOOGLE_API_KEY:
        return None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": area, "key": GOOGLE_API_KEY}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if data.get("status") != "OK" or not data.get("results"):
        return None

    loc = data["results"][0]["geometry"]["location"]
    return (loc["lat"], loc["lng"])


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine great-circle distance in km. Ported from FuelQ."""
    R = 6371
    d_lat = (lat2 - lat1) * pi / 180
    d_lng = (lng2 - lng1) * pi / 180
    a = (
        sin(d_lat / 2) ** 2
        + cos(lat1 * pi / 180) * cos(lat2 * pi / 180) * sin(d_lng / 2) ** 2
    )
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))
