"""render_markdown MCP tool handler — assemble BriefingData and produce markdown."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path

from daily_planner.config.loader import load_configuration
from daily_planner.markdown.renderer import render_briefing_markdown
from daily_planner.models import (
    BriefingData,
    CalendarEvent,
    Configuration,
    Repository,
    RepoSummary,
    Task,
)
from daily_planner.models.repo import ActivityItem
from daily_planner.models.task import ActionSuggestion

_logger = logging.getLogger("daily_planner.debug")

# Allowed base directory for output (user's home directory)
_ALLOWED_BASE = Path.home().resolve()


def _validate_output_path(output_path: str) -> str:
    """Validate that output_path resolves within the user's home directory."""
    resolved = Path(output_path).expanduser().resolve()
    try:
        resolved.relative_to(_ALLOWED_BASE)
    except ValueError:
        raise ValueError(
            f"output_path must be within {_ALLOWED_BASE}, got: {resolved}"
        )
    return str(resolved)


async def render_markdown(
    repo_summaries: list[dict],
    calendar_events: list[dict] | None = None,
    calendar_error: str | None = None,
    today_tasks: list[dict] | None = None,
    today_error: str | None = None,
    tomorrow_tasks: list[dict] | None = None,
    tomorrow_error: str | None = None,
    action_suggestions: list[dict] | None = None,
    output_path: str | None = None,
) -> str:
    """Accept all gathered briefing data and produce a markdown file.

    Returns JSON string with markdown_path.
    """
    config = load_configuration()
    if output_path:
        validated_path = _validate_output_path(output_path)
        config = Configuration(
            output_path=validated_path,
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

    # Parse action suggestions
    parsed_suggestions: list[ActionSuggestion] = []
    if action_suggestions:
        parsed_suggestions = [ActionSuggestion.from_dict(s) for s in action_suggestions]

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
        action_suggestions=parsed_suggestions,
    )

    _logger.debug(
        "Rendering markdown briefing",
        extra={
            "operation": "render_markdown",
            "direction": "internal",
            "data": {
                "event_count": len(parsed_events) if parsed_events else 0,
                "today_count": len(parsed_today) if parsed_today else 0,
                "tomorrow_count": len(parsed_tomorrow) if parsed_tomorrow else 0,
                "repo_count": len(parsed_summaries),
                "suggestion_count": len(parsed_suggestions),
            },
        },
    )

    markdown_path = render_briefing_markdown(briefing)

    _logger.info(
        "Markdown briefing written",
        extra={
            "operation": "render_markdown",
            "direction": "response",
            "data": {"path": str(markdown_path)},
        },
    )

    return json.dumps({"markdown_path": str(markdown_path)})


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
            body=act.get("body"),
            labels=act.get("labels", []),
            related_refs=act.get("related_refs", []),
        ))

    return RepoSummary(
        repo=repo,
        activities=activities,
        narrative=data.get("narrative"),
        error=data.get("error"),
    )
