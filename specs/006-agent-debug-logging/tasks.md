# Tasks: Agent Debug Logging

**Feature**: 006-agent-debug-logging  
**Input**: Design documents from `/specs/006-agent-debug-logging/` (plan.md, spec.md, research.md, data-model.md)  
**Status**: Ready for implementation  
**Prerequisites**: None — can start immediately (no external feature dependencies)

**Tests**: Included throughout — pytest unit tests for logging module, integration tests for end-to-end debug runs, and isolated stdout verification tests per spec requirement FR-005.

**Organization**: Tasks grouped by user story (US1, US2, US3) to enable independent, parallel implementation and testing. Setup and Foundational phases must complete before user stories begin. User Story 3 can run in parallel with US1 and US2 (isolation tests).

---

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[ ]**: Unchecked — task not yet started
- **[ID]**: Task identifier (T001, T002, etc.) — sequential execution order
- **[P]**: Can run in parallel (different files, no internal dependencies)
- **[Story]**: User story this task belongs to (US1, US2, US3)
- File paths included in all descriptions for clarity

---

## Phase 1: Setup

**Goal**: Create module skeletons and test file stubs. No business logic yet.

- [ ] T001 Create `src/daily_planner/logging.py` with `from __future__ import annotations`, module docstring, and import statements (`logging`, `json`, `sys`, `os`, `pathlib`)
- [ ] T002 [P] Create `tests/unit/test_logging.py` with `from __future__ import annotations`, module docstring, `import pytest`, and skeleton comment for logging tests
- [ ] T003 [P] Create `tests/integration/test_debug_logging.py` with `from __future__ import annotations`, module docstring, `import pytest`, and skeleton comment for integration tests

**Checkpoint**: Project structure ready. Three files created, no logic yet.

---

## Phase 2: Foundational

**Goal**: Implement core logging infrastructure (formatter, truncation, setup) that ALL user stories depend on. No instrumentation yet.

**CRITICAL GATE**: Phase 2 MUST complete and pass all tests before any user story instrumentation begins.

### Truncation & Serialization Helpers

- [ ] T004 Implement `_truncate_dict(data: dict, max_size: int = 5000) -> dict` function in `src/daily_planner/logging.py`. Recursively walks dicts and lists, truncates string values exceeding `max_size` chars, appends `"...[truncated]"` suffix, returns new dict without mutating input. Handle nested structures and non-string types unchanged.

- [ ] T005 Implement `_json_default(obj)` function in `src/daily_planner/logging.py` to handle non-JSON-serializable types: `datetime` objects → `.isoformat()`, `Path` objects → `str()`, `date` objects → `.isoformat()`, fallback `str(obj)` for unknown types.

### JSON Formatter

- [ ] T006 Implement `class JsonlFormatter(logging.Formatter)` in `src/daily_planner/logging.py` with `format(record: logging.LogRecord) -> str` method that:
  - Extracts fields from `record` and `record.__dict__`: `timestamp` (ISO 8601 from record creation time), `level` (record.levelname), `operation` (from `record.operation` extra field), `message` (record.getMessage()), `direction` (from `record.direction` extra field), `data` (from `record.data` extra field, truncated via `_truncate_dict`)
  - Handles exception info: if `record.exc_info`, call `self.formatException(record.exc_info)` and include as `"traceback"` key in output
  - Builds a dict, serializes via `json.dumps(entry, default=_json_default)`, returns as single line
  - Optional fields (`direction`, `data`, `traceback`, `duration_ms`) omitted from JSON if not present in record

### Setup & Initialization

