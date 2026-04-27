"""Data models for the daily planner."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from daily_planner.models.calendar import CalendarEvent
from daily_planner.models.config import Configuration
from daily_planner.models.repo import ActivityItem, Repository, RepoSummary
from daily_planner.models.task import ActionSuggestion, Task


@dataclass
class BriefingData:
    """Top-level data structure passed to render_markdown.

    Assembles all sections for one briefing run.
    """

    date: date
    config: Configuration
    calendar_events: list[CalendarEvent] | None = None
    calendar_error: str | None = None
    today_tasks: list[Task] | None = None
    today_error: str | None = None
    tomorrow_tasks: list[Task] | None = None
    tomorrow_error: str | None = None
    repo_summaries: list[RepoSummary] = field(default_factory=list)
    action_suggestions: list[ActionSuggestion] = field(default_factory=list)


__all__ = [
    "ActionSuggestion",
    "ActivityItem",
    "BriefingData",
    "CalendarEvent",
    "Configuration",
    "RepoSummary",
    "Repository",
    "Task",
]
