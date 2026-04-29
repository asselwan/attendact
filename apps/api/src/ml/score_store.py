"""In-memory score store for aggregation, insights, and outcome feedback.

Holds the last N scores in a dict keyed by appointment_id.
Replaced by DB queries in Week 2.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScoredAppointment:
    appointment_id: str
    scored_at: datetime
    specialty: str
    clinic_area: str
    patient_area: str
    emirate: str
    probability: float
    risk_band: str
    distance_km: float | None
    lead_time_days: int
    insurance_tier: str
    booking_channel: str
    patient_age_band: str
    patient_gender: str
    language_pref: str
    time_of_day_band: str
    is_ramadan: bool
    top_factors: list[dict] = field(default_factory=list)
    # Outcome (filled later when uploaded)
    outcome: str | None = None  # "attended" | "no_show" | "cancelled"
    outcome_recorded_at: datetime | None = None


# Ordered dict keyed by appointment_id — keeps last 5000
_store: OrderedDict[str, ScoredAppointment] = OrderedDict()
MAX_SIZE = 5000


def append(record: ScoredAppointment) -> None:
    _store[record.appointment_id] = record
    while len(_store) > MAX_SIZE:
        _store.popitem(last=False)


def get(appointment_id: str) -> ScoredAppointment | None:
    return _store.get(appointment_id)


def record_outcome(appointment_id: str, outcome: str) -> bool:
    """Record the actual outcome for a scored appointment. Returns True if found."""
    record = _store.get(appointment_id)
    if not record:
        return False
    record.outcome = outcome
    record.outcome_recorded_at = datetime.utcnow()
    return True


def recent(n: int = 500) -> list[ScoredAppointment]:
    """Return the most recent n scored appointments."""
    items = list(_store.values())
    return items[-n:]


def with_outcomes() -> list[ScoredAppointment]:
    """Return all scores that have an outcome recorded."""
    return [s for s in _store.values() if s.outcome is not None]


def prediction_errors() -> list[ScoredAppointment]:
    """Return scores where the prediction was materially wrong.

    False negatives: predicted low/moderate but patient no-showed.
    False positives: predicted high/very_high but patient attended.
    """
    errors = []
    for s in _store.values():
        if s.outcome is None:
            continue
        if s.outcome == "no_show" and s.risk_band in ("low", "moderate"):
            errors.append(s)
        elif s.outcome == "attended" and s.risk_band in ("high", "very_high"):
            errors.append(s)
    return errors


def calibration_stats() -> dict:
    """Compute calibration metrics from outcome data.

    Returns accuracy by risk band — the core input for weight adjustment.
    """
    labeled = with_outcomes()
    if not labeled:
        return {"total_labeled": 0, "bands": {}}

    bands: dict[str, dict] = {}
    for s in labeled:
        b = bands.setdefault(s.risk_band, {"predicted": 0, "actual_noshow": 0, "total": 0})
        b["total"] += 1
        b["predicted"] += s.probability
        if s.outcome == "no_show":
            b["actual_noshow"] += 1

    result_bands = {}
    for band, stats in bands.items():
        n = stats["total"]
        result_bands[band] = {
            "count": n,
            "avg_predicted_probability": round(stats["predicted"] / n, 4),
            "actual_noshow_rate": round(stats["actual_noshow"] / n, 4),
            "calibration_error": round(
                abs(stats["predicted"] / n - stats["actual_noshow"] / n), 4
            ),
        }

    return {"total_labeled": len(labeled), "bands": result_bands}


def count() -> int:
    return len(_store)
