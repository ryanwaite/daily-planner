"""MCP tool handlers for get_today_tasks and get_tomorrow_tasks."""

from __future__ import annotations

import json
import logging
from datetime import date

from daily_planner.business_day import next_business_day
from daily_planner.integrations.things import get_tasks_for_date

_logger = logging.getLogger("daily_planner.debug")


async def get_today_tasks() -> str:
    """Retrieve today's tasks from Things 3 in the application's default sort order.

    Returns JSON string with tasks list or error.
    """
    today = date.today()
    _logger.debug(
        "Fetching today tasks",
        extra={
            "operation": "get_today_tasks",
            "direction": "request",
            "data": {"date": today.isoformat()},
        },
    )
    tasks = get_tasks_for_date(today, query_type="today")

    if tasks is None:
        return json.dumps({"tasks": None, "error": "Things database not found or inaccessible"})

    _logger.debug(
        "Today tasks retrieved",
        extra={
            "operation": "get_today_tasks",
            "direction": "response",
            "data": {"task_count": len(tasks)},
        },
    )

    return json.dumps({
        "tasks": [
            {
                "title": t.title,
                "due_date": t.due_date.isoformat(),
                "sort_position": t.sort_position,
                "project": t.project,
                "area": t.area,
                "area_created": t.area_created.isoformat() if t.area_created else None,
                "tags": t.tags,
            }
            for t in tasks
        ]
    })


async def get_tomorrow_tasks() -> str:
    """Retrieve tasks due the next business day from Things 3.

    Friday → Monday; otherwise next calendar day.
    Returns JSON string with tasks list, target_date, or error.
    """
    today = date.today()
    target = next_business_day(today)
    _logger.debug(
        "Fetching tomorrow tasks",
        extra={
            "operation": "get_tomorrow_tasks",
            "direction": "request",
            "data": {"date": today.isoformat(), "target_date": target.isoformat()},
        },
    )
    tasks = get_tasks_for_date(target, query_type="date")

    if tasks is None:
        return json.dumps({
            "tasks": None,
            "target_date": target.isoformat(),
            "error": "Things database not found or inaccessible",
        })

    _logger.debug(
        "Tomorrow tasks retrieved",
        extra={
            "operation": "get_tomorrow_tasks",
            "direction": "response",
            "data": {"task_count": len(tasks), "target_date": target.isoformat()},
        },
    )

    return json.dumps({
        "tasks": [
            {
                "title": t.title,
                "due_date": t.due_date.isoformat(),
                "sort_position": t.sort_position,
                "project": t.project,
                "area": t.area,
                "area_created": t.area_created.isoformat() if t.area_created else None,
                "tags": t.tags,
            }
            for t in tasks
        ],
        "target_date": target.isoformat(),
    })
