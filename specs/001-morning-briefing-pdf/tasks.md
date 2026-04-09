# Tasks: Morning Briefing PDF Generator

**Input**: Design documents from `/specs/001-morning-briefing-pdf/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included per constitution requirement ("Every feature branch MUST include tests that exercise the new behaviour before the implementation is considered complete").

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## User Story Mapping

Tasks use US1–US5 numbering which maps to the spec's user stories as follows:

| Tasks Reference | Spec User Story | Description |
|-----------------|-----------------|-------------|
| US1 (Phase 3) | Spec US1 — Daily View | Calendar column + PDF renderer |
| US2 (Phase 4) | Spec US1 — Daily View | Today's Things tasks (column 2) |
| US3 (Phase 5) | Spec US1 — Daily View | Tomorrow's tasks + note space (column 3) |
| US4 (Phase 6) | Spec US2 — Repo Activity | Repository activity summary (page two) |
| US5 (Phase 7) | Spec US4 — Configuration | Configurable font sizes and repo list |

> **Note — Spec US3 (Combined Two-Page Briefing)**: The acceptance scenarios for spec US3 are
> covered by the `render_pdf` implementation in T016 (Phase 3), which accepts all briefing data
> and produces a 1- or 2-page PDF depending on available data. No separate tasks are needed.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [x] T001 Create project directory structure with all directories and `__init__.py` files per plan.md (`src/daily_planner/`, `src/daily_planner/tools/`, `src/daily_planner/integrations/`, `src/daily_planner/models/`, `src/daily_planner/pdf/`, `src/daily_planner/config/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `config/`, `.github/agents/`)
- [x] T002 Initialize UV project — write `pyproject.toml` with dependencies (`mcp>=1.0.0`, `reportlab>=4.1`, `httpx>=0.27`, `keyring>=25.0`, `things.py>=0.0.15`), dev dependencies (`ruff>=0.4`, `pytest>=8.0`, `pytest-asyncio>=0.23`, `respx>=0.21`, `pip-audit>=2.7`), ruff config (rules E/F/I/N/W/UP, line-length 99, target py312), and run `uv lock` in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, config loading, business day logic, and MCP server scaffold that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Define `CalendarEvent` dataclass with validation (title non-empty, start < end, all-day flag) and `from_dict` class method in `src/daily_planner/models/calendar.py`
- [x] T004 [P] Define `Task` dataclass with validation (title non-empty, sort_position, optional project/tags) and `from_dict` class method in `src/daily_planner/models/task.py`
- [x] T005 [P] Define `Repository`, `ActivityItem`, and `RepoSummary` dataclasses with validation and `from_dict` methods in `src/daily_planner/models/repo.py`
- [x] T006 [P] Define `Configuration` dataclass with defaults (`page_one_font_size=9.0`, `page_two_font_size=8.0`, `output_path=~/Desktop`, `repos_file=config/repos.txt`) in `src/daily_planner/models/config.py`
- [x] T007 Define `BriefingData` dataclass (date, calendar_events, today_tasks, tomorrow_tasks, repo_summaries, per-section error fields, config) in `src/daily_planner/models/__init__.py`
- [x] T008 [P] Implement business day helpers (`next_business_day`: Fri→Mon; `last_business_day`: Mon→Fri; `n_business_days_back`: walk back N business days, raises `ValueError` for n < 1) in `src/daily_planner/business_day.py`
- [x] T009 Implement config loader — parse `settings.toml` into `Configuration`, parse `repos.txt` into `list[Repository]`, handle missing files with defaults or clear errors, validate repo line format and skip invalid entries with stderr warning in `src/daily_planner/config/loader.py`
- [x] T010 Implement MCP server entry point with FastMCP, stdio transport, server name "daily-planner", and empty tool registration scaffold in `src/daily_planner/server.py`
- [x] T011 [P] Write unit tests for all model dataclasses (validation rules, defaults, `from_dict`), business day helpers (Fri→Mon, Mon→Fri, mid-week, `n_business_days_back` with weekend crossings and invalid input), and config loader (valid TOML, missing file defaults, missing repos file error, invalid repo line format) in `tests/unit/test_models.py`, `tests/unit/test_business_day.py`, `tests/unit/test_config_loader.py`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Calendar Column & PDF Renderer (Priority: P1) 🎯 MVP

**Goal**: Calendar events from Work IQ (passed by agent) render in page one column 1 of the landscape PDF, chronological with all-day events first, date header in "dddd, MMMM D, YYYY" format

