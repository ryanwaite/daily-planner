# Feature Specification: Markdown Briefing Overhaul

**Feature Branch**: `005-markdown-briefing-overhaul`  
**Created**: 2026-04-26  
**Status**: Draft  
**Input**: User description: "Switch from PDF to markdown output, add output path configuration, group Things tasks by Area, add AI action suggestions for unassigned tasks, and improve repo report formatting with line breaks between themes"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Markdown Output Instead of PDF (Priority: P1)

The user invokes the morning briefing agent and receives a markdown file instead of a PDF. The markdown file contains all the same information as the current PDF (calendar events, tasks, repository activity) but rendered as well-structured markdown that can be opened, read, and searched in any text editor, IDE, or markdown viewer.

**Why this priority**: This is the foundational change. All other stories build on top of the markdown output format. Without this, no other changes can be verified.

**Independent Test**: Invoke the morning briefing agent end-to-end and confirm a `.md` file is produced at the configured output location with all expected sections populated.

**Acceptance Scenarios**:

1. **Given** the MCP server is running and all data sources are available, **When** the agent completes the briefing workflow, **Then** a markdown file is written to disk containing sections for Calendar Events, Today Tasks, Tomorrow Tasks, and Repository Activity.
2. **Given** the briefing workflow completes, **When** the user opens the markdown file, **Then** the content is valid markdown that renders correctly in a standard markdown viewer.
3. **Given** the MCP server is running, **When** the agent calls the render tool, **Then** no PDF file is generated — only a markdown file.

---

### User Story 2 — Configurable Output Path (Priority: P1)

The user specifies the output directory for the generated markdown file in the settings configuration file. The configuration file already contains an `[output]` section; the output path setting there now controls where the markdown file is placed.

**Why this priority**: The user needs to control where the file lands. This is tightly coupled to Story 1 since changing the output format requires updating the output path handling.

**Independent Test**: Change the `path` value in `config/settings.toml`, run the briefing, and confirm the markdown file appears in the specified directory.

**Acceptance Scenarios**:

1. **Given** the settings file has `path = "~/Documents/briefings"`, **When** the briefing is rendered, **Then** the markdown file is saved to `~/Documents/briefings/`.
2. **Given** the output directory does not exist, **When** the briefing is rendered, **Then** the directory is created and the file is saved there.
3. **Given** the output path is not specified in the settings file, **When** the briefing is rendered, **Then** a sensible default location is used (e.g., `~/Desktop`).

---

### User Story 3 — Tasks Grouped by Things Area (Priority: P2)

When the morning briefing is generated, the task lists (Today and Tomorrow) display tasks organized under their Things "Area" headings. Tasks that do not belong to any Area appear at the top of the list under a clearly labeled group (e.g., "No Area").

**Why this priority**: This provides meaningful structure to what is currently a flat list, making the briefing more scannable. It is independent of the output format change but depends on the markdown renderer being in place.

**Independent Test**: Create tasks in Things 3 across multiple Areas and some with no Area, run the briefing, and confirm the markdown output groups tasks under the correct Area headings with unassigned tasks listed first.

**Acceptance Scenarios**:

1. **Given** today's tasks include items in "Work", "Personal", and no Area, **When** the briefing is rendered, **Then** the Today Tasks section shows tasks grouped under "No Area" (first), "Personal", and "Work" headings.
2. **Given** all tasks belong to an Area, **When** the briefing is rendered, **Then** no "No Area" group appears.
3. **Given** a task belongs to a Project that is inside an Area, **When** the briefing is rendered, **Then** that task appears under the correct Area heading.
4. **Given** the `get_today_tasks` or `get_tomorrow_tasks` tool is called, **When** the JSON is returned, **Then** each task object includes its `area` field (or null if unassigned).

---

### User Story 4 — AI Action Suggestions for Unassigned Tasks (Priority: P2)

The briefing includes a new section between the task lists and the Repository Activity section. This section picks up to 5 tasks from the "No Area" (unassigned) group and provides a short, actionable suggestion for each one — a concrete next step the user could take to move that item closer to completion.

**Why this priority**: This adds unique value by leveraging the LLM agent's reasoning ability to provide personalized productivity coaching. It depends on the Area grouping (Story 3) to identify unassigned tasks.

