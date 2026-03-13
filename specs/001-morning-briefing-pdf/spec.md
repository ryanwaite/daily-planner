# Feature Specification: Morning Briefing PDF Generator

**Feature Branch**: `001-morning-briefing-pdf`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "Build an MCP server (Python) that exposes daily-planner tools, orchestrated by a Copilot CLI agent skill. The agent gathers data, uses its own LLM for repo-activity summarization, and calls the MCP server to render a printable two-page PDF morning briefing. Page one is a three-column layout (Outlook calendar via Work IQ MCP, today's Things tasks, tomorrow's tasks + note space). Page two is a two-column LLM-summarized repository activity view. Font sizes and repo lists are configurable via files."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Generate Today's Calendar Column (Priority: P1)

As a user, I ask the Copilot CLI agent to generate my morning
briefing. The agent connects directly to the Microsoft Work IQ MCP
server, authenticates, and retrieves my Outlook calendar events for
today as structured event data. The agent then passes this data to
the daily-planner MCP server's `render_pdf` tool. Events are listed
chronologically from earliest to latest, showing each event's time
range, title, and location (if present). The date at the top of the
page is displayed in the format "dddd, MMMM D, YYYY" (e.g.,
"Thursday, March 12, 2026").

**Why this priority**: The calendar is the backbone of the morning
overview — without knowing what meetings are scheduled, the rest of
the briefing loses context.

**Independent Test**: Configure the agent with valid Work IQ
credentials, trigger the briefing, and confirm the PDF contains a
first column listing all of today's calendar events in chronological
order.

**Acceptance Scenarios**:

1. **Given** valid Work IQ MCP credentials are configured, **When**
   the agent triggers the briefing, **Then** the first column of
   page one lists all Outlook calendar events for today in
   chronological order with time, title, and location.
2. **Given** a calendar event has no location, **When** the PDF is
   generated, **Then** the event is still shown with time and title
   and no blank or placeholder location field.
3. **Given** the Work IQ MCP server is unreachable, **When** the
   agent triggers the briefing, **Then** the agent passes an error
   indicator to `render_pdf`, which displays a clear "Unavailable"
   notice in the calendar column while the remaining columns still
   render.

---

### User Story 2 — Show Today's Things Tasks (Priority: P1)

As a user, I see my Things to-do items for today in the second
column of page one. The agent calls the MCP server's
`get_today_tasks` tool, which reads tasks from Things in the
application's default sort order. Each task shows its title and,
optionally, any tags or project context that Things provides.

**Why this priority**: Task visibility is equally critical to
calendar visibility — together they form the actionable core of the
briefing.

**Independent Test**: Invoke the `get_today_tasks` MCP tool with a
populated Things task list and verify the returned data contains all
due-today tasks in the correct order.

**Acceptance Scenarios**:

1. **Given** Things contains tasks due today, **When** the agent
   triggers the briefing, **Then** the second column lists all
   due-today tasks in Things' default sort order.
2. **Given** there are no tasks due today in Things, **When** the
   agent triggers the briefing, **Then** the second column shows a
   friendly "No tasks due today" message.
3. **Given** Things is unreachable, **When** the agent triggers the
   briefing, **Then** the second column displays an "Unavailable"
   notice and the remaining columns still render.

---

### User Story 3 — Show Tomorrow's Tasks and Note Space (Priority: P2)

As a user, I see the top portion of the third column on page one
populated with tasks from Things that are due the next business day.
The agent calls the MCP server's `get_tomorrow_tasks` tool. The
bottom portion of the third column is intentionally left as empty
white space so I can handwrite notes after printing.

**Why this priority**: Seeing tomorrow's tasks helps me plan ahead,
and having a built-in note area turns the printout into a working
document for the day.

**Independent Test**: Invoke the `get_tomorrow_tasks` MCP tool and
verify the returned data contains tasks due the next business day.

**Acceptance Scenarios**:

1. **Given** Things contains tasks due tomorrow, **When** the agent
   triggers the briefing, **Then** the top of the third column
   lists those tasks.
