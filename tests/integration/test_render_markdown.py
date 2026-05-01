"""Integration tests for the markdown renderer."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from daily_planner.markdown.renderer import _group_tasks_by_area, render_briefing_markdown
from daily_planner.models import BriefingData
from daily_planner.models.calendar import CalendarEvent
from daily_planner.models.config import Configuration
from daily_planner.models.repo import Repository, RepoSummary
from daily_planner.models.task import ActionSuggestion, Task


@pytest.fixture()
def sample_briefing(tmp_path: Path) -> BriefingData:
    return BriefingData(
        date=date(2026, 4, 26),
        config=Configuration(output_path=str(tmp_path)),
        calendar_events=[
            CalendarEvent(
                title="Standup",
                start_time=datetime(2026, 4, 26, 9, 0),
                end_time=datetime(2026, 4, 26, 9, 30),
            ),
            CalendarEvent(
                title="Holiday",
                start_time=datetime(2026, 4, 26, 0, 0),
                end_time=datetime(2026, 4, 26, 0, 0),
                is_all_day=True,
            ),
        ],
        today_tasks=[
            Task(title="Unassigned task", due_date=date(2026, 4, 26)),
            Task(title="Work task", due_date=date(2026, 4, 26), area="Work",
                 area_created=date(2025, 1, 1)),
            Task(title="Personal task", due_date=date(2026, 4, 26), area="Personal",
                 area_created=date(2025, 6, 1)),
        ],
        tomorrow_tasks=[
            Task(title="Monday task", due_date=date(2026, 4, 27), area="Work",
                 area_created=date(2025, 1, 1)),
        ],
        repo_summaries=[
            RepoSummary(
                repo=Repository(
                    platform="github", owner="octocat", name="hello",
                    url="https://github.com/octocat/hello",
                ),
                narrative="Theme 1: Auth overhaul.\n\nTheme 2: CI fixes.",
            ),
        ],
        action_suggestions=[
            ActionSuggestion(task_title="Unassigned task", suggestion="Break it into subtasks."),
        ],
    )


class TestRenderBriefingMarkdown:
    def test_file_created(self, sample_briefing: BriefingData, tmp_path: Path):
        path = render_briefing_markdown(sample_briefing)
        assert path.exists()
        assert path.name == "2026-04-26-morning-briefing.md"
        assert path.parent == tmp_path

    def test_correct_filename_format(self, sample_briefing: BriefingData):
        path = render_briefing_markdown(sample_briefing)
        assert path.name.startswith("2026-04-26-")
        assert path.name.endswith(".md")

    def test_all_sections_present(self, sample_briefing: BriefingData):
        path = render_briefing_markdown(sample_briefing)
        content = path.read_text()
        assert "# Morning Briefing" in content
        assert "## Calendar Events" in content
        assert "## Today Tasks" in content
        assert "## Tomorrow Tasks" in content
        assert "## Action Suggestions" in content
        assert "## Repository Activity" in content

    def test_calendar_events_rendered(self, sample_briefing: BriefingData):
        path = render_briefing_markdown(sample_briefing)
        content = path.read_text()
        assert "09:00–09:30" in content
        assert "Standup" in content
        assert "All day" in content
        assert "Holiday" in content

    def test_task_grouping_by_area(self, sample_briefing: BriefingData):
        path = render_briefing_markdown(sample_briefing)
        content = path.read_text()
        # No Area should come first
        no_area_pos = content.index("### No Area")
        work_pos = content.index("### Work")
        personal_pos = content.index("### Personal")
        assert no_area_pos < work_pos
        assert no_area_pos < personal_pos

    def test_area_sort_by_creation_date(self, sample_briefing: BriefingData):
        """Work (created 2025-01-01) should come before Personal (created 2025-06-01)."""
        path = render_briefing_markdown(sample_briefing)
        content = path.read_text()
        work_pos = content.index("### Work")
        personal_pos = content.index("### Personal")
        assert work_pos < personal_pos

    def test_area_sort_alphabetical_fallback(self, tmp_path: Path):
        """When area_created is None, fall back to alphabetical sort."""
        briefing = BriefingData(
            date=date(2026, 4, 26),
            config=Configuration(output_path=str(tmp_path)),
            today_tasks=[
                Task(title="Z task", due_date=date(2026, 4, 26), area="Zebra"),
                Task(title="A task", due_date=date(2026, 4, 26), area="Alpha"),
            ],
        )
        path = render_briefing_markdown(briefing)
        content = path.read_text()
        alpha_pos = content.index("### Alpha")
        zebra_pos = content.index("### Zebra")
        assert alpha_pos < zebra_pos

    def test_action_suggestions_present(self, sample_briefing: BriefingData):
        path = render_briefing_markdown(sample_briefing)
        content = path.read_text()
        assert "**Unassigned task**" in content
        assert "Break it into subtasks." in content

    def test_action_suggestions_omitted_when_empty(self, tmp_path: Path):
        briefing = BriefingData(
            date=date(2026, 4, 26),
            config=Configuration(output_path=str(tmp_path)),
            action_suggestions=[],
        )
        path = render_briefing_markdown(briefing)
        content = path.read_text()
        assert "## Action Suggestions" not in content

    def test_repo_narrative_preserves_blank_lines(self, sample_briefing: BriefingData):
        path = render_briefing_markdown(sample_briefing)
        content = path.read_text()
        assert "Theme 1: Auth overhaul.\n\nTheme 2: CI fixes." in content

    def test_overwrite_existing_file(self, sample_briefing: BriefingData, tmp_path: Path):
        path1 = render_briefing_markdown(sample_briefing)
        content1 = path1.read_text()
        path2 = render_briefing_markdown(sample_briefing)
        assert path1 == path2
        assert path2.read_text() == content1

    def test_creates_missing_directory(self, tmp_path: Path):
        nested = tmp_path / "nested" / "deep"
        briefing = BriefingData(
            date=date(2026, 4, 26),
            config=Configuration(output_path=str(nested)),
        )
        path = render_briefing_markdown(briefing)
        assert path.exists()
        assert nested.exists()

    def test_calendar_error_shown(self, tmp_path: Path):
        briefing = BriefingData(
            date=date(2026, 4, 26),
            config=Configuration(output_path=str(tmp_path)),
            calendar_error="Calendar API timeout",
        )
        path = render_briefing_markdown(briefing)
        content = path.read_text()
        assert "Calendar API timeout" in content

    def test_tasks_unavailable(self, tmp_path: Path):
        briefing = BriefingData(
            date=date(2026, 4, 26),
            config=Configuration(output_path=str(tmp_path)),
        )
        path = render_briefing_markdown(briefing)
        content = path.read_text()
        assert "Tasks unavailable" in content

    def test_header_date_format(self, sample_briefing: BriefingData):
        path = render_briefing_markdown(sample_briefing)
        content = path.read_text()
        # April 26, 2026 is a Sunday
        assert "# Morning Briefing — Sunday, April 26, 2026" in content

    def test_repo_error_shown(self, tmp_path: Path):
        briefing = BriefingData(
            date=date(2026, 4, 26),
            config=Configuration(output_path=str(tmp_path)),
            repo_summaries=[
                RepoSummary(
                    repo=Repository(
                        platform="github", owner="o", name="r",
                        url="https://github.com/o/r",
                    ),
                    error="Rate limited",
                ),
            ],
        )
        path = render_briefing_markdown(briefing)
        content = path.read_text()
        assert "Rate limited" in content


class TestGroupTasksByArea:
    def test_no_area_first(self):
        tasks = [
            Task(title="A", due_date=date(2026, 4, 26), area="Work"),
            Task(title="B", due_date=date(2026, 4, 26)),
        ]
        groups = _group_tasks_by_area(tasks)
        assert groups[0][0] == "No Area"
        assert groups[1][0] == "Work"

    def test_all_assigned_no_no_area_group(self):
        tasks = [
            Task(title="A", due_date=date(2026, 4, 26), area="Work"),
        ]
        groups = _group_tasks_by_area(tasks)
        assert len(groups) == 1
        assert groups[0][0] == "Work"

    def test_sort_by_creation_date(self):
        tasks = [
            Task(title="B", due_date=date(2026, 4, 26), area="Beta",
                 area_created=date(2025, 1, 1)),
            Task(title="A", due_date=date(2026, 4, 26), area="Alpha",
                 area_created=date(2026, 1, 1)),
        ]
        groups = _group_tasks_by_area(tasks)
        assert groups[0][0] == "Beta"  # older
        assert groups[1][0] == "Alpha"  # newer

    def test_alphabetical_fallback(self):
        tasks = [
            Task(title="Z", due_date=date(2026, 4, 26), area="Zebra"),
            Task(title="A", due_date=date(2026, 4, 26), area="Alpha"),
        ]
        groups = _group_tasks_by_area(tasks)
        assert groups[0][0] == "Alpha"
        assert groups[1][0] == "Zebra"

    def test_mixed_dated_and_undated_areas(self):
        tasks = [
            Task(title="Z", due_date=date(2026, 4, 26), area="Zebra"),
            Task(title="A", due_date=date(2026, 4, 26), area="Alpha",
                 area_created=date(2026, 1, 1)),
        ]
        groups = _group_tasks_by_area(tasks)
        # Alpha has a date so comes first; Zebra has no date, sorted after
        assert groups[0][0] == "Alpha"
        assert groups[1][0] == "Zebra"
