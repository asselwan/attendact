"""Heuristic baseline scorer.

Weighted additive scorer using published feature importances from no-show literature.
Calibrated against Brazil Kaggle dataset class balance (~30% no-show rate).

v2: Added medical conditions, SMS reminder, welfare, neighbourhood baseline,
prior appointment count, and temporal signals from medical-appointment-no-shows
scout ref (LightGBM model, 30 features, AUC 0.797).
"""


# Weights derived from published literature (Carreras-Garcia 2020, Dantas 2018, Norris 2014)
# v2: expanded with medical/socioeconomic features.
# Recalibrated so sum of max contributions ≈ 0.92 (headroom for calibration multipliers)
FEATURE_WEIGHTS = {
    "prior_noshow_rate_12mo": 0.22,       # highest predictor (reduced slightly to accommodate new features)
    "lead_time_days": 0.13,               # strong predictor
    "is_ramadan": 0.07,                   # UAE-specific
    "is_eid_window": 0.05,
    "is_summer_exodus": 0.04,
    "distance_band": 0.09,
    "heat_index_band": 0.05,
    "insurance_tier": 0.04,
    "booking_channel": 0.04,
    "time_of_day_band": 0.03,
    "specialty_baseline_rate": 0.05,
    "patient_age_band": 0.03,
    "is_post_iftar": 0.02,
    # v2 additions from scout ref medical-appointment-no-shows
    "sms_reminder_sent": 0.06,            # SMS reminder reduces no-show (protective)
    "has_hypertension": 0.02,             # chronic conditions reduce no-show (regular attendees)
    "has_diabetes": 0.02,
    "has_disability": 0.02,
    "neighbourhood_baseline_rate": 0.04,  # area-level no-show rate
    # v3 additions from scout ref predict-appointment-noshow
    "visit_regularity": 0.05,            # irregular visitors are higher no-show risk
    "reschedule_count": 0.03,            # multiple reschedules = higher risk
    "is_new_patient": 0.03,             # first-timers have different no-show profile
}


class HeuristicScorer:
    """Additive heuristic scorer. Returns calibrated probability [0, 1].

    Uses base weights adjusted by calibration multipliers from outcome feedback.
    """

    def __init__(self):
        # Import here to avoid circular imports at module load
        from .calibrate import get_effective_weights
        self._weights = get_effective_weights()

    def score(self, features: dict) -> float:
        raw = 0.0
        w = self._weights

        # Prior no-show rate (continuous, already 0-1)
        raw += w.get("prior_noshow_rate_12mo", 0.25) * features.get(
            "prior_noshow_rate_12mo", 0.2
        )

        # Lead time (longer = higher risk, normalise to 0-1 with cap at 60 days)
        lead_days = min(features.get("lead_time_days", 7), 60)
        raw += w.get("lead_time_days", 0.15) * (lead_days / 60)

        # Binary flags
        if features.get("is_ramadan"):
            raw += w.get("is_ramadan", 0.08)
        if features.get("is_eid_window"):
            raw += w.get("is_eid_window", 0.06)
        if features.get("is_summer_exodus"):
            raw += w.get("is_summer_exodus", 0.05)
        if features.get("is_post_iftar"):
            raw += w.get("is_post_iftar", 0.02)

        # Distance band
        distance_scores = {"<5km": 0.0, "5-15km": 0.3, "15-30km": 0.6, "30km+": 1.0, "unknown": 0.3}
        raw += w.get("distance_band", 0.10) * distance_scores.get(
            features.get("distance_band", "unknown"), 0.3
        )

        # Heat index band
        heat_scores = {"low": 0.0, "moderate": 0.3, "high": 1.0}
        raw += w.get("heat_index_band", 0.06) * heat_scores.get(
            features.get("heat_index_band", "moderate"), 0.3
        )

        # Insurance tier (self-pay and basic have higher no-show)
        tier_scores = {
            "thiqa": 0.2,
            "daman_basic": 0.7,
            "daman_enhanced": 0.3,
            "commercial": 0.4,
            "self_pay": 0.9,
        }
        raw += w.get("insurance_tier", 0.05) * tier_scores.get(
            features.get("insurance_tier", "commercial"), 0.4
        )

        # Booking channel (walk-in lowest risk, app highest)
        channel_scores = {"walk_in": 0.1, "phone": 0.4, "web": 0.6, "app": 0.7}
        raw += w.get("booking_channel", 0.05) * channel_scores.get(
            features.get("booking_channel", "phone"), 0.4
        )

        # Time of day
        tod_scores = {
            "early_morning": 0.7,
            "morning": 0.3,
            "midday": 0.5,
            "afternoon": 0.4,
            "evening": 0.6,
        }
        raw += w.get("time_of_day_band", 0.04) * tod_scores.get(
            features.get("time_of_day_band", "morning"), 0.4
        )

        # Specialty baseline rate (continuous, 0-1)
        raw += w.get("specialty_baseline_rate", 0.06) * features.get(
            "specialty_baseline_rate", 0.21
        )

        # Age band
        age_scores = {"0-17": 0.5, "18-39": 0.6, "40-64": 0.3, "65+": 0.2}
        raw += w.get("patient_age_band", 0.03) * age_scores.get(
            features.get("patient_age_band", "18-39"), 0.4
        )

        # ── v2 features (from medical-appointment-no-shows scout ref) ──

        # SMS reminder sent (protective factor — reduces risk)
        if features.get("sms_reminder_sent"):
            raw -= w.get("sms_reminder_sent", 0.06) * 0.7  # 70% reduction effect

        # Chronic conditions (protective — regular attendees are more committed)
        if features.get("has_hypertension"):
            raw -= w.get("has_hypertension", 0.02) * 0.5
        if features.get("has_diabetes"):
            raw -= w.get("has_diabetes", 0.02) * 0.5
        if features.get("has_disability"):
            raw += w.get("has_disability", 0.02) * 0.6  # mobility barrier

        # Neighbourhood baseline rate (continuous, 0-1)
        raw += w.get("neighbourhood_baseline_rate", 0.04) * features.get(
            "neighbourhood_baseline_rate", 0.21
        )

        # ── v3 features (from predict-appointment-noshow scout ref) ──

        # Visit regularity (0=regular, 1=irregular; irregular = higher risk)
        raw += w.get("visit_regularity", 0.05) * features.get("visit_regularity", 0.5)

        # Reschedule count (each reschedule adds risk, capped at 3)
        reschedule_count = min(features.get("reschedule_count", 0), 3)
        raw += w.get("reschedule_count", 0.03) * (reschedule_count / 3)

        # New patient (first appointment has elevated no-show risk)
        if features.get("is_new_patient"):
            raw += w.get("is_new_patient", 0.03) * 0.6

        # Clamp to [0.02, 0.95] for calibration
        return max(0.02, min(0.95, raw))
