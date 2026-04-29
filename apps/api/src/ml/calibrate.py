"""Model self-calibration from outcome feedback.

Pure statistics — no LLM. Compares predicted risk vs actual outcomes
and adjusts heuristic weights to reduce calibration error.

The mechanism:
1. Collect labeled data (prediction + actual outcome)
2. For each feature, compute its discrimination power:
   - Average feature score in no-shows vs attended
   - Features that separate well → increase weight
   - Features that don't separate → decrease weight
3. Apply bounded updates to avoid overcorrection
4. Store adjustment factors for the scorer to use

This runs on-demand or after each batch outcome upload.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from . import score_store
from .heuristic import FEATURE_WEIGHTS


@dataclass
class CalibrationResult:
    samples_used: int
    adjustments: dict[str, float]  # feature -> multiplier (1.0 = no change)
    overall_calibration_error: float
    recommendation: str


# Persistent weight adjustments (applied on top of base weights)
# Starts at 1.0 (no adjustment) for each feature
_weight_adjustments: dict[str, float] = {k: 1.0 for k in FEATURE_WEIGHTS}


def get_adjustments() -> dict[str, float]:
    """Current weight adjustment multipliers."""
    return dict(_weight_adjustments)


def get_effective_weights() -> dict[str, float]:
    """Base weights * adjustments = what the scorer should use."""
    return {
        k: round(v * _weight_adjustments.get(k, 1.0), 4)
        for k, v in FEATURE_WEIGHTS.items()
    }


def recalibrate(min_samples: int = 20) -> CalibrationResult:
    """Recalibrate weights based on accumulated outcome data.

    Returns the calibration result with any adjustments made.
    Requires at least min_samples labeled outcomes to act.
    """
    labeled = score_store.with_outcomes()

    if len(labeled) < min_samples:
        return CalibrationResult(
            samples_used=len(labeled),
            adjustments=dict(_weight_adjustments),
            overall_calibration_error=0.0,
            recommendation=f"Need at least {min_samples} outcomes to calibrate. Currently have {len(labeled)}.",
        )

    # Split into no-shows and attended
    noshows = [s for s in labeled if s.outcome == "no_show"]
    attended = [s for s in labeled if s.outcome == "attended"]

    if not noshows or not attended:
        return CalibrationResult(
            samples_used=len(labeled),
            adjustments=dict(_weight_adjustments),
            overall_calibration_error=0.0,
            recommendation="Need both no-show and attended outcomes to calibrate.",
        )

    # Overall calibration error
    avg_predicted = sum(s.probability for s in labeled) / len(labeled)
    actual_rate = len(noshows) / len(labeled)
    overall_error = abs(avg_predicted - actual_rate)

    # Feature-level discrimination analysis
    # For categorical features, compute: P(noshow | feature_value) vs P(attended | feature_value)
    feature_scores_noshow: dict[str, list[float]] = defaultdict(list)
    feature_scores_attended: dict[str, list[float]] = defaultdict(list)

    for s in labeled:
        # Map scored features to discrimination signals
        signals = _extract_feature_signals(s)
        target = feature_scores_noshow if s.outcome == "no_show" else feature_scores_attended
        for feat, val in signals.items():
            target[feat].append(val)

    # Compute adjustment multipliers
    new_adjustments: dict[str, float] = {}
    for feat in FEATURE_WEIGHTS:
        ns_vals = feature_scores_noshow.get(feat, [])
        at_vals = feature_scores_attended.get(feat, [])

        if not ns_vals or not at_vals:
            new_adjustments[feat] = _weight_adjustments.get(feat, 1.0)
            continue

        ns_mean = sum(ns_vals) / len(ns_vals)
        at_mean = sum(at_vals) / len(at_vals)

        # Discrimination = how much higher the feature score is for no-shows
        discrimination = ns_mean - at_mean

        if discrimination > 0.1:
            # Feature discriminates well — increase weight slightly
            multiplier = min(1.3, 1.0 + discrimination * 0.5)
        elif discrimination < -0.05:
            # Feature is inversely predictive — reduce weight
            multiplier = max(0.5, 1.0 + discrimination * 0.5)
        else:
            # Feature is neutral — slight decay toward baseline
            current = _weight_adjustments.get(feat, 1.0)
            multiplier = current * 0.95 + 1.0 * 0.05  # drift toward 1.0

        # Bound to [0.5, 1.5] to prevent runaway adjustments
        new_adjustments[feat] = round(max(0.5, min(1.5, multiplier)), 4)

    # Apply adjustments
    _weight_adjustments.update(new_adjustments)

    # Recommendation
    if overall_error < 0.05:
        rec = "Model is well calibrated. No significant adjustments needed."
    elif overall_error < 0.15:
        rec = f"Moderate calibration drift ({overall_error:.1%}). Weights adjusted."
    else:
        rec = f"Significant calibration error ({overall_error:.1%}). Consider retraining with XGBoost."

    return CalibrationResult(
        samples_used=len(labeled),
        adjustments=new_adjustments,
        overall_calibration_error=round(overall_error, 4),
        recommendation=rec,
    )


def _extract_feature_signals(s: score_store.ScoredAppointment) -> dict[str, float]:
    """Map a scored appointment to feature signal values (0 to 1 scale)."""
    signals: dict[str, float] = {}

    # Prior noshow rate — use probability as proxy (it's the strongest signal)
    signals["prior_noshow_rate_12mo"] = min(s.probability, 1.0)

    # Lead time (normalised)
    signals["lead_time_days"] = min(s.lead_time_days / 60, 1.0)

    # Distance
    if s.distance_km is not None:
        if s.distance_km < 5:
            signals["distance_band"] = 0.0
        elif s.distance_km < 15:
            signals["distance_band"] = 0.3
        elif s.distance_km < 30:
            signals["distance_band"] = 0.6
        else:
            signals["distance_band"] = 1.0
    else:
        signals["distance_band"] = 0.3

    # Insurance tier
    tier_scores = {"thiqa": 0.2, "daman_basic": 0.7, "daman_enhanced": 0.3, "commercial": 0.4, "self_pay": 0.9}
    signals["insurance_tier"] = tier_scores.get(s.insurance_tier, 0.4)

    # Booking channel
    channel_scores = {"walk_in": 0.1, "phone": 0.4, "web": 0.6, "app": 0.7}
    signals["booking_channel"] = channel_scores.get(s.booking_channel, 0.4)

    # Time of day
    tod_scores = {"early_morning": 0.7, "morning": 0.3, "midday": 0.5, "afternoon": 0.4, "evening": 0.6}
    signals["time_of_day_band"] = tod_scores.get(s.time_of_day_band, 0.4)

    # Age band
    age_scores = {"0-17": 0.5, "18-39": 0.6, "40-64": 0.3, "65+": 0.2}
    signals["patient_age_band"] = age_scores.get(s.patient_age_band, 0.4)

    # Ramadan
    signals["is_ramadan"] = 1.0 if s.is_ramadan else 0.0

    return signals
