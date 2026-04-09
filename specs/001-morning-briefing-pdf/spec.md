# Feature Specification: Morning Briefing PDF Generator

**Feature Branch**: `001-morning-briefing-pdf`  
**Created**: 2026-03-12  
**Updated**: 2026-04-02  
**Status**: Draft  
**Input**: User description: "Build an MCP server (Python) that exposes daily-planner tools, orchestrated by two separate Copilot CLI agent skills. Skill 1 (Daily View) gathers today's Outlook calendar via the WorkIQ MCP server and today's/tomorrow's Things tasks, then calls the MCP server to render page one of a printable two-page PDF morning briefing — a three-column layout (calendar, today's tasks, tomorrow's tasks + note space). Skill 2 (Repo Activity) gathers repository activity from configured GitHub and ADO repos, uses the agent's LLM for summarization, and calls the MCP server to render page two — a two-column LLM-summarized repository activity view. Either skill can be invoked independently. Font sizes and repo lists are configurable via files."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Generate Daily View (Priority: P1)

As a user, I invoke the "Morning Briefing" Copilot CLI agent skill to
generate my morning briefing. The agent connects to the
Microsoft WorkIQ MCP server to retrieve my Outlook calendar events
for today, calls the daily-planner MCP server to retrieve today's
and tomorrow's Things tasks, and then calls the `render_pdf`
tool to produce the PDF. Page one uses a three-column
layout: Column 1 lists today's calendar events chronologically
(time range, title, location if present); Column 2 lists today's
Things tasks in the application's default sort order; Column 3
shows tomorrow's tasks at the top with blank note space below. The
date at the top is displayed in the format "dddd, MMMM D, YYYY"
(e.g., "Thursday, March 12, 2026").

The daily view page is always generated as part of the agent
workflow. If calendar or task data is unavailable, the affected
columns show error notices while remaining columns still render.

**Why this priority**: Calendar and task visibility form the
actionable core of any morning briefing. A user can get immediate
value from this single skill alone, even without repository
summaries.

**Independent Test**: Configure the agent with valid WorkIQ
credentials and a populated Things task list. Invoke the agent
and confirm the PDF page one contains three columns: calendar
events, today's tasks, and tomorrow's tasks with note space.

**Acceptance Scenarios**:

1. **Given** valid WorkIQ MCP credentials are configured and Things
   contains tasks due today, **When** the user invokes the agent,
   **Then** page one of the PDF is produced with three
   columns: chronological calendar events, today's tasks, and
   tomorrow's tasks with note space.
2. **Given** a calendar event has no location, **When** the PDF is
   generated, **Then** the event is still shown with time and title
   and no blank or placeholder location field.
3. **Given** the WorkIQ MCP server is unreachable, **When** the
   user invokes the agent, **Then** the calendar column
   displays a clear "Unavailable" notice while the task columns
   still render.
4. **Given** there are no tasks due today in Things, **When** the
   user invokes the agent, **Then** the second column
   shows a friendly "No tasks due today" message.
5. **Given** Things is unreachable, **When** the user invokes the
   agent, **Then** the task columns display an
   "Unavailable" notice and the calendar column still renders.
6. **Given** the current day is Friday, **When** the user invokes
   the agent, **Then** "tomorrow" is interpreted as the
   next Monday for the third column.

---

### User Story 2 — Generate Repo Activity Summary (Priority: P2)

As a user, the "Morning Briefing" agent also generates page two of
my briefing. The agent calls the daily-planner MCP server's
`get_repo_activity` tool to fetch raw activity since the last
business day by default (e.g., on Monday it covers Friday through
Sunday) from my configured GitHub and ADO repositories. If I want
a wider window, I can pass `since_business_days` (e.g. 5 for the
past work week). The agent then uses its own LLM to produce a
concise narrative summary per repo, explaining what happened and
how it fits into the broader goals of the repository. The
summarised text is passed to the MCP server's `render_pdf` tool,
which produces the second page of the PDF with a two-column layout
of repository activity summaries.

