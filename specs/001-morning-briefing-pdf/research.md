# Research: Morning Briefing PDF Generator

**Date**: 2026-03-12
**Feature**: [spec.md](spec.md) | [plan.md](plan.md)

## R1. MCP Python SDK — stdio Server

**Decision**: Use the `mcp` Python package with `MCPServer` class
and `@mcp.tool()` decorator over stdio transport.

**Rationale**: The high-level `MCPServer` API provides decorator-based
tool registration, automatic JSON schema generation from type hints,
and built-in stdio transport via `mcp.server.stdio.stdio_server()`.
This is the simplest approach (Principle I) and the officially
supported Python SDK.

**Alternatives considered**:
- Low-level `Server` class with manual `on_call_tool` handlers —
  rejected because more boilerplate for no benefit.
- FastMCP / third-party wrappers — rejected because the first-party
  SDK is sufficient and avoids an extra dependency.

**Key pattern**:
```python
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("daily-planner")

@mcp.tool()
async def get_today_tasks() -> dict:
    """Get today's tasks from Things."""
    ...
```

**Stdio entry point**:
```python
async with mcp.server.stdio.stdio_server() as (read, write):
    await server.run(read, write, init_options)
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

## R3. OAuth2 Device-Code Flow (GitHub + ADO)

**Decision**: Implement device-code flow directly with `httpx`.
Store tokens in macOS Keychain via `keyring`.

**Rationale**: Device-code flow is a simple poll loop (two HTTP
endpoints per provider). A direct httpx implementation avoids
heavy dependencies like `msal` (Principle I).

**Alternatives considered**:
- `msal` (Microsoft Authentication Library) — rejected for ADO
  because it's heavyweight and pulls in many transitive deps.
  May reconsider if AAD complexity grows.
- Personal access tokens (PATs) — rejected per clarification:
  user chose OAuth2 device-code for both platforms.

**GitHub specifics**:
- Initiate: `POST https://github.com/login/device/code`
- Exchange: `POST https://github.com/login/oauth/access_token`
- Scopes: `repo` (read commits, PRs, issues)
- **No refresh tokens** — GitHub OAuth tokens do not support
  refresh. Must re-authenticate when token expires (~8 hours).
- **Implication**: Store `access_token` + `expires_at` in
  Keychain. On expiry, trigger interactive device-code flow.

**ADO specifics**:
- Initiate: `POST https://login.microsoftonline.com/common/oauth2/v2.0/devicecode`
- Exchange: `POST https://login.microsoftonline.com/common/oauth2/v2.0/token`
- Scopes: `https://dev.azure.com/.default`
- **Refresh tokens supported** — ~90 day lifetime.
- Store `access_token`, `refresh_token`, `expires_at` in Keychain.

**Keychain pattern**:
```python
import keyring

keyring.set_password("daily-planner", "github_access_token", token)
keyring.set_password("daily-planner", "github_expires_at", str(ts))
token = keyring.get_password("daily-planner", "github_access_token")
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
- US Letter: 612 × 792 points (8.5″ × 11″)
- Page 1: three `Frame` objects (calendar, today tasks, tomorrow + notes)
- Page 2: two `Frame` objects (repo activity left, repo activity right)
- Font sizes read from config; defaults sensible for print

```python
from reportlab.platypus import Frame, PageTemplate
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Page 1: 3 columns
col_w = (letter[0] - 1.5*inch) / 3
frames_p1 = [
    Frame(0.5*inch, 0.5*inch, col_w, 10*inch, id='calendar'),
    Frame(0.5*inch + col_w + 0.25*inch, 0.5*inch, col_w, 10*inch, id='today'),
    Frame(0.5*inch + 2*(col_w + 0.25*inch), 0.5*inch, col_w, 10*inch, id='tomorrow'),
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
with YAML frontmatter referencing the daily-planner MCP server
and Work IQ MCP server.

**Rationale**: This is the standard Copilot CLI agent skill
format found in the existing `.github/agents/` directory.

**Key structure**:
```yaml
---
name: morning-briefing
description: Generate a PDF morning briefing
tools:
  - type: mcp
    server: daily-planner
  - type: mcp
    server: workiq
---

[Orchestration instructions for the agent]
```
