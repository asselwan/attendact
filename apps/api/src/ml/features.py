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
        # Medical condition flags (from Brazil Kaggle dataset, Carreras-Garcia 2020)
        "has_hypertension": bool(raw.get("has_hypertension", False)),
        "has_diabetes": bool(raw.get("has_diabetes", False)),
        "has_alcoholism": bool(raw.get("has_alcoholism", False)),
        "has_disability": bool(raw.get("has_disability", False)),
        # Socioeconomic and engagement signals
        "has_welfare": bool(raw.get("has_welfare", False)),
        "sms_reminder_sent": bool(raw.get("sms_reminder_sent", False)),
        # Prior appointment count (patient engagement proxy)
        "prior_appointment_count": raw.get("prior_appointment_count", 0),
        # Temporal signals
        "is_quarter_end": appointment_at.month in (3, 6, 9, 12) and appointment_at.day >= 25,
        "is_month_end": appointment_at.day >= 28,
        # Neighbourhood/area baseline (populated from DB later)
        "neighbourhood_baseline_rate": raw.get("neighbourhood_baseline_rate", 0.21),
        # Placeholders for tenant-level baselines (populated from DB later)
        "specialty_baseline_rate": 0.21,
        "provider_baseline_rate": 0.21,
        # Heat index (populated from Open-Meteo in production)
        "heat_index_band": "moderate",
        # Appointment regularity (from predict-appointment-noshow scout ref)
        # Measures consistency of visit intervals — irregular visitors are higher risk
        "visit_regularity": _visit_regularity(raw.get("prior_visit_intervals_days")),
        # Reschedule count — patients who reschedule multiple times are higher risk
        "reschedule_count": raw.get("reschedule_count", 0),
        # Is this a rescheduled appointment (vs original booking)
        "is_rescheduled": bool(raw.get("is_rescheduled", False)),
        # New patient flag (first-ever appointment has different no-show profile)
        "is_new_patient": raw.get("prior_appointment_count", 0) == 0,
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


def _visit_regularity(intervals: list | None) -> float:
    """Compute visit regularity score from prior visit intervals.

    Ported from predict-appointment-noshow (scout-refs/noshight/) automated
    feature engineering. Measures coefficient of variation of inter-visit
    intervals. Regular visitors (low CV) are less likely to no-show.

    Returns: 0.0 (perfectly regular) to 1.0 (highly irregular).
    Returns 0.5 (neutral) when insufficient data.
    """
    if not intervals or len(intervals) < 2:
        return 0.5  # neutral when insufficient history

    mean_interval = sum(intervals) / len(intervals)
    if mean_interval == 0:
        return 0.5

    variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
    std_dev = math.sqrt(variance)
    cv = std_dev / mean_interval  # coefficient of variation

    # Clamp CV to [0, 1] range. CV > 1 = highly irregular, cap at 1.0.
    return round(min(cv, 1.0), 4)


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