**Why this priority**: Repository awareness prevents surprises in
stand-ups and helps prioritise code review, but this depends
on the MCP server infrastructure that is also used by the daily
view.

**Independent Test**: Invoke the agent with a repos
config file listing at least one GitHub and one ADO repo. Verify
the returned PDF page two contains LLM-summarised activity in a
two-column layout.

**Acceptance Scenarios**:

1. **Given** a repos config file lists GitHub and ADO repositories,
   **When** the user invokes the agent, **Then** page two of the
   PDF shows LLM-summarised activity since the last business day
   for each repo in a two-column layout.
2. **Given** a configured repository has no activity since the last
   business day, **When** the agent runs, **Then** that repo's
   section shows "No recent activity."
3. **Given** one repository is unreachable, **When** the agent
   runs, **Then** that repo's section shows "Unavailable" and the
   remaining repos still render.
4. **Given** today is Monday, **When** the user invokes the
   agent, **Then** the activity window spans from the
   prior Friday through Sunday.
5. **Given** the agent's LLM summarization fails, **When** the
   agent renders page two, **Then** the page falls back to
   raw activity lists with an in-PDF notice that summarisation was
   unavailable.

---

### User Story 3 — Combined Two-Page Briefing (Priority: P2)

As a user, the single agent invocation produces the full two-page
morning briefing PDF. The agent gathers all data (calendar, tasks,
repo activity), generates LLM summaries, and calls `render_pdf`
once with all assembled data. When some data sources are unavailable,
`render_pdf` gracefully handles missing sections and produces a 1-
or 2-page PDF accordingly.

**Why this priority**: The combined output is the original vision.
Since a single agent handles everything in one invocation, the
combined briefing is the default behavior.

**Independent Test**: Invoke the agent with all data sources
configured and verify the output is a single two-page PDF with
page one showing the daily view and page two showing repo activity.

**Acceptance Scenarios**:

1. **Given** all data sources are available, **When** the user
   invokes the agent, **Then** a single two-page PDF is produced
   with page one as the daily view and page two as the repo
   activity summary.
2. **Given** calendar and task data is available but repo activity
   data is unavailable, **When** the user invokes the agent,
   **Then** the PDF is produced with page one populated and page
   two showing error notices for the unavailable repos.
3. **Given** repo activity is available but WorkIQ and Things are
   unreachable, **When** the user invokes the agent, **Then** the
   PDF is produced with page one showing error notices and page two
   populated with repo summaries.

---

### User Story 4 — Configurable Font Sizes and Repo List (Priority: P3)

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
   page-two sizes, **When** the agent triggers PDF rendering,
   **Then** the PDF uses the specified sizes for the respective
   page.
2. **Given** no font-size config file exists, **When** the agent
   triggers PDF rendering, **Then** the PDF uses sensible default
   font sizes.
3. **Given** a repos config file lists three GitHub repos and two
   ADO repos, **When** the user invokes the agent,
   **Then** the repo activity page includes activity only for those
   five repos.
4. **Given** a repos config file is missing, **When** the user
   invokes the agent, **Then** the MCP server returns
   a clear error indicating the file is required and its expected
   path.

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
- What happens when the user invokes the agent but one data source
  fails? The remaining sections still render. The affected section
  shows an error notice in the PDF.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The "Daily View" Copilot CLI agent skill MUST connect
  directly to the Microsoft WorkIQ MCP server to retrieve Outlook
  calendar data for the current day. The skill MUST pass the
  structured calendar events to the daily-planner MCP server's
  `render_pdf` tool along with task data.
- **FR-002**: System MUST retrieve today's tasks from Things in the
  application's default sort order.
- **FR-003**: System MUST retrieve tasks due the next business day
  from Things (skipping weekends: Friday → Monday).