**Independent Test**: Call `render_pdf` with sample `calendar_events` JSON and verify the output PDF has a first column listing events chronologically with time, title, and optional location

### Tests for User Story 1

> **Write tests FIRST — ensure they FAIL before implementation**

- [x] T012 [P] [US1] Contract test for `render_pdf` MCP tool schema (input/output shape validation) in `tests/contract/test_tool_schemas.py`
- [x] T013 [P] [US1] Integration test for `render_pdf` — supply sample `BriefingData`, verify two-page PDF is written with correct filename format ("YYYY-MM-DD dddd.pdf") and non-zero size in `tests/integration/test_render_pdf.py`

### Implementation for User Story 1

- [x] T014 [US1] Implement PDF renderer engine — landscape US Letter (792×612pt) `BaseDocTemplate`, page margins (0.5″ L/R, 0.75″ top, 0.5″ bottom), 0.25″ gutter, three-column `Frame` layout for page one, two-column `Frame` layout for page two, HelveticaNeue font registration, date header per FR-007, paragraph styles (`p1_heading`, `p1_body`, `p1_task`, `p1_error`, `p2_heading`, `p2_body`, `p2_error`) in `src/daily_planner/pdf/renderer.py`
- [x] T015 [US1] Implement page one calendar column rendering — chronological event list (all-day first), time range + title + optional location, "Calendar data unavailable" error notice fallback, overflow with ellipsis indicator ("… and N more events") after `MAX_CALENDAR_EVENTS` in `src/daily_planner/pdf/page_one.py`
- [x] T016 [US1] Implement `render_pdf` tool handler — accept `calendar_events`, tasks, `repo_summaries`, `output_path`; assemble `BriefingData`; call renderer; write PDF with filename "YYYY-MM-DD dddd.pdf" per FR-007; return `pdf_path` and page count JSON in `src/daily_planner/tools/render_pdf.py`
- [x] T017 [US1] Register `render_pdf` tool with `@mcp.tool()` decorator as thin wrapper delegating to handler in `src/daily_planner/server.py`

**Checkpoint**: `render_pdf` produces a two-page landscape PDF with calendar column populated — MVP complete

---

## Phase 4: User Story 2 — Today's Things Tasks (Priority: P1)

**Goal**: Today's Things tasks appear in page one column 2, in Things' default sort order with title and optional project/tag context

**Independent Test**: Invoke `get_today_tasks` MCP tool and verify returned JSON contains all tasks due today in sort order; call `render_pdf` with that data and verify column 2 is populated

### Tests for User Story 2

> **Write tests FIRST — ensure they FAIL before implementation**

- [x] T018 [P] [US2] Contract test for `get_today_tasks` MCP tool schema in `tests/contract/test_tool_schemas.py`
- [x] T019 [P] [US2] Unit test for Things reader — mock `things.py` library calls, verify `list[Task]` output and DB-not-found error handling in `tests/unit/test_things_reader.py`

### Implementation for User Story 2

- [x] T020 [US2] Implement Things 3 integration — locate DB, read tasks by due date using `things.py` library, return `list[Task]` in `sort_position` order, handle DB-not-found gracefully in `src/daily_planner/integrations/things.py`
- [x] T021 [US2] Implement `get_today_tasks` tool handler — call Things integration with today's date, return tasks JSON or error in `src/daily_planner/tools/tasks.py`
- [x] T022 [US2] Register `get_today_tasks` tool with `@mcp.tool()` decorator in `src/daily_planner/server.py`
- [x] T023 [US2] Implement page one today-tasks column rendering — task list with title/project/tags, "No tasks due today" empty state, "Unavailable" error fallback in `src/daily_planner/pdf/page_one.py`

**Checkpoint**: `get_today_tasks` returns Things data; PDF column 2 shows today's tasks

---

## Phase 5: User Story 3 — Tomorrow's Tasks and Note Space (Priority: P2)

**Goal**: Tomorrow's Things tasks (next business day) appear at the top of page one column 3; bottom of column 3 is intentionally blank for handwritten notes

**Independent Test**: Invoke `get_tomorrow_tasks` on a Friday and verify returned JSON targets Monday; call `render_pdf` with that data and verify column 3 has tasks at top and blank space below

### Tests for User Story 3

> **Write tests FIRST — ensure they FAIL before implementation**

- [x] T024 [P] [US3] Contract test for `get_tomorrow_tasks` MCP tool schema in `tests/contract/test_tool_schemas.py`
- [x] T025 [P] [US3] Unit test for next-business-day edge cases (Friday→Monday, Saturday→Monday, Sunday→Monday, mid-week→next day) in `tests/unit/test_business_day.py`

