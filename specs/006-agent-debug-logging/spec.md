# Feature Specification: Agent Debug Logging

**Feature Branch**: `006-agent-debug-logging`  
**Created**: 2026-04-26  
**Status**: Draft  
**Input**: User description: "I'd like there to be a debug flag where the agent logs will be captured. From there we can look at the logs and determine how we can update the application to remove problems agents have completing the work."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enable Debug Logging for a Briefing Run (Priority: P1)

A developer or power user wants to understand what happened during a morning briefing generation — which tools were called, what data was received, what errors or unexpected responses occurred — so they can diagnose why the agent produced an incomplete or incorrect briefing.

The user enables a debug flag before the agent runs. During the briefing generation, the MCP server captures structured log entries for every significant operation: tool invocations, external API calls, data transformations, and the final render step. After the run completes, the user opens the log file and can trace the full execution flow to identify where things went wrong.

**Why this priority**: Without observability into what the MCP server is doing, debugging agent failures is guesswork. This is the foundational capability that all other debugging workflows depend on.

**Independent Test**: Can be fully tested by enabling the debug flag, running the briefing generation, and verifying that a log file is created containing structured entries for each tool call and external integration.

**Acceptance Scenarios**:

1. **Given** the debug flag is enabled, **When** the agent runs a full morning briefing, **Then** a log file is created in the configured output location containing timestamped entries for every tool invocation and external API call.
2. **Given** the debug flag is not enabled, **When** the agent runs a full morning briefing, **Then** no log file is created and no debug output is emitted to stderr.
3. **Given** the debug flag is enabled, **When** an external API call fails (e.g. GitHub returns an error), **Then** the log file captures the error details including the failing request context and the error response.

---

### User Story 2 - Review Log File to Diagnose a Specific Failure (Priority: P2)

After a briefing run with debug enabled, the user opens the log file to investigate why a specific section (e.g. repository activity) was missing or incorrect. The log entries are structured and human-readable, making it straightforward to locate the relevant tool call, see what inputs were provided, and identify whether the failure was in the external service response or in the server's data processing.

**Why this priority**: The log file is only useful if its contents are structured and easy to navigate. Without clear formatting and sufficient detail, the user would still be guessing.

**Independent Test**: Can be tested by intentionally triggering a known failure scenario (e.g. invalid repo config), enabling debug, running the briefing, and verifying the log file contains enough information to identify the root cause without any other debugging tools.

**Acceptance Scenarios**:

1. **Given** a debug log file from a completed run, **When** the user reads it, **Then** each entry includes a timestamp, the operation name, the direction (request/response), and the relevant data payload.
2. **Given** a debug log file from a run where one repo returned an error, **When** the user searches for that repo name, **Then** they find the outgoing request details and the error response grouped together.

---

### User Story 3 - Debug Mode Does Not Interfere with Normal Output (Priority: P2)

When debug logging is active, the briefing generation still produces its normal markdown output file. The debug log is written to a separate file and does not pollute the MCP server's stdout (which is the MCP transport channel) or alter the briefing content in any way.

**Why this priority**: The MCP server communicates over stdio. Any debug output that leaks to stdout would corrupt the MCP protocol messages and break the agent. This must be guaranteed.

**Independent Test**: Can be tested by enabling debug, running the full briefing, and verifying that the markdown output is identical to a run without debug enabled, and that no extra content appears on stdout.

**Acceptance Scenarios**:

1. **Given** the debug flag is enabled, **When** the briefing generation completes, **Then** the resulting markdown file is identical to what would be produced without the debug flag.
2. **Given** the debug flag is enabled, **When** any part of the system writes debug information, **Then** no debug content is written to stdout.

### Edge Cases

- What happens when the configured log output directory does not exist or is not writable? The system should log a warning to stderr and continue without debug logging rather than crashing.
- What happens when a single tool call produces a very large response (e.g. thousands of commits)? Log entries for large payloads should be truncated to a reasonable size to prevent log files from growing unbounded.
- What happens when two briefing runs happen in quick succession? Each run should produce a separate log file with a unique name (e.g. timestamp-based) so logs are never overwritten.
- What happens when the debug flag is enabled but the server encounters an unhandled exception? The exception should still be captured in the log file before the process exits.

### Out of Scope

