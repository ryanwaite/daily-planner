# Tasks: Morning Briefing PDF Generator

**Input**: Design documents from `/specs/001-morning-briefing-pdf/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included per constitution requirement ("Every feature branch MUST include tests that exercise the new behaviour before the implementation is considered complete").

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [ ] T001 Create project directory structure with all directories and `__init__.py` files per plan.md (`src/daily_planner/`, `src/daily_planner/tools/`, `src/daily_planner/integrations/`, `src/daily_planner/models/`, `src/daily_planner/pdf/`, `src/daily_planner/config/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `config/`, `.github/agents/`)
- [ ] T002 Initialize UV project — write pyproject.toml with dependencies (mcp, reportlab, httpx, keyring, things.py), dev dependencies (ruff, pytest, pytest-asyncio, respx, pip-audit), ruff config, and run `uv lock` in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, config loading, business day logic, and MCP server scaffold that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [P] Define CalendarEvent dataclass with validation (title non-empty, start < end, all-day flag) in src/daily_planner/models/calendar.py
- [ ] T004 [P] Define Task dataclass with validation (title non-empty, sort_position, optional project/tags) in src/daily_planner/models/task.py
- [ ] T005 [P] Define Repository, ActivityItem, and RepoSummary dataclasses with validation in src/daily_planner/models/repo.py
- [ ] T006 [P] Define Configuration dataclass with sensible defaults (page_one_font_size=9.0, page_two_font_size=8.0, output_path=~/Desktop, repos_file=config/repos.txt) in src/daily_planner/models/config.py
- [ ] T007 Define BriefingData dataclass (date, calendar_events, today_tasks, tomorrow_tasks, repo_summaries, per-section error fields, config) in src/daily_planner/models/__init__.py
- [ ] T008 [P] Implement business day helpers (next_business_day: Fri→Mon; last_business_day: Mon→Fri) in src/daily_planner/business_day.py
- [ ] T009 Implement config loader — parse settings.toml into Configuration, parse repos.txt into list[Repository], handle missing files with defaults or clear errors, validate repo line format and skip invalid entries with stderr warning in src/daily_planner/config/loader.py
- [ ] T010 Implement MCP server entry point with stdio transport, server name "daily-planner", and empty tool registration scaffold in src/daily_planner/server.py
- [ ] T011 [P] Write unit tests for all model dataclasses (validation rules, defaults), business day helpers (Fri→Mon, Mon→Fri, mid-week), and config loader (valid TOML, missing file defaults, missing repos file error, invalid repo line format) in tests/unit/test_models.py, tests/unit/test_business_day.py, tests/unit/test_config_loader.py

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Generate Today's Calendar Column (Priority: P1) 🎯 MVP

**Goal**: Calendar events from Work IQ (passed by agent) render in page one column 1 of the PDF, chronological with all-day events first, date header in "dddd, MMMM D, YYYY" format

**Independent Test**: Call `render_pdf` with sample calendar_events JSON and verify the output PDF has a first column listing events chronologically with time, title, and optional location

### Tests for User Story 1

> **Write tests FIRST — ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Contract test for render_pdf MCP tool schema (input/output shape validation) in tests/contract/test_tool_schemas.py
- [ ] T013 [P] [US1] Integration test for render_pdf — supply sample BriefingData, verify two-page PDF is written with correct filename format and non-zero size in tests/integration/test_render_pdf.py

### Implementation for User Story 1

- [ ] T014 [US1] Implement PDF renderer engine — two-page US Letter (612×792pt) template, page margins, three-column Frame layout for page one, two-column Frame layout for page two, date header per FR-007 in src/daily_planner/pdf/renderer.py
- [ ] T015 [US1] Implement page one calendar column rendering — chronological event list (all-day first), time range + title + optional location, "Calendar data unavailable" error notice fallback, overflow with ellipsis indicator ("… and N more events") in src/daily_planner/pdf/page_one.py
- [ ] T016 [US1] Implement render_pdf tool handler — accept calendar_events, tasks, repo_summaries, output_path; assemble BriefingData; call renderer; write PDF with filename "YYYY-MM-DD dddd.pdf" per FR-007; return pdf_path; target <30s wall time per SC-001 in src/daily_planner/tools/render_pdf.py
- [ ] T017 [US1] Register render_pdf tool with @mcp.tool() decorator in src/daily_planner/server.py

**Checkpoint**: render_pdf produces a two-page PDF with calendar column populated — MVP complete

---

## Phase 4: User Story 2 — Show Today's Things Tasks (Priority: P1)

**Goal**: Today's Things tasks appear in page one column 2, in Things' default sort order with title and optional project/tag context

**Independent Test**: Invoke `get_today_tasks` MCP tool and verify returned JSON contains all tasks due today in sort order; call `render_pdf` with that data and verify column 2 is populated

### Tests for User Story 2

> **Write tests FIRST — ensure they FAIL before implementation**

- [ ] T018 [P] [US2] Contract test for get_today_tasks MCP tool schema in tests/contract/test_tool_schemas.py
- [ ] T019 [P] [US2] Unit test for Things reader — mock things.py library calls, verify list[Task] output and DB-not-found error handling in tests/unit/test_things_reader.py