**Independent Test**: Ensure there are at least 5 unassigned tasks in Things, run the briefing, and confirm the markdown file contains a section with exactly 5 (or fewer if fewer exist) tasks, each with a suggestion.

**Acceptance Scenarios**:

1. **Given** there are 8 unassigned tasks, **When** the briefing is rendered, **Then** the "Action Suggestions" section contains exactly 5 tasks with suggestions.
2. **Given** there are 3 unassigned tasks, **When** the briefing is rendered, **Then** the "Action Suggestions" section contains all 3 tasks with suggestions.
3. **Given** there are no unassigned tasks, **When** the briefing is rendered, **Then** the "Action Suggestions" section is omitted entirely.
4. **Given** an unassigned task titled "Fix the leaky faucet", **When** the agent generates a suggestion, **Then** the suggestion is a specific, actionable next step (e.g., "Search for a local plumber and request a quote, or watch a 10-minute YouTube tutorial on fixing a compression faucet").
5. **Given** the briefing is generated, **When** the user reads the Action Suggestions section, **Then** each suggestion is 1–3 sentences, specific, and oriented toward making tangible progress.

---

### User Story 5 — Improved Repository Report Formatting (Priority: P3)

In the Repository Activity section of the markdown output, each repository's narrative includes visual separation (blank lines) between the major themes of work. This makes large repository reports easier to scan rather than appearing as a wall of text.

**Why this priority**: This is a presentation polish item. The content is already correct; this improves readability. Lowest priority because it is cosmetic and does not change data or behavior.

**Independent Test**: Generate a briefing for a repository with multiple themes of work and confirm the markdown output has clear visual separation between themes.

**Acceptance Scenarios**:

1. **Given** a repository narrative contains 3 themes of work, **When** the markdown is rendered, **Then** each theme is separated by a blank line.
2. **Given** a repository narrative contains only 1 theme, **When** the markdown is rendered, **Then** no extra separators are inserted.
3. **Given** the agent writes a narrative, **When** formatting is applied, **Then** the narrative retains all factual content — only whitespace is added.

---

### Edge Cases

- What happens when Things 3 is not installed or the database is inaccessible? The briefing should still render with an error message in the tasks section, same as today.
- What happens when no repositories have any activity? The Repository Activity section should still appear with a note that no recent activity was found.
- What happens when the configured output directory is not writable? The system should raise a clear error message indicating the path is not writable.
- What happens when a task's Area is renamed in Things between the data fetch and render? The system uses the Area name at the time of fetch; no real-time sync is expected.
- What happens when all tasks are assigned to Areas? The "No Area" group does not appear, and the Action Suggestions section is omitted.
- What happens when the briefing is run multiple times on the same day? The existing file is overwritten silently with the latest data.

## Clarifications

### Session 2026-04-26

- Q: If the user runs the morning briefing twice on the same day, what should happen to the existing file? → A: Overwrite the existing file silently.
- Q: When more than 5 unassigned tasks exist, how should the 5 for Action Suggestions be chosen? → A: Pick randomly to surface variety each day.
- Q: Should the application keep the MCP server architecture or switch to Skills + Python scripts? → A: Keep MCP server (already built, change only what the spec describes).
- Q: The current MCP tool is named `render_pdf`. Since the output is now markdown, should the tool be renamed? → A: Rename to `render_markdown`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a markdown (`.md`) file as the output format instead of a PDF. The MCP tool MUST be renamed from `render_pdf` to `render_markdown`.
- **FR-002**: System MUST read the output directory path from the `[output]` section of `config/settings.toml`.
- **FR-003**: System MUST create the output directory if it does not already exist.
- **FR-004**: System MUST name the output file with the current date (e.g., `morning-briefing-2026-04-26.md`). If a file with the same name already exists, it MUST be overwritten silently.
- **FR-005**: System MUST include the following sections in the markdown output, in order: Calendar Events, Today Tasks, Tomorrow Tasks, Action Suggestions (conditional), Repository Activity.
- **FR-006**: System MUST group tasks under their Things Area heading, with each Area as a subheading.
- **FR-007**: System MUST place tasks that have no assigned Area at the top of the task list under a "No Area" heading.
- **FR-008**: System MUST sort Area groups by Area creation date (oldest first) after the "No Area" group. If creation date is unavailable, fall back to alphabetical order.
- **FR-009**: System MUST include an "Action Suggestions" section that selects up to 5 tasks randomly from the unassigned (No Area) group to surface variety across runs.
- **FR-010**: For each selected unassigned task, the agent MUST generate a short (1–3 sentence) actionable suggestion describing a concrete next step to move the task toward completion.
- **FR-011**: System MUST omit the "Action Suggestions" section entirely when there are no unassigned tasks.
- **FR-012**: The `get_today_tasks` and `get_tomorrow_tasks` MCP tools MUST include the `area` field in each task's JSON output.
- **FR-013**: Repository narratives MUST include line breaks (blank lines) between major themes of work.
- **FR-014**: System MUST validate that the output path resolves within the user's home directory (existing security constraint).
- **FR-015**: System MUST remove all PDF generation code and dependencies (ReportLab) from the rendering pipeline. The `render_pdf` tool handler, server registration, and `pdf/` module MUST be replaced by the `render_markdown` equivalents.
- **FR-016**: System MUST remove all PDF-specific configuration: the `[page_one]` and `[page_two]` sections (including `font_size` settings) from `config/settings.toml`, and the corresponding `page_one_font_size` / `page_two_font_size` fields from the Configuration model. The `render_markdown` tool response MUST NOT include a `pages` count.

