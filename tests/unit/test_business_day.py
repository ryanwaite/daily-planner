"""Unit tests for business day helpers."""

from datetime import date

import pytest

from daily_planner.business_day import last_business_day, n_business_days_back, next_business_day


class TestNextBusinessDay:
    def test_monday_to_tuesday(self):
        assert next_business_day(date(2026, 3, 9)) == date(2026, 3, 10)

    def test_tuesday_to_wednesday(self):
        assert next_business_day(date(2026, 3, 10)) == date(2026, 3, 11)

    def test_wednesday_to_thursday(self):
        assert next_business_day(date(2026, 3, 11)) == date(2026, 3, 12)

    def test_thursday_to_friday(self):
        assert next_business_day(date(2026, 3, 12)) == date(2026, 3, 13)

    def test_friday_to_monday(self):
        assert next_business_day(date(2026, 3, 13)) == date(2026, 3, 16)

    def test_saturday_to_monday(self):
        assert next_business_day(date(2026, 3, 14)) == date(2026, 3, 16)

    def test_sunday_to_monday(self):
        assert next_business_day(date(2026, 3, 15)) == date(2026, 3, 16)


class TestLastBusinessDay:
    def test_monday_to_friday(self):
        assert last_business_day(date(2026, 3, 16)) == date(2026, 3, 13)

    def test_tuesday_to_monday(self):
        assert last_business_day(date(2026, 3, 10)) == date(2026, 3, 9)

    def test_wednesday_to_tuesday(self):
        assert last_business_day(date(2026, 3, 11)) == date(2026, 3, 10)

    def test_friday_to_thursday(self):
        assert last_business_day(date(2026, 3, 13)) == date(2026, 3, 12)

    def test_saturday_to_friday(self):
        assert last_business_day(date(2026, 3, 14)) == date(2026, 3, 13)

    def test_sunday_to_friday(self):
        assert last_business_day(date(2026, 3, 15)) == date(2026, 3, 13)


class TestNBusinessDaysBack:
    def test_one_day_same_as_last_business_day(self):
        # Wednesday 2026-03-11 → Tuesday 2026-03-10
        assert n_business_days_back(date(2026, 3, 11), 1) == last_business_day(date(2026, 3, 11))

    def test_two_days_from_wednesday(self):
        # Wednesday 2026-03-11 → Monday 2026-03-09
        assert n_business_days_back(date(2026, 3, 11), 2) == date(2026, 3, 9)

    def test_five_days_full_work_week(self):
        # Friday 2026-03-13 → back 5 business days → Friday 2026-03-06
        assert n_business_days_back(date(2026, 3, 13), 5) == date(2026, 3, 6)

    def test_three_days_crossing_weekend(self):
        # Tuesday 2026-03-10 → back 3 → Thursday 2026-03-05
        assert n_business_days_back(date(2026, 3, 10), 3) == date(2026, 3, 5)

    def test_from_monday_crosses_weekend(self):
        # Monday 2026-03-16 → back 2 → Thursday 2026-03-12
        assert n_business_days_back(date(2026, 3, 16), 2) == date(2026, 3, 12)

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="n must be >= 1"):
            n_business_days_back(date(2026, 3, 11), 0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="n must be >= 1"):
            n_business_days_back(date(2026, 3, 11), -1)