- [ ] T007 Implement `setup_debug_logging(output_dir: str | pathlib.Path) -> logging.Logger` function in `src/daily_planner/logging.py` that:
  - Checks `DAILY_PLANNER_DEBUG` environment variable (accept any non-empty value as "enabled")
  - If NOT enabled: return logger with `logging.NullHandler()` (all log calls are no-ops)
  - If enabled:
    - Create named logger `"daily_planner.debug"` with level `logging.DEBUG`
    - Set `propagate=False` (critical for stdout safety)
    - Check if `output_dir` is writable (try opening a temp file); if not writable, emit warning to stderr (e.g., "Warning: Could not create debug log file at [path]. Debug logging disabled.") and return logger with `NullHandler`
    - Generate log filename: `debug_{date}_{time}_{pid}.jsonl` where date is YYYY-MM-DD, time is HHMMSS, pid is process ID (to prevent collisions on rapid successive runs)
    - Create `FileHandler` pointing to `output_dir / filename` with `mode='a'` and `encoding='utf-8'`
    - Attach `JsonlFormatter` to the handler
    - Attach handler to logger
    - Return the logger

- [ ] T008 Add module-level global `_debug_logger: logging.Logger | None = None` to `src/daily_planner/logging.py` (populated by setup function; exported for use in tools/integrations via `logging.getLogger("daily_planner.debug")`)

### Unit Tests for Foundational Phase

- [ ] T009 Add unit tests for `_truncate_dict` in `tests/unit/test_logging.py`:
  - Test: 5000-char string NOT truncated
  - Test: 5001-char string IS truncated with `"...[truncated]"` suffix
  - Test: nested dict with long string in value is truncated
  - Test: list with long string element is truncated
  - Test: non-string values (int, bool, None) passed through unchanged
  - Test: input dict not mutated (returns new dict)
  - Test: mixed types in nested structures handled correctly

- [ ] T010 Add unit tests for `JsonlFormatter.format()` in `tests/unit/test_logging.py`:
  - Test: output is valid single-line JSON (can be parsed with `json.loads`)
  - Test: required fields present: `timestamp`, `level`, `operation`, `message`
  - Test: optional fields omitted when not in extra (no null keys)
  - Test: `exc_info=True` produces `"traceback"` key with exception details
  - Test: `data` field is truncated via `_truncate_dict`
  - Test: `datetime` objects in data handled by `_json_default`
  - Test: `Path` objects in data converted to strings

- [ ] T011 Add unit tests for `setup_debug_logging` in `tests/unit/test_logging.py`:
  - Test: with `DAILY_PLANNER_DEBUG=1` set, returns logger with `FileHandler`
  - Test: with `DAILY_PLANNER_DEBUG` unset, returns logger with `NullHandler`
  - Test: log file created with correct name pattern (matches `debug_YYYY-MM-DD_HHMMSS_\d+.jsonl`)
  - Test: unwritable output dir emits warning to stderr and returns logger with `NullHandler`
  - Test: returned logger has `propagate=False`
  - Test: returned logger's `propagate=False` survives multiple calls (not interfered with by global config)

- [ ] T012 Run `uv run pytest tests/unit/test_logging.py -v` and verify all tests pass before moving to next phase

**Checkpoint**: Logging module complete and fully unit-tested. Core infrastructure ready for instrumentation.

---

## Phase 3: User Story 1 — Enable Debug Logging for a Briefing Run (P1)

**Goal**: Wire up debug logging so that `DAILY_PLANNER_DEBUG=1` produces a JSONL log file with entries for every tool invocation and external API call.

**Independent Test Criteria**: 
- Enable debug flag, run a full briefing, verify:
  - Log file exists in output directory
  - Log file contains valid JSONL (each line parses as JSON)
  - At least one entry per MCP tool call
  - At least one entry per external API call (GitHub, ADO, Things)

### Entry Point & Config Setup

- [ ] T013 [US1] Modify `src/daily_planner/__main__.py` to call `setup_debug_logging(output_dir)` immediately after resolving config (before `serve()` call). Import `setup_debug_logging` from `daily_planner.logging`. Pass the resolved output path from config. Store returned logger in a module variable (not used here, but imported elsewhere).

- [ ] T014 [US1] Verify `src/daily_planner/config/loader.py` exposes a function or property that returns the resolved absolute output path from `settings.toml` `[output].path`. If not exposed, add a getter function `get_resolved_output_path() -> pathlib.Path`.

