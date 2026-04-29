"""Outcome recording and model calibration endpoints.

The self-learning loop:
1. Score appointments → stored with features + prediction
2. Upload actual outcomes (attended / no_show / cancelled)
3. Compare predictions vs reality
4. View where the model was wrong
5. Trigger recalibration to adjust weights
"""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

from ..ml import score_store
from ..ml.calibrate import recalibrate, get_adjustments, get_effective_weights
from ..ml.heuristic import FEATURE_WEIGHTS

router = APIRouter()


# --- Outcome Recording ---


class OutcomeInput(BaseModel):
    appointment_id: str
    outcome: str  # "attended" | "no_show" | "cancelled"


class BulkOutcomeInput(BaseModel):
    outcomes: list[OutcomeInput]


class OutcomeResponse(BaseModel):
    recorded: int
    not_found: int
    not_found_ids: list[str]


@router.post("/record", response_model=OutcomeResponse)
async def record_outcomes(body: BulkOutcomeInput):
    """Record actual outcomes for previously scored appointments."""
    recorded = 0
    not_found_ids = []

    for o in body.outcomes:
        if o.outcome not in ("attended", "no_show", "cancelled"):
            continue
        if score_store.record_outcome(o.appointment_id, o.outcome):
            recorded += 1
        else:
            not_found_ids.append(o.appointment_id)

    return OutcomeResponse(
        recorded=recorded,
        not_found=len(not_found_ids),
        not_found_ids=not_found_ids[:20],
    )


# --- Prediction Review ---


class PredictionError(BaseModel):
    appointment_id: str
    specialty: str
    risk_band: str
    probability: float
    outcome: str
    error_type: str  # "false_negative" | "false_positive"
    top_factors: list[dict]
    clinic_area: str
    patient_area: str
    distance_km: float | None


class ReviewResponse(BaseModel):
    total_with_outcomes: int
    total_errors: int
    false_negatives: int
    false_positives: int
    errors: list[PredictionError]
    calibration: dict


@router.get("/review", response_model=ReviewResponse)
async def review_predictions():
    """Show where the model was wrong — the core feedback for self-learning."""
    errors = score_store.prediction_errors()
    labeled = score_store.with_outcomes()
    calibration = score_store.calibration_stats()

    fn = [e for e in errors if e.outcome == "no_show"]
    fp = [e for e in errors if e.outcome == "attended"]

    error_list = []
    for e in errors:
        error_list.append(PredictionError(
            appointment_id=e.appointment_id,
            specialty=e.specialty,
            risk_band=e.risk_band,
            probability=e.probability,
            outcome=e.outcome or "",
            error_type="false_negative" if e.outcome == "no_show" else "false_positive",
            top_factors=e.top_factors,
            clinic_area=e.clinic_area,
            patient_area=e.patient_area,
            distance_km=e.distance_km,
        ))

    return ReviewResponse(
        total_with_outcomes=len(labeled),
        total_errors=len(errors),
        false_negatives=len(fn),
        false_positives=len(fp),
        errors=error_list,
        calibration=calibration,
    )


# --- Calibration ---


class CalibrationResponse(BaseModel):
    samples_used: int
    adjustments: dict[str, float]
    effective_weights: dict[str, float]
    overall_calibration_error: float
    recommendation: str


@router.post("/calibrate", response_model=CalibrationResponse)
async def trigger_calibration():
    """Trigger model recalibration based on accumulated outcomes."""
    result = recalibrate()
    return CalibrationResponse(
        samples_used=result.samples_used,
        adjustments=result.adjustments,
        effective_weights=get_effective_weights(),
        overall_calibration_error=result.overall_calibration_error,
        recommendation=result.recommendation,
    )


@router.get("/weights", response_model=dict)
async def get_current_weights():
    """View current weight adjustments and effective weights."""
    return {
        "base_weights": dict(FEATURE_WEIGHTS),
        "adjustments": get_adjustments(),
        "effective_weights": get_effective_weights(),
    }


# --- Metrics ---


@router.get("/metrics")
async def get_metrics():
    """Calibration metrics and scoring stats."""
    calibration = score_store.calibration_stats()
    return {
        "total_scored": score_store.count(),
        "total_with_outcomes": calibration.get("total_labeled", 0),
        "calibration_by_band": calibration.get("bands", {}),
    }
