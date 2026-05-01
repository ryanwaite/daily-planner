"""Unit tests for local .tmp/ directory configuration."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from daily_planner.__main__ import _setup_local_tmpdir


class TestSetupLocalTmpdir:
    """Verify that _setup_local_tmpdir sets both TMPDIR and tempfile.tempdir."""

    def test_sets_tmpdir_env_var(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_local_tmpdir()
        assert os.environ.get("TMPDIR") == str(tmp_path / ".tmp")

    def test_sets_tempfile_tempdir(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        original = tempfile.tempdir
        try:
            tempfile.tempdir = None
            _setup_local_tmpdir()
            assert tempfile.tempdir == str(tmp_path / ".tmp")
        finally:
            tempfile.tempdir = original

    def test_creates_tmp_directory(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _setup_local_tmpdir()
        assert (tmp_path / ".tmp").is_dir()

    def test_tmpdir_env_and_tempfile_tempdir_agree(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        original = tempfile.tempdir
        try:
            tempfile.tempdir = None
            _setup_local_tmpdir()
            assert os.environ.get("TMPDIR") == tempfile.tempdir
        finally:
            tempfile.tempdir = original


class TestRendererRlTmpdir:
    """Verify that importing the renderer module points ReportLab at .tmp/reportlab/.
    
    DEPRECATED: PDF feature was removed in spec 005 (markdown-briefing-overhaul).
    These tests are obsolete and marked as skipped.
    """

    @pytest.mark.skip(reason="PDF feature removed in spec 005; using markdown instead")
    def test_renderer_configures_rl_tempdir_to_local_tmp(self):
        """After renderer is imported, _rl_tempdir must point to .tmp/reportlab/ under cwd."""
        from reportlab.lib import rltempfile

        import daily_planner.pdf.renderer  # noqa: F401

        assert rltempfile._rl_tempdir is not None
        rl_dir = Path(rltempfile._rl_tempdir)
        # Must be named "reportlab" inside a ".tmp" directory
        assert rl_dir.name == "reportlab"
        assert rl_dir.parent.name == ".tmp"

    @pytest.mark.skip(reason="PDF feature removed in spec 005; using markdown instead")
    def test_renderer_rl_tempdir_exists(self):
        """The .tmp/reportlab/ directory must be created by the renderer on import."""
        from reportlab.lib import rltempfile

        import daily_planner.pdf.renderer  # noqa: F401

        assert rltempfile._rl_tempdir is not None
        assert Path(rltempfile._rl_tempdir).is_dir()
