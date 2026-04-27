# Tasks: Markdown Briefing Overhaul

**Input**: Design documents from `/specs/005-markdown-briefing-overhaul/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Remove PDF pipeline, update dependencies, simplify configuration

- [X] T001 Remove `reportlab>=4.1` from dependencies in pyproject.toml
- [X] T002 [P] Delete src/daily_planner/pdf/__init__.py, src/daily_planner/pdf/renderer.py, src/daily_planner/pdf/page_one.py, src/daily_planner/pdf/page_two.py
- [X] T003 [P] Delete src/daily_planner/tools/render_pdf.py
- [X] T004 [P] Delete tests/integration/test_render_pdf.py
- [X] T005 Remove `page_one_font_size` and `page_two_font_size` fields from Configuration dataclass in src/daily_planner/models/config.py, keeping only `output_path` and `repos_file`
- [X] T006 Remove `[page_one]` and `[page_two]` sections from config/settings.toml and update comment to reference markdown instead of PDF
- [X] T007 Update `load_configuration()` in src/daily_planner/config/loader.py to remove `page_one`/`page_two` dict lookups and only parse `[output]` section
- [X] T008 Run `uv sync` to update lock file after dependency removal

**Checkpoint**: PDF pipeline fully removed. Project compiles and lints (minus broken imports in server.py which Phase 2 fixes).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: New model, markdown renderer, and tool handler that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Add `ActionSuggestion` dataclass to src/daily_planner/models/task.py with `task_title: str`, `suggestion: str`, `__post_init__` validation, and `from_dict` classmethod per data-model.md
- [X] T010 Add `action_suggestions: list[ActionSuggestion]` field to `BriefingData` in src/daily_planner/models/__init__.py and update docstring from "render_pdf" to "render_markdown"; add `ActionSuggestion` to `__all__`
- [X] T011 Create src/daily_planner/markdown/__init__.py (empty)
- [X] T012 Create src/daily_planner/markdown/renderer.py with `render_briefing_markdown(briefing: BriefingData) -> Path` function that builds the full markdown string and writes to disk using f-string concatenation per research.md R1
- [X] T013 Create src/daily_planner/tools/render_markdown.py with async `render_markdown()` handler that parses input dicts, assembles BriefingData (including ActionSuggestion parsing), validates output path, calls markdown renderer, and returns JSON `{"markdown_path": ...}` per contracts/mcp-tools.md
- [X] T014 Update src/daily_planner/server.py: replace `render_pdf` tool registration with `render_markdown` tool registration calling the new handler, add `action_suggestions` parameter, update docstring

**Checkpoint**: Foundation ready — `render_markdown` MCP tool is callable and produces a basic markdown file. User story implementation can now begin.

---

## Phase 3: User Story 1 — Markdown Output Instead of PDF (Priority: P1) 🎯 MVP

**Goal**: The briefing produces a well-structured markdown file with all sections (Calendar Events, Today Tasks, Tomorrow Tasks, Repository Activity)

**Independent Test**: Call `render_markdown` with sample data and confirm a `.md` file is produced with all expected section headings

### Implementation for User Story 1

- [X] T015 [US1] Implement calendar events section in markdown renderer: `## Calendar Events` heading with bullet list of events (time range + title), or error message if `calendar_error` is set, in src/daily_planner/markdown/renderer.py
- [X] T016 [US1] Implement today tasks section in markdown renderer: `## Today Tasks` heading with bullet list of task titles, or error message if `today_error` is set, in src/daily_planner/markdown/renderer.py
- [X] T017 [US1] Implement tomorrow tasks section in markdown renderer: `## Tomorrow Tasks` heading with bullet list of task titles, or error message if `tomorrow_error` is set, in src/daily_planner/markdown/renderer.py
- [X] T018 [US1] Implement repository activity section in markdown renderer: `## Repository Activity` heading with `### owner/name` subheadings and narrative text per repo, or error message per repo, in src/daily_planner/markdown/renderer.py
- [X] T019 [US1] Implement markdown file header: `# Morning Briefing — dddd, MMMM D, YYYY` date heading per constitution date format, in src/daily_planner/markdown/renderer.py
- [X] T020 [US1] Implement file writing: output to `morning-briefing-YYYY-MM-DD.md` in configured directory, create directory if missing (`mkdir(parents=True, exist_ok=True)`), overwrite silently, in src/daily_planner/markdown/renderer.py

**Checkpoint**: User Story 1 complete — a valid markdown file with all 4 sections is produced.

---

## Phase 4: User Story 2 — Configurable Output Path (Priority: P1)

**Goal**: The output directory is read from `config/settings.toml` and the path is validated

