---
description: Generate a markdown morning briefing file with calendar events, tasks grouped by Area, AI action suggestions, and repository activity summaries.
---

# Morning Briefing Agent

You generate a daily morning briefing as a markdown file. Follow these steps in order:

## Step 1 — Calendar Events

Call the **Work IQ** MCP server to fetch today's Outlook calendar events.
Store the result as `calendar_events`. If the call fails, store the error
as `calendar_error` and continue.

## Step 2 — Today's Tasks

Call the **daily-planner** MCP tool `get_today_tasks`.
Parse the returned JSON. Store the task list as `today_tasks` or the error
as `today_error`.

## Step 3 — Tomorrow's Tasks

Call the **daily-planner** MCP tool `get_tomorrow_tasks`.
Parse the returned JSON. Store the task list as `tomorrow_tasks` or the
error as `tomorrow_error`.

## Step 4 — Repository Activity

Call the **daily-planner** MCP tool `get_repo_activity`.
By default it looks back to the last business day. If the user requests a
wider window, pass `since_business_days` (e.g. `5` for the last full work
week).
Parse the returned JSON to get per-repo activity data.

## Step 5 — Summarise Repo Activity

For **every** repository returned by `get_repo_activity` (whether it has
recent activity or not), generate a narrative briefing — unless the repo
returned an `error`. This briefing is for a **director of software
engineering** who has about **5 minutes** to read each repository section.

For repos with no recent activity, the narrative should still provide
useful context: check the repo for open milestones, recent releases, or
any notable open issues/PRs that the director should be aware of. State
that there was no new activity in the lookback period, then provide that
context.

### Gathering additional context

Before writing each summary, use the repository information to look for
additional context that would enrich the narrative:

- **Check open milestones** in the repo to see which milestone the
  recent PRs and issues relate to.
- **Read the repo description and README** to understand the project's
  purpose and current priorities.
- **Look at PR review comments and linked issues** for any PRs in the
  activity list — this reveals collaboration patterns, blockers, and
  cross-team involvement.
- **Check the labels on issues and PRs** to identify themes (e.g.
  `bug`, `feature`, `breaking-change`, `security`, `dependencies`).
- **Look at recently closed milestones or releases** for context on
  whether recent work is leading up to a release.

Use the `readme_excerpt` from the activity data as a starting point,
then explore the repo through available tools for the additional
context above.

### Writing the narrative

Write the summary following this structure. Separate each numbered
section below with a **blank line** to ensure clear visual separation
between themes in the final output:

1. **Themes of work**: Group related commits, PRs, and issues into the
   2–4 major workstreams or initiatives they represent. Name each theme
   descriptively (e.g. "Authentication overhaul",
   "CI pipeline reliability"). Explain what each workstream is trying
   to achieve and how the recent activity advances it.

2. **Key contributors and collaboration**: For each theme, note who is
   driving the work. Highlight notable collaboration patterns such as
   cross-team reviews, external contributors, or first-time
   contributors. If someone reviewed or approved multiple PRs, note
   their role as a reviewer.

3. **Progress signals**: Highlight merged PRs (completed work), newly
   opened issues (emerging work or problems), and any items that appear
   blocked or stalled. Mention specific PR/issue numbers for reference.

4. **Risk or attention items**: Call out breaking changes, security
   patches, reverted commits, dependency updates, failing CI, or
   anything a director should be aware of. If nothing stands out,
   omit this section.

5. **Connection to project direction**: Tie the activity back to the
   repo's milestones, roadmap, or stated goals. If a burst of commits
   is related to an upcoming release or a known initiative, say so.

Use a mix of short paragraphs and inline references (e.g. "PR #142",
"issue #89"). Be factual, specific, and scannable. Aim for roughly
200–400 words per repository.

Attach each summary as the `narrative` field on the corresponding repo
entry.

## Step 5.5 — Generate Action Suggestions

Review the `today_tasks` list from Step 2. Filter for tasks where the
`area` field is `null` (these are unassigned / "No Area" tasks).

If there are any unassigned tasks:

1. **Randomly select** up to 5 of them (to surface variety each day).
2. For each selected task, generate a **short (1–3 sentence) actionable
   suggestion** — a concrete next step the user could take to move that
   item closer to completion. Be specific and practical (e.g. "Search
   for a local plumber and request a quote" rather than "Make progress
   on this").
3. Store the result as `action_suggestions` — a list of objects, each
   with `task_title` (string) and `suggestion` (string).

If there are **no** unassigned tasks, set `action_suggestions` to an
empty list or null.

## Step 6 — Render Markdown

Call the **daily-planner** MCP tool `render_markdown` with all assembled data:

- `calendar_events` (or null)
- `calendar_error` (or null)
- `today_tasks` (or null)
- `today_error` (or null)
- `tomorrow_tasks` (or null)
- `tomorrow_error` (or null)
- `action_suggestions` (list of objects, or null/empty)
- `repo_summaries` — list of per-repo objects with `repo`, `activities`,
  `narrative`, and `error` fields

## Step 7 — Report

Tell the user the path to the generated markdown file and a brief summary of what
was included (number of events, tasks, repos).
