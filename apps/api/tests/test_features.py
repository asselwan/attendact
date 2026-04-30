"""Tests for UAE-specific feature engineering."""

from datetime import datetime

from src.ml.features import compute_features


def test_lead_time_calculation():
    raw = {
        "appointment_at": datetime(2026, 7, 15, 10, 0),
        "booked_at": datetime(2026, 6, 15, 10, 0),
        "specialty": "cardiology",
        "patient_age_band": "40-64",
        "patient_gender": "m",
        "insurance_tier": "thiqa",
        "booking_channel": "app",
        "emirate": "AD",
    }
    features = compute_features(raw)
    assert features["lead_time_days"] == 30
    assert features["lead_time_band"] == "15-30d"


def test_ramadan_detection():
    # March 2026 falls during Ramadan (Ramadan 1447 starts ~Feb 28 2026)
    raw = {
        "appointment_at": datetime(2026, 3, 15, 10, 0),
        "booked_at": datetime(2026, 3, 1, 10, 0),
        "specialty": "general",
        "patient_age_band": "18-39",
        "patient_gender": "f",
        "insurance_tier": "commercial",
        "booking_channel": "phone",
        "emirate": "AD",
    }
    features = compute_features(raw)
    assert features["is_ramadan"] is True


def test_summer_exodus():
    raw = {
        "appointment_at": datetime(2026, 7, 20, 14, 0),
        "booked_at": datetime(2026, 7, 1, 10, 0),
        "specialty": "dermatology",
        "patient_age_band": "18-39",
        "patient_gender": "f",
        "insurance_tier": "daman_enhanced",
        "booking_channel": "web",
        "emirate": "DXB",
    }
    features = compute_features(raw)
    assert features["is_summer_exodus"] is True


def test_prior_noshow_smoothing():
    raw = {
        "appointment_at": datetime(2026, 5, 10, 9, 0),
        "booked_at": datetime(2026, 5, 8, 9, 0),
        "specialty": "general",
        "patient_age_band": "18-39",
        "patient_gender": "m",
        "insurance_tier": "commercial",
        "booking_channel": "phone",
        "prior_noshow_count_12mo": 1,
        "prior_attended_count_12mo": 1,
        "emirate": "AD",
    }
    features = compute_features(raw)
    # Total < 3, should use smoothed default of 0.2
    assert features["prior_noshow_rate_12mo"] == 0.2


def test_distance_band():
    raw = {
        "appointment_at": datetime(2026, 5, 10, 9, 0),
        "booked_at": datetime(2026, 5, 8, 9, 0),
        "specialty": "general",
        "patient_age_band": "65+",
        "patient_gender": "m",
        "insurance_tier": "thiqa",
        "booking_channel": "phone",
        "distance_km": 35.0,
        "emirate": "AD",
    }
    features = compute_features(raw)
    assert features["distance_band"] == "30km+"


def test_visit_regularity_regular():
    raw = {
        "appointment_at": datetime(2026, 5, 10, 9, 0),
        "booked_at": datetime(2026, 5, 8, 9, 0),
        "specialty": "general",
        "patient_age_band": "40-64",
        "patient_gender": "m",
        "insurance_tier": "commercial",
        "booking_channel": "phone",
        "emirate": "AD",
        # Monthly visits with low variance
        "prior_visit_intervals_days": [30, 31, 29, 30, 31],
    }
    features = compute_features(raw)
    # Regular visitor should have low regularity score (near 0)
    assert features["visit_regularity"] < 0.1


def test_visit_regularity_irregular():
    raw = {
        "appointment_at": datetime(2026, 5, 10, 9, 0),
        "booked_at": datetime(2026, 5, 8, 9, 0),
        "specialty": "general",
        "patient_age_band": "18-39",
        "patient_gender": "f",
        "insurance_tier": "commercial",
        "booking_channel": "app",
        "emirate": "AD",
        # Highly irregular intervals
        "prior_visit_intervals_days": [7, 90, 14, 120, 3],
    }
    features = compute_features(raw)
    # Irregular visitor should have high regularity score (near 1)
    assert features["visit_regularity"] > 0.7


def test_new_patient_flag():
    raw = {
        "appointment_at": datetime(2026, 5, 10, 9, 0),
        "booked_at": datetime(2026, 5, 8, 9, 0),
        "specialty": "general",
        "patient_age_band": "18-39",
        "patient_gender": "m",
        "insurance_tier": "self_pay",
        "booking_channel": "web",
        "emirate": "AD",
        "prior_appointment_count": 0,
    }
    features = compute_features(raw)
    assert features["is_new_patient"] is True
