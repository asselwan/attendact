"""SHAP-style explanation generator.

For heuristic_v1: hand-mapped contributions from feature weights.
For XGBoost models: SHAP TreeExplainer (implemented when model ships).
"""

from .heuristic import FEATURE_WEIGHTS, HeuristicScorer

# Human-readable explanation templates (no hyphens per NOMOI house style)
EXPLANATION_TEMPLATES = {
    "prior_noshow_rate_12mo": "Patient has missed {noshow} of {total} recent appointments",
    "lead_time_days": "Booked {days} days in advance",
    "is_ramadan": "Appointment falls during Ramadan",
    "is_eid_window": "Appointment is within the Eid holiday window",
    "is_summer_exodus": "Scheduled during the summer travel season (June to August)",
    "is_post_iftar": "Evening appointment during Ramadan, post iftar surge window",
    "is_pre_sahur": "Early morning during Ramadan, pre sahur window",
    "distance_band_30km+": "Long travel distance to the clinic (30km or more)",
    "distance_band_15-30km": "Moderate travel distance to the clinic (15 to 30km)",
    "heat_index_band_high": "Appointment on a high heat day (above 42C)",
    "insurance_tier_self_pay": "Self pay patient, higher likelihood of cost related cancellation",
    "insurance_tier_daman_basic": "Basic insurance tier, cost sensitivity may affect attendance",
    "booking_channel_app": "Booked via app, which correlates with higher rescheduling rates",
    "time_of_day_band_early_morning": "Early morning slot, higher abandonment rate",
    "specialty_baseline_rate": "This specialty historically has a {rate}% no show rate",
}


def explain_score(features: dict, probability: float, scorer: HeuristicScorer) -> list[dict]:
    """Return top 3 contributing factors with plain language explanations."""
    contributions = _compute_contributions(features)

    # Sort by absolute contribution, take top 3
    sorted_factors = sorted(contributions, key=lambda x: abs(x["contribution"]), reverse=True)[:3]

    return sorted_factors


def _compute_contributions(features: dict) -> list[dict]:
    """Compute per-feature contribution to the heuristic score."""
    contributions = []

    # Prior no-show rate
    rate = features.get("prior_noshow_rate_12mo", 0.2)
    contrib = FEATURE_WEIGHTS["prior_noshow_rate_12mo"] * rate
    noshow = features.get("prior_noshow_count_12mo", 0)
    total = noshow + features.get("prior_attended_count_12mo", 0)
    if total > 0:
        text = EXPLANATION_TEMPLATES["prior_noshow_rate_12mo"].format(noshow=noshow, total=total)
    else:
        text = "No prior appointment history available"
    contributions.append({
        "feature": "prior_noshow_rate_12mo",
        "value": rate,
        "contribution": round(contrib, 4),
        "plain_text": text,
    })

    # Lead time
    lead_days = min(features.get("lead_time_days", 7), 60)
    contrib = FEATURE_WEIGHTS["lead_time_days"] * (lead_days / 60)
    contributions.append({
        "feature": "lead_time_days",
        "value": lead_days,
        "contribution": round(contrib, 4),
        "plain_text": EXPLANATION_TEMPLATES["lead_time_days"].format(days=lead_days),
    })

    # Ramadan
    if features.get("is_ramadan"):
        contributions.append({
            "feature": "is_ramadan",
            "value": True,
            "contribution": round(FEATURE_WEIGHTS["is_ramadan"], 4),
            "plain_text": EXPLANATION_TEMPLATES["is_ramadan"],
        })

    # Eid window
    if features.get("is_eid_window"):
        contributions.append({
            "feature": "is_eid_window",
            "value": True,
            "contribution": round(FEATURE_WEIGHTS["is_eid_window"], 4),
            "plain_text": EXPLANATION_TEMPLATES["is_eid_window"],
        })

    # Summer exodus
    if features.get("is_summer_exodus"):
        contributions.append({
            "feature": "is_summer_exodus",
            "value": True,
            "contribution": round(FEATURE_WEIGHTS["is_summer_exodus"], 4),
            "plain_text": EXPLANATION_TEMPLATES["is_summer_exodus"],
        })

    # Post iftar
    if features.get("is_post_iftar"):
        contributions.append({
            "feature": "is_post_iftar",
            "value": True,
            "contribution": round(FEATURE_WEIGHTS["is_post_iftar"], 4),
            "plain_text": EXPLANATION_TEMPLATES["is_post_iftar"],
        })

    # Distance
    dist_band = features.get("distance_band", "unknown")
    distance_scores = {"<5km": 0.0, "5-15km": 0.3, "15-30km": 0.6, "30km+": 1.0, "unknown": 0.3}
    contrib = FEATURE_WEIGHTS["distance_band"] * distance_scores.get(dist_band, 0.3)
    dist_key = f"distance_band_{dist_band}"
    text = EXPLANATION_TEMPLATES.get(dist_key, f"Travel distance: {dist_band}")
    contributions.append({
        "feature": "distance_band",
        "value": dist_band,
        "contribution": round(contrib, 4),
        "plain_text": text,
    })

    # Heat
    heat_band = features.get("heat_index_band", "moderate")
    heat_scores = {"low": 0.0, "moderate": 0.3, "high": 1.0}
    contrib = FEATURE_WEIGHTS["heat_index_band"] * heat_scores.get(heat_band, 0.3)
    heat_key = f"heat_index_band_{heat_band}"
    text = EXPLANATION_TEMPLATES.get(heat_key, f"Heat index: {heat_band}")
    contributions.append({
        "feature": "heat_index_band",
        "value": heat_band,
        "contribution": round(contrib, 4),
        "plain_text": text,
    })

    # Insurance tier
    tier = features.get("insurance_tier", "commercial")
    tier_scores = {
        "thiqa": 0.2, "daman_basic": 0.7, "daman_enhanced": 0.3,
        "commercial": 0.4, "self_pay": 0.9,
    }
    contrib = FEATURE_WEIGHTS["insurance_tier"] * tier_scores.get(tier, 0.4)
    tier_key = f"insurance_tier_{tier}"
    text = EXPLANATION_TEMPLATES.get(tier_key, f"Insurance tier: {tier}")
    contributions.append({
        "feature": "insurance_tier",
        "value": tier,
        "contribution": round(contrib, 4),
        "plain_text": text,
    })

    # Booking channel
    channel = features.get("booking_channel", "phone")
    channel_scores = {"walk_in": 0.1, "phone": 0.4, "web": 0.6, "app": 0.7}
    contrib = FEATURE_WEIGHTS["booking_channel"] * channel_scores.get(channel, 0.4)
    channel_key = f"booking_channel_{channel}"
    text = EXPLANATION_TEMPLATES.get(channel_key, f"Booking channel: {channel}")
    contributions.append({
        "feature": "booking_channel",
        "value": channel,
        "contribution": round(contrib, 4),
        "plain_text": text,
    })

    return contributions
