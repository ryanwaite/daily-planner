# Implementation Plan: Morning Briefing PDF Generator

**Branch**: `001-morning-briefing-pdf` | **Date**: 2026-04-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-morning-briefing-pdf/spec.md`

## Summary

Build an MCP server in Python (stdio transport, managed by UV) that
exposes four tools — `get_today_tasks`, `get_tomorrow_tasks`,
`get_repo_activity`, and `render_pdf` — orchestrated by a Copilot CLI
agent skill. The agent also connects to the Microsoft Work IQ MCP
server for calendar data and uses its own LLM for repo-activity
summarization. The `render_pdf` tool produces a two-page landscape
US Letter PDF: page one has a three-column layout (calendar, today's
tasks, tomorrow's tasks + note area); page two has a two-column layout
of LLM-summarized repository activity. Font sizes and repo lists are
configurable via files.

## Technical Context

**Language/Version**: Python ≥ 3.12 (managed by UV); `from __future__ import annotations` in every module
**Package Manager**: UV (`uv` CLI for venv, dependency resolution, and lock file)
**Primary Dependencies**:
  - `mcp>=1.0.0` (Model Context Protocol SDK — FastMCP server, stdio transport)
  - `reportlab>=4.1` (PDF generation with Platypus layout engine)
  - `httpx>=0.27` (async HTTP client for GitHub/ADO APIs)
  - `keyring>=25.0` (macOS Keychain access for token storage)
  - `things.py>=0.0.15` (Things 3 local database — handles DB locking and Core Data timestamps)
**Storage**: Things 3 local SQLite DB (read-only); macOS Keychain for tokens; plain-text config files (TOML + line-oriented)
**Testing**: `pytest>=8.0` + `pytest-asyncio>=0.23`; `respx>=0.21` for HTTP mocking; `pip-audit>=2.7` for vulnerability scanning
**Linting**: `ruff>=0.4` — rules `E, F, I, N, W, UP`; line length 99; target Python 3.12
**Target Platform**: macOS (single-user local machine)
**Project Type**: MCP server + Copilot CLI agent skill
**Performance Goals**: Complete briefing in <30 seconds (SC-001b); <45 seconds with degraded sources (SC-003)
**Constraints**: Landscape US Letter paper only; no data persisted beyond single run; no plain-text credential storage
**Scale/Scope**: Single user, ~5–15 repos, ~10–30 calendar events per day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate | Status |
|---|-----------|------|--------|
| I | Simplicity First | No unnecessary abstractions; each module has single responsibility; simplest approach chosen | ✅ PASS — 4 MCP tools, flat module structure, no ORM or framework overhead; FastMCP for thin wrappers |
| II | Privacy by Default | No PII persisted beyond run; credentials in env vars or secure store; PDF written locally only | ✅ PASS — Keychain for tokens with env/CLI fallback, no data retention, local PDF output only |
| III | Resilient Integrations | Timeout + retry on every external call; graceful degradation per source; isolated modules | ✅ PASS — FR-011 mandates per-section error notices; httpx has configurable timeouts; per-section `*_error` fields |
| IV | Testability | All integrations mockable; business logic separated from I/O; PDF verifiable via intermediate data | ✅ PASS — respx for HTTP mocking; data models separate from rendering; 72 tests across 9 files |
| V | Actionable Output | Scannable layout; timestamps per section; date formats per constitution; exit codes | ✅ PASS — three-column + two-column landscape layout; date formats per FR-007/constitution |
| — | Dependency Security | Pinned versions; pip-audit before release; no unresolved critical CVEs | ✅ PASS — UV lock file pins all versions; pip-audit in dev dependencies |

**Pre-Phase 0 gate result**: ALL PASS — proceed to research.

## Project Structure

### Documentation (this feature)

```text
specs/001-morning-briefing-pdf/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
│   └── mcp-tools.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── daily_planner/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point (stdio server launcher, .tmp/ setup)
│   ├── business_day.py      # Date arithmetic (next/last/n_business_days_back)
│   ├── server.py            # MCP server entry point (thin @mcp.tool() wrappers)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── tasks.py         # get_today_tasks, get_tomorrow_tasks handlers
│   │   ├── repo_activity.py # get_repo_activity handler
│   │   └── render_pdf.py    # render_pdf handler
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── things.py        # Things 3 SQLite reader (via things.py library)
│   │   ├── github.py        # GitHub REST API client (httpx)
│   │   ├── ado.py           # Azure DevOps REST API client (httpx)
│   │   └── auth.py          # Token resolution: env var → CLI tool → Keychain
│   ├── models/
│   │   ├── __init__.py      # BriefingData top-level model
│   │   ├── calendar.py      # CalendarEvent dataclass
│   │   ├── task.py          # Task dataclass
│   │   ├── repo.py          # Repository, ActivityItem, RepoSummary dataclasses
│   │   └── config.py        # Configuration dataclass
│   ├── pdf/
│   │   ├── __init__.py
│   │   ├── renderer.py      # PDF layout engine (BaseDocTemplate, Frames, styles)
│   │   ├── page_one.py      # Page 1: three-column calendar/tasks layout
│   │   └── page_two.py      # Page 2: two-column repo activity layout
│   └── config/
│       ├── __init__.py
│       └── loader.py        # TOML + repos.txt file readers
tests/
├── conftest.py
├── unit/
│   ├── test_business_day.py     # 20 tests (next/last/n_business_days_back)
│   ├── test_config_loader.py    # 10 tests (TOML, repos.txt, error handling)
│   ├── test_models.py           # 20 tests (all dataclass validation)
│   └── test_things_reader.py    # 3 tests (Things DB read, empty, missing)
├── integration/
│   ├── test_render_pdf.py       # 4 tests (PDF creation, filename, size)
│   ├── test_github_client.py    # 3 tests (GitHub API mock)
│   └── test_ado_client.py       # 3 tests (ADO API mock)
└── contract/
    └── test_tool_schemas.py     # 9 tests (MCP tool schema validation)