2. **Given** there are no tasks due tomorrow, **When** the agent
   triggers the briefing, **Then** the top of the third column
   shows "No tasks due tomorrow" and the rest is blank.
3. **Given** the current day is Friday, **When** the agent triggers
   the briefing, **Then** "tomorrow" is interpreted as the next
   Monday.

---

### User Story 4 — Repository Activity Summary (Priority: P2)

As a user, I see page two of the PDF with a two-column summary of
recent activity across my configured GitHub and ADO repositories.
The agent calls the MCP server's `get_repo_activity` tool to fetch
raw activity since the last business day (e.g., on Monday it covers
Friday through Sunday). The agent then uses its own LLM to produce
a concise narrative summary per repo, explaining what happened and
how it fits into the broader goals of the repository. The
summarised text is passed back to the MCP server's `render_pdf`
tool for inclusion on page two.

**Why this priority**: Repository awareness prevents surprises in
stand-ups and helps prioritise code review.

**Independent Test**: Invoke the `get_repo_activity` MCP tool with
a repos config file listing at least one GitHub and one ADO repo.
Verify the returned raw data. Then invoke `render_pdf` with
agent-provided summaries and verify page two renders in two-column
layout.

**Acceptance Scenarios**:

1. **Given** a repos config file lists GitHub and ADO repositories,
   **When** the agent triggers the briefing, **Then** page two
   shows LLM-summarised activity since the last business day for
   each repo.
2. **Given** a configured repository has no activity since the last
   business day, **When** the agent triggers the briefing, **Then**
   that repo's section shows "No recent activity."
3. **Given** one repository is unreachable, **When** the agent
   triggers the briefing, **Then** that repo's section shows
   "Unavailable" and the remaining repos still render.
4. **Given** today is Monday, **When** the agent triggers the
   briefing, **Then** the activity window spans from the prior
   Friday through Sunday.
5. **Given** the agent's LLM summarization fails, **When** the
   agent triggers the briefing, **Then** page two falls back to
   raw activity lists with an in-PDF notice that summarisation
   was unavailable.

---

### User Story 5 — Configurable Font Sizes and Repo List (Priority: P3)

As a user, I can customise font sizes for page one and page two
independently through a configuration file. I also maintain a
separate text file listing the GitHub and ADO repositories to track.
Changes to either file take effect on the next briefing run without
modifying code.

**Why this priority**: Personalisation is important for print
readability but the tool is fully functional without it (reasonable
defaults suffice).

**Independent Test**: Edit the config files, trigger the agent
twice with different font sizes, and confirm the PDF output reflects
the changes.

**Acceptance Scenarios**:

1. **Given** a font-size config file exists with page-one and
   page-two sizes, **When** the agent triggers the briefing,
   **Then** the PDF uses the specified sizes.
2. **Given** no font-size config file exists, **When** the agent
   triggers the briefing, **Then** the PDF uses sensible default
   font sizes.
3. **Given** a repos config file lists three GitHub repos and two
   ADO repos, **When** the agent triggers the briefing, **Then**
   page two includes activity only for those five repos.
4. **Given** a repos config file is missing, **When** the agent
   triggers the briefing, **Then** the MCP server returns a clear
   error indicating the file is required and its expected path.

---

### Edge Cases

- What happens when the user has an all-day event in Outlook?
  Display it at the top of the calendar column marked "All Day."
- What happens when there are more calendar events than fit in the
  column? Reduce font size within the column or overflow with an
  ellipsis indicator ("… and N more events").
- What happens when the PDF is generated on a public holiday?
  Treat it as a normal weekday; the tool does not maintain a
  holiday calendar.
- What happens when the repos config file contains an invalid repo
  URL? Skip that entry, print a warning to stderr, and continue
  generating the PDF with valid repos.
- What happens when credentials expire mid-run? Treat it the same
  as an unreachable service — render an error notice in the affected
  PDF section stating the data is unavailable and warn on stderr.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Copilot CLI agent MUST connect directly to the
  Microsoft Work IQ MCP server to retrieve Outlook calendar data
  for the current day. The agent MUST pass the structured calendar
  events to the daily-planner MCP server's `render_pdf` tool.