### MCP Tool Instrumentation

- [ ] T015 [US1] Modify `src/daily_planner/server.py` MCP tool wrappers to add debug logging:
  - At tool start: `logger.debug(..., extra={"operation": "<tool_name>", "direction": "request", "data": {...input params...}})`
  - At tool end: `logger.debug(..., extra={"operation": "<tool_name>", "direction": "response", "data": {...result...}, "duration_ms": ...})`
  - Import logger via `logging.getLogger("daily_planner.debug")`
  - Apply to all three tools: `get_today_tasks`, `get_tomorrow_tasks`, `get_repo_activity`, `render_markdown`

### External Integration Instrumentation

- [ ] T016 [P] [US1] Modify `src/daily_planner/integrations/github.py` to add debug log calls:
  - Before each HTTP request: `logger.debug(..., extra={"operation": "github.<method>", "direction": "request", "data": {"url": ..., "params": ...}})`
  - After successful response: `logger.debug(..., extra={"operation": "github.<method>", "direction": "response", "data": {"status": ..., "result_count": ...}, "duration_ms": ...})`
  - Import logger via `logging.getLogger("daily_planner.debug")`

- [ ] T017 [P] [US1] Modify `src/daily_planner/integrations/ado.py` to add debug log calls (same pattern as GitHub):
  - Before each HTTP request with `operation`, `direction`, `data`
  - After response with status, result count, duration
  - Import logger via `logging.getLogger("daily_planner.debug")`

- [ ] T018 [P] [US1] Modify `src/daily_planner/integrations/things.py` to add debug log calls for database reads:
  - Before/after query execution: operation name (e.g., `"things.get_tasks"`), direction, data (query context, result count)
  - Import logger via `logging.getLogger("daily_planner.debug")`

### Tool Handler Instrumentation

- [ ] T019 [P] [US1] Modify `src/daily_planner/tools/repo_activity.py` to add debug log calls:
  - At start of `get_repo_activity`: log request with repo list
  - At end: log response with repo count and summary
  - Log any per-repo API calls (delegation to GitHub/ADO)

- [ ] T020 [P] [US1] Modify `src/daily_planner/tools/tasks.py` to add debug log calls:
  - At start/end of `get_today_tasks` and `get_tomorrow_tasks`: operation name, direction, data (task count, areas)

- [ ] T021 [US1] Modify `src/daily_planner/tools/render_markdown.py` to add debug log calls:
  - At start: log input briefing data (operation=`"render_markdown"`, direction=`"request"`)
  - At end: log output path and file size (direction=`"response"`, level=`"INFO"` for final output)

- [ ] T022 [US1] Modify `src/daily_planner/markdown/renderer.py` to add debug log calls for data transformation steps:
  - Before/after task grouping by area: log operation, data (task count before/after)
  - Final render: log output file path and size
  - Import logger via `logging.getLogger("daily_planner.debug")`

### Integration Tests for User Story 1

- [ ] T023 [US1] Add integration test in `tests/integration/test_debug_logging.py`:
  - Test name: `test_debug_logging_enabled_creates_file`
  - Set `DAILY_PLANNER_DEBUG=1` environment variable
  - Call `setup_debug_logging(tmp_dir)`
  - Verify log file is created with correct name pattern in `tmp_dir`
  - Write several test log entries
  - Verify file contains valid JSONL (each line parses as JSON with all required fields)

- [ ] T024 [US1] Add integration test in `tests/integration/test_debug_logging.py`:
  - Test name: `test_debug_logging_disabled_no_file`
  - Unset `DAILY_PLANNER_DEBUG` environment variable
  - Call `setup_debug_logging(tmp_dir)`
  - Verify NO log file is created in `tmp_dir`
  - Verify logger uses `NullHandler` (log calls are no-ops)

- [ ] T025 [US1] Add integration test in `tests/integration/test_debug_logging.py`:
  - Test name: `test_debug_log_contains_tool_entries`
  - Enable debug, run a mock briefing (call tools directly with test data)
  - Verify log file contains entries for each tool invocation
  - Verify entries have `"operation"` field matching tool name