### Implementation for User Story 2

- [ ] T020 [US2] Implement Things 3 integration — locate DB, read tasks by due date using things.py library, return list[Task] in sort_position order, handle DB-not-found gracefully in src/daily_planner/integrations/things.py
- [ ] T021 [US2] Implement get_today_tasks tool handler — call Things integration with today's date, return tasks JSON or error in src/daily_planner/tools/tasks.py
- [ ] T022 [US2] Register get_today_tasks tool with @mcp.tool() decorator in src/daily_planner/server.py
- [ ] T023 [US2] Implement page one today-tasks column rendering — task list with title/project/tags, "No tasks due today" empty state, "Unavailable" error fallback in src/daily_planner/pdf/page_one.py

**Checkpoint**: get_today_tasks returns Things data; PDF column 2 shows today's tasks

---

## Phase 5: User Story 3 — Show Tomorrow's Tasks and Note Space (Priority: P2)

**Goal**: Tomorrow's Things tasks (next business day) appear in the top of page one column 3; bottom of column 3 is intentionally blank for handwritten notes

**Independent Test**: Invoke `get_tomorrow_tasks` on a Friday and verify returned JSON targets Monday; call `render_pdf` with that data and verify column 3 has tasks at top and blank space below

### Tests for User Story 3

> **Write tests FIRST — ensure they FAIL before implementation**

- [ ] T024 [P] [US3] Contract test for get_tomorrow_tasks MCP tool schema in tests/contract/test_tool_schemas.py
- [ ] T025 [P] [US3] Unit test for next-business-day edge cases (Friday→Monday, Saturday→Monday, Sunday→Monday, mid-week→next day) in tests/unit/test_business_day.py

### Implementation for User Story 3

- [ ] T026 [US3] Extend Things integration with a query-by-target-date method using next_business_day helper in src/daily_planner/integrations/things.py
- [ ] T027 [US3] Implement get_tomorrow_tasks tool handler — compute next business day, call Things integration, return tasks JSON with target_date or error in src/daily_planner/tools/tasks.py
- [ ] T028 [US3] Register get_tomorrow_tasks tool with @mcp.tool() decorator in src/daily_planner/server.py
- [ ] T029 [US3] Implement page one tomorrow-tasks column — tasks at top of column 3, "No tasks due tomorrow" empty state, blank note area in lower portion, error fallback in src/daily_planner/pdf/page_one.py

**Checkpoint**: get_tomorrow_tasks returns next-business-day tasks; PDF column 3 has tasks + note space

---

## Phase 6: User Story 4 — Repository Activity Summary (Priority: P2)

**Goal**: Page two shows a two-column layout of LLM-summarised (or raw fallback) repository activity since the last business day for all configured GitHub and ADO repos

**Independent Test**: Configure repos.txt with at least one GitHub and one ADO repo; invoke `get_repo_activity` and verify structured activity data; call `render_pdf` with agent-provided narrative summaries and verify page two renders in two-column layout

### Tests for User Story 4

> **Write tests FIRST — ensure they FAIL before implementation**

- [ ] T030 [P] [US4] Contract test for get_repo_activity MCP tool schema in tests/contract/test_tool_schemas.py
- [ ] T031 [P] [US4] Integration test for GitHub API client — mock HTTP responses with respx, verify commits/PRs/issues parsing and error handling in tests/integration/test_github_client.py
- [ ] T032 [P] [US4] Integration test for ADO API client — mock HTTP responses with respx, verify commits/PRs/work-items parsing and error handling in tests/integration/test_ado_client.py

### Implementation for User Story 4

- [ ] T033 [US4] Implement OAuth2 device-code flow — initiate device code, poll for token, store access_token/refresh_token/expires_at in macOS Keychain via keyring, handle token refresh (ADO) and re-auth (GitHub) in src/daily_planner/integrations/auth.py
- [ ] T034 [P] [US4] Implement GitHub API client — fetch commits, PRs (opened/merged/closed), and issues since a given date using httpx with configurable timeouts and single retry with exponential backoff per R5; fetch README excerpt for LLM context in src/daily_planner/integrations/github.py
- [ ] T035 [P] [US4] Implement ADO API client — fetch commits, PRs, and work items (via WIQL) since a given date using httpx with configurable timeouts and single retry with exponential backoff per R5; fetch repo description for LLM context in src/daily_planner/integrations/ado.py
- [ ] T036 [US4] Implement get_repo_activity tool handler — load repos from config, compute last_business_day, fetch activity from GitHub/ADO clients per repo, return structured RepoSummary list with per-repo errors for unreachable repos in src/daily_planner/tools/repo_activity.py
- [ ] T037 [US4] Register get_repo_activity tool with @mcp.tool() decorator in src/daily_planner/server.py
- [ ] T038 [US4] Implement page two two-column rendering — LLM narrative per repo (or raw activity list fallback with "Summarisation unavailable" notice), "No recent activity" empty state, per-repo error notices in src/daily_planner/pdf/page_two.py