- **FR-002**: System MUST retrieve today's tasks from Things in the
  application's default sort order.
- **FR-003**: System MUST retrieve tasks due the next business day
  from Things (skipping weekends: Friday → Monday).
- **FR-004**: The MCP server MUST expose a `get_repo_activity`
  tool that retrieves recent activity (since the last business
  day) from each repository listed in the repos config file,
  supporting both GitHub and Azure DevOps. Activity types MUST
  include commits, pull requests (opened, merged, closed), and
  issue or work-item updates. Authentication MUST use an OAuth2
  device-code flow for both platforms, with tokens cached locally
  for subsequent runs (ADO: refresh tokens, ~90 day lifetime;
  GitHub: access tokens with interactive re-authentication on
  expiry, ~8 hours). The tool MUST return structured
  raw activity data to the calling agent.
- **FR-005**: The Copilot CLI agent skill MUST use its own LLM to
  generate a contextual narrative summary for each repository's
  activity, given the raw activity data (from `get_repo_activity`)
  plus the repo's README or description. The summarised text MUST
  be passed to the MCP server's `render_pdf` tool. If the agent's
  LLM summarization fails, the MCP server MUST fall back to
  rendering a raw activity list (type, title, author, timestamp)
  with an in-PDF notice that summarisation was unavailable.
- **FR-006**: System MUST render a two-page PDF:
  - **Page 1**: Three-column layout — Column 1: today's calendar;
    Column 2: today's tasks; Column 3 top: tomorrow's tasks,
    Column 3 bottom: blank note area.
  - **Page 2**: Two-column layout — repository activity summaries.
- **FR-007**: System MUST display dates in the PDF using the format
  "dddd, MMMM D, YYYY" and use the format "YYYY-MM-DD dddd" in
  saved file names.
- **FR-008**: System MUST read font-size settings from a
  configuration file, with separate values for page one and page
  two.
- **FR-009**: System MUST fall back to sensible default font sizes
  when no font-size configuration file is present.
- **FR-010**: System MUST read the list of tracked repositories
  (GitHub and ADO) from a plain-text configuration file.