- **FR-004**: The MCP server MUST expose a `get_repo_activity`
  tool that retrieves recent activity (since the last business
  day by default) from each repository listed in the repos config
  file, supporting both GitHub and Azure DevOps. The tool MUST
  accept an optional `since_business_days` parameter (integer)
  that widens the lookback window to N business days (e.g. 5 for
  the last full work week); when omitted or 1, the default is the
  last business day. Activity types MUST include commits, pull
  requests (opened, merged, closed), and issue or work-item
  updates. Authentication MUST use a three-step token resolution
  chain for both platforms: (1) environment variable (`GITHUB_TOKEN`
  / `ADO_TOKEN`), (2) platform CLI tool (`gh auth token` /
  `az account get-access-token`) with a 10-second timeout, (3)
  macOS Keychain via the `keyring` library. The tool MUST return
  structured raw activity data to the calling agent.
- **FR-005**: The "Repo Activity" Copilot CLI agent skill MUST use
  its own LLM to generate a contextual narrative summary for each
  repository's activity, given the raw activity data (from
  `get_repo_activity`) plus the repo's README or description. The
  summarised text MUST be passed to the MCP server's
  `render_pdf` tool. If the agent's LLM summarization
  fails, the MCP server MUST fall back to rendering a raw activity
  list (type, title, author, timestamp) with an in-PDF notice
  that summarisation was unavailable.
