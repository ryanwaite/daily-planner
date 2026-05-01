# Implementation Plan: Agent Debug Logging

**Branch**: `006-agent-debug-logging` | **Date**: 2026-04-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-agent-debug-logging/spec.md`

## Summary

Add structured debug logging capability to the MCP server that captures all tool invocations, external API calls, and data transformations when the `DAILY_PLANNER_DEBUG` environment variable is set. Debug logs are written as JSON Lines (JSONL) to a timestamped file in the configured output directory, with automatic truncation of large payloads (>5000 chars). Debug output is isolated to stderr and the log file — never to stdout (which is used for MCP protocol transport).

## Technical Context

**Language/Version**: Python ≥ 3.12 (managed by UV); `from __future__ import annotations` in every module
**Package Manager**: UV (`uv` CLI for venv, dependency resolution, and lock file)
**Primary Dependencies**:
  - `mcp>=1.0.0` (Model Context Protocol SDK — FastMCP server, stdio transport)
  - `httpx>=0.27` (async HTTP client for GitHub/ADO APIs)
  - `keyring>=25.0` (macOS Keychain access for token storage)
  - `things.py>=0.0.15` (Things 3 local database reader)
  - `python-json-logger` or stdlib `json` + manual line writing (NEEDS CLARIFICATION: which JSON logging approach)
**Storage**: Plain-text JSONL debug log file written to configured output directory; no database changes
**Testing**: `pytest>=8.0` + `pytest-asyncio>=0.23`; `respx>=0.21` for HTTP mocking; new unit tests for debug logger; integration tests for log format and truncation
**Linting**: `ruff>=0.4` — rules `E, F, I, N, W, UP`; line length 99; target Python 3.12
**Target Platform**: macOS (single-user local machine)
**Project Type**: MCP server with debug instrumentation
**Performance Goals**: Debug logging adds negligible overhead (<5% to briefing generation time); synchronous I/O with immediate flush
**Constraints**: No debug output to stdout (MCP protocol channel); log entries truncated to 5000 chars; graceful degradation if log directory not writable
**Scale/Scope**: Single user, ~5–15 repos, ~10–30 calendar events; debug log file expected to be <100KB per run

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate | Status |
|---|-----------|------|--------|
| I | Simplicity First | Use Python `logging` module + custom Formatter for JSONL (no new dependency); single module; sync writes | ✅ PASS — Stdlib logging is simpler than adding `python-json-logger` dependency. Research confirms this approach. |
| II | Privacy by Default | User is responsible for protecting log file (contains PII verbatim); no automatic log deletion or cloud storage; no new data flows | ✅ PASS — Logs stay local; user has full control over log file lifecycle. |
| III | Resilient Integrations | Log file write failures do not crash the server; warning to stderr only; briefing generation continues normally | ✅ PASS — Graceful degradation; non-fatal I/O errors. |
| IV | Testability | All logging callable from unit tests; log format is text-based (easy assertions); mock file I/O for testing write failures | ✅ PASS — JSONL is machine-parseable; simple to validate in tests. |
| V | Actionable Output | Debug logs are human-readable JSON (grep-friendly); timestamps and operation names make it easy to trace execution flow | ✅ PASS — JSONL structure supports both human reading and machine parsing. |
| — | Dependency Security | No new security-sensitive dependencies; stdlib logging only; pinned versions in pyproject.toml | ✅ PASS — Using stdlib; no new dependencies added. |

**Pre-Phase 0 gate result**: ALL PASS — proceed to Phase 0 research.

**Phase 0 Status**: ✅ COMPLETE — All clarifications resolved in [research.md](research.md)

## Project Structure

### Documentation (this feature)

```text
specs/006-agent-debug-logging/
├── plan.md              # This file
├── research.md          # Phase 0 output (logging approach comparison)
├── data-model.md        # Phase 1 output (DebugLogger, LogEntry entities)
├── quickstart.md        # Phase 1 output (how to enable debug mode)
├── contracts/           # Phase 1 output (debug log format contract)
│   └── debug-log-format.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── daily_planner/
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point (pass debug flag to logger setup)
│   ├── business_day.py          # (unchanged)
│   ├── server.py                # MCP server entry point (configure debug logger early)
│   ├── logging.py               # MODIFIED — add DebugLogger class, setup function, truncation logic
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── tasks.py             # (log in get_today_tasks, get_tomorrow_tasks)
│   │   ├── repo_activity.py     # (log in get_repo_activity, per-repo calls)
│   │   └── render_markdown.py   # (log final output path, render steps)
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── things.py            # (log Things database queries)
│   │   ├── github.py            # (log GitHub API requests/responses)
│   │   ├── ado.py               # (log ADO API requests/responses)
│   │   └── auth.py              # (unchanged)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── (all unchanged)
│   └── config/
│       ├── __init__.py
│       └── loader.py            # (unchanged)

tests/
├── unit/
│   ├── test_logging.py          # NEW — test DebugLogger, truncation, stderr formatting
│   ├── test_debug_integration.py # NEW — test logging from tools (mocked integrations)
│   └── (existing tests continue)
└── integration/
    ├── test_debug_logging.py    # NEW — end-to-end debug run with real file I/O
    └── (existing tests continue)
```

**Structure Decision**: Add a new `DebugLogger` class to the existing `src/daily_planner/logging.py` module. This module already has a setup function and formatting logic; extending it keeps debug infrastructure centralized. Tool handlers will call a global logger instance during execution. No new top-level module needed — aligns with Principle I (Simplicity First).

## Complexity Tracking

No constitution violations. Adding debug logging is a pure extension (new code, no refactoring of existing modules). The single design choice (stdlib `json` vs `python-json-logger`) is addressed in Phase 0 research.