- [ ] T026 [US1] Run `uv run pytest tests/integration/test_debug_logging.py::test_debug_logging_enabled_creates_file -v` and verify pass

**Checkpoint**: User Story 1 complete. Debug logging produces JSONL log files with tool and API entries. MVP is now testable.

---

## Phase 4: User Story 2 — Review Log File to Diagnose a Specific Failure (P2)

**Goal**: Enhance log entries with error context (tracebacks, input parameters, operation details) so users can diagnose failures by reading the log alone.

**Independent Test Criteria**: 
- Trigger a known failure scenario (e.g., invalid repo config, API error)
- Enable debug logging
- Verify log file contains operation name, input params, error message, and traceback
- Confirm a user can identify the root cause without additional tools

### Error Logging in Integrations

- [ ] T027 [P] [US2] Modify `src/daily_planner/integrations/github.py` exception handlers to add error-level debug logs:
  - In each `except` block: `logger.error(..., exc_info=True, extra={"operation": "...", "data": {...input...}})`
  - Include request parameters, error type, error message
  - `exc_info=True` ensures traceback is included in `"traceback"` field

- [ ] T028 [P] [US2] Modify `src/daily_planner/integrations/ado.py` exception handlers to add error-level debug logs (same pattern as GitHub)

- [ ] T029 [P] [US2] Modify `src/daily_planner/integrations/things.py` exception handlers to add error-level debug logs

### Error Logging in Tool Handlers

- [ ] T030 [P] [US2] Modify `src/daily_planner/tools/repo_activity.py` exception handlers to add error-level debug logs:
  - Log operation name, input repos, error details

- [ ] T031 [P] [US2] Modify `src/daily_planner/tools/tasks.py` exception handlers to add error-level debug logs:
  - Log operation name, error details for both `get_today_tasks` and `get_tomorrow_tasks`

- [ ] T032 [US2] Modify `src/daily_planner/tools/render_markdown.py` exception handlers to add error-level debug logs

### Integration Tests for User Story 2

- [ ] T033 [US2] Add integration test in `tests/integration/test_debug_logging.py`:
  - Test name: `test_debug_log_error_entries`
  - Enable debug logging
  - Simulate an error (e.g., mock an API to return 500)
  - Call tool handler, catch exception
  - Verify log file contains ERROR entry with `"traceback"` field and full error context

- [ ] T034 [US2] Add integration test in `tests/integration/test_debug_logging.py`:
  - Test name: `test_debug_log_duration_timing`
  - Enable debug logging
  - Perform a timed operation (e.g., sleep for 100ms, then log with duration)
  - Verify log entry contains `"duration_ms"` field with reasonable value (≥100)

- [ ] T035 [US2] Run `uv run pytest tests/integration/test_debug_logging.py::test_debug_log_error_entries -v` and verify pass

**Checkpoint**: User Story 2 complete. Log entries now contain diagnostic detail (errors, tracebacks, durations) sufficient for root cause analysis.

---

## Phase 5: User Story 3 — Debug Mode Does Not Interfere with Normal Output (P2)

**Goal**: Verify that debug logging never pollutes stdout (critical for MCP protocol safety) and that markdown output is unaffected by debug mode.

**Independent Test Criteria**:
- Debug enabled, run full briefing
- Verify: stdout contains no debug content, markdown output identical to non-debug run, no stderr pollution (except write-failure warning)

### Implementation for User Story 3

- [ ] T036 [US3] Add defensive code comment in `src/daily_planner/logging.py` `setup_debug_logging` function highlighting that `propagate=False` is **critical** for MCP protocol safety: "Do NOT remove this — stdout is used for MCP stdio transport. Any debug content on stdout breaks the protocol."

- [ ] T037 [P] [US3] Add unit test in `tests/unit/test_logging.py`:
  - Test name: `test_logger_propagate_is_false`
  - Verify logger returned by `setup_debug_logging` has `propagate=False`
  - Verify this property survives logger re-fetch via `logging.getLogger("daily_planner.debug")`