### Implementation for User Story 3

- [x] T026 [US3] Extend Things integration with a query-by-target-date method using `next_business_day` helper in `src/daily_planner/integrations/things.py`
- [x] T027 [US3] Implement `get_tomorrow_tasks` tool handler — compute next business day, call Things integration, return tasks JSON with `target_date` or error in `src/daily_planner/tools/tasks.py`
- [x] T028 [US3] Register `get_tomorrow_tasks` tool with `@mcp.tool()` decorator in `src/daily_planner/server.py`
- [x] T029 [US3] Implement page one tomorrow-tasks column — tasks at top of column 3, "No tasks due tomorrow" empty state, blank note area in lower portion, error fallback in `src/daily_planner/pdf/page_one.py`

**Checkpoint**: `get_tomorrow_tasks` returns next-business-day tasks; PDF column 3 has tasks + note space

---

## Phase 6: User Story 4 — Repository Activity Summary (Priority: P2)

**Goal**: Page two shows a two-column layout of LLM-summarised (or raw fallback) repository activity since the last business day for all configured GitHub and ADO repos; optional `since_business_days` parameter widens lookback window

**Independent Test**: Configure `repos.txt` with at least one GitHub and one ADO repo; invoke `get_repo_activity` and verify structured activity data; call `render_pdf` with agent-provided narrative summaries and verify page two renders in two-column layout

### Tests for User Story 4

> **Write tests FIRST — ensure they FAIL before implementation**

- [x] T030 [P] [US4] Contract test for `get_repo_activity` MCP tool schema (including optional `since_business_days` param) in `tests/contract/test_tool_schemas.py`
- [x] T031 [P] [US4] Integration test for GitHub API client — mock HTTP responses with respx, verify commits/PRs/issues parsing and error handling in `tests/integration/test_github_client.py`
- [x] T032 [P] [US4] Integration test for ADO API client — mock HTTP responses with respx, verify commits/PRs/work-items parsing and error handling in `tests/integration/test_ado_client.py`

### Implementation for User Story 4

- [x] T033 [US4] Implement token resolution — three-step fallback chain (env var → CLI tool → macOS Keychain) for both GitHub (`GITHUB_TOKEN` / `gh auth token`) and ADO (`ADO_TOKEN` / `az account get-access-token`) with 10s CLI timeout in `src/daily_planner/integrations/auth.py`
- [x] T034 [P] [US4] Implement GitHub API client — fetch commits, PRs (opened/merged/closed), and issues since a given date using `httpx.AsyncClient` with configurable timeouts and single retry; fetch README excerpt for LLM context in `src/daily_planner/integrations/github.py`
- [x] T035 [P] [US4] Implement ADO API client — fetch commits, PRs, and work items (via WIQL) since a given date using `httpx.AsyncClient` with configurable timeouts and single retry; fetch repo description for LLM context in `src/daily_planner/integrations/ado.py`
- [x] T036 [US4] Implement `get_repo_activity` tool handler — load repos from config, compute `last_business_day` or `n_business_days_back` based on optional `since_business_days` param, fetch activity from GitHub/ADO clients per repo, return structured JSON with per-repo errors for unreachable repos in `src/daily_planner/tools/repo_activity.py`
- [x] T037 [US4] Register `get_repo_activity` tool with `@mcp.tool()` decorator (with `since_business_days: int | None = None` param) in `src/daily_planner/server.py`
- [x] T038 [US4] Implement page two two-column rendering — LLM narrative per repo (or raw activity list fallback with "Summarisation unavailable" notice), "No recent activity" empty state, per-repo error notices, balanced column split in `src/daily_planner/pdf/page_two.py`

**Checkpoint**: `get_repo_activity` fetches from GitHub/ADO; PDF page two shows repo summaries in two-column layout

---

## Phase 7: User Story 5 — Configurable Font Sizes and Repo List (Priority: P3)

**Goal**: Users can customise page-one and page-two font sizes via `settings.toml` and manage tracked repos via `repos.txt`; changes take effect on next run without code changes

**Independent Test**: Edit `config/settings.toml` to change font sizes, run briefing twice with different values, and confirm PDF output reflects the changes

### Implementation for User Story 5

