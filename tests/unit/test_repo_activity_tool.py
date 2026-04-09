"""Unit tests for the get_repo_activity tool handler — file-based output."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from daily_planner.models.repo import ActivityItem, Repository
from daily_planner.tools.repo_activity import _repo_file_name

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_repo(platform="github", owner="acme", name="anvil"):
    return Repository(
        platform=platform,
        owner=owner,
        name=name,
        url=f"https://example.com/{owner}/{name}",
    )


def _make_activity(repo, activity_type="commit"):
    return ActivityItem(
        repo=repo,
        activity_type=activity_type,
        title=f"A {activity_type}",
        author="alice",
        timestamp=datetime(2026, 4, 3, 10, 0, 0, tzinfo=UTC),
        url="https://example.com/1",
    )


# ---------------------------------------------------------------------------
# _repo_file_name helper
# ---------------------------------------------------------------------------

class TestRepoFileName:
    def test_github_simple(self):
        repo = _make_repo(platform="github", owner="acme", name="anvil")
        assert _repo_file_name(repo) == "github_acme_anvil.json"

    def test_github_owner_with_hyphen(self):
        repo = _make_repo(platform="github", owner="radius-project", name="radius")
        assert _repo_file_name(repo) == "github_radius-project_radius.json"

    def test_ado_repo(self):
        repo = Repository(
            platform="ado",
            owner="myorg",
            name="backend",
            url="https://dev.azure.com/myorg/myproject/_git/backend",
            project="myproject",
        )
        assert _repo_file_name(repo) == "ado_myorg_backend.json"


# ---------------------------------------------------------------------------
# get_repo_activity integration (mocked externals)
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_activity_dir(tmp_path, monkeypatch):
    """Redirect _ACTIVITY_DIR to a temp directory for the duration of the test."""
    activity_dir = tmp_path / "repo_activity"
    monkeypatch.setattr(
        "daily_planner.tools.repo_activity._ACTIVITY_DIR", activity_dir
    )
    return activity_dir


def _mock_config(repos_file="repos.txt"):
    cfg = MagicMock()
    cfg.repos_file = repos_file
    return cfg


_MOD = "daily_planner.tools.repo_activity"


class TestGetRepoActivityTool:
    """Verify that get_repo_activity writes files and returns a summary."""

    async def test_writes_per_repo_file(self, tmp_activity_dir):
        repo = _make_repo()
        activities = [
            _make_activity(repo, "commit"),
            _make_activity(repo, "pr"),
            _make_activity(repo, "issue"),
        ]
        with (
            patch(f"{_MOD}.load_configuration", return_value=_mock_config()),
            patch(f"{_MOD}.load_repositories", return_value=[repo]),
            patch(f"{_MOD}.get_github_token", return_value="tok"),
            patch(f"{_MOD}.get_ado_token", return_value=None),
            patch(
                f"{_MOD}.fetch_github_activity",
                new=AsyncMock(return_value=(activities, "readme text")),
            ),
            patch(f"{_MOD}.last_business_day", return_value=date(2026, 4, 3)),
        ):
            from daily_planner.tools.repo_activity import get_repo_activity
            result = await get_repo_activity()

        summary = json.loads(result)
        assert summary["since_date"] == "2026-04-03"
        assert "activity_dir" in summary

        # One repo entry in summary
        assert len(summary["repos"]) == 1
        entry = summary["repos"][0]
        assert entry["name"] == "acme/anvil"
        assert entry["platform"] == "github"
        assert entry["commits"] == 1
        assert entry["prs"] == 1
        assert entry["issues"] == 1
        assert entry["error"] is None

        # File should exist
        file_path = tmp_activity_dir / "github_acme_anvil.json"
        assert file_path.exists(), "Per-repo JSON file was not created"

        # File content should be valid per-repo data
        data = json.loads(file_path.read_text())
        assert data["repo"]["owner"] == "acme"
        assert data["repo"]["name"] == "anvil"
        assert len(data["activities"]) == 3
        assert data["readme_excerpt"] == "readme text"
        assert data["error"] is None

        # Summary file path should be relative
        assert entry["file"].startswith(".tmp")

    async def test_error_repo_has_null_file(self, tmp_activity_dir):
        repo = _make_repo()
        with (
            patch(f"{_MOD}.load_configuration", return_value=_mock_config()),
            patch(f"{_MOD}.load_repositories", return_value=[repo]),
            patch(f"{_MOD}.get_github_token", return_value=None),
            patch(f"{_MOD}.get_ado_token", return_value=None),
            patch(f"{_MOD}.last_business_day", return_value=date(2026, 4, 3)),
        ):
            from daily_planner.tools.repo_activity import get_repo_activity
            result = await get_repo_activity()

        summary = json.loads(result)
        assert len(summary["repos"]) == 1
        entry = summary["repos"][0]
        assert entry["file"] is None
        assert entry["error"] == "GitHub authentication required"
        assert entry["commits"] == 0

    async def test_activity_dir_created(self, tmp_activity_dir):
        """The .tmp/repo_activity directory is created even if it doesn't exist yet."""
        assert not tmp_activity_dir.exists()

        repo = _make_repo()
        with (
            patch(f"{_MOD}.load_configuration", return_value=_mock_config()),
            patch(f"{_MOD}.load_repositories", return_value=[repo]),
            patch(f"{_MOD}.get_github_token", return_value="tok"),
            patch(f"{_MOD}.get_ado_token", return_value=None),
            patch(
                f"{_MOD}.fetch_github_activity",
                new=AsyncMock(return_value=([], None)),
            ),
            patch(f"{_MOD}.last_business_day", return_value=date(2026, 4, 3)),
        ):
            from daily_planner.tools.repo_activity import get_repo_activity
            await get_repo_activity()

        assert tmp_activity_dir.exists()

    async def test_summary_is_small(self, tmp_activity_dir):
        """Summary should be well under 5 KB even for many activities."""
        repo = _make_repo()
        # Simulate 200 activities
        activities = [_make_activity(repo, "commit") for _ in range(200)]
        with (
            patch(f"{_MOD}.load_configuration", return_value=_mock_config()),
            patch(f"{_MOD}.load_repositories", return_value=[repo]),
            patch(f"{_MOD}.get_github_token", return_value="tok"),
            patch(f"{_MOD}.get_ado_token", return_value=None),
            patch(
                f"{_MOD}.fetch_github_activity",
                new=AsyncMock(return_value=(activities, None)),
            ),
            patch(f"{_MOD}.last_business_day", return_value=date(2026, 4, 3)),
        ):
            from daily_planner.tools.repo_activity import get_repo_activity
            result = await get_repo_activity()

        assert len(result.encode()) < 5 * 1024, (
            f"Summary exceeds 5 KB: {len(result.encode())} bytes"
        )
        summary = json.loads(result)
        assert summary["repos"][0]["commits"] == 200