- [ ] T038 [P] [US3] Add unit test in `tests/unit/test_logging.py`:
  - Test name: `test_logger_has_no_stream_handler`
  - Verify logger returned by `setup_debug_logging` has handlers list containing only `FileHandler` (no `StreamHandler`, no `NullHandler` mixins)

- [ ] T039 [P] [US3] Add unit test in `tests/unit/test_logging.py`:
  - Test name: `test_debug_output_not_to_stdout`
  - Set up debug logging to a temp file
  - Write several log entries
  - Capture stdout during logging
  - Verify stdout is empty (no debug content)

- [ ] T040 [P] [US3] Add unit test in `tests/unit/test_logging.py`:
  - Test name: `test_stderr_only_for_write_failure`
  - Attempt to set up debug logging to an unwritable directory
  - Capture stderr
  - Verify warning message appears on stderr
  - Clear env var and try again with writable dir; verify no warning on stderr

- [ ] T041 [US3] Add integration test in `tests/integration/test_debug_logging.py`:
  - Test name: `test_debug_does_not_affect_markdown_output`
  - Run briefing generation twice: once with `DAILY_PLANNER_DEBUG=1`, once without
  - Verify resulting markdown files are byte-for-byte identical
  - Verify only non-debug run is missing the log file

- [ ] T042 [US3] Run `uv run pytest tests/unit/test_logging.py -v -k "stdout or stderr or propagate or stream_handler"` and verify all US3 unit tests pass

**Checkpoint**: User Story 3 complete. Isolation guarantees verified. MCP protocol safety confirmed.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Documentation, linting, final validation, readiness for release.

- [ ] T043 [P] Update `README.md` to add section: "## Debug Logging"
  - Document `DAILY_PLANNER_DEBUG=1` environment variable
  - Show example: `export DAILY_PLANNER_DEBUG=1 && uv run python -m daily_planner`
  - Explain log file location and naming convention
  - Show example JSONL output and how to read with `jq`, `grep`, `cat`

- [ ] T044 [P] Update `.github/copilot-instructions.md` Architecture > Layer structure section:
  - Add entry for `logging.py` module: "Debug logging infrastructure for structured JSONL logging when `DAILY_PLANNER_DEBUG` env var is set."

- [ ] T045 [P] Verify `src/daily_planner/` has `from __future__ import annotations` at the top of all Python files (should already be in place from convention)

- [ ] T046 Run `uv run ruff check src/ tests/` and fix any lint violations introduced by this feature (E, F, I, N, W, UP rules)

- [ ] T047 Run `uv run pytest tests/ -v` to verify all tests pass (existing + new)

- [ ] T048 Manual validation: Set `export DAILY_PLANNER_DEBUG=1`, run `uv run python -m daily_planner`, verify:
  - `.jsonl` debug log file is created in configured output directory
  - File contains valid JSONL (can be parsed with `jq`, `cat`, `grep`)
  - Markdown briefing file is created normally and is readable
  - No debug content appears on stdout or stderr (except write-failure warning if applicable)

**Checkpoint**: Feature complete, tested, documented, and ready for integration.

---

## Summary Table

| Phase | ID Range | Goal | Blocking? | Est. Effort |
|-------|----------|------|-----------|------------|
| 1 Setup | T001–T003 | Module skeletons | ❌ No | ~15 min |
| 2 Foundational | T004–T012 | Core logging infrastructure | ✅ YES — GATE | ~90 min |
| 3 US1 (P1) | T013–T026 | Debug flag produces log files | ❌ Depends on Phase 2 | ~120 min |
| 4 US2 (P2) | T027–T035 | Error entries with diagnostics | ❌ Depends on Phase 3 | ~60 min |
| 5 US3 (P2) | T036–T042 | Isolation + MCP safety | ❌ Depends on Phase 2 | ~75 min |
| 6 Polish | T043–T048 | Docs, lint, final validation | ❌ Depends on all phases | ~45 min |

