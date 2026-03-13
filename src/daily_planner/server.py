"""MCP server entry point — stdio transport, server name 'daily-planner'."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("daily-planner")


# --- Tool: render_pdf ---
@mcp.tool()
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

    Returns JSON with pdf_path and page count.
    """
    from daily_planner.tools.render_pdf import render_pdf as _render_pdf

    return await _render_pdf(
        repo_summaries=repo_summaries,
        calendar_events=calendar_events,
        calendar_error=calendar_error,
        today_tasks=today_tasks,
        today_error=today_error,
        tomorrow_tasks=tomorrow_tasks,
        tomorrow_error=tomorrow_error,
        output_path=output_path,
    )


# --- Tool: get_today_tasks ---
@mcp.tool()
async def get_today_tasks() -> str:
    """Retrieve today's tasks from Things 3 in the application's default sort order."""
    from daily_planner.tools.tasks import get_today_tasks as _get_today_tasks

    return await _get_today_tasks()


# --- Tool: get_tomorrow_tasks ---
@mcp.tool()
async def get_tomorrow_tasks() -> str:
    """Retrieve tasks due the next business day from Things 3. Friday → Monday."""
    from daily_planner.tools.tasks import get_tomorrow_tasks as _get_tomorrow_tasks

    return await _get_tomorrow_tasks()


# --- Tool: get_repo_activity ---
@mcp.tool()
async def get_repo_activity() -> str:
    """Fetch recent commit, PR, and issue activity from all configured repositories."""
    from daily_planner.tools.repo_activity import get_repo_activity as _get_repo_activity

    return await _get_repo_activity()


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