- **FR-006**: The MCP server MUST expose a single `render_pdf` tool
  that accepts all gathered briefing data — calendar events (from
  WorkIQ, passed by the agent), task data (today and tomorrow), and
  repository activity summaries (with optional LLM narratives) — and
  produces a landscape US Letter PDF. Page one uses a three-column
  layout (Column 1: today's calendar; Column 2: today's tasks;
  Column 3 top: tomorrow's tasks, Column 3 bottom: blank note area).
  Page two uses a two-column layout of repository activity summaries.
  When only page-one or page-two data is available, a single-page
  PDF MUST be produced.
- **FR-007**: System MUST display dates in the PDF using the format
  "dddd, MMMM D, YYYY" and use the format "YYYY-MM-DD dddd" in
  saved file names.
- **FR-008**: System MUST read font-size settings from a
  configuration file, with separate values for the daily view page
  and the repo activity page.
- **FR-009**: System MUST fall back to sensible default font sizes
  when no font-size configuration file is present.
- **FR-010**: System MUST read the list of tracked repositories
  (GitHub and ADO) from a plain-text configuration file.
- **FR-011**: System MUST gracefully degrade when any single data
  source (WorkIQ, Things, GitHub, or ADO) is unavailable, or when
  the agent's LLM summarization fails. The affected section of the
  PDF MUST render a visible error notice (e.g., "Calendar data
  unavailable — WorkIQ error" or "Summarisation unavailable —
  showing raw activity") so the printed document clearly
  communicates which information is missing. All remaining healthy
  sections MUST still be generated.
- **FR-012**: System MUST write the generated PDF to a user-specified
  or default local path and MUST NOT transmit personal data to any
  service other than the configured integrations.
- **FR-013**: WorkIQ MCP authentication is handled by the agent
  skill (which connects to the WorkIQ MCP server directly). GitHub
  and ADO MUST authenticate via a three-step token resolution
  chain: environment variable → platform CLI tool → macOS Keychain
  (via the `keyring` Python library). No credentials MUST be
  hard-coded or stored in plain-text files.
- **FR-014**: The MCP server MUST use stdio transport so the
  Copilot CLI agent can spawn it as a subprocess automatically
  with no manual server start required. When invoked directly as
  a CLI (e.g., for testing), it MUST exit with code 0 on success
  and non-zero on failure, printing errors to stderr and progress
  to stdout.
- **FR-015**: The system MUST be implemented as an MCP server
  exposing four tools: `get_today_tasks` (fetch today's Things
  tasks), `get_tomorrow_tasks` (fetch next-business-day Things
  tasks), `get_repo_activity` (fetch raw repo activity), and
  `render_pdf` (accept all briefing data and produce the final
  PDF). Calendar data is supplied by the agent skill from the
  WorkIQ MCP server, not fetched by this MCP server.
- **FR-016**: A single Copilot CLI agent skill file
  (`morning-briefing.agent.md`) MUST be provided. The agent
  orchestrates the full workflow: (1) connect to the WorkIQ MCP
  server for calendar data, (2) call `get_today_tasks` and
  `get_tomorrow_tasks`, (3) call `get_repo_activity`, (4) use
  its own LLM to generate narrative summaries per repo, and
  (5) call `render_pdf` with all assembled data. The agent
  produces a single two-page PDF in one invocation.

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
- Q: How should the tool authenticate with GitHub and ADO? → A: Three-step token resolution: (1) environment variable, (2) platform CLI (`gh` / `az`), (3) macOS Keychain. Simplest approach per Principle I.
- Q: Which types of repository activity should be included? → A: Commits, pull requests (opened/merged/closed), and issue or work-item updates.
- Q: How should the system handle failures (WorkIQ, LLM, Things, GitHub, ADO)? → A: Always render an error notice in the affected PDF section so the printed document makes missing data visible. Additionally log a warning to stderr.
- Q: Should the PDF support A4 paper or only US Letter? → A: US Letter only.
- Q: Should the application be a pure CLI, an MCP server with agent skill, or hybrid? → A: MCP server + Copilot CLI agent skill (Option B). The agent orchestrates data gathering and LLM summarization; the MCP server handles data fetching and PDF rendering. This enables future LLM-powered features like meeting preparation advice.
- Q: How should the daily-planner MCP server access WorkIQ calendar data? → A: The agent calls WorkIQ MCP directly and passes calendar events to the daily-planner's render tool. No `get_calendar` tool on the daily-planner MCP server.
- Q: Where should tokens for GitHub and ADO be stored as a last resort? → A: macOS Keychain via the `keyring` Python library — encrypted, OS-managed, access-controlled. Primary resolution prefers env vars or CLI tools.
- Q: How should the daily-planner MCP server be started? → A: stdio transport — the agent spawns the MCP server as a subprocess automatically; no manual server start needed.

### Session 2026-04-02

- Q: Should the system use one agent skill or multiple? → A: One unified agent skill (`morning-briefing`). It orchestrates the full workflow (calendar → tasks → repo activity → LLM summarization → render_pdf) in a single invocation.
- Q: How many render tools does the MCP server expose? → A: One — `render_pdf` accepts all briefing data and produces the complete PDF. Simpler than separate per-page tools per Principle I.
- Q: Can the PDF be produced with partial data? → A: Yes — `render_pdf` gracefully handles missing sections (null calendar, null tasks, empty repo summaries) and produces a 1- or 2-page PDF accordingly.

## Assumptions

- The Microsoft WorkIQ MCP server provides a standard
  authentication flow (e.g., token-based) and exposes calendar
  events through a documented interface.
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
- The agent orchestrates the complete workflow in a single
  invocation, producing a two-page PDF (or single-page if some
  data is unavailable).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can generate the daily view page in
  under 15 seconds from the time the agent is invoked.
- **SC-001a**: User can generate the repo activity page
  in under 30 seconds from the time the agent is invoked.
- **SC-001b**: User can generate the combined two-page PDF in under
  30 seconds when the agent is invoked.
- **SC-002**: When all data sources are available, every section of
  the PDF (calendar, today's tasks, tomorrow's tasks on page one;
  repo activity on page two) is populated with current data.
- **SC-003**: When any single data source is down, the PDF is still
  generated within 45 seconds, with the unavailable section clearly
  marked.
- **SC-004**: Font-size changes in the config file are reflected in
  the very next PDF generation without code changes or restarts.
- **SC-005**: Adding or removing a repository in the repos config
  file is reflected in the very next agent invocation.
- **SC-006**: Each generated PDF page is printable on US Letter
  paper (8.5 × 11 in) with all content legible and properly laid
  out.
- **SC-007**: The agent gracefully handles partial data — if any
  data source is unavailable, the remaining sections are still
  generated with error notices for the missing data.