**Total Effort**: ~405 minutes (~6.75 hours)

---

## Parallel Execution Paths

### Fast Path (User Story 1 MVP only)

```
Phase 1 (T001–T003) 
  ↓ [Wait]
Phase 2 (T004–T012) 
  ↓ [Wait]
US1 Implementation (T013–T022)
  ├── T014 [P] — config setup
  ├── T015 [P] — server.py instrumentation
  ├── [GitHub, ADO, Things instrumentation] T016 | T017 | T018
  ├── [Tool instrumentation] T019 | T020 | T021 | T022
  └── US1 Tests (T023–T026)

Deployable MVP: Debug logging captures and writes JSONL log file.
```

### Full Feature Path

```
Phase 1 (T001–T003)
  ↓ [Wait]
Phase 2 (T004–T012)
  ↓ [Wait]
US1 (T013–T026) + US3 unit tests (T037–T042) [Can run in parallel]
  ├── US1: T013 → T014 → [T015, T016, T017, T018, T019, T020, T021, T022] → T023–T026
  └── US3: T036 → [T037, T038, T039, T040] → T041 → T042
  ↓ [Wait for both]
US2 (T027–T035)
  ├── [Integration errors] T027 | T028 | T029
  ├── [Tool errors] T030 | T031 | T032
  └── US2 Tests (T033–T035)
  ↓ [Wait]
Polish (T043–T048)

Full feature released with complete test coverage, docs, and isolation guarantees.
```

---

## Success Criteria (from spec)

- ✅ SC-001: User can enable debug logging and receive log file 100% of time (if output dir writable) — Achieved by Phase 3
- ✅ SC-002: Log contains ≥1 entry per tool call, ≥1 per API call — Achieved by Phase 3 + instrumentation
- ✅ SC-003: User can diagnose failure by reading log alone — Achieved by Phase 4 (error entries + context)
- ✅ SC-004: Markdown output identical with/without debug — Verified in Phase 5 (T041)
- ✅ SC-005: No debug content on stdout — Verified in Phase 5 (T039, T042)

### Implementation for User Story 1

- [x] T011 [US1] Modify `src/daily_planner/__main__.py` to call `setup_debug_logging(output_dir)` before `serve()`, passing the resolved output path from config. Import `setup_debug_logging` from `daily_planner.logging`. Store returned logger in module-level variable.
- [x] T012 [US1] Modify `src/daily_planner/config/loader.py` to expose a function or attribute that returns the resolved absolute output path from `settings.toml` `[output].path`, so `__main__.py` can pass it to `setup_debug_logging`.
- [x] T013 [US1] Modify `src/daily_planner/server.py` to add debug log calls in each `@mcp.tool()` wrapper: log at tool start (operation=tool name, direction="request", data=input params) and tool end (direction="response", data=truncated result, duration_ms). Import logger via `logging.getLogger("daily_planner.debug")`.
- [x] T014 [P] [US1] Modify `src/daily_planner/integrations/github.py` to add debug log calls for each HTTP request (operation="github.<method>", direction="request", data=url+params) and response (direction="response", data=status_code+truncated body, duration_ms).
- [x] T015 [P] [US1] Modify `src/daily_planner/integrations/ado.py` to add debug log calls for each HTTP request (operation="ado.<method>", direction="request", data=url+params) and response (direction="response", data=status_code+truncated body, duration_ms).
- [x] T016 [P] [US1] Modify `src/daily_planner/integrations/things.py` to add debug log calls for database reads (operation="things.<method>", direction="request"/"response", data=query context and result count).
- [x] T017 [US1] Modify `src/daily_planner/tools/render_markdown.py` to add debug log calls at start (direction="request", data=input summary) and end (direction="response", data=output path). Import logger via `logging.getLogger("daily_planner.debug")`.
- [x] T018 [P] [US1] Modify `src/daily_planner/tools/repo_activity.py` to add debug log calls at start (direction="request", data=since_business_days) and end (direction="response", data=repo count + summary).
- [x] T019 [P] [US1] Modify `src/daily_planner/tools/tasks.py` to add debug log calls at start/end of both `get_today_tasks` and `get_tomorrow_tasks` handlers.
- [x] T020 [US1] Modify `src/daily_planner/markdown/renderer.py` to add debug log call for data transformation steps (operation="render_markdown.group_tasks", direction="internal") and final output path (level=INFO).
- [x] T021 [US1] Add integration test in `tests/integration/test_debug_logging.py`: with `DAILY_PLANNER_DEBUG=1` set, call `setup_debug_logging` with a tmp dir, verify log file is created with correct name pattern, verify file contains valid JSONL (each line parses as JSON), verify required fields present in each entry.
- [x] T022 [US1] Add integration test in `tests/integration/test_debug_logging.py`: with `DAILY_PLANNER_DEBUG` unset, call `setup_debug_logging`, verify no log file is created and logger uses NullHandler.

