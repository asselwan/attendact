"""UAE-specific feature engineering for no-show prediction."""

from __future__ import annotations

import math
from datetime import datetime

from .calendar import is_eid_window, is_post_iftar, is_pre_sahur, is_ramadan, is_summer_exodus


def compute_features(raw: dict) -> dict:
    """Transform raw appointment input into model features.

    All features are pure computations with no side effects.
    """
    appointment_at = _parse_dt(raw["appointment_at"])
    booked_at = _parse_dt(raw["booked_at"])

    lead_time_days = (appointment_at - booked_at).days
    ramadan = is_ramadan(appointment_at)

    # Prior no-show rate with smoothing
    noshow_count = raw.get("prior_noshow_count_12mo", 0)
    attended_count = raw.get("prior_attended_count_12mo", 0)
    total = noshow_count + attended_count
    if total < 3:
        prior_noshow_rate = 0.2  # smoothed default
    else:
        prior_noshow_rate = noshow_count / total

    # Hour of day (cyclic encoding)
    hour = appointment_at.hour
    hour_sin = math.sin(2 * math.pi * hour / 24)
    hour_cos = math.cos(2 * math.pi * hour / 24)

    # Day of week (cyclic encoding)
    dow = appointment_at.weekday()
    dow_sin = math.sin(2 * math.pi * dow / 7)
    dow_cos = math.cos(2 * math.pi * dow / 7)

    # Distance band
    distance_km = raw.get("distance_km")
    distance_band = _distance_band(distance_km)

    # Lead time band
    lead_time_band = _lead_time_band(lead_time_days)

    # Time of day band
    time_of_day_band = _time_of_day_band(hour)

    return {
        "lead_time_days": lead_time_days,
        "lead_time_band": lead_time_band,
        "prior_noshow_rate_12mo": round(prior_noshow_rate, 4),
        "prior_noshow_count_12mo": noshow_count,
        "prior_attended_count_12mo": attended_count,
        "is_ramadan": ramadan,
        "is_eid_window": is_eid_window(appointment_at),
        "is_summer_exodus": is_summer_exodus(appointment_at),
        "is_post_iftar": is_post_iftar(appointment_at, ramadan),
        "is_pre_sahur": is_pre_sahur(appointment_at, ramadan),
        "hour_sin": round(hour_sin, 4),
        "hour_cos": round(hour_cos, 4),
        "hour_of_day": hour,
        "dow_sin": round(dow_sin, 4),
        "dow_cos": round(dow_cos, 4),
        "day_of_week": dow,
        "time_of_day_band": time_of_day_band,
        "distance_band": distance_band,
        "distance_km": distance_km,
        "specialty": raw.get("specialty", "general"),
        "booking_channel": raw.get("booking_channel", "phone"),
        "language_pref": raw.get("language_pref", "en"),
        "insurance_tier": raw.get("insurance_tier", "commercial"),
        "patient_age_band": raw.get("patient_age_band", "18-39"),
        "patient_gender": raw.get("patient_gender", "unknown"),
        "emirate": raw.get("emirate", "AD"),
        # Placeholders for tenant-level baselines (populated from DB later)
        "specialty_baseline_rate": 0.21,
        "provider_baseline_rate": 0.21,
        # Heat index (populated from Open-Meteo in production)
        "heat_index_band": "moderate",
    }


def _parse_dt(val) -> datetime:
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        return datetime.fromisoformat(val)
    raise ValueError(f"Cannot parse datetime from {type(val)}")


def _distance_band(km: float | None) -> str:
    if km is None:
        return "unknown"
    if km < 5:
        return "<5km"
    elif km < 15:
        return "5-15km"
    elif km < 30:
        return "15-30km"
    return "30km+"


def _lead_time_band(days: int) -> str:
    if days <= 0:
        return "same_day"
    elif days <= 3:
        return "1-3d"
    elif days <= 7:
        return "4-7d"
    elif days <= 14:
        return "8-14d"
    elif days <= 30:
        return "15-30d"
    return "30d+"


def _time_of_day_band(hour: int) -> str:
    if hour < 7:
        return "early_morning"
    elif hour < 10:
        return "morning"
    elif hour < 13:
        return "midday"
    elif hour < 17:
        return "afternoon"
    return "evening"
