# Research: Morning Briefing PDF Generator

**Date**: 2026-03-12
**Feature**: [spec.md](spec.md) | [plan.md](plan.md)

## R1. MCP Python SDK — stdio Server

**Decision**: Use the `mcp` Python package with `FastMCP` class
and `@mcp.tool()` decorator over stdio transport.

**Rationale**: The `FastMCP` API provides decorator-based
tool registration, automatic JSON schema generation from type hints,
and built-in stdio transport via `mcp.run(transport="stdio")`.
This is the simplest approach (Principle I) and the officially
supported Python SDK.

**Alternatives considered**:
- Low-level `Server` class with manual `on_call_tool` handlers —
  rejected because more boilerplate for no benefit.
- Third-party wrappers — rejected because the first-party
  SDK is sufficient and avoids an extra dependency.

**Key pattern**:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("daily-planner")

@mcp.tool()
async def get_today_tasks() -> str:
    """Get today's tasks from Things."""
    ...
```

**Stdio entry point**:
```python
def main() -> None:
    mcp.run(transport="stdio")
```

## R2. Things 3 Data Access

**Decision**: Use the `things.py` library (PyPI: `things.py`) for
reading Things 3 tasks.

**Rationale**: `things.py` handles database location discovery,
file locking (copies DB to temp), Core Data timestamp conversion,
and schema parsing. Using it avoids reimplementing all of those
concerns (Principle I: simplest approach).

**Alternatives considered**:
- Direct `sqlite3` access — rejected because it requires handling
  DB locking, timestamp conversion, and schema knowledge manually.
- Things URL scheme — rejected because it opens the Things UI and
  is not suitable for headless/automated use.

**Key details**:
- DB location: `~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/`
- Tasks table: `TMTask` (title, dueDate, status, sortOrder)
- Due dates are Core Data timestamps (seconds since 2001-01-01)
- Filter: `status=0` (open), `deletedDate IS NULL`
- DB is locked while Things is running — `things.py` copies to temp

## R3. Authentication — Token Resolution (GitHub + ADO)

**Decision**: Use a three-step fallback chain for both platforms:
environment variable → CLI tool → macOS Keychain.

**Rationale**: GitHub CLI (`gh`) and Azure CLI (`az`) are already
installed on the developer machine and handle token lifecycle
(including refresh) automatically. Delegating to these tools avoids
implementing a full OAuth2 device-code flow (Principle I: simplest
approach). Environment variables provide override capability for CI;
Keychain is the final fallback.

**Alternatives considered**:
- Full OAuth2 device-code flow with `httpx` — rejected because it
  requires implementing poll loops, token refresh, and expiry
  tracking manually. Was the original plan (R3 v1) but replaced
  after discovering that CLI tools handle this transparently.
- `msal` (Microsoft Authentication Library) — rejected because it's
  heavyweight and pulls in many transitive deps.
- Personal access tokens (PATs) only — rejected because they must
  be stored in plain text or manually rotated.

**GitHub resolution chain**:
1. `GITHUB_TOKEN` environment variable
2. `gh auth token` CLI command (10s timeout)
3. macOS Keychain: `service=daily-planner`, `account=github_access_token`

**ADO resolution chain**:
1. `ADO_TOKEN` environment variable
2. `az account get-access-token --resource 499b84ac-...` CLI command (10s timeout)
3. macOS Keychain: `service=daily-planner`, `account=ado_access_token`

**Key pattern**:
```python
def get_github_token() -> str | None:
    # 1. Environment variable
    if token := os.environ.get("GITHUB_TOKEN"):
        return token
    # 2. GitHub CLI
    if token := _run_cli(["gh", "auth", "token"]):
        return token
    # 3. macOS Keychain
    return keyring.get_password("daily-planner", "github_access_token")
