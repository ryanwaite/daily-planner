# Implementation Plan: Morning Briefing PDF Generator

**Branch**: `001-morning-briefing-pdf` | **Date**: 2026-03-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-morning-briefing-pdf/spec.md`

## Summary

Build an MCP server in Python (stdio transport, managed by UV) that
exposes four tools — `get_today_tasks`, `get_tomorrow_tasks`,
`get_repo_activity`, and `render_pdf` — orchestrated by a Copilot CLI
agent skill. The agent also connects to the Microsoft Work IQ MCP
server for calendar data and uses its own LLM for repo-activity
summarization. The `render_pdf` tool produces a two-page US Letter
PDF: page one has a three-column layout (calendar, today's tasks,
tomorrow's tasks + note area); page two has a two-column layout of
LLM-summarized repository activity. Font sizes and repo lists are
configurable via files.

## Technical Context

**Language/Version**: Python ≥ 3.9 (targeting 3.12, managed by UV)
**Package Manager**: UV (`uv` CLI for venv, dependency resolution, and lock file)
**Primary Dependencies**:
  - `mcp` (Model Context Protocol SDK for Python — stdio server)
  - `reportlab` (PDF generation with precise layout control)
  - `httpx` (async HTTP client for GitHub/ADO APIs)
  - `keyring` (macOS Keychain access for OAuth2 token storage)
  - `things.py` (Things 3 local database on macOS — handles DB locking and Core Data timestamps)
**Storage**: Things 3 local SQLite DB (read-only); macOS Keychain for tokens; plain-text config files
**Testing**: `pytest` + `pytest-asyncio`; `respx` for HTTP mocking
**Target Platform**: macOS (single-user local machine)
**Project Type**: MCP server + Copilot CLI agent skill
**Performance Goals**: Complete PDF generation in <30 seconds (SC-001); <45 seconds with degraded sources (SC-003)
**Constraints**: US Letter paper only; no data persisted beyond single run; no plain-text credential storage
**Scale/Scope**: Single user, ~5–15 repos, ~10–30 calendar events per day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate | Status |
|---|-----------|------|--------|
| I | Simplicity First | No unnecessary abstractions; each module has single responsibility; simplest approach chosen | ✅ PASS — 4 MCP tools, flat module structure, no ORM or framework overhead |
| II | Privacy by Default | No PII persisted beyond run; credentials in env vars or secure store; PDF written locally only | ✅ PASS — Keychain for tokens, no data retention, local PDF output only |
| III | Resilient Integrations | Timeout + retry on every external call; graceful degradation per source; isolated modules | ✅ PASS — FR-011 mandates per-section error notices; httpx has configurable timeouts |
| IV | Testability | All integrations mockable; business logic separated from I/O; PDF verifiable via intermediate data | ✅ PASS — respx for HTTP mocking; data models separate from rendering |
| V | Actionable Output | Scannable layout; timestamps per section; date formats per constitution; exit codes | ✅ PASS — three-column + two-column layout; date formats specified in FR-007 |
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
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── daily_planner/
│   ├── __init__.py
│   ├── server.py            # MCP server entry point (stdio transport)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── tasks.py         # get_today_tasks, get_tomorrow_tasks
│   │   ├── repo_activity.py # get_repo_activity
│   │   └── render_pdf.py    # render_pdf
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── things.py        # Things 3 SQLite reader
│   │   ├── github.py        # GitHub API client
│   │   ├── ado.py           # Azure DevOps API client
│   │   └── auth.py          # OAuth2 device-code flow + Keychain storage
│   ├── models/
│   │   ├── __init__.py
│   │   ├── calendar.py      # CalendarEvent model
│   │   ├── task.py          # Task model
│   │   ├── repo.py          # Repository, ActivityItem models
│   │   └── config.py        # Configuration model
│   ├── pdf/
│   │   ├── __init__.py
│   │   ├── renderer.py      # PDF layout engine (reportlab)
│   │   ├── page_one.py      # Page 1: three-column layout
│   │   └── page_two.py      # Page 2: two-column layout
│   └── config/
│       ├── __init__.py
│       └── loader.py        # Config file reader (font sizes, repos list)
tests/
├── conftest.py
├── unit/
│   ├── test_models.py
│   ├── test_config_loader.py
│   ├── test_things_reader.py
│   ├── test_business_day.py
│   └── test_pdf_data.py
├── integration/
│   ├── test_github_client.py
│   ├── test_ado_client.py
│   └── test_render_pdf.py
└── contract/
    ├── test_mcp_tools.py
    └── test_tool_schemas.py
config/
├── repos.txt                # User-editable repo list
└── settings.toml            # Font sizes + output path
.github/
└── agents/
    └── morning-briefing.agent.md  # Copilot CLI agent skill
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
| I | Simplicity First | ✅ PASS — 4 tools, 6 modules. `things.py` wraps DB complexity. Direct httpx for OAuth. reportlab for PDF. No unnecessary abstractions. |
| II | Privacy by Default | ✅ PASS — Keychain for tokens (no plain text). No PII persisted. `render_pdf` writes locally only. |
| III | Resilient Integrations | ✅ PASS — Each integration isolated in `integrations/`. `BriefingData` supports per-section `*_error` fields. httpx configurable timeouts. |
| IV | Testability | ✅ PASS — Pure data models. `respx` HTTP mocking. PDF verifiable via `BriefingData` inspection. MCP tool schemas contract-testable. |
| V | Actionable Output | ✅ PASS — Three-column + two-column layout. Timestamps per section. Date formats per FR-007/constitution. |
| — | Dependency Security | ✅ PASS — UV lock file pins all versions. `pip-audit` in dev deps. All libraries well-maintained. |

**Post-design gate result**: ALL PASS — ready for task generation.