### Key Entities

- **Task**: A Things 3 to-do item. Key attributes: title, due date, sort position, project, area (nullable), tags.
- **Area**: A Things 3 organizational grouping for tasks. Key attributes: name, creation date. A task belongs to zero or one Area.
- **Repository**: A GitHub or Azure DevOps repository being tracked. Key attributes: platform, owner, name.
- **RepoSummary**: Narrative and activity data for a repository. Key attributes: repo, narrative, activities, error.
- **BriefingData**: Container for all sections of the morning briefing. Key attributes: date, config, calendar events, today tasks, tomorrow tasks, repo summaries.
- **Configuration**: Settings for the briefing. Key attributes: output path, repos file path. (Font size and page layout attributes are removed as part of the PDF-to-markdown transition.)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The morning briefing produces a valid markdown file that renders correctly in any standard markdown viewer (GitHub, VS Code, Obsidian).
- **SC-002**: The briefing file appears in the directory specified by the user's configuration within the same time it currently takes to generate the PDF.
- **SC-003**: 100% of tasks with assigned Areas appear under their correct Area heading in the output.
- **SC-004**: The "No Area" group always appears before any named Area groups when unassigned tasks exist.
- **SC-005**: The Action Suggestions section contains at most 5 items, each with a specific, actionable recommendation that a reader can act on immediately.
- **SC-006**: Repository narratives with multiple themes have visible separation between themes, requiring no more than 2 seconds of visual scanning to identify distinct themes.
- **SC-007**: All existing MCP tool contracts (input/output schemas) remain backward-compatible or are updated with clear versioning so the agent can adapt.

## Assumptions

- The existing `config/settings.toml` file is the correct place for output path configuration. The `[output]` section already exists and can be extended.
- The markdown file naming convention uses the date of generation (e.g., `morning-briefing-2026-04-26.md`). This intentionally departs from the constitution's `YYYY-MM-DD dddd` filename convention because the `morning-briefing-` prefix provides sufficient context and spaces in filenames are undesirable.
- "Area" in Things 3 refers to the top-level organizational grouping accessible via the Things SQLite database. The existing `things.py` integration already reads Area data.
- The action suggestions are generated by the LLM agent (in the agent instructions), not by the MCP server itself. The MCP server surfaces the unassigned tasks; the agent writes the suggestions and passes them back for inclusion in the markdown.
- The agent identifies unassigned tasks by filtering the `get_today_tasks` response for tasks with a null `area` field. No new MCP tool is needed for this.
- The MCP server architecture is retained. No migration to Skills + Python scripts.
- ReportLab and all PDF-specific code can be fully removed since the output format is changing to markdown.
- The agent instructions (`.github/agents/morning-briefing.agent.md`) will need to be updated to reflect the new workflow steps (Area grouping, action suggestions, markdown rendering).
- **Constitution follow-up**: The constitution (v1.2.0) references "PDF" in Principles II, IV, V, and Technology Standards. A separate constitution amendment PR should be filed after this feature lands to update those references to markdown/format-agnostic language.