```

## R4. PDF Generation with ReportLab

**Decision**: Use `reportlab` with Platypus `Frame` objects for
multi-column layouts.

**Rationale**: ReportLab is the most mature Python PDF library.
Platypus Frames provide structured multi-column layout without
manual coordinate math, while still giving full control over font
sizes and positioning. `weasyprint` was considered but requires
system-level dependencies (Cairo, Pango) that complicate
installation.

**Alternatives considered**:
- `weasyprint` — rejected because it depends on system packages
  (Cairo, Pango) that must be installed separately on macOS.
  ReportLab is pure Python and installs cleanly with UV.
- `fpdf2` — rejected because it has weaker multi-column/frame
  support compared to ReportLab's Platypus.

**Key pattern**:
- Landscape US Letter: 792 × 612 points (11″ × 8.5″)
- Margins: 0.5″ left/right, 0.75″ top, 0.5″ bottom
- Gutter: 0.25″ between columns
- Page 1: three `Frame` objects (calendar, today tasks, tomorrow + notes)
- Page 2: two `Frame` objects (repo activity left, repo activity right)
- Fonts: HelveticaNeue (system TTC) with CascadiaCode fallback
- Font sizes read from config; defaults sensible for print

```python
from reportlab.platypus import Frame, PageTemplate, BaseDocTemplate
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch

page_w, page_h = landscape(letter)  # 792 x 612

# Page 1: 3 columns
usable_w = page_w - 2 * 0.5 * inch
col_w = (usable_w - 2 * 0.25 * inch) / 3
frames_p1 = [
    Frame(0.5*inch, 0.5*inch, col_w, page_h - 1.25*inch, id='calendar'),
    Frame(0.5*inch + col_w + 0.25*inch, ..., id='today'),
    Frame(0.5*inch + 2*(col_w + 0.25*inch), ..., id='tomorrow'),
]
```

## R5. GitHub and ADO API Patterns

**Decision**: Use GitHub REST API v3 and Azure DevOps REST API for
fetching commits, PRs, and issues/work items.

**Rationale**: REST APIs are well-documented, support filtering by
date, and work with OAuth tokens. GraphQL (GitHub v4) was
considered but adds complexity for no benefit at this scale
(Principle I).

**GitHub endpoints**:
- Commits: `GET /repos/{owner}/{repo}/commits?since={date}`
- PRs: `GET /repos/{owner}/{repo}/pulls?state=all&sort=updated&since={date}`
- Issues: `GET /repos/{owner}/{repo}/issues?state=all&since={date}`
- README: `GET /repos/{owner}/{repo}/readme` (for LLM context)

**ADO endpoints** (base: `https://dev.azure.com/{org}/{project}/_apis`):
- Commits: `GET /git/repositories/{repo}/commits?searchCriteria.fromDate={date}&api-version=7.1`
- PRs: `GET /git/repositories/{repo}/pullrequests?searchCriteria.status=all&api-version=7.1`
- Work items (via WIQL): `POST /wit/wiql?api-version=7.1`

**Common pattern**: All calls use `httpx.AsyncClient` with
configurable timeouts (default 10s connect, 30s read) and a
single retry with exponential backoff.

## R6. Copilot CLI Agent Skill File

**Decision**: Create `.github/agents/morning-briefing.agent.md`
as a single unified agent that orchestrates both the daily view
and repo activity workflows.

**Rationale**: A single agent skill simplifies invocation — the
user calls one agent that handles the full briefing. The MCP server
config is declared in `.github/copilot/mcp.json` (VS Code) and
`~/.copilot/mcp-config.json` (CLI).

**Key structure** (`.github/agents/morning-briefing.agent.md`):
```markdown
---
description: Generate a printable two-page PDF morning briefing ...
---

# Morning Briefing Agent

## Step 1 — Calendar Events
Call Work IQ MCP ...

## Step 2 — Today's Tasks
Call daily-planner get_today_tasks ...

## Step 3 — Tomorrow's Tasks
Call daily-planner get_tomorrow_tasks ...

## Step 4 — Repository Activity
Call daily-planner get_repo_activity ...
(optional since_business_days parameter)

## Step 5 — Summarise Repo Activity
Use LLM to generate narrative per repo ...

## Step 6 — Render PDF
Call daily-planner render_pdf with all data ...

## Step 7 — Report
Tell user the PDF path ...
```