**Checkpoint**: User Story 1 complete — debug flag produces a log file with entries for all tool and integration calls.

---

## Phase 4: User Story 2 — Review Log File to Diagnose a Specific Failure (Priority: P2)

**Goal**: Ensure log entries contain enough structured detail (operation, direction, data payloads, tracebacks, duration) that a user can diagnose failures by reading the log file alone.

**Independent Test**: Trigger a known failure, enable debug, verify the log file contains enough information to identify the root cause.

### Implementation for User Story 2

- [x] T023 [US2] Modify `src/daily_planner/integrations/github.py` to add error-level debug log calls in exception handlers: log operation, input parameters, error message, and traceback via `logger.error(..., exc_info=True, extra={...})`.
- [x] T024 [P] [US2] Modify `src/daily_planner/integrations/ado.py` to add error-level debug log calls in exception handlers with full context (operation, input parameters, error message, traceback).
- [x] T025 [P] [US2] Modify `src/daily_planner/integrations/things.py` to add error-level debug log calls in exception handlers with full context.
- [x] T026 [US2] Modify `src/daily_planner/tools/render_markdown.py` to add error-level debug log call in exception handler with full context (input summary, error, traceback).
- [x] T027 [P] [US2] Modify `src/daily_planner/tools/repo_activity.py` to add error-level debug log call in exception handler with full context.
- [x] T028 [P] [US2] Modify `src/daily_planner/tools/tasks.py` to add error-level debug log calls in exception handlers for both `get_today_tasks` and `get_tomorrow_tasks`.
- [x] T029 [US2] Add integration test in `tests/integration/test_debug_logging.py`: simulate an error scenario (e.g. log an error with exc_info), verify the log entry contains `"level": "ERROR"`, a `"traceback"` field with the exception details, and the `"operation"` and `"data"` fields with input context.
- [x] T030 [US2] Add integration test in `tests/integration/test_debug_logging.py`: verify that `duration_ms` is present on tool-end and API-response log entries and is a positive number.

**Checkpoint**: User Story 2 complete — log entries contain structured, navigable detail sufficient for root cause diagnosis.

---

## Phase 5: User Story 3 — Debug Mode Does Not Interfere with Normal Output (Priority: P2)

**Goal**: Guarantee that debug logging never writes to stdout (preserving MCP stdio transport) and that markdown output is unaffected by the debug flag.

**Independent Test**: Enable debug, run briefing, verify stdout has no debug content and markdown output is identical to a non-debug run.

### Implementation for User Story 3

- [x] T031 [US3] Verify in `src/daily_planner/logging.py` that `setup_debug_logging` sets `propagate=False` on the logger and attaches only a `FileHandler` (no `StreamHandler`). Add a defensive assertion/comment documenting this is critical for MCP transport safety.
- [x] T032 [US3] Add unit test in `tests/unit/test_logging.py`: verify the logger returned by `setup_debug_logging` has `propagate == False` and its handlers list contains only `FileHandler` (no `StreamHandler`).
- [x] T033 [US3] Add unit test in `tests/unit/test_logging.py`: capture `sys.stdout` during a debug log write, verify nothing is written to stdout. Capture `sys.stderr`, verify no debug content appears there either (only the unwritable-dir warning case should use stderr).
- [x] T034 [US3] Add integration test in `tests/integration/test_debug_logging.py`: set up debug logging, write several log entries, verify the generated log file content does not appear anywhere in a captured stdout stream.

