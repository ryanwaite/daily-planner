# Implementation Plan: Markdown Briefing Overhaul

**Branch**: `005-markdown-briefing-overhaul` | **Date**: 2026-04-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-markdown-briefing-overhaul/spec.md`

## Summary

Replace the PDF rendering pipeline with a markdown renderer. The MCP
server keeps its four-tool architecture; `render_pdf` is renamed to
`render_markdown` and now writes a `.md` file instead of calling
ReportLab. Task tools gain the `area` field in their JSON output. The
agent instructions are updated to group tasks by Area, generate action
suggestions for up to 5 random unassigned tasks, and request line breaks
between repo narrative themes. ReportLab is removed from dependencies;
the `pdf/` module is replaced by a `markdown/` module. Configuration
drops font-size settings.

## Technical Context

**Language/Version**: Python ≥ 3.12 (managed by UV); `from __future__ import annotations` in every module
**Package Manager**: UV (`uv` CLI for venv, dependency resolution, and lock file)
**Primary Dependencies**:
  - `mcp>=1.0.0` (Model Context Protocol SDK — FastMCP server, stdio transport)
  - `httpx>=0.27` (async HTTP client for GitHub/ADO APIs)
  - `keyring>=25.0` (macOS Keychain access for token storage)
  - `things.py>=0.0.15` (Things 3 local database reader)
  - ~~`reportlab>=4.1`~~ (REMOVED — no longer needed)
**Storage**: Things 3 local SQLite DB (read-only); macOS Keychain for tokens; plain-text config files (TOML + line-oriented)
**Testing**: `pytest>=8.0` + `pytest-asyncio>=0.23`; `respx>=0.21` for HTTP mocking; `pip-audit>=2.7` for vulnerability scanning
**Linting**: `ruff>=0.4` — rules `E, F, I, N, W, UP`; line length 99; target Python 3.12
**Target Platform**: macOS (single-user local machine)
**Project Type**: MCP server + Copilot CLI agent skill
**Performance Goals**: Complete briefing in <30 seconds
**Constraints**: No data persisted beyond single run; no plain-text credential storage; output path must resolve within user's home directory
**Scale/Scope**: Single user, ~5–15 repos, ~10–30 calendar events per day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate | Status |
|---|-----------|------|--------|
| I | Simplicity First | No unnecessary abstractions; each module has single responsibility; simplest approach chosen | ✅ PASS — Replacing ReportLab multi-page layout engine with simple string concatenation for markdown is a net simplification. No new dependencies. |
| II | Privacy by Default | No PII persisted beyond run; credentials in env vars or secure store; output written locally only | ✅ PASS — Same as before. Markdown file written locally only. No new data flows. |
| III | Resilient Integrations | Timeout + retry on every external call; graceful degradation per source; isolated modules | ✅ PASS — No change to integration layer. Per-section `*_error` fields still flow through to markdown output. |
| IV | Testability | All integrations mockable; business logic separated from I/O; output verifiable via intermediate data | ✅ PASS — Markdown output is even easier to test than PDF (plain text assertions vs binary inspection). |
| V | Actionable Output | Scannable layout; timestamps per section; date formats per constitution | ✅ PASS — Markdown sections with headings are scannable. Date format in heading. Tasks grouped by Area improve scannability. |
| — | Dependency Security | Pinned versions; pip-audit before release; no unresolved critical CVEs | ✅ PASS — Removing reportlab reduces dependency surface. No new dependencies added. |

**Pre-Phase 0 gate result**: ALL PASS — proceed to research.

## Project Structure

### Documentation (this feature)

```text
specs/005-markdown-briefing-overhaul/
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
│   ├── __main__.py              # CLI entry point (stdio server launcher, .tmp/ setup)
│   ├── business_day.py          # Date arithmetic (unchanged)
│   ├── server.py                # MCP server entry point (rename render_pdf → render_markdown)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── tasks.py             # get_today_tasks, get_tomorrow_tasks (add `area` field)
│   │   ├── repo_activity.py     # get_repo_activity (unchanged)
│   │   └── render_markdown.py   # NEW — render_markdown handler (replaces render_pdf.py)
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── things.py            # Things 3 SQLite reader (unchanged — already reads areas)
│   │   ├── github.py            # GitHub REST API client (unchanged)
│   │   ├── ado.py               # Azure DevOps REST API client (unchanged)
│   │   └── auth.py              # Token resolution (unchanged)
│   ├── models/
│   │   ├── __init__.py          # BriefingData (add action_suggestions field)
│   │   ├── calendar.py          # CalendarEvent dataclass (unchanged)
│   │   ├── task.py              # Task dataclass (unchanged — already has area field)
│   │   ├── repo.py              # Repository, ActivityItem, RepoSummary (unchanged)
│   │   └── config.py            # Configuration (remove font sizes)
│   ├── markdown/
│   │   ├── __init__.py
│   │   └── renderer.py          # NEW — markdown string builder
│   └── config/
│       ├── __init__.py
│       └── loader.py            # TOML reader (remove font size parsing)
tests/
├── conftest.py
├── unit/
│   ├── test_business_day.py         # (unchanged)
│   ├── test_config_loader.py        # Updated (font sizes removed from assertions)
│   ├── test_models.py               # Updated (Configuration without font sizes)
│   └── test_things_reader.py        # (unchanged)
├── integration/
│   ├── test_render_markdown.py      # NEW — replaces test_render_pdf.py
│   ├── test_github_client.py        # (unchanged)
│   └── test_ado_client.py           # (unchanged)
└── contract/
    └── test_tool_schemas.py         # Updated (render_markdown schema)
