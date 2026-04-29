"""Hijri calendar, Ramadan, Eid, and UAE heat helpers."""

from __future__ import annotations

from datetime import date, datetime

from hijri_converter import Hijri, Gregorian


def is_ramadan(dt: datetime | date) -> bool:
    """Check if a given date falls within Ramadan."""
    d = dt.date() if isinstance(dt, datetime) else dt
    hijri = Gregorian(d.year, d.month, d.day).to_hijri()
    return hijri.month == 9


def is_eid_window(dt: datetime | date, window_days: int = 3) -> bool:
    """Check if date is within +/- window_days of Eid al-Fitr or Eid al-Adha."""
    d = dt.date() if isinstance(dt, datetime) else dt
    hijri = Gregorian(d.year, d.month, d.day).to_hijri()

    # Eid al-Fitr: Shawwal 1 (month 10, day 1)
    # Eid al-Adha: Dhul Hijjah 10 (month 12, day 10)
    eid_dates = [
        (10, 1),   # Eid al-Fitr
        (12, 10),  # Eid al-Adha
    ]

    for eid_month, eid_day in eid_dates:
        try:
            eid_hijri = Hijri(hijri.year, eid_month, eid_day)
            eid_greg = eid_hijri.to_gregorian()
            delta = abs((d - eid_greg).days)
            if delta <= window_days:
                return True
        except (ValueError, OverflowError):
            continue

    return False


def is_summer_exodus(dt: datetime | date) -> bool:
    """June 15 to August 31: expat travel season."""
    d = dt.date() if isinstance(dt, datetime) else dt
    return (d.month == 6 and d.day >= 15) or d.month in (7, 8)


def is_post_iftar(dt: datetime, ramadan: bool) -> bool:
    """During Ramadan: 1900 to 2300 local time."""
    if not ramadan:
        return False
    return 19 <= dt.hour <= 22


def is_pre_sahur(dt: datetime, ramadan: bool) -> bool:
    """During Ramadan: 0300 to 0500 local time."""
    if not ramadan:
        return False
    return 3 <= dt.hour <= 4
