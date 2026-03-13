"""render_pdf MCP tool handler — assemble BriefingData and produce PDF."""

from __future__ import annotations

import json
from datetime import date, datetime

from daily_planner.config.loader import load_configuration
from daily_planner.models import (
    BriefingData,
    CalendarEvent,
    Configuration,
    Repository,
    RepoSummary,
    Task,
)
from daily_planner.models.repo import ActivityItem
from daily_planner.pdf.renderer import render_briefing_pdf


async def render_pdf(
    repo_summaries: list[dict],
    calendar_events: list[dict] | None = None,
    calendar_error: str | None = None,
    today_tasks: list[dict] | None = None,
    today_error: str | None = None,
    tomorrow_tasks: list[dict] | None = None,
    tomorrow_error: str | None = None,
    output_path: str | None = None,
) -> str:
    """Accept all gathered briefing data and produce a two-page US Letter PDF.

    Returns JSON string with pdf_path and pages count.
    """
    config = load_configuration()
    if output_path:
        config = Configuration(
            page_one_font_size=config.page_one_font_size,
            page_two_font_size=config.page_two_font_size,
            output_path=output_path,
            repos_file=config.repos_file,
        )

    # Parse calendar events
    parsed_events: list[CalendarEvent] | None = None
    if calendar_events is not None:
        parsed_events = [CalendarEvent.from_dict(e) for e in calendar_events]

    # Parse tasks
    parsed_today: list[Task] | None = None
    if today_tasks is not None:
        parsed_today = [Task.from_dict(t) for t in today_tasks]

    parsed_tomorrow: list[Task] | None = None
    if tomorrow_tasks is not None:
        parsed_tomorrow = [Task.from_dict(t) for t in tomorrow_tasks]

    # Parse repo summaries
    parsed_summaries = [_parse_repo_summary(rs) for rs in repo_summaries]

    briefing = BriefingData(
        date=date.today(),
        config=config,
        calendar_events=parsed_events,
        calendar_error=calendar_error,
        today_tasks=parsed_today,
        today_error=today_error,
        tomorrow_tasks=parsed_tomorrow,
        tomorrow_error=tomorrow_error,
        repo_summaries=parsed_summaries,
    )

    pdf_path = render_briefing_pdf(briefing)

    return json.dumps({"pdf_path": str(pdf_path), "pages": 2})


def _parse_repo_summary(data: dict) -> RepoSummary:
    """Parse a repo summary dict into a RepoSummary model."""
    repo_data = data["repo"]
    repo = Repository(
        platform=repo_data["platform"],
        owner=repo_data["owner"],
        name=repo_data["name"],
        url=repo_data.get("url", ""),
        project=repo_data.get("project"),
    )

    activities = []
    for act in data.get("activities", []):
        activities.append(ActivityItem(
            repo=repo,
            activity_type=act["activity_type"],
            title=act["title"],
            author=act["author"],
            timestamp=datetime.fromisoformat(act["timestamp"]),
            url=act.get("url"),
            pr_state=act.get("pr_state"),
        ))

    return RepoSummary(
        repo=repo,
        activities=activities,
        narrative=data.get("narrative"),
        error=data.get("error"),
    )