config/
├── repos.txt                    # User-editable repo list
└── settings.toml                # Font sizes + output path
.github/
├── agents/
│   └── morning-briefing.agent.md  # Copilot CLI agent skill
├── copilot/
│   └── mcp.json                   # VS Code MCP server config
└── copilot-instructions.md        # Project conventions for Copilot
```

**Structure Decision**: Single project layout with `src/daily_planner/`
package. Modules are grouped by responsibility: `tools/` (MCP tool
handlers), `integrations/` (external API clients), `models/` (data
classes), `pdf/` (rendering), `config/` (file loading). This is the
simplest structure that keeps each module single-responsibility per
Principle I.

## Complexity Tracking

> No violations detected. All gates pass without exceptions.

## Constitution Re-Check (Post Phase 1 Design)

*Re-evaluated after research.md, data-model.md, and contracts/ are complete.*

| # | Principle | Post-Design Status |
|---|-----------|---|
| I | Simplicity First | ✅ PASS — 4 tools, 6 modules. `things.py` wraps DB complexity. Direct httpx for HTTP. reportlab for PDF. No unnecessary abstractions. Auth uses 3-step fallback (env → CLI → Keychain) — simpler than full OAuth2 device-code flow. |
| II | Privacy by Default | ✅ PASS — Keychain for tokens (no plain text). No PII persisted. `render_pdf` writes locally only. Temp files in `.tmp/` cleaned up at exit. |
| III | Resilient Integrations | ✅ PASS — Each integration isolated in `integrations/`. `BriefingData` supports per-section `*_error` fields. httpx configurable timeouts. Token fallback chain degrades gracefully. |
| IV | Testability | ✅ PASS — Pure data models with `__post_init__` validation. `respx` HTTP mocking. PDF verifiable via `BriefingData` inspection. MCP tool schemas contract-testable. 72 tests across unit/integration/contract. |
| V | Actionable Output | ✅ PASS — Three-column + two-column landscape layout. Date header "dddd, MMMM D, YYYY". Filename "YYYY-MM-DD dddd.pdf". Error sections render red text. |
| — | Dependency Security | ✅ PASS — UV lock file pins all versions. `pip-audit` in dev deps. All libraries well-maintained. |

**Post-design gate result**: ALL PASS — ready for task generation.