**Checkpoint**: User Story 3 complete — debug logging is fully isolated from stdout and markdown output.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final cleanup.

- [x] T035 [P] Update `README.md` to add a "Debug Logging" section documenting the `DAILY_PLANNER_DEBUG` env var and how to read JSONL logs
- [x] T036 [P] Update `.github/copilot-instructions.md` to mention the debug logging module in the Architecture > Layer structure section
- [x] T037 Run `uv run ruff check src/ tests/` and fix any lint violations introduced by this feature
- [x] T038 Run `uv run pytest` to verify all tests pass (existing + new)
- [x] T039 Run quickstart.md validation: set `DAILY_PLANNER_DEBUG=1`, start the MCP server, verify a `.jsonl` file is created in the output directory

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 3 (builds on instrumentation from US1)
- **User Story 3 (Phase 5)**: Depends on Phase 2 (can run in parallel with US1/US2)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Foundational only — core instrumentation
- **User Story 2 (P2)**: Depends on US1 — adds error-level logging to the instrumentation points created in US1
- **User Story 3 (P2)**: Depends on Foundational only — verifies isolation guarantees. Can run in parallel with US1 and US2.

### Within Each User Story

- Tool handler instrumentation (server.py, tools/) before integration instrumentation
- Integration instrumentation tasks marked [P] can run in parallel (different files)
- Tests after implementation tasks within the same story

### Parallel Opportunities

**Phase 1**: T002 and T003 can run in parallel with each other (and after T001)

**Phase 2**: T004, T005 are independent foundations; T006 depends on both; T007 depends on T006; T008/T009/T010 (tests) can run in parallel after their implementation targets

**Phase 3 (US1)**: T014, T015, T016 (integration files) can run in parallel. T018, T019 (tool files) can run in parallel.

**Phase 4 (US2)**: T024, T025 (integration error logging) can run in parallel. T027, T028 (tool error logging) can run in parallel.

**Phase 5 (US3)**: T032, T033 (unit tests) can run in parallel.

**Phase 6**: T035, T036 (documentation) can run in parallel.

---

## Parallel Example: User Story 1

```text
# After Phase 2 is complete:

# Sequential: Wire up the entry point and config
T011 → T012 → T013

# Parallel: Instrument all integration clients simultaneously
T014 (github.py) | T015 (ado.py) | T016 (things.py)

# Parallel: Instrument tool handlers simultaneously
T018 (repo_activity.py) | T019 (tasks.py)

# Sequential: Instrument remaining files
T017 (render_markdown.py) → T020 (renderer.py)

# Tests after implementation
T021 → T022
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T010)
3. Complete Phase 3: User Story 1 (T011–T022)
4. **STOP and VALIDATE**: Set `DAILY_PLANNER_DEBUG=1`, run MCP server, verify JSONL log file is produced with entries for tool calls and API requests
5. This is a deployable MVP — basic debug logging works

### Incremental Delivery

1. Setup + Foundational → Logging module ready
2. User Story 1 → Debug logging produces log files (MVP!)
3. User Story 2 → Error entries have full diagnostic context
4. User Story 3 → Isolation guarantees verified with tests
5. Polish → Documentation and final validation

---

## Notes

- All log calls use `logging.getLogger("daily_planner.debug")` — the same named logger configured in `setup_debug_logging`
- Log calls use `extra={"operation": ..., "direction": ..., "data": ...}` to pass structured fields to the formatter
- Duration tracking uses `time.perf_counter()` around timed operations, converted to milliseconds
- The `NullHandler` path ensures zero overhead when debug is disabled — `logger.debug()` calls are no-ops
