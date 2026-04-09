<!--
  Sync Impact Report
  ===================
  Version change: 1.1.0 → 1.2.0
  Modified principles: None
  Added sections:
    - Dependency security checks under Technology Standards
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ reviewed (no changes needed)
    - .specify/templates/spec-template.md ✅ reviewed (no changes needed)
    - .specify/templates/tasks-template.md ✅ reviewed (no changes needed)
  Follow-up TODOs: None
-->

# Daily Planner Constitution

## Core Principles

### I. Simplicity First

- All solutions MUST use the simplest viable approach; complexity
  MUST be justified in writing before implementation.
- YAGNI: features and abstractions MUST NOT be added until a
  concrete, immediate need exists.
- Each module MUST have a single, clear responsibility.
- When choosing between two approaches of similar capability, the
  one with fewer moving parts MUST be selected.

**Rationale**: A CLI tool that aggregates external data sources
benefits most from a small, auditable codebase. Every unnecessary
abstraction is a maintenance liability.

### II. Privacy by Default

- Raw personal data (emails, calendar entries, to-do items) MUST
  NOT be persisted to disk beyond the lifetime of a single run
  unless the user explicitly opts in.
- API tokens and credentials MUST be read from environment
  variables or a secure credential store; they MUST NOT be
  hard-coded or committed to version control.
- Generated PDF output MUST be written only to a user-specified
  or well-known local path; no data MUST be transmitted to
  third-party services beyond the configured integrations
  (Microsoft Work IQ, GitHub, ADO, Things).

**Rationale**: The tool processes sensitive work communications
and schedules. Minimizing data retention and enforcing credential
hygiene reduces exposure from accidental leaks.

### III. Resilient Integrations

- Every external API call (Work IQ, GitHub, ADO, Things) MUST
  have a timeout, retry policy, and graceful degradation path.
- If an integration is unreachable, the daily planner MUST still
  produce output for the remaining healthy sources and clearly
  indicate which sections are unavailable.
- Integration modules MUST be isolated behind a common interface
  so that adding, removing, or replacing a data source requires
  changes in only one module.

**Rationale**: The tool contacts multiple external services each
morning. A single outage MUST NOT block the user's entire daily
overview.

### IV. Testability

- All integration modules MUST be testable with mocked HTTP
  responses; no test MUST require live credentials or network
  access.
- Business logic (aggregation, filtering, summarization) MUST be
  separated from I/O so it can be unit-tested in isolation.
- PDF output MUST be verifiable by checking structured
  intermediate data (e.g., a dict/model) before rendering.

**Rationale**: External dependencies change frequently. Tests
that rely on live services are fragile and slow; mocked tests
ensure fast, deterministic feedback.

### V. Actionable Output

- The generated PDF MUST prioritise scannability: calendar at a
  glance, followed by to-dos, then repo activity, then inbox
  actions.
- Every section MUST include a clear heading and timestamp of
  data retrieval so the user knows how fresh the information is.
- Dates displayed in the PDF MUST use the human-readable format
  `dddd, MMMM D, YYYY` (e.g., "Thursday, March 12, 2026").
- The CLI MUST exit with code 0 on success and non-zero on
  failure, printing errors to stderr and progress to stdout.

**Rationale**: The purpose of the tool is a quick, printable
morning briefing. Output that requires effort to parse defeats
the goal.

## Technology Standards

- **Language**: Python ≥ 3.12.
- **Project management**: `pyproject.toml` with dependencies
  declared under `[project.dependencies]`.
- **Server framework**: MCP server via FastMCP (stdio transport);
  heavy frameworks MUST be avoided.
- **PDF generation**: A library suitable for simple document
  layout (e.g., `reportlab` or `weasyprint`).
- **HTTP client**: `httpx` or `requests` with configurable
  timeouts.
- **Testing**: `pytest` as the test runner; `responses` or
  `respx` for HTTP mocking.
- **Linting/formatting**: `ruff` for linting and formatting.
- **Type checking**: Type hints MUST be used on all public
  function signatures.
- **Date formats**:
  - File names and saved metadata MUST use
    `YYYY-MM-DD dddd` (e.g., `2026-03-12 Thursday`).
  - PDF display dates MUST use
    `dddd, MMMM D, YYYY` (e.g., `Thursday, March 12, 2026`).
- **Dependency security**:
  - All third-party packages MUST be pinned to exact versions in
    `pyproject.toml` (or a lock file) to prevent silent upgrades.
  - Before adding or upgrading a dependency, a basic security
    check MUST be performed: verify the package is published by
    a known maintainer, has no open critical/high CVEs (e.g., via
    `pip-audit` or `safety`), and is actively maintained.
  - `pip-audit` (or an equivalent tool) MUST be run as part of
    the CI pipeline and before any release to detect known
    vulnerabilities in the dependency tree.
  - Dependencies with unresolved critical or high CVEs MUST NOT
    be used unless a documented exception with mitigation is
    approved.

## Development Workflow

- Every feature branch MUST include tests that exercise the new
  behaviour before the implementation is considered complete.
- Code reviews MUST verify compliance with this constitution's
  principles before merge.
- The `main` branch MUST always be in a releasable state; broken
  builds MUST be fixed immediately.
- Commit messages MUST follow the Conventional Commits format
  (e.g., `feat:`, `fix:`, `docs:`).

## Governance

- This constitution is the authoritative source of project
  standards. In case of conflict with other documentation, the
  constitution takes precedence.
- Amendments MUST be proposed via pull request with a clear
  rationale. The constitution version MUST be incremented per
  semantic versioning:
  - **MAJOR**: Principle removal or backward-incompatible
    governance change.
  - **MINOR**: New principle or materially expanded guidance.
  - **PATCH**: Clarifications, wording, or typo fixes.
- A compliance check against these principles MUST be part of
  every feature planning cycle (see Constitution Check in
  plan-template.md).

**Version**: 1.2.0 | **Ratified**: 2026-03-12 | **Last Amended**: 2026-03-12
