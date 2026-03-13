"""Unit tests for business day helpers."""

from datetime import date

from daily_planner.business_day import last_business_day, next_business_day


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