- Log viewer, analysis, or search tooling — users read the JSONL file directly with standard tools (`cat`, `grep`, `jq`).
- Log rotation or retention policies — old log files are not automatically cleaned up.
- Any runtime behavior changes beyond writing the log file (e.g. slower execution, extra validation, altered error handling).
- A `settings.toml` configuration option for debug mode — activation is via the `DAILY_PLANNER_DEBUG` environment variable only.

## Clarifications

### Session 2026-04-26

- Q: How should the system handle sensitive data (auth tokens, task titles, calendar details) in debug log entries? → A: Log everything verbatim — the user is responsible for protecting the log file.
- Q: What format should debug log entries use (plain text, JSONL, or full JSON array)? → A: JSON Lines (JSONL) — one JSON object per line, machine-parseable and grep-friendly.
- Q: What should be explicitly declared out of scope? → A: Log viewer/analysis tools, log rotation/retention policies, and runtime behavior changes beyond writing the log file.
- Q: Should debug logging be synchronous or asynchronous? → A: Synchronous — guaranteed flush before continuing, negligible overhead for this I/O-bound workload.
- Q: What should the payload truncation threshold be, and should it be runtime-configurable? → A: 5,000 characters hardcoded default, not runtime-configurable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support a debug flag that can be activated via an environment variable (`DAILY_PLANNER_DEBUG`).
- **FR-002**: When the debug flag is active, the system MUST write structured log entries to a dedicated log file in the configured output directory.
- **FR-003**: Each log entry MUST be a single JSON object on its own line (JSONL format) and MUST include: a timestamp, a log level (DEBUG, INFO, WARNING, ERROR), the operation name (e.g. tool name, integration name), and relevant context data.
- **FR-004**: The system MUST log the following events when debug is active: tool invocation start/end, external API request/response (including status codes), data transformation steps (e.g. task grouping, area sorting), and the final render output path.
- **FR-005**: The system MUST NOT write any debug output to stdout, since stdout is used for MCP stdio transport.
- **FR-006**: The system MUST produce a separate log file per run, named with a timestamp to avoid collisions.
- **FR-007**: When the debug flag is not active, the system MUST NOT create any log files or emit debug output.
- **FR-008**: Log entries for individual data payloads MUST be truncated if they exceed 5,000 characters to prevent unbounded log growth. This threshold is a hardcoded default, not runtime-configurable.
- **FR-009**: If the log output directory is not writable, the system MUST emit a warning to stderr and continue operating normally without debug logging.
- **FR-010**: The system MUST log errors and exceptions with full context (operation name, input parameters, error message, traceback) when they occur during a debug-enabled run.

### Key Entities

- **Debug Log File**: A timestamped file containing all structured log entries from a single briefing run. Located in the configured output directory. Named with a pattern that includes the run date and time.
- **Log Entry**: A single JSON object on its own line representing one logged event. Contains timestamp, level, operation, direction (request/response/internal), and a data payload (potentially truncated). Each line is independently parseable with standard JSON tools (e.g. `jq`, `grep`).

## Assumptions

- The environment variable approach (`DAILY_PLANNER_DEBUG=1`) is the most natural activation mechanism for an MCP server, since MCP servers are invoked by the host process and don't have their own CLI flags.
- Log files will use the same output directory as the markdown briefing (configured in `settings.toml` under `[output].path`), keeping all artifacts together.
- Debug logging will use Python's built-in `logging` module, which naturally supports the structured entry format and file-based output described here.
- Large payload truncation is set at 5,000 characters per field (hardcoded), which is sufficient for diagnosis without producing multi-megabyte log files. No runtime configuration knob is provided.
- Debug logs capture all data verbatim, including auth tokens, task titles, and calendar content. No sanitization or redaction is applied. The user is responsible for protecting the local log file.
- Debug log writes are synchronous (flush after each entry). This guarantees no entries are lost on crash and adds negligible overhead since the server is I/O-bound against network APIs and a local SQLite database.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can enable debug logging and receive a complete log file after a briefing run in 100% of cases where the output directory is writable.
- **SC-002**: The log file contains at least one entry per MCP tool invocation and one entry per external API call made during the run.
- **SC-003**: A user can identify the root cause of a failed or incomplete briefing section by reading only the log file, without needing additional debugging tools, in typical failure scenarios (API errors, missing data, malformed responses).
- **SC-004**: Debug-enabled runs produce markdown output identical to non-debug runs — zero impact on the generated briefing.
- **SC-005**: No debug content is ever written to stdout, preserving the MCP stdio transport integrity.
