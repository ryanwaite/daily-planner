# Copilot Instructions — daily-planner

## What this project is

A Python MCP (Model Context Protocol) server that generates a markdown morning briefing file. It is **not** a standalone app — it is invoked by a Copilot CLI agent skill (`morning-briefing`) which orchestrates the multi-step data gathering and calls back into the MCP tools to render the final markdown file.

The agent (defined in `.github/agents/morning-briefing.agent.md`) calls four MCP tools exposed by this server:

1. `get_today_tasks` / `get_tomorrow_tasks` — read from the local Things 3 SQLite database
2. `get_repo_activity` — fetch commits, PRs, and issues from GitHub and Azure DevOps APIs
3. `render_markdown` — accept all gathered data and produce the markdown briefing file

The agent itself generates the LLM-written repo narrative summaries and action suggestions between steps 2 and 3.

## Commands

```bash
# Run full test suite
uv run pytest

# Run a single test file
uv run pytest tests/unit/test_business_day.py

# Run a single test by name
uv run pytest -k "test_friday_to_monday"

# Lint
uv run ruff check src/ tests/

# Lint with auto-fix
uv run ruff check --fix src/ tests/

# Start MCP server locally (stdio transport, for testing)
uv run python -m daily_planner
```

## Architecture

### MCP tool registration pattern

All MCP tools are registered in `src/daily_planner/server.py` as thin wrappers using `@mcp.tool()`. Each wrapper delegates to a handler function in `src/daily_planner/tools/`. This keeps the server module free of business logic.

### Layer structure

```
server.py            — MCP tool registration (thin wrappers only)
tools/               — MCP tool handlers (orchestration, JSON serialization)
integrations/        — External API clients (github.py, ado.py, things.py, auth.py)
models/              — Dataclasses (no logic beyond validation in __post_init__)
markdown/            — Markdown renderer (renderer.py)
config/              — TOML/txt config file loaders
business_day.py      — Date arithmetic (next/last business day)
logging.py           — Debug JSONL logging (setup, formatter, truncation)
```

### Markdown rendering

The markdown file is a single file built with f-string concatenation in `markdown/renderer.py`. Tasks are grouped by Area ("No Area" first, then by area creation date). The renderer writes to the configured output directory.

### Authentication resolution

`integrations/auth.py` resolves tokens in a three-step fallback chain: environment variable → CLI tool (`gh`/`az`) → macOS Keychain. This pattern is the same for both GitHub and ADO.

## Conventions

- **Python ≥ 3.12** with `from __future__ import annotations` in every module.
- **UV** is the package manager — always use `uv run` to execute commands, never bare `python` or `pytest`.
- **Dataclasses only** for models — no Pydantic. Models validate in `__post_init__` and provide `from_dict` class methods for deserialization.
- **`httpx.AsyncClient`** for all HTTP calls (not `requests`).
- **Ruff** for linting: rules `E, F, I, N, W, UP`; line length 99.
- **Test layout**: `tests/unit/` for pure logic, `tests/integration/` for PDF generation, `tests/contract/` for MCP tool schema validation. Tests use `pytest-asyncio` with `asyncio_mode = "auto"`.
- **Config files** live in `config/` — `settings.toml` (TOML) and `repos.txt` (line-oriented, `github:owner/repo` or `ado:org/project/repo`).
- Temp files go to a local `.tmp/` directory (set via `TMPDIR` override in `__main__.py`) to avoid macOS sandbox permission prompts.

## Spec-driven development

Feature specs live under `specs/<number>-<slug>/` and include `spec.md`, `plan.md`, `tasks.md`, and supporting docs. The `.specify/` directory contains templates used by the speckit agent skills for generating these artifacts.