config/
├── repos.txt                        # (unchanged)
└── settings.toml                    # Simplified (remove page_one, page_two sections)
.github/
├── agents/
│   └── morning-briefing.agent.md    # Updated (new workflow steps)
└── copilot-instructions.md          # Updated (reflect markdown, not PDF)
```

**Files to DELETE**:
- `src/daily_planner/tools/render_pdf.py`
- `src/daily_planner/pdf/__init__.py`
- `src/daily_planner/pdf/renderer.py`
- `src/daily_planner/pdf/page_one.py`
- `src/daily_planner/pdf/page_two.py`
- `tests/integration/test_render_pdf.py`

**Structure Decision**: Same single-project layout as 001. The `pdf/`
package is replaced by `markdown/` with a single `renderer.py` module
(much simpler than the three-file PDF layout engine). The tool handler
file is renamed from `render_pdf.py` to `render_markdown.py`.

## Complexity Tracking

> No violations detected. All gates pass without exceptions.
> This feature is a net reduction in complexity (removing ReportLab,
> multi-column layout, font management, page templates).

## Constitution Re-Check (Post Phase 1 Design)

*Re-evaluated after research.md, data-model.md, and contracts/ are complete.*

| # | Principle | Post-Design Status |
|---|-----------|---|
| I | Simplicity First | ✅ PASS — Replacing 4-file PDF engine with 1-file markdown builder. Removing reportlab dependency. Configuration drops from 4 fields to 2. Net reduction in code and complexity. New `ActionSuggestion` dataclass is minimal (2 fields). |
| II | Privacy by Default | ✅ PASS — No new data flows. Markdown file written locally only, same as PDF was. Action suggestions are ephemeral (generated per run, not persisted). |
| III | Resilient Integrations | ✅ PASS — No changes to integration layer. Per-section `*_error` fields still propagate to markdown output. Action suggestions section is simply omitted if no unassigned tasks exist. |
| IV | Testability | ✅ PASS — Markdown output is plain text, making assertions simpler than PDF binary inspection. New `ActionSuggestion` model has `__post_init__` validation. Contract tests updated for `render_markdown` schema. |
| V | Actionable Output | ✅ PASS — Tasks grouped by Area improve scannability. Action suggestions add actionable next steps. Repo narratives gain visual separation between themes. Date format in heading follows constitution. |
| — | Dependency Security | ✅ PASS — Net reduction: removing reportlab (and its transitive deps). No new dependencies added. |

**Post-design gate result**: ALL PASS — ready for task generation.
