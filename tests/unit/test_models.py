"""Unit tests for data model dataclasses."""

from datetime import date, datetime

import pytest

from daily_planner.models import BriefingData
from daily_planner.models.calendar import CalendarEvent
from daily_planner.models.config import Configuration
from daily_planner.models.repo import ActivityItem, Repository
from daily_planner.models.task import Task

# --- CalendarEvent ---


class TestCalendarEvent:
    def test_valid_event(self):
        e = CalendarEvent(
            title="Standup",
            start_time=datetime(2026, 3, 13, 9, 0),
            end_time=datetime(2026, 3, 13, 9, 30),
        )
        assert e.title == "Standup"
        assert e.is_all_day is False

    def test_all_day_event(self):
        e = CalendarEvent(
            title="Holiday",
            start_time=datetime(2026, 3, 13, 0, 0),
            end_time=datetime(2026, 3, 13, 0, 0),
            is_all_day=True,
        )
        assert e.is_all_day is True

    def test_empty_title_raises(self):
        with pytest.raises(ValueError, match="title must be non-empty"):
            CalendarEvent(
                title="  ",
                start_time=datetime(2026, 3, 13, 9, 0),
                end_time=datetime(2026, 3, 13, 10, 0),
            )

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="start_time must be before end_time"):
            CalendarEvent(
                title="Meeting",
                start_time=datetime(2026, 3, 13, 11, 0),
                end_time=datetime(2026, 3, 13, 10, 0),
            )

    def test_from_dict(self):
        e = CalendarEvent.from_dict({
            "title": "Lunch",
            "start_time": "2026-03-13T12:00:00",
            "end_time": "2026-03-13T13:00:00",
            "location": "Café",
            "is_all_day": False,
        })
        assert e.title == "Lunch"
        assert e.location == "Café"


# --- Task ---


class TestTask:
    def test_valid_task(self):
        t = Task(title="Review PR", due_date=date(2026, 3, 13), sort_position=1)
        assert t.title == "Review PR"

    def test_empty_title_raises(self):
        with pytest.raises(ValueError, match="title must be non-empty"):
            Task(title="", due_date=date(2026, 3, 13))

    def test_from_dict(self):
        t = Task.from_dict({
            "title": "Deploy",
            "due_date": "2026-03-13",
            "sort_position": 5,
            "project": "backend",
            "tags": ["urgent"],
        })
        assert t.project == "backend"
        assert t.tags == ["urgent"]

    def test_defaults(self):
        t = Task(title="Simple", due_date=date(2026, 3, 13))
        assert t.sort_position == 0
        assert t.project is None
        assert t.tags == []


# --- Repository ---


class TestRepository:
    def test_valid_github(self):
        r = Repository(platform="github", owner="octocat", name="hello", url="https://github.com/octocat/hello")
        assert r.platform == "github"

    def test_valid_ado(self):
        r = Repository(
            platform="ado", owner="org", name="repo",
            url="https://dev.azure.com/org/proj/_git/repo",
            project="proj",
        )
        assert r.project == "proj"

    def test_invalid_platform_raises(self):
        with pytest.raises(ValueError, match="platform must be"):
            Repository(platform="gitlab", owner="o", name="n", url="x")

    def test_ado_requires_project(self):
        with pytest.raises(ValueError, match="ADO repositories require a project"):
            Repository(platform="ado", owner="org", name="repo", url="x")

    def test_empty_owner_raises(self):
        with pytest.raises(ValueError, match="owner must be non-empty"):
            Repository(platform="github", owner="  ", name="repo", url="x")


# --- ActivityItem ---


class TestActivityItem:
    def _repo(self):
        return Repository(platform="github", owner="o", name="n", url="x")

    def test_valid(self):
        a = ActivityItem(
            repo=self._repo(),
            activity_type="commit",
            title="Fix bug",
            author="alice",
            timestamp=datetime(2026, 3, 13, 10, 0),
        )
        assert a.activity_type == "commit"

    def test_invalid_type(self):
        with pytest.raises(ValueError, match="activity_type must be"):
            ActivityItem(
                repo=self._repo(),
                activity_type="deployment",
                title="v1",
                author="bob",
                timestamp=datetime.now(),
            )


# --- Configuration ---


class TestConfiguration:
    def test_defaults(self):
        c = Configuration()
        assert c.page_one_font_size == 9.0
        assert c.page_two_font_size == 8.0
        assert c.output_path == "~/Desktop"
        assert c.repos_file == "config/repos.txt"

    def test_resolved_output_path(self):
        c = Configuration(output_path="~/Documents")
        assert "Documents" in str(c.resolved_output_path)
        assert "~" not in str(c.resolved_output_path)


# --- BriefingData ---


class TestBriefingData:
    def test_minimal(self):
        b = BriefingData(date=date(2026, 3, 13), config=Configuration())
        assert b.calendar_events is None
        assert b.calendar_error is None
        assert b.repo_summaries == []

    def test_with_data(self):
        b = BriefingData(
            date=date(2026, 3, 13),
            config=Configuration(),
            calendar_events=[
                CalendarEvent(
                    title="Standup",
                    start_time=datetime(2026, 3, 13, 9, 0),
                    end_time=datetime(2026, 3, 13, 9, 30),
                )
            ],
            today_tasks=[Task(title="Review", due_date=date(2026, 3, 13))],
        )
        assert len(b.calendar_events) == 1
        assert len(b.today_tasks) == 1
