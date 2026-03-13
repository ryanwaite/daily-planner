"""Business day helpers for date calculations."""

from __future__ import annotations

from datetime import date, timedelta


def next_business_day(d: date) -> date:
    """Return the next business day after *d*.

    Friday → Monday, Saturday → Monday, Sunday → Monday.
    Otherwise → next calendar day.
    """
    weekday = d.weekday()  # Mon=0 … Sun=6
    if weekday == 4:  # Friday
        return d + timedelta(days=3)
    if weekday == 5:  # Saturday
        return d + timedelta(days=2)
    if weekday == 6:  # Sunday
        return d + timedelta(days=1)
    return d + timedelta(days=1)


def last_business_day(d: date) -> date:
    """Return the most recent business day before *d*.

    Monday → Friday, Sunday → Friday, Saturday → Friday.
    Otherwise → previous calendar day.
    """
    weekday = d.weekday()
    if weekday == 0:  # Monday
        return d - timedelta(days=3)
    if weekday == 6:  # Sunday
        return d - timedelta(days=2)
    if weekday == 5:  # Saturday
        return d - timedelta(days=1)
    return d - timedelta(days=1)
