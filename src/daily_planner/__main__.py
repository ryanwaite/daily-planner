"""CLI entry point — run the MCP server over stdio.

Usage:
    uv run python -m daily_planner          # start MCP server (stdio)
"""

from __future__ import annotations

import sys


def main() -> None:
    try:
        from daily_planner.server import main as serve
        serve()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"daily-planner: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
