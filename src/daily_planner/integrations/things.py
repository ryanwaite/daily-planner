"""Things 3 integration — read tasks from the local database via things.py."""

from __future__ import annotations

import logging
import sys
import time
from datetime import date, datetime

from daily_planner.models.task import Task

_logger = logging.getLogger("daily_planner.debug")

try:
    import things
    from things.database import Database
except ImportError:
    things = None  # type: ignore[assignment]
    Database = None  # type: ignore[assignment,misc]


def _build_metadata_maps() -> tuple[dict[str, str], dict[str, str], dict[str, date]]:
    """Build mappings of task UUID -> area title, project UUID -> project title,
    and area_title -> creation date.

    Returns:
        A tuple of (task_area_map, project_title_map, area_created_map).
    """
    if Database is None:
        return {}, {}, {}

    try:
        db = Database()
        old_factory = db.connection.row_factory
        db.connection.row_factory = None

        try:
            # uuid -> title for all areas, plus creation date
            area_titles: dict[str, str] = {}
            area_created: dict[str, date] = {}  # area_title -> creation date
            for row in db.connection.execute(
                "SELECT uuid, title, creationDate FROM TMArea"
            ).fetchall():
                area_titles[row[0]] = row[1]
                if row[2]:
                    try:
                        area_created[row[1]] = datetime.fromtimestamp(row[2]).date()
                    except (ValueError, OSError, TypeError):
                        pass

            # project uuid -> project title (type=1 is project in Things DB)
            project_titles: dict[str, str] = {}
            for row in db.connection.execute(
                "SELECT uuid, title FROM TMTask WHERE type = 1"
            ).fetchall():
                project_titles[row[0]] = row[1]

            # task uuid -> area title
            task_area: dict[str, str] = {}
            rows = db.connection.execute(
                "SELECT uuid, area, project FROM TMTask WHERE status = 0 AND start = 1"
            ).fetchall()
            for row in rows:
                task_uuid, area_uuid, project_uuid = row[0], row[1], row[2]
                if area_uuid and area_uuid in area_titles:
                    task_area[task_uuid] = area_titles[area_uuid]
                elif project_uuid:
                    # Check the project's area
                    proj_row = db.connection.execute(
                        "SELECT area FROM TMTask WHERE uuid = ?", (project_uuid,)
                    ).fetchone()
                    if proj_row and proj_row[0] and proj_row[0] in area_titles:
                        task_area[task_uuid] = area_titles[proj_row[0]]

            return task_area, project_titles, area_created
        finally:
            db.connection.row_factory = old_factory
            db.connection.close()
    except Exception as exc:
        print(f"Warning: Failed to read metadata: {exc}", file=sys.stderr)
        return {}, {}, {}


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
        _logger.debug(
            "Querying Things 3 database",
            extra={
                "operation": "things.get_tasks",
                "direction": "request",
                "data": {"target_date": target_date.isoformat(), "query_type": query_type},
            },
        )
        t0 = time.perf_counter()
        if query_type == "today":
            raw_tasks = things.today()
        else:
            # Query all tasks and filter by due date
            raw_tasks = things.tasks(
                status="incomplete",
                start_date=target_date.isoformat(),
            )
    except Exception as exc:
        _logger.error(
            f"Failed to read Things database: {exc}",
            exc_info=True,
            extra={
                "operation": "things.get_tasks",
                "data": {"target_date": target_date.isoformat(), "query_type": query_type},
            },
        )
        print(f"Warning: Failed to read Things database: {exc}", file=sys.stderr)
        return None

    elapsed = (time.perf_counter() - t0) * 1000

    area_map, project_titles, area_created_map = _build_metadata_maps()

    tasks: list[Task] = []
    for i, raw in enumerate(raw_tasks):
        task_uuid = raw.get("uuid", "")
        project_uuid = raw.get("project") if isinstance(raw.get("project"), str) else None
        project_name = project_titles.get(project_uuid, None) if project_uuid else None
        area_name = area_map.get(task_uuid)
        tasks.append(Task(
            title=raw.get("title", "Untitled"),
            due_date=target_date,
            sort_position=i,
            project=project_name,
            area=area_name,
            area_created=area_created_map.get(area_name) if area_name else None,
            tags=raw.get("tags", []) if isinstance(raw.get("tags"), list) else [],
        ))

    _logger.debug(
        "Things 3 query completed",
        extra={
            "operation": "things.get_tasks",
            "direction": "response",
            "data": {"task_count": len(tasks)},
            "duration_ms": round(elapsed, 2),
        },
    )

    return tasks
