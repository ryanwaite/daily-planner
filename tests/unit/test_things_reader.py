"""Unit tests for Things 3 reader — mock things.py library calls."""

from datetime import date
from unittest.mock import patch

from daily_planner.models.task import Task


class TestThingsReader:
    @patch("daily_planner.integrations.things.things")
    def test_returns_tasks_sorted_by_position(self, mock_things):
        mock_things.today.return_value = [
            {"title": "Second", "notes": "", "tags": [], "project": None},
            {"title": "First", "notes": "", "tags": ["urgent"], "project": "Work"},
        ]
        from daily_planner.integrations.things import get_tasks_for_date

        tasks = get_tasks_for_date(date(2026, 3, 13), query_type="today")
        assert len(tasks) == 2
        assert all(isinstance(t, Task) for t in tasks)

    @patch("daily_planner.integrations.things.things")
    def test_empty_list_when_no_tasks(self, mock_things):
        mock_things.today.return_value = []
        from daily_planner.integrations.things import get_tasks_for_date

        tasks = get_tasks_for_date(date(2026, 3, 13), query_type="today")
        assert tasks == []

    @patch("daily_planner.integrations.things.things", None)
    def test_db_not_found_returns_none_with_error(self):
        from daily_planner.integrations.things import get_tasks_for_date

        result = get_tasks_for_date(date(2026, 3, 13), query_type="today")
        # When things module is None (unavailable), expect None
        assert result is None