**Independent Test**: Change `path` in settings.toml, run render, confirm file appears in new directory

### Implementation for User Story 2

- [X] T021 [US2] Verify `load_configuration()` in src/daily_planner/config/loader.py correctly reads `output.path` and `output.repos_file` from settings.toml after the Phase 1 simplification (T007) — fix if needed
- [X] T022 [US2] Verify output path validation in src/daily_planner/tools/render_markdown.py: `_validate_output_path()` ensures path resolves within `Path.home()`, raises ValueError otherwise — port from render_pdf.py logic
- [X] T023 [US2] Verify the markdown renderer in src/daily_planner/markdown/renderer.py uses `briefing.config.resolved_output_path` for the output directory and creates it if missing

**Checkpoint**: User Story 2 complete — output path is configurable via settings.toml and validated.

---

## Phase 5: User Story 3 — Tasks Grouped by Things Area (Priority: P2)

**Goal**: Task sections show tasks organized under Area headings, with "No Area" tasks first

**Independent Test**: Pass tasks with mixed areas (some null, some named) to `render_markdown` and confirm grouped output

### Implementation for User Story 3

- [X] T024 [P] [US3] Add `area` and `area_created` fields to task JSON output in `get_today_tasks()` in src/daily_planner/tools/tasks.py — add `"area": t.area, "area_created": t.area_created.isoformat() if t.area_created else None` to each task dict
- [X] T025 [P] [US3] Add `area` and `area_created` fields to task JSON output in `get_tomorrow_tasks()` in src/daily_planner/tools/tasks.py — add `"area": t.area, "area_created": t.area_created.isoformat() if t.area_created else None` to each task dict
- [X] T026 [US3] Implement `_group_tasks_by_area(tasks: list[Task]) -> list[tuple[str, list[Task]]]` helper in src/daily_planner/markdown/renderer.py that groups tasks by `area` field, places null-area tasks under "No Area" first, then sorts remaining Area groups by `area_created` date (oldest first); fall back to alphabetical order when creation date is unavailable
- [X] T026a [US3] Update `_build_metadata_maps()` in src/daily_planner/integrations/things.py to also fetch `creationDate` from `TMArea` table and return an area_created_map (area_title -> date); populate `Task.area_created` in `get_tasks_for_date()`
- [X] T026b [US3] Add `area_created: date | None = None` field to Task dataclass in src/daily_planner/models/task.py and update `from_dict()` to parse it from ISO string if present
- [X] T027 [US3] Update today tasks section in src/daily_planner/markdown/renderer.py to use `_group_tasks_by_area()` and render each group with an `### AreaName` subheading followed by task bullet list
- [X] T028 [US3] Update tomorrow tasks section in src/daily_planner/markdown/renderer.py to use `_group_tasks_by_area()` with the same grouped rendering

**Checkpoint**: User Story 3 complete — tasks are grouped by Area with unassigned tasks first.

---

## Phase 6: User Story 4 — AI Action Suggestions for Unassigned Tasks (Priority: P2)

**Goal**: Briefing includes an "Action Suggestions" section with up to 5 AI-generated suggestions for unassigned tasks

**Independent Test**: Pass `action_suggestions` list to `render_markdown` and confirm the section appears between tasks and repo activity; pass empty/null and confirm section is omitted

### Implementation for User Story 4

- [X] T029 [US4] Implement action suggestions section in markdown renderer: `## Action Suggestions` heading with blockquote per suggestion (`> **task_title**: suggestion`), omit section entirely if `action_suggestions` is empty, in src/daily_planner/markdown/renderer.py
- [X] T030 [US4] Update section ordering in src/daily_planner/markdown/renderer.py to place Action Suggestions between Tomorrow Tasks and Repository Activity per FR-005
- [X] T031 [US4] Update `.github/agents/morning-briefing.agent.md`: add Step 5.5 — "Generate Action Suggestions" instructing the agent to filter today_tasks for null-area items, randomly select up to 5, generate a 1–3 sentence actionable suggestion for each, and store as `action_suggestions` list
- [X] T032 [US4] Update `.github/agents/morning-briefing.agent.md` Step 6: change tool call from `render_pdf` to `render_markdown`, add `action_suggestions` parameter to the call

**Checkpoint**: User Story 4 complete — action suggestions section renders when unassigned tasks exist and is omitted otherwise.

---

## Phase 7: User Story 5 — Improved Repository Report Formatting (Priority: P3)

**Goal**: Repository narratives have visual separation between major themes of work

**Independent Test**: Pass a narrative with multiple themes to `render_markdown` and confirm blank lines separate themes in output

### Implementation for User Story 5

