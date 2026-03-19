"""CLI entry point — run the MCP server over stdio.

Usage:
    uv run python -m daily_planner          # start MCP server (stdio)
"""

from __future__ import annotations

import atexit
import os
import shutil
import sys
from pathlib import Path


def _setup_local_tmpdir() -> None:
    """Redirect temp files to a local .tmp directory to avoid macOS permission prompts."""
    tmp_dir = Path.cwd() / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    os.environ["TMPDIR"] = str(tmp_dir)

    def _cleanup() -> None:
        try:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

    atexit.register(_cleanup)


def main() -> None:
    _setup_local_tmpdir()
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
