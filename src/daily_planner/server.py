"""MCP server entry point — stdio transport, server name 'daily-planner'."""

from __future__ import annotations

import logging
import time

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("daily-planner")

_logger = logging.getLogger("daily_planner.debug")


# --- Tool: render_markdown ---
@mcp.tool()
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
    """Accept all gathered briefing data and produce a markdown morning briefing.

    Returns JSON with markdown_path.
    """
    _logger.debug(
        "Tool invocation started",
        extra={
            "operation": "render_markdown",
            "direction": "request",
            "data": {
                "repo_count": len(repo_summaries),
                "has_calendar": calendar_events is not None,
                "has_today": today_tasks is not None,
                "has_tomorrow": tomorrow_tasks is not None,
                "has_suggestions": bool(action_suggestions),
                "output_path": output_path,
            },
        },
    )
    t0 = time.perf_counter()
    from daily_planner.tools.render_markdown import render_markdown as _render_markdown

    result = await _render_markdown(
        repo_summaries=repo_summaries,
        calendar_events=calendar_events,
        calendar_error=calendar_error,
        today_tasks=today_tasks,
        today_error=today_error,
        tomorrow_tasks=tomorrow_tasks,
        tomorrow_error=tomorrow_error,
        action_suggestions=action_suggestions,
        output_path=output_path,
    )
    elapsed = (time.perf_counter() - t0) * 1000
    _logger.debug(
        "Tool invocation completed",
        extra={
            "operation": "render_markdown",
            "direction": "response",
            "data": {"result": result},
            "duration_ms": round(elapsed, 2),
        },
    )
    return result


# --- Tool: get_today_tasks ---
@mcp.tool()
async def get_today_tasks() -> str:
    """Retrieve today's tasks from Things 3 in the application's default sort order."""
    _logger.debug(
        "Tool invocation started",
        extra={"operation": "get_today_tasks", "direction": "request"},
    )
    t0 = time.perf_counter()
    from daily_planner.tools.tasks import get_today_tasks as _get_today_tasks

    result = await _get_today_tasks()
    elapsed = (time.perf_counter() - t0) * 1000
    _logger.debug(
        "Tool invocation completed",
        extra={
            "operation": "get_today_tasks",
            "direction": "response",
            "data": {"result": result},
            "duration_ms": round(elapsed, 2),
        },
    )
    return result


# --- Tool: get_tomorrow_tasks ---
@mcp.tool()
async def get_tomorrow_tasks() -> str:
    """Retrieve tasks due the next business day from Things 3. Friday → Monday."""
    _logger.debug(
        "Tool invocation started",
        extra={"operation": "get_tomorrow_tasks", "direction": "request"},
    )
    t0 = time.perf_counter()
    from daily_planner.tools.tasks import get_tomorrow_tasks as _get_tomorrow_tasks

    result = await _get_tomorrow_tasks()
    elapsed = (time.perf_counter() - t0) * 1000
    _logger.debug(
        "Tool invocation completed",
        extra={
            "operation": "get_tomorrow_tasks",
            "direction": "response",
            "data": {"result": result},
            "duration_ms": round(elapsed, 2),
        },
    )
    return result


# --- Tool: get_repo_activity ---
@mcp.tool()
async def get_repo_activity(since_business_days: int | None = None) -> str:
    """Fetch recent commit, PR, and issue activity from all configured repositories.

    Args:
        since_business_days: Number of business days to look back.
            Defaults to 1 (the last business day). Pass a higher number to
            widen the lookback window (e.g. 5 for the last full work week).
    """
    _logger.debug(
        "Tool invocation started",
        extra={
            "operation": "get_repo_activity",
            "direction": "request",
            "data": {"since_business_days": since_business_days},
        },
    )
    t0 = time.perf_counter()
    from daily_planner.tools.repo_activity import get_repo_activity as _get_repo_activity

    result = await _get_repo_activity(since_business_days=since_business_days)
    elapsed = (time.perf_counter() - t0) * 1000
    _logger.debug(
        "Tool invocation completed",
        extra={
            "operation": "get_repo_activity",
            "direction": "response",
            "data": {"result": result},
            "duration_ms": round(elapsed, 2),
        },
    )
    return result


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
