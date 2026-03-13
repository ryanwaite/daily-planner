"""Things 3 integration — read tasks from the local database via things.py."""

from __future__ import annotations

import sys
from datetime import date

from daily_planner.models.task import Task

try:
    import things
except ImportError:
    things = None  # type: ignore[assignment]


def get_tasks_for_date(target_date: date, query_type: str = "today") -> list[Task] | None:
    """Get tasks for a specific date from Things 3.

    Args:
        target_date: The date to query tasks for.
        query_type: "today" to use things.today(), or "date" to filter by due date.

    Returns:
        List of Task objects sorted by position, or None if Things is unavailable.
    """
    if things is None:
        print(
            "Warning: Things 3 database not available (things.py not installed)",
            file=sys.stderr,
        )
        return None

    try:
        if query_type == "today":
            raw_tasks = things.today()
        else:
            # Query all tasks and filter by due date
            raw_tasks = things.tasks(
                status="incomplete",
                start_date=target_date.isoformat(),
            )
    except Exception as exc:
        print(f"Warning: Failed to read Things database: {exc}", file=sys.stderr)
        return None

    tasks: list[Task] = []
    for i, raw in enumerate(raw_tasks):
        tasks.append(Task(
            title=raw.get("title", "Untitled"),
            due_date=target_date,
            sort_position=i,
            project=raw.get("project") if isinstance(raw.get("project"), str) else None,
            tags=raw.get("tags", []) if isinstance(raw.get("tags"), list) else [],
        ))

    return tasks
