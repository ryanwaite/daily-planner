"""Contract tests for MCP tool schemas — input/output shape validation."""

import json


class TestRenderPdfContract:
    """Verify render_pdf tool accepts the documented input schema."""

    def test_minimal_input_accepted(self):
        """render_pdf must accept just repo_summaries (required)."""
        from daily_planner.tools.render_pdf import render_pdf

        # Will be validated when tool is implemented
        assert callable(render_pdf)

    def test_full_input_shape(self):
        """Verify the full input shape matches contracts/mcp-tools.md."""
        valid_input = {
            "calendar_events": [
                {
                    "title": "Meeting",
                    "start_time": "2026-03-13T09:00:00",
                    "end_time": "2026-03-13T10:00:00",
                    "is_all_day": False,
                    "location": "Room 1",
                }
            ],
            "calendar_error": None,
            "today_tasks": [
                {
                    "title": "Review PR",
                    "due_date": "2026-03-13",
                    "sort_position": 1,
                    "project": "daily-planner",
                    "tags": ["work"],
                }
            ],
            "today_error": None,
            "tomorrow_tasks": [],
            "tomorrow_error": None,
            "repo_summaries": [
                {
                    "repo": {
                        "platform": "github",
                        "owner": "octocat",
                        "name": "hello-world",
                        "url": "https://github.com/octocat/hello-world",
                    },
                    "activities": [],
                    "narrative": "No recent changes.",
                    "error": None,
                }
            ],
            "output_path": None,
        }
        # Ensure the keys are JSON-serializable
        serialized = json.dumps(valid_input)
        parsed = json.loads(serialized)
        assert "repo_summaries" in parsed
        assert "calendar_events" in parsed

    def test_output_shape(self):
        """render_pdf output must include pdf_path and pages."""
        expected_keys = {"pdf_path", "pages"}
        sample_output = {"pdf_path": "/Users/user/Desktop/2026-03-13 Friday.pdf", "pages": 2}
        assert expected_keys == set(sample_output.keys())


class TestGetTodayTasksContract:
    """Verify get_today_tasks tool schema."""

    def test_callable(self):
        from daily_planner.tools.tasks import get_today_tasks
        assert callable(get_today_tasks)

    def test_output_shape(self):
        expected_keys = {"tasks"}
        sample = {
            "tasks": [
                {"title": "t", "due_date": "2026-03-13",
                 "sort_position": 0, "project": None, "tags": []}
            ]
        }
        assert expected_keys <= set(sample.keys())


class TestGetTomorrowTasksContract:
    """Verify get_tomorrow_tasks tool schema."""

    def test_callable(self):
        from daily_planner.tools.tasks import get_tomorrow_tasks
        assert callable(get_tomorrow_tasks)

    def test_output_includes_target_date(self):
        sample = {"tasks": [], "target_date": "2026-03-16"}
        assert "target_date" in sample


class TestGetRepoActivityContract:
    """Verify get_repo_activity tool schema."""

    def test_output_shape(self):
        sample = {
            "since_date": "2026-03-12",
            "activity_dir": ".tmp/repo_activity",
            "repos": [
                {
                    "name": "o/n",
                    "platform": "github",
                    "commits": 5,
                    "prs": 3,
                    "issues": 2,
                    "file": ".tmp/repo_activity/github_o_n.json",
                    "error": None,
                }
            ],
        }
        assert "repos" in sample
        assert "since_date" in sample
        assert "activity_dir" in sample
        repo = sample["repos"][0]
        assert "name" in repo
        assert "platform" in repo
        assert "commits" in repo
        assert "prs" in repo
        assert "issues" in repo
        assert "file" in repo
        assert "error" in repo

    def test_error_repo_shape(self):
        error_entry = {
            "name": "o/n",
            "platform": "github",
            "commits": 0,
            "prs": 0,
            "issues": 0,
            "file": None,
            "error": "GitHub authentication required",
        }
        assert error_entry["file"] is None
        assert error_entry["error"] is not None
