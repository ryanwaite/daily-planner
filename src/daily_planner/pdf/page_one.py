"""Page 1: three-column layout — calendar, today tasks, tomorrow tasks + notes."""

from __future__ import annotations

from collections import OrderedDict

from reportlab.platypus import FrameBreak, Paragraph, Spacer

from daily_planner.models import BriefingData, CalendarEvent
from daily_planner.models.task import Task

MAX_CALENDAR_EVENTS = 25  # Ellipsis after this many
INBOX_AREA = "Inbox"


def build_page_one_stories(briefing: BriefingData, styles: dict) -> list:
    """Build Platypus flowables for all three columns of page one."""
    story: list = []

    # --- Column 1: Calendar ---
    story.append(Paragraph("Calendar", styles["p1_heading"]))
    story.extend(_build_calendar_column(briefing, styles))
    story.append(FrameBreak())

    # --- Column 2: Today's Tasks ---
    story.append(Paragraph("Today's Tasks", styles["p1_heading"]))
    story.extend(_build_today_tasks_column(briefing, styles))
    story.append(FrameBreak())

    # --- Column 3: Tomorrow's Tasks + Note Space ---
    story.append(Paragraph("Tomorrow's Tasks", styles["p1_heading"]))
    story.extend(_build_tomorrow_tasks_column(briefing, styles))
    # Remaining space is intentionally blank for handwritten notes

    return story


def _build_calendar_column(briefing: BriefingData, styles: dict) -> list:
    """Render calendar events or error notice."""
    if briefing.calendar_error:
        msg = f"Calendar data unavailable — {briefing.calendar_error}"
        return [Paragraph(msg, styles["p1_error"])]

    if briefing.calendar_events is None:
        return [Paragraph("Calendar data unavailable", styles["p1_error"])]

    if not briefing.calendar_events:
        return [Paragraph("No calendar events today", styles["p1_body"])]

    # Sort: all-day first, then by start_time
    events = sorted(
        briefing.calendar_events,
        key=lambda e: (not e.is_all_day, e.start_time),
    )

    items: list = []
    displayed = events[:MAX_CALENDAR_EVENTS]
    overflow_count = len(events) - len(displayed)

    for event in displayed:
        items.append(Paragraph(_format_event(event), styles["p1_body"]))

    if overflow_count > 0:
        items.append(Paragraph(f"… and {overflow_count} more events", styles["p1_body"]))

    return items


def _format_event(event: CalendarEvent) -> str:
    """Format a single calendar event as a display string."""
    if event.is_all_day:
        text = f"<b>All Day</b> — {_escape(event.title)}"
    else:
        start = event.start_time.strftime("%-I:%M %p")
        end = event.end_time.strftime("%-I:%M %p")
        text = f"<b>{start}–{end}</b> {_escape(event.title)}"

    if event.location:
        text += f"<br/><i>{_escape(event.location)}</i>"

    return text


def _build_today_tasks_column(briefing: BriefingData, styles: dict) -> list:
    """Render today's tasks grouped by area, or error/empty notice."""
    if briefing.today_error:
        return [Paragraph(f"Tasks unavailable — {briefing.today_error}", styles["p1_error"])]

    if briefing.today_tasks is None:
        return [Paragraph("Tasks unavailable", styles["p1_error"])]

    if not briefing.today_tasks:
        return [Paragraph("No tasks due today", styles["p1_body"])]

    return _build_area_grouped_tasks(briefing.today_tasks, styles)


def _build_tomorrow_tasks_column(briefing: BriefingData, styles: dict) -> list:
    """Render tomorrow's tasks grouped by area, or error/empty notice."""
    if briefing.tomorrow_error:
        return [Paragraph(f"Tasks unavailable — {briefing.tomorrow_error}", styles["p1_error"])]

    if briefing.tomorrow_tasks is None:
        return [Paragraph("Tomorrow's tasks unavailable", styles["p1_error"])]

    if not briefing.tomorrow_tasks:
        return [Paragraph("No tasks due tomorrow", styles["p1_body"])]

    items = _build_area_grouped_tasks(briefing.tomorrow_tasks, styles)
    items.append(Spacer(1, 12))
    return items


def _group_tasks_by_area_and_project(
    tasks: list[Task],
) -> OrderedDict[str, OrderedDict[str, list[Task]]]:
    """Group tasks by area then project, preserving original sort order.

    Returns OrderedDict[area_name, OrderedDict[project_name, tasks]].
    Tasks without an area are grouped under "Inbox" at the top.
    Tasks without a project are grouped under "" (empty string) within their area.
    """
    groups: OrderedDict[str, OrderedDict[str, list[Task]]] = OrderedDict()
    for task in tasks:
        area = task.area or INBOX_AREA
        project = task.project or ""
        if area not in groups:
            groups[area] = OrderedDict()
        if project not in groups[area]:
            groups[area][project] = []
        groups[area][project].append(task)

    # Move Inbox to the top if it exists and isn't the only group
    if INBOX_AREA in groups and len(groups) > 1:
        inbox = groups.pop(INBOX_AREA)
        new_groups: OrderedDict[str, OrderedDict[str, list[Task]]] = OrderedDict()
        new_groups[INBOX_AREA] = inbox
        new_groups.update(groups)
        return new_groups

    return groups


def _build_area_grouped_tasks(tasks: list[Task], styles: dict) -> list:
    """Build flowables for tasks grouped by area and project."""
    groups = _group_tasks_by_area_and_project(tasks)

    items: list = []
    for area_name, projects in groups.items():
        items.append(Paragraph(f"<b>{_escape(area_name)}</b>", styles["p1_body"]))
        for project_name, project_tasks in projects.items():
            if project_name:
                items.append(Paragraph(
                    f"<i>{_escape(project_name)}</i>", styles["p1_body"]
                ))
            for task in project_tasks:
                items.append(Paragraph(_format_task(task), styles["p1_task"]))
        items.append(Spacer(1, 4))

    return items


def _format_task(task: Task) -> str:
    """Format a single task with a checkbox and hanging indent."""
    box = '<font name="CascadiaCode">\u2610</font>'
    return f"{box} {_escape(task.title)}"


def _escape(text: str) -> str:
    """Escape XML special characters for reportlab Paragraphs."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
