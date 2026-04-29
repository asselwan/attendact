import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile
from pydantic import BaseModel, Field

from ..ml.features import compute_features
from ..ml.heuristic import HeuristicScorer
from ..ml.explain import explain_score
from ..ml.locations import compute_distance
from ..ml import score_store
from ..ml.score_store import ScoredAppointment

router = APIRouter()


class AppointmentInput(BaseModel):
    appointment_at: datetime
    booked_at: datetime
    specialty: str
    clinic_area: Optional[str] = None
    patient_area: Optional[str] = None
    patient_age_band: str = Field(pattern=r"^(0-17|18-39|40-64|65\+)$")
    patient_gender: str = Field(pattern=r"^(m|f|unknown)$")
    insurance_tier: str
    booking_channel: str
    language_pref: str = "en"
    prior_noshow_count_12mo: int = 0
    prior_attended_count_12mo: int = 0
    emirate: str = "AD"


class ScoreResult(BaseModel):
    appointment_id: str
    probability: float
    risk_band: str
    top_factors: list[dict]
    model_version: str
    recommended_action: str
    distance_km: Optional[float] = None


@router.post("/single", response_model=ScoreResult)
async def score_single(appointment: AppointmentInput):
    raw = appointment.model_dump()

    # Compute distance from fixed clinic/area coordinate lookup
    distance_km = compute_distance(appointment.clinic_area, appointment.patient_area)
    if distance_km is not None:
        raw["distance_km"] = distance_km

    features = compute_features(raw)
    scorer = HeuristicScorer()
    probability = scorer.score(features)
    risk_band = _to_risk_band(probability)
    factors = explain_score(features, probability, scorer)
    action = _recommended_action(risk_band, factors)

    result = ScoreResult(
        appointment_id=str(uuid.uuid4()),
        probability=round(probability, 4),
        risk_band=risk_band,
        top_factors=factors,
        model_version="heuristic_v1",
        recommended_action=action,
        distance_km=distance_km,
    )

    # Append to in-memory store for insights and outcome tracking
    score_store.append(ScoredAppointment(
        appointment_id=result.appointment_id,
        scored_at=datetime.utcnow(),
        specialty=appointment.specialty,
        clinic_area=appointment.clinic_area or "",
        patient_area=appointment.patient_area or "",
        emirate=appointment.emirate,
        probability=result.probability,
        risk_band=risk_band,
        distance_km=distance_km,
        lead_time_days=features.get("lead_time_days", 0),
        insurance_tier=appointment.insurance_tier,
        booking_channel=appointment.booking_channel,
        patient_age_band=appointment.patient_age_band,
        patient_gender=appointment.patient_gender,
        language_pref=appointment.language_pref,
        time_of_day_band=features.get("time_of_day_band", "morning"),
        is_ramadan=features.get("is_ramadan", False),
        top_factors=factors,
    ))

    return result


@router.post("/bulk")
async def score_bulk(file: UploadFile):
    """Accept CSV upload, score each row, return scored CSV."""
    return {"status": "not_implemented", "message": "Bulk scoring available in week 3"}


def _to_risk_band(probability: float) -> str:
    if probability >= 0.7:
        return "very_high"
    elif probability >= 0.5:
        return "high"
    elif probability >= 0.3:
        return "moderate"
    return "low"


def _recommended_action(risk_band: str, factors: list[dict]) -> str:
    if risk_band == "very_high":
        top_feature = factors[0]["feature"] if factors else ""
        if "distance" in top_feature or "heat" in top_feature:
            return "Offer transport voucher or telemedicine alternative"
        return "Proactive outreach in patient preferred language"
    elif risk_band == "high":
        return "Confirm appointment in patient preferred language"
    elif risk_band == "moderate":
        return "Standard reminder is sufficient"
    return "No additional action needed"
