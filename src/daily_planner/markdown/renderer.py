"""Markdown renderer — build the morning briefing as a .md file."""

from __future__ import annotations

import logging
from pathlib import Path

from daily_planner.models import BriefingData
from daily_planner.models.task import Task

_logger = logging.getLogger("daily_planner.debug")


def render_briefing_markdown(briefing: BriefingData) -> Path:
    """Build the full markdown briefing and write it to disk.

    Returns the Path to the written file.
    """
    sections: list[str] = []

    # Header
    sections.append(_render_header(briefing))

    # Calendar Events
    sections.append(_render_calendar(briefing))

    # Today Tasks
    sections.append(
        _render_tasks_section("Today Tasks", briefing.today_tasks, briefing.today_error)
    )

    # Tomorrow Tasks
    sections.append(
        _render_tasks_section(
            "Tomorrow Tasks", briefing.tomorrow_tasks, briefing.tomorrow_error
        )
    )

    # Action Suggestions (conditional — omit if empty)
    if briefing.action_suggestions:
        sections.append(_render_action_suggestions(briefing))

    # Repository Activity
    sections.append(_render_repo_activity(briefing))

    content = "\n\n".join(sections) + "\n"

    # Write to disk
    out_dir = briefing.config.resolved_output_path
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{briefing.date.isoformat()}-morning-briefing.md"
    out_path = out_dir / filename
    out_path.write_text(content, encoding="utf-8")

    _logger.info(
        "Briefing markdown file written",
        extra={
            "operation": "render_markdown",
            "direction": "internal",
            "data": {"path": str(out_path), "size_bytes": len(content)},
        },
    )

    return out_path


def _render_header(briefing: BriefingData) -> str:
    """Render the top-level heading with human-readable date."""
    # Constitution format: dddd, MMMM D, YYYY
    d = briefing.date
    formatted = d.strftime("%A, %B ") + str(d.day) + d.strftime(", %Y")
    return f"# Morning Briefing — {formatted}"


def _render_calendar(briefing: BriefingData) -> str:
    """Render the Calendar Events section."""
    lines = ["## Calendar Events"]
    if briefing.calendar_error:
        lines.append(f"*{briefing.calendar_error}*")
    elif briefing.calendar_events is None:
        lines.append("*Calendar data unavailable.*")
    elif not briefing.calendar_events:
        lines.append("No events scheduled.")
    else:
        for event in briefing.calendar_events:
            if event.is_all_day:
                lines.append(f"- **All day** — {event.title}")
            else:
                start = event.start_time.strftime("%H:%M")
                end = event.end_time.strftime("%H:%M")
                lines.append(f"- **{start}–{end}** — {event.title}")
    return "\n".join(lines)


def _render_tasks_section(
    heading: str,
    tasks: list[Task] | None,
    error: str | None,
) -> str:
    """Render a task section (Today or Tomorrow) with area grouping."""
    lines = [f"## {heading}"]
    if error:
        lines.append(f"*{error}*")
    elif tasks is None:
        lines.append("*Tasks unavailable.*")
    elif not tasks:
        lines.append("No tasks.")
    else:
        groups = _group_tasks_by_area(tasks)
        for area_name, area_tasks in groups:
            lines.append(f"### {area_name}")
            for t in area_tasks:
                lines.append(f"- {t.title}")
    return "\n".join(lines)


def _group_tasks_by_area(
    tasks: list[Task],
) -> list[tuple[str, list[Task]]]:
    """Group tasks by area. 'No Area' first, then by area_created date (oldest first).

    Falls back to alphabetical order when creation date is unavailable.
    """
    no_area: list[Task] = []
    by_area: dict[str, list[Task]] = {}
    area_dates: dict[str, object] = {}  # area_name -> date | None

    for t in tasks:
        if t.area is None:
            no_area.append(t)
        else:
            by_area.setdefault(t.area, []).append(t)
            # Track earliest known creation date per area
            if t.area not in area_dates or (
                t.area_created is not None
                and (area_dates[t.area] is None or t.area_created < area_dates[t.area])
            ):
                area_dates[t.area] = t.area_created

    _logger.debug(
        "Tasks grouped by area",
        extra={
            "operation": "render_markdown.group_tasks",
            "direction": "internal",
            "data": {
                "no_area_count": len(no_area),
                "area_count": len(by_area),
                "areas": list(by_area.keys()),
            },
        },
    )

    # Sort areas: by creation date (oldest first), then alphabetically as fallback
    def _sort_key(area_name: str) -> tuple[int, object, str]:
        created = area_dates.get(area_name)
        if created is not None:
            return (0, created, area_name)
        return (1, "", area_name)

    sorted_areas = sorted(by_area.keys(), key=_sort_key)

    result: list[tuple[str, list[Task]]] = []
    if no_area:
        result.append(("No Area", no_area))
    for area_name in sorted_areas:
        result.append((area_name, by_area[area_name]))
    return result


def _render_action_suggestions(briefing: BriefingData) -> str:
    """Render the Action Suggestions section."""
    lines = ["## Action Suggestions"]
    for s in briefing.action_suggestions:
        lines.append(f"> **{s.task_title}**: {s.suggestion}")
    return "\n\n".join(lines)


def _render_repo_activity(briefing: BriefingData) -> str:
    """Render the Repository Activity section, preserving narrative formatting."""
    lines = ["## Repository Activity"]
    if not briefing.repo_summaries:
        lines.append("No repositories configured.")
    else:
        parts = [lines[0]]
        for summary in briefing.repo_summaries:
            repo = summary.repo
            part_lines = [f"### {repo.owner}/{repo.name}"]
            if summary.error:
                part_lines.append(f"*Error: {summary.error}*")
            elif summary.narrative:
                # Preserve narrative as-is (including blank lines for theme separation)
                part_lines.append(summary.narrative)
            else:
                part_lines.append("No recent activity.")
            parts.append("\n".join(part_lines))
        return "\n\n".join(parts)
    return "\n".join(lines)
