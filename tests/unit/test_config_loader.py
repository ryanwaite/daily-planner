"""Unit tests for config loader — settings.toml and repos.txt parsing."""

import textwrap
from pathlib import Path

import pytest

from daily_planner.config.loader import load_configuration, load_repositories


class TestLoadConfiguration:
    def test_missing_file_returns_defaults(self, tmp_path: Path):
        cfg = load_configuration(str(tmp_path / "nonexistent.toml"))
        assert cfg.output_path == "~/Desktop"
        assert cfg.repos_file == "config/repos.txt"

    def test_valid_toml(self, tmp_path: Path):
        toml_file = tmp_path / "settings.toml"
        toml_file.write_text(textwrap.dedent("""\
            [output]
            path = "~/Documents"
            repos_file = "my_repos.txt"
        """))
        cfg = load_configuration(str(toml_file))
        assert cfg.output_path == "~/Documents"
        assert cfg.repos_file == "my_repos.txt"

    def test_partial_toml_uses_defaults(self, tmp_path: Path):
        toml_file = tmp_path / "settings.toml"
        toml_file.write_text("[output]\npath = \"~/Downloads\"\n")
        cfg = load_configuration(str(toml_file))
        assert cfg.output_path == "~/Downloads"
        assert cfg.repos_file == "config/repos.txt"  # default


class TestLoadRepositories:
    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match="Repos config file not found"):
            load_repositories(tmp_path / "no_such_file.txt")

    def test_valid_github_repo(self, tmp_path: Path):
        f = tmp_path / "repos.txt"
        f.write_text("github:octocat/hello-world\n")
        repos = load_repositories(f)
        assert len(repos) == 1
        assert repos[0].platform == "github"
        assert repos[0].owner == "octocat"
        assert repos[0].name == "hello-world"
        assert "github.com" in repos[0].url

    def test_valid_ado_repo(self, tmp_path: Path):
        f = tmp_path / "repos.txt"
        f.write_text("ado:myorg/myproject/myrepo\n")
        repos = load_repositories(f)
        assert len(repos) == 1
        assert repos[0].platform == "ado"
        assert repos[0].project == "myproject"

    def test_mixed_repos(self, tmp_path: Path):
        f = tmp_path / "repos.txt"
        f.write_text("github:a/b\nado:o/p/r\n")
        repos = load_repositories(f)
        assert len(repos) == 2

    def test_comments_and_blanks_skipped(self, tmp_path: Path):
        f = tmp_path / "repos.txt"
        f.write_text("# my repos\n\ngithub:a/b\n  \n")
        repos = load_repositories(f)
        assert len(repos) == 1

    def test_invalid_line_skipped_with_warning(self, tmp_path: Path, capsys):
        f = tmp_path / "repos.txt"
        f.write_text("github:a/b\nbadformat\ngithub:c/d\n")
        repos = load_repositories(f)
        assert len(repos) == 2
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "badformat" in captured.err

    def test_invalid_github_format_skipped(self, tmp_path: Path, capsys):
        f = tmp_path / "repos.txt"
        f.write_text("github:only_one_part\n")
        repos = load_repositories(f)
        assert len(repos) == 0
        assert "Warning" in capsys.readouterr().err

    def test_unknown_platform_skipped(self, tmp_path: Path, capsys):
        f = tmp_path / "repos.txt"
        f.write_text("gitlab:user/repo\n")
        repos = load_repositories(f)
        assert len(repos) == 0
        assert "Unknown platform" in capsys.readouterr().err