- [X] T033 [US5] Update `.github/agents/morning-briefing.agent.md` Step 5 narrative writing instructions: add explicit instruction to separate each numbered theme section (Themes of work, Key contributors, Progress signals, Risk items, Connection to project direction) with a blank line between them
- [X] T034 [US5] Verify the markdown renderer in src/daily_planner/markdown/renderer.py preserves blank lines within narrative text when rendering the Repository Activity section — narratives are passed as plain strings and should be inserted as-is

**Checkpoint**: User Story 5 complete — repo narratives have clear visual separation between themes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Update tests, documentation, and validate end-to-end

- [X] T035 [P] Update tests/unit/test_models.py: update Configuration tests to remove font_size assertions, add ActionSuggestion validation tests (empty title, empty suggestion, from_dict)
- [X] T036 [P] Update tests/unit/test_config_loader.py: remove font_size assertions from load_configuration tests, verify only output_path and repos_file are loaded
- [X] T037 [P] Create tests/integration/test_render_markdown.py: test markdown file creation (file exists, correct filename format), test all sections present in output, test task grouping by area, test Area group sort order (by creation date, alphabetical fallback), test action suggestions section present/omitted, test output path validation, test non-writable directory raises clear error
- [X] T038 [P] Update tests/contract/test_tool_schemas.py: replace render_pdf schema tests with render_markdown schema tests (new parameter `action_suggestions`, response field `markdown_path` instead of `pdf_path`, no `pages` field)
- [X] T039 Update `.github/agents/morning-briefing.agent.md` description frontmatter: change from "PDF" to "markdown file" and update Step 7 to report markdown path
- [X] T040 Update `.github/copilot-instructions.md` and README.md: replace PDF references with markdown references where applicable
- [X] T041 Update pyproject.toml project description from "two-page PDF morning briefing" to "markdown morning briefing"
- [X] T042 Run `uv run ruff check src/ tests/` and fix any lint errors
- [X] T043 Run `uv run pytest` and verify all tests pass
- [X] T044 Run quickstart.md validation: start MCP server with `uv run python -m daily_planner` and verify it initializes without import errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T005, T007 specifically — Configuration model and loader must be simplified before new tool handler references them)
- **US1 (Phase 3)**: Depends on Phase 2 (T012 renderer must exist)
- **US2 (Phase 4)**: Depends on Phase 2 (T013 tool handler must exist). Can run in parallel with US1.
- **US3 (Phase 5)**: Depends on Phase 3 (T016/T017 task sections must exist to add grouping). T024/T025 can start after Phase 1.
- **US4 (Phase 6)**: Depends on Phase 3 (T012 renderer sections must exist). Agent updates (T031/T032) can start after Phase 1.
- **US5 (Phase 7)**: Depends on Phase 3 (T018 repo section must exist). Agent update (T033) can start after Phase 1.
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Foundational only — no dependency on other stories
- **US2 (P1)**: Foundational only — can run in parallel with US1
- **US3 (P2)**: Depends on US1 task sections being implemented (T016/T017)
- **US4 (P2)**: Depends on US1 renderer sections existing. Agent-side tasks (T031/T032) are independent.
- **US5 (P3)**: Depends on US1 repo section being implemented (T018). Agent-side task (T033) is independent.

### Parallel Opportunities

- **Phase 1**: T002, T003, T004 can all run in parallel (deleting independent files)
- **Phase 2**: T009 and T011 can run in parallel (different files)
- **Phase 3**: T015–T018 touch the same file but are independent sections — can be done as one pass
- **Phase 5**: T024 and T025 can run in parallel (different functions in same file)
- **Phase 8**: T035, T036, T037, T038 can all run in parallel (different test files)

---

## Parallel Example: User Story 3

```
                T024 (add area to get_today_tasks)
               /                                    \
Phase 2 done →                                       → T026 (group helper) → T027, T028 (update sections)
               \                                    /
                T025 (add area to get_tomorrow_tasks)
```

---

## Implementation Strategy

### MVP Scope

User Story 1 (Phase 3) alone delivers a working markdown briefing that
replaces the PDF. This is the minimum viable increment — all other
stories are enhancements on top.

### Incremental Delivery

1. **Phases 1–3 (MVP)**: Working markdown output with flat task lists and repo narratives → immediately usable
2. **Phase 4 (US2)**: Output path configuration → user controls file location
3. **Phase 5 (US3)**: Task grouping by Area → improved scannability
4. **Phase 6 (US4)**: Action suggestions → AI-powered productivity coaching
5. **Phase 7 (US5)**: Repo formatting → polish
6. **Phase 8 (Polish)**: Tests, docs, validation → production-ready
