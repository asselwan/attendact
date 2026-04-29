"""In-memory score store for aggregation and insights.

Holds the last N scores in a deque. Replaced by DB queries in Week 2.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScoredAppointment:
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
    time_of_day_band: str
    top_factors: list[dict] = field(default_factory=list)


# Bounded deque — keeps last 2000 scores in memory
_store: deque[ScoredAppointment] = deque(maxlen=2000)


def append(record: ScoredAppointment) -> None:
    _store.append(record)


def recent(n: int = 500) -> list[ScoredAppointment]:
    """Return the most recent n scored appointments."""
    items = list(_store)
    return items[-n:]


def count() -> int:
    return len(_store)
