"""Integration tests for render_pdf — verify actual PDF generation."""

from datetime import date, datetime
from pathlib import Path

from daily_planner.models import (
    BriefingData,
    CalendarEvent,
    Configuration,
    Repository,
    RepoSummary,
    Task,
)


class TestRenderPdfIntegration:
    def _sample_briefing(self, output_dir: Path) -> BriefingData:
        return BriefingData(
            date=date(2026, 3, 13),
            config=Configuration(output_path=str(output_dir)),
            calendar_events=[
                CalendarEvent(
                    title="Team Standup",
                    start_time=datetime(2026, 3, 13, 9, 0),
                    end_time=datetime(2026, 3, 13, 9, 30),
                    location="Room 42",
                ),
                CalendarEvent(
                    title="All Day Training",
                    start_time=datetime(2026, 3, 13, 0, 0),
                    end_time=datetime(2026, 3, 13, 23, 59),
                    is_all_day=True,
                ),
            ],
            today_tasks=[
                Task(
                    title="Review PR #42", due_date=date(2026, 3, 13),
                    sort_position=1, project="daily-planner",
                ),
            ],
            tomorrow_tasks=[
                Task(title="Sprint planning", due_date=date(2026, 3, 16), sort_position=1),
            ],
            repo_summaries=[
                RepoSummary(
                    repo=Repository(platform="github", owner="octocat", name="hello-world", url="https://github.com/octocat/hello-world"),
                    narrative="Minor documentation updates and a bug fix for the login flow.",
                ),
            ],
        )

    def test_pdf_created_with_correct_filename(self, tmp_path: Path):
        from daily_planner.pdf.renderer import render_briefing_pdf

        briefing = self._sample_briefing(tmp_path)
        pdf_path = render_briefing_pdf(briefing)
        assert pdf_path.exists()
        assert pdf_path.name == "2026-03-13 Friday.pdf"

    def test_pdf_is_nonzero_size(self, tmp_path: Path):
        from daily_planner.pdf.renderer import render_briefing_pdf

        briefing = self._sample_briefing(tmp_path)
        pdf_path = render_briefing_pdf(briefing)
        assert pdf_path.stat().st_size > 0

    def test_pdf_with_calendar_error(self, tmp_path: Path):
        from daily_planner.pdf.renderer import render_briefing_pdf

        briefing = BriefingData(
            date=date(2026, 3, 13),
            config=Configuration(output_path=str(tmp_path)),
            calendar_events=None,
            calendar_error="Work IQ unavailable",
            repo_summaries=[],
        )
        pdf_path = render_briefing_pdf(briefing)
        assert pdf_path.exists()

    def test_pdf_completely_empty_data(self, tmp_path: Path):
        from daily_planner.pdf.renderer import render_briefing_pdf

        briefing = BriefingData(
            date=date(2026, 3, 13),
            config=Configuration(output_path=str(tmp_path)),
            repo_summaries=[],
        )
        pdf_path = render_briefing_pdf(briefing)
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0