- [x] T039 [P] [US5] Create default `config/settings.toml` with `[page_one] font_size=9.0`, `[page_two] font_size=8.0`, `[output] path=~/Desktop` and `repos_file=config/repos.txt` in `config/settings.toml`
- [x] T040 [P] [US5] Create `config/repos.txt` with documented format (`github:owner/repo`, `ado:org/project/repo`) and example entries in `config/repos.txt`
- [x] T041 [US5] Wire `Configuration.page_one_font_size` and `page_two_font_size` into PDF paragraph styles in `src/daily_planner/pdf/renderer.py`

**Checkpoint**: Font sizes and repo list are user-configurable via plain-text files

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Agent skill, CLI entry point, MCP config, documentation, and security validation

- [x] T042 [P] Create Copilot CLI agent skill file — YAML frontmatter with description, orchestration instructions (call Work IQ → `get_today_tasks` → `get_tomorrow_tasks` → `get_repo_activity` → LLM summarize → `render_pdf`), document optional `since_business_days` param in Step 4 in `.github/agents/morning-briefing.agent.md`
- [x] T043 [P] Add `__main__.py` entry point — create `.tmp/` dir, set `TMPDIR`, register atexit cleanup, import and call `server.main()`, catch `KeyboardInterrupt` and generic exceptions with stderr output and exit codes in `src/daily_planner/__main__.py`
- [x] T044 [P] Create `.github/copilot/mcp.json` with daily-planner MCP server config (stdio transport, `uv run python -m daily_planner`) in `.github/copilot/mcp.json`
- [x] T045 Update `README.md` with installation (UV), configuration (`settings.toml`, `repos.txt`, Keychain setup), agent skill usage, and direct CLI usage instructions in `README.md`
- [x] T046 Run `pip-audit` against locked dependencies and verify no unresolved critical CVEs per constitution dependency security requirements
- [x] T047 Run full test suite (`uv run pytest`) and verify all 72 tests pass before merge

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Foundational — creates PDF renderer used by all later stories
- **US2 (Phase 4)**: Depends on Foundational + US1 (extends `page_one.py` created in US1)
- **US3 (Phase 5)**: Depends on Foundational + US2 (extends Things integration and `page_one.py`)
- **US4 (Phase 6)**: Depends on Foundational + US1 (needs `renderer.py` for page two); **independent of US2/US3**
- **US5 (Phase 7)**: Depends on Foundational + US1 (wires font sizes into `renderer.py`)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1 (Setup)
  └─► Phase 2 (Foundational)
        ├─► Phase 3 (US1: Calendar + Renderer) ──► Phase 4 (US2: Today Tasks) ──► Phase 5 (US3: Tomorrow Tasks)
        │         │
        │         ├─► Phase 6 (US4: Repo Activity)  [parallel with US2/US3]
        │         └─► Phase 7 (US5: Configuration)   [parallel with US2-US4]
        └─► Phase 8 (Polish) [after all stories]
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/integrations before tool handlers
- Tool handlers before server registration
- PDF rendering extends existing modules
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T003–T006 (all model dataclasses) can run in parallel; T008 (business day) in parallel with models
- **Phase 3**: T012–T013 (tests) in parallel before implementation
- **Phase 4**: T018–T019 (tests) in parallel
- **Phase 6**: T030–T032 (all tests) in parallel; T034–T035 (GitHub + ADO clients) in parallel
- **Phase 7**: T039–T040 (config files) in parallel
- **Phase 8**: T042–T044 (agent skill, CLI entry, MCP config) all in parallel
- **Cross-story**: US4 can start immediately after US1 (independent of US2/US3); US5 likewise

---

## Parallel Example: User Story 4

```bash
# After Phase 2 (Foundational) + Phase 3 (US1) complete:

# Launch all tests in parallel:
Task T030: Contract test for get_repo_activity schema
Task T031: Integration test for GitHub client
Task T032: Integration test for ADO client

# Then auth (required by both clients):
Task T033: Token resolution (env → CLI → Keychain)

# Launch both API clients in parallel:
Task T034: GitHub API client
Task T035: ADO API client

# Then sequential:
Task T036: get_repo_activity tool handler
Task T037: Register tool in server.py
Task T038: Page two rendering
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (calendar column + PDF renderer)
4. **STOP and VALIDATE**: Call `render_pdf` with sample data, verify landscape PDF output
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Calendar + Renderer) → Test independently → **MVP!**
3. Add US2 (Today Tasks) → Test independently → Column 2 populated
4. Add US3 (Tomorrow Tasks) → Test independently → All 3 columns of page 1 complete
5. Add US4 (Repo Activity) → Test independently → Page 2 complete
6. Add US5 (Configuration) → Test independently → User-customisable
7. Polish → Agent skill, docs, security audit