**Checkpoint**: get_repo_activity fetches from GitHub/ADO; PDF page two shows repo summaries in two-column layout

---

## Phase 7: User Story 5 — Configurable Font Sizes and Repo List (Priority: P3)

**Goal**: Users can customise page-one and page-two font sizes via settings.toml and manage tracked repos via repos.txt; changes take effect on next run without code changes

**Independent Test**: Edit config/settings.toml to change font sizes, run briefing twice with different values, and confirm PDF output reflects the changes

### Implementation for User Story 5

- [ ] T039 [P] [US5] Create default config/settings.toml with [page_one] font_size=9.0, [page_two] font_size=8.0, [output] path=~/Desktop and repos_file=config/repos.txt in config/settings.toml
- [ ] T040 [P] [US5] Create config/repos.txt with documented format (github:owner/repo, ado:org/project/repo) and example entries in config/repos.txt
- [ ] T041 [US5] Wire Configuration.page_one_font_size and page_two_font_size into PDF paragraph styles in src/daily_planner/pdf/renderer.py

**Checkpoint**: Font sizes and repo list are user-configurable via plain-text files

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Agent skill, CLI entry point, documentation, and security validation

- [ ] T042 [P] Create Copilot CLI agent skill file — YAML frontmatter referencing daily-planner and Work IQ MCP servers, orchestration instructions (call Work IQ → get_today_tasks → get_tomorrow_tasks → get_repo_activity → LLM summarize → render_pdf) in .github/agents/morning-briefing.agent.md
- [ ] T043 [P] Add `__main__.py` entry point for direct CLI invocation — parse optional args, run MCP server or single-shot PDF generation, exit code 0 on success / non-zero on failure, errors to stderr in src/daily_planner/__main__.py
- [ ] T044 Update README.md with installation (UV), configuration (settings.toml, repos.txt, Keychain setup), agent skill usage, and direct CLI usage instructions in README.md
- [ ] T045 Run pip-audit against locked dependencies and verify no unresolved critical CVEs per constitution dependency security requirements
- [ ] T046 Run full test suite (`pytest`) and verify all tests pass before merge

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Foundational — creates PDF renderer used by all later stories
- **US2 (Phase 4)**: Depends on Foundational + US1 (extends page_one.py created in US1)
- **US3 (Phase 5)**: Depends on Foundational + US2 (extends Things integration and page_one.py)
- **US4 (Phase 6)**: Depends on Foundational + US1 (needs renderer.py for page_two); **independent of US2/US3**
- **US5 (Phase 7)**: Depends on Foundational + US1 (wires font sizes into renderer.py)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

```
Phase 1 (Setup)
  └─► Phase 2 (Foundational)
        ├─► Phase 3 (US1: Calendar) ──► Phase 4 (US2: Today Tasks) ──► Phase 5 (US3: Tomorrow Tasks)
        │         │
        │         ├─► Phase 6 (US4: Repo Activity)  [parallel with US2/US3]
        │         └─► Phase 7 (US5: Configuration)   [parallel with US2-US4]
        └─► Phase 8 (Polish) [after all stories]
```

### Within Each User Story

- Tests FIRST — write and verify they FAIL before implementation
- Models/integrations before tool handlers
- Tool handlers before server registration
- PDF rendering can parallel with tool implementation (different files)
- Story complete before dependent stories begin

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T003, T004, T005, T006 — all model files, no interdependency
- T008 — business day helpers, standalone

**Within Phase 6 (US4)**:
- T034 (GitHub client) and T035 (ADO client) — after T033 (auth), different files

**Within Phase 7 (US5)**:
- T039 (settings.toml) and T040 (repos.txt) — independent config files

**Within Phase 8 (Polish)**:
- T042 (agent skill) and T043 (__main__.py) — independent files

**Cross-Story Parallelism**:
- US4 (Phase 6) can start immediately after US1 (Phase 3) — does not depend on US2 or US3
- US5 (Phase 7) can start immediately after US1 (Phase 3) — does not depend on US2-US4

---

## Parallel Example: User Story 4

```bash
# After Phase 2 (Foundational) + Phase 3 (US1) complete:

# These can run in parallel — both depend only on auth.py (T033)
Task T034: GitHub client    ─────────────────►
Task T035: ADO client       ─────────────────►

# Then sequential:
Task T036: get_repo_activity tool handler (depends on T034, T035) ──►
Task T037: Register tool in server.py ──►
Task T038: Page two rendering ──►
```

---

## Implementation Strategy

### MVP Scope (Recommended First Milestone)

**Phases 1–3 (Setup + Foundational + US1)**: Delivers a working `render_pdf` tool that produces a two-page PDF with calendar data. This validates the core PDF pipeline end-to-end.

### Incremental Delivery

1. **MVP**: Phases 1–3 → PDF with calendar column
2. **+Tasks**: Phase 4 → add today's Things tasks
3. **+Tomorrow**: Phase 5 → add tomorrow's tasks + note space
4. **+Repos**: Phase 6 → add repository activity on page two
5. **+Config**: Phase 7 → user-configurable font sizes and repo list
6. **+Polish**: Phase 8 → agent skill, CLI entry point, docs, security audit