- **FR-011**: System MUST gracefully degrade when any single data
  source (Work IQ, Things, GitHub, or ADO) is unavailable, or when
  the agent's LLM summarization fails. The affected section of the
  PDF MUST render a visible error notice (e.g., "Calendar data
  unavailable — Work IQ error" or "Summarisation unavailable —
  showing raw activity") so the printed document clearly
  communicates which information is missing. All remaining healthy
  sections MUST still be generated.
- **FR-012**: System MUST write the generated PDF to a user-specified
  or default local path and MUST NOT transmit personal data to any
  service other than the configured integrations.
- **FR-013**: Work IQ MCP authentication is handled by the agent
  (which connects to the Work IQ MCP server directly). GitHub and
  ADO MUST authenticate via OAuth2 device-code flow with refresh
  tokens cached in the macOS Keychain (via the `keyring` Python
  library). No credentials MUST be hard-coded or stored in
  plain-text files.
- **FR-014**: The MCP server MUST use stdio transport so the
  Copilot CLI agent can spawn it as a subprocess automatically
  with no manual server start required. When invoked directly as
  a CLI (e.g., for testing), it MUST exit with code 0 on success
  and non-zero on failure, printing errors to stderr and progress
  to stdout.
- **FR-015**: The system MUST be implemented as an MCP server
  exposing the following tools: `get_today_tasks` (fetch today's
  Things tasks), `get_tomorrow_tasks` (fetch next-business-day
  Things tasks), `get_repo_activity` (fetch raw repo activity),
  and `render_pdf` (accept all gathered data — calendar events,
  tasks, repo activity, and optional LLM-generated summaries —
  and produce the two-page PDF). Calendar data is supplied by
  the agent from the Work IQ MCP server, not fetched by this
  MCP server.
- **FR-016**: A Copilot CLI agent skill file (`.agent.md`) MUST be
  provided that orchestrates the morning briefing workflow: calling
  the Work IQ MCP server for calendar data, calling the
  daily-planner MCP server tools for tasks and repo activity, using
  the agent's LLM for repo-activity summarization, and invoking
  `render_pdf` with the assembled data.

### Key Entities

- **Calendar Event**: Represents an Outlook calendar entry for
  today. Key attributes: start time, end time, title, location
  (optional), all-day flag.
- **Task**: Represents a Things to-do item. Key attributes: title,
  due date, sort position, project/tag context (optional).
- **Repository**: A configured GitHub or ADO repo to track. Key
  attributes: platform (GitHub or ADO), owner/organisation, repo
  name, URL.
- **Activity Item**: A single event in a repository since the last
  business day. Key attributes: type (commit, pull request, or
  issue/work-item update), title, author, timestamp, contextual
  summary.
- **Configuration**: User-editable settings. Key attributes:
  page-one font size, page-two font size, repos list file path,
  output path.

## Clarifications

### Session 2026-03-12

- Q: How should the contextual repository activity summary be produced? → A: LLM-assisted — batch raw activity items plus the repo's README/description to an LLM for a concise narrative summary per repo.
- Q: How should the tool authenticate with GitHub and ADO? → A: OAuth2 device-code flow for both — interactive browser login with a locally cached refresh token.
- Q: Which types of repository activity should be included? → A: Commits, pull requests (opened/merged/closed), and issue or work-item updates.
- Q: How should the system handle failures (Work IQ, LLM, Things, GitHub, ADO)? → A: Always render an error notice in the affected PDF section so the printed document makes missing data visible. Additionally log a warning to stderr.
- Q: Should the PDF support A4 paper or only US Letter? → A: US Letter only.
- Q: Should the application be a pure CLI, an MCP server with agent skill, or hybrid? → A: MCP server + Copilot CLI agent skill (Option B). The agent orchestrates data gathering and LLM summarization; the MCP server handles data fetching and PDF rendering. This enables future LLM-powered features like meeting preparation advice.
- Q: How should the daily-planner MCP server access Work IQ calendar data? → A: The agent calls Work IQ MCP directly and passes calendar events to the daily-planner's `render_pdf` tool. No `get_calendar` tool on the daily-planner MCP server.
- Q: Where should OAuth2 refresh tokens for GitHub and ADO be stored? → A: macOS Keychain via the `keyring` Python library — encrypted, OS-managed, access-controlled.
- Q: How should the daily-planner MCP server be started? → A: stdio transport — the agent spawns the MCP server as a subprocess automatically; no manual server start needed.

## Assumptions

- The Microsoft Work IQ MCP server provides a standard
  authentication flow (e.g., OAuth2 device-code or token-based)
  and exposes calendar events through a documented interface.
- Things data is accessible locally on macOS (e.g., through its
  built-in URL scheme or local database) without requiring a
  network call.
- "Last business day" means the most recent weekday (Monday–Friday);
  public holidays are not accounted for.
- The tool is intended for a single user on their local machine and
  does not need multi-user or server deployment considerations.
- Repository activity refers to commits, pull requests
  (opened/merged/closed), and issue or work-item updates visible
  to the authenticated user.
- Copilot CLI is installed and available on the user's machine, and
  supports invoking agent skills and connecting to local MCP
  servers.
- The agent's LLM capabilities (via Copilot CLI) are available for
  repo-activity summarization; if unavailable, the system falls
  back to raw activity lists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can generate a complete two-page PDF briefing in
  under 30 seconds from the time the agent command is invoked.
- **SC-002**: When all data sources are available, every section of
  the PDF (calendar, today's tasks, tomorrow's tasks, repo
  activity) is populated with current data.
- **SC-003**: When any single data source is down, the PDF is still
  generated within 45 seconds, with the unavailable section clearly
  marked.
- **SC-004**: Font-size changes in the config file are reflected in
  the very next PDF generation without code changes or restarts.
- **SC-005**: Adding or removing a repository in the repos config
  file is reflected in the very next PDF generation.
- **SC-006**: The generated PDF is printable on US Letter paper
  (8.5 × 11 in) with all content legible and properly laid out
  across both pages.
