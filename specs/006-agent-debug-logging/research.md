# Phase 0 Research: Agent Debug Logging

**Feature**: 006-agent-debug-logging  
**Date**: 2026-04-26  
**Status**: Complete

## Topic 1: Logging Library Choice (Resolves NEEDS CLARIFICATION)

**Decision**: Use Python's `logging` module (stdlib) with a custom `Formatter` subclass that outputs JSONL. Do NOT use `python-json-logger` third-party library.

**Rationale**: 
- **Simplicity**: The `logging` module is already in stdlib; no new dependencies. A custom Formatter subclass is simpler than adding a third-party logger.
- **Control**: Subclassing `logging.Formatter` gives precise control over JSON structure, truncation logic, and error handling. No framework surprises.
- **Spec compliance**: Spec says "Synchronous — guaranteed flush before continuing." Python's `logging.FileHandler.emit()` already calls `flush()` after every record; no additional work needed.
- **Alignment**: Existing `src/daily_planner/logging.py` already has logging setup; extending it with a custom Formatter maintains consistency.

**Alternatives considered**:
- `python-json-logger`: Third-party dependency; adds 1 library to maintain. Rejected for Principle I (Simplicity).
- `structlog`: Heavy ORM-like logging library; overkill for one-off debug output. Rejected.
- Manual `json.dumps()` + file write (no logging module): Loses Python logging infrastructure (levels, handlers, propagation). Rejected as less flexible.

---

## Topic 2: JSONL Schema and Format

**Decision**: Use Python's `logging.Formatter` to produce one JSON object per line. Each object contains: `timestamp`, `level`, `operation`, `direction`, `data`.

**Rationale**:
- **Standard**: JSON Lines (RFC 7464) is grep-friendly and parseable with `jq`, `grep`, etc.
- **Keys**:
  - `timestamp`: ISO 8601 with microseconds (e.g., `2026-04-30T08:15:32.123456Z`).
  - `level`: DEBUG, INFO, WARNING, ERROR.
  - `operation`: Tool or integration name (e.g., `get_repo_activity`, `github_rest_api`).
  - `direction`: `request` | `response` | `internal` — clarifies data flow.
  - `data`: The payload (request body, response, processing result) — truncated to 5000 chars.

**Example**:
```json
{"timestamp": "2026-04-30T08:15:32.123456Z", "level": "DEBUG", "operation": "get_today_tasks", "direction": "internal", "data": {"count": 13, "areas": ["No Area", "Work", "Personal"]}}
```

**Implementation**: 
- Subclass `logging.Formatter`, override `format()` to build a dict and return `json.dumps(...)`.
- Pass extra fields via the `extra` kwarg: `logger.debug("message", extra={"operation": "X", "direction": "request", "data": {...}})`.
- Handle non-serializable types (e.g., `datetime`, `Path`) with a custom `default` function for `json.dumps`.
- Handle exceptions: If `record.exc_info` is present, call `self.formatException()` and include as a `"traceback"` key in the JSON (prevents multi-line traceback from breaking JSONL).

---

## Topic 3: Payload Truncation Strategy

**Decision**: Truncate before JSON serialization by recursively walking the `data` dict and truncating string values that exceed 5000 characters. Append `"...[truncated]"` to indicate truncation. Do not mutate caller data (return a copy).

**Rationale**:
- **Prevents broken JSONL**: Truncating the final JSON string can break JSON structure (mid-key, mid-UTF-8). Truncating source dict values preserves valid JSON.
- **Recursive handling**: API responses have nested dicts (e.g., commit lists). Must handle all levels.
- **5000 char threshold**: Balances detail (covers most API responses) vs. log file size (<500KB per run; typical ~50–100 entries × 5KB max).
- **Immutability**: Truncate a copy; don't mutate caller's dict (prevents subtle bugs).

**Alternatives considered**:
- Truncate only top-level values — misses nested large strings in API responses.
- Truncate final JSON string — breaks JSON structure; useless with `jq`.
- Omit large fields — loses diagnostic info.

**Function signature**:
```python
def _truncate_dict(data: dict, max_size: int = 5000) -> dict:
    """Recursively truncate string values exceeding max_size."""
    # Implementation: walk dict, list, and string types; truncate strings
```

---

## Topic 4: Avoiding Stdout Pollution (MCP Protocol Safety)

**Decision**: 
- Create a dedicated named logger (`daily_planner.debug`).
- Attach only a `FileHandler` to this logger (no console/stderr output of debug entries).
- Set `propagate = False` to prevent bubbling to root logger.
- Only configure this logger if `DAILY_PLANNER_DEBUG` env var is set.
- Never call `logging.basicConfig()` from debug setup.
- Only emit warnings to stderr if the log file cannot be created (FR-009).

**Rationale**:
- **MCP protocol requirement** (FR-005): stdout is reserved for MCP transport. Any debug output there breaks the protocol. Setting `propagate = False` is the strongest isolation.
- **Spec requirement** (FR-009): Warn to stderr only if log creation fails, then continue without debug.
- **Non-intrusive**: Debug logs should be discoverable (user looks in output dir) but not intrusive (not cluttering stderr).

**Alternatives considered**:
- `logging.basicConfig()` — configures root logger; risky side effects with MCP SDK.
- Adding FileHandler to root logger — captures all library logs (httpx, anyio, etc.), too noisy.
- Relying on root logger configuration — less isolated; MCP SDK config could interfere.

---

## Topic 5: Synchronous Write + Flush Behavior

**Decision**: Use Python's standard `logging.FileHandler`. Its `emit()` method (inherited from `StreamHandler`) already calls `self.flush()` after every record. No subclassing or additional configuration needed.

**Rationale**:
- **Spec requirement**: Spec says "Synchronous — guaranteed flush before continuing."
- **CPython behavior**: `logging.FileHandler` (via `StreamHandler.emit()`) calls `flush()` after every log record. Documented behavior, no surprises.
- **Performance**: ~1KB JSON line + flush takes <1ms. ~50 entries over 30 seconds = negligible.
- **Crash safety**: Sync guarantees no log entries are lost if process crashes.

**Alternatives considered**:
- Subclassing FileHandler to add explicit flush() — redundant; already happens.
- Manual `os.fsync()` — overkill; `flush()` to OS buffer is sufficient per spec.

---

## Topic 6: Log File Naming and Collision Avoidance

**Decision**: Filename format: `{date}T{time}-debug.jsonl` where date is YYYY-MM-DD and time is HHmmss (no colons, no microseconds). Example: `2026-04-30T082150-debug.jsonl`.

**Rationale**:
- **Unique per run**: Timestamp ensures no collisions even if multiple runs in quick succession.
- **Filesystem-friendly**: No colons (problematic on Windows) or microseconds (too long).
- **Human-readable**: Easy to sort, grep by date.
- **No cleanup**: Out of scope (spec excludes log rotation). User manages old logs.

---

## Topic 7: Error Handling — Non-Writable Output Directory

**Decision**: 
- Attempt to create the log file during `__main__.py` setup.
- If `PermissionError`, `FileNotFoundError`, or other `OSError` occurs, emit a warning to stderr (e.g., `Warning: Could not create debug log file. Debug logging disabled.`).
- Set a module-level flag to disable all subsequent logging calls (e.g., `_debug_logger = None`).
- Continue briefing generation without debug logs.

**Rationale**:
- **Spec requirement** (FR-009): "If the log output directory is not writable, the system MUST emit a warning to stderr and continue operating normally without debug logging."
- **Graceful degradation**: Per Principle III (Resilient Integrations), a write error should not crash the server.

---

## Topic 8: What to Instrument (Scope Definition)

**Decision**: Log these events when debug is active (per spec FR-004):
1. **Tool invocation start/end**: MCP tool name, parameters, return value or error.
2. **External API requests/responses**: GitHub, ADO, Things queries — request details, response status/body (truncated).
3. **Data transformations**: Task grouping by area, repo activity summary generation.
4. **Render step**: `render_markdown` output path, file size.
5. **Errors**: Any operation that fails (include exception type, message, traceback).

**Not logged**:
- Every intermediate variable assignment (too verbose).
- Third-party library internals (httpx, anyio, etc. — use their own logging if needed).

**Implementation**: Each tool/integration calls `logger.debug(..., extra={"operation": "X", "direction": "Y", "data": {...}})` at key points.

---

## Topic 9: Configuration (Environment Variable Only)

**Decision**: Use the `DAILY_PLANNER_DEBUG` environment variable to enable debug mode. No `settings.toml` option. Any value (`1`, `true`, `yes`, etc.) enables it; absence disables it.

**Rationale**:
- **Spec requirement**: "A `settings.toml` configuration option for debug mode — activation is via the `DAILY_PLANNER_DEBUG` environment variable only."
- **Simplicity**: Environment variables are ephemeral; no persistent config to maintain.
- **Security**: Debug logs contain PII; forcing explicit env var activation is safer than a persistent setting.

---

## Summary Table

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Logging lib | Python `logging` module + custom Formatter | Stdlib, no new dependency, precise control |
| JSONL schema | `timestamp`, `level`, `operation`, `direction`, `data` | Standard format, grep-friendly |
| Truncation | 5000 char dict-walk (before serialization) | Prevents broken JSON; preserves detail |
| Output isolation | Dedicated logger, FileHandler only, `propagate=False` | Protects MCP protocol on stdout |
| Write model | FileHandler.emit() calls flush() natively | Sync guarantee per spec; simple |
| File naming | `{date}T{time}-debug.jsonl` | Unique, filesystem-friendly |
| Write failures | Warn stderr, disable logging, continue | Spec FR-009; graceful degradation |
| Instrumentation | Tool start/end, API calls, transforms, render, errors | Per spec FR-004 |
| Config method | `DAILY_PLANNER_DEBUG` env var only | Spec requirement; simple, secure |

---

## Next Steps (Phase 1: Design)

- **Data Model** (`data-model.md`): Define `DebugLogFormatter` class, truncation function, log entry structure.
- **Contracts** (`contracts/debug-log-format.md`): Formalize JSONL schema with before/after examples.
- **Quickstart** (`quickstart.md`): Show how to enable debug mode (`export DAILY_PLANNER_DEBUG=1`), run briefing, read log file with `jq`, `grep`, `cat`.
- **Phase 2 Implementation**: Add logging calls to each tool and integration; write unit + integration tests.

## Topic 5: Log file naming with timestamps for collision avoidance

**Decision**: Use format `debug_YYYY-MM-DD_HHMMSS_<pid>.jsonl` in local time. PID handles same-second collisions.

**Rationale**: `YYYY-MM-DD_HHMMSS` sorts lexicographically and is human-readable. Local time is more intuitive for a single-user developer tool. PID (`os.getpid()`) guarantees uniqueness since concurrent processes always have different PIDs — simpler than microseconds or random suffixes. The `.jsonl` extension signals the file format.

**Alternatives considered**:
- Microsecond precision — longer filenames, harder to read, still theoretically collision-possible.
- UUID suffix — guaranteed unique but unreadable and unsortable.
- UTC timestamps — more standard for servers but this is a local developer tool.
- Sequence number — requires shared state between runs, unnecessary complexity.
