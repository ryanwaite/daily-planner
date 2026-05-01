"""Unit tests for the debug logging module."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date, datetime
from io import StringIO
from pathlib import Path

import pytest

from daily_planner.logging import (
    JsonlFormatter,
    _json_default,
    setup_debug_logging,
    truncate_payload,
)

# ---------------------------------------------------------------------------
# T008 — truncate_payload
# ---------------------------------------------------------------------------


class TestTruncatePayload:
    def test_short_string_unchanged(self):
        assert truncate_payload("hello") == "hello"

    def test_exact_boundary_not_truncated(self):
        s = "x" * 5000
        assert truncate_payload(s) == s

    def test_one_over_boundary_truncated(self):
        s = "x" * 5001
        result = truncate_payload(s)
        assert result == "x" * 5000 + "...[truncated]"

    def test_nested_dict_truncation(self):
        data = {"outer": {"inner": "y" * 6000}}
        result = truncate_payload(data)
        assert len(result["outer"]["inner"]) == 5000 + len("...[truncated]")
        assert result["outer"]["inner"].endswith("...[truncated]")

    def test_list_element_truncation(self):
        data = ["a" * 6000, "short"]
        result = truncate_payload(data)
        assert result[0].endswith("...[truncated]")
        assert result[1] == "short"

    def test_non_string_values_unchanged(self):
        data = {"num": 42, "flag": True, "nothing": None}
        assert truncate_payload(data) == data

    def test_input_not_mutated(self):
        original = {"key": "z" * 6000}
        _ = truncate_payload(original)
        assert len(original["key"]) == 6000  # not mutated

    def test_custom_max_length(self):
        s = "abcdef"
        result = truncate_payload(s, max_length=3)
        assert result == "abc...[truncated]"


# ---------------------------------------------------------------------------
# T009 — JsonlFormatter
# ---------------------------------------------------------------------------


class TestJsonlFormatter:
    def _make_record(self, **extra):
        logger = logging.getLogger("test.formatter")
        record = logger.makeRecord(
            name="test.formatter",
            level=logging.DEBUG,
            fn="test.py",
            lno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        for k, v in extra.items():
            setattr(record, k, v)
        return record

    def test_output_is_valid_single_line_json(self):
        record = self._make_record(operation="test_op")
        fmt = JsonlFormatter()
        line = fmt.format(record)
        parsed = json.loads(line)
        assert isinstance(parsed, dict)
        assert "\n" not in line

    def test_required_fields_present(self):
        record = self._make_record(operation="my_tool")
        fmt = JsonlFormatter()
        parsed = json.loads(fmt.format(record))
        assert "timestamp" in parsed
        assert parsed["level"] == "DEBUG"
        assert parsed["operation"] == "my_tool"
        assert parsed["message"] == "test message"

    def test_optional_fields_omitted_when_absent(self):
        record = self._make_record(operation="op")
        fmt = JsonlFormatter()
        parsed = json.loads(fmt.format(record))
        assert "direction" not in parsed
        assert "data" not in parsed
        assert "traceback" not in parsed
        assert "duration_ms" not in parsed

    def test_optional_fields_present_when_set(self):
        record = self._make_record(
            operation="op",
            direction="request",
            data={"repo": "test"},
            duration_ms=42.5,
        )
        fmt = JsonlFormatter()
        parsed = json.loads(fmt.format(record))
        assert parsed["direction"] == "request"
        assert parsed["data"] == {"repo": "test"}
        assert parsed["duration_ms"] == 42.5

    def test_exc_info_produces_traceback_key(self):
        record = self._make_record(operation="op")
        try:
            raise ValueError("boom")
        except ValueError:
            record.exc_info = sys.exc_info()

        fmt = JsonlFormatter()
        parsed = json.loads(fmt.format(record))
        assert "traceback" in parsed
        assert "ValueError" in parsed["traceback"]
        assert "boom" in parsed["traceback"]

    def test_data_field_is_truncated(self):
        record = self._make_record(operation="op", data={"big": "x" * 6000})
        fmt = JsonlFormatter()
        parsed = json.loads(fmt.format(record))
        assert parsed["data"]["big"].endswith("...[truncated]")

    def test_non_serializable_types_handled(self):
        record = self._make_record(
            operation="op",
            data={
                "date": date(2026, 4, 26),
                "dt": datetime(2026, 4, 26, 8, 30),
                "path": Path("/tmp/test"),
            },
        )
        fmt = JsonlFormatter()
        parsed = json.loads(fmt.format(record))
        assert parsed["data"]["date"] == "2026-04-26"
        assert "2026-04-26" in parsed["data"]["dt"]
        assert parsed["data"]["path"] == "/tmp/test"

    def test_operation_defaults_to_unknown(self):
        record = self._make_record()
        fmt = JsonlFormatter()
        parsed = json.loads(fmt.format(record))
        assert parsed["operation"] == "unknown"


# ---------------------------------------------------------------------------
# T010 — setup_debug_logging
# ---------------------------------------------------------------------------


class TestSetupDebugLogging:
    def _cleanup_logger(self):
        logger = logging.getLogger("daily_planner.debug")
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)
        logger.setLevel(logging.WARNING)

    def setup_method(self):
        self._cleanup_logger()

    def teardown_method(self):
        self._cleanup_logger()

    def test_returns_logger_with_filehandler_when_env_set(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_returns_logger_with_nullhandler_when_env_unset(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DAILY_PLANNER_DEBUG", raising=False)
        logger = setup_debug_logging(tmp_path)
        assert all(isinstance(h, logging.NullHandler) for h in logger.handlers)
        assert len(logger.handlers) == 1

    def test_log_file_created_with_correct_pattern(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        setup_debug_logging(tmp_path)
        files = list(tmp_path.glob("debug_*.jsonl"))
        assert len(files) == 1
        name = files[0].name
        assert name.startswith("debug_")
        assert name.endswith(".jsonl")
        # Contains PID
        assert str(os.getpid()) in name

    def test_unwritable_dir_emits_stderr_warning(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        bad_dir = tmp_path / "nope"
        bad_dir.mkdir()
        bad_dir.chmod(0o000)
        try:
            captured = StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured
            try:
                logger = setup_debug_logging(bad_dir / "subdir")
            finally:
                sys.stderr = old_stderr
            assert all(isinstance(h, logging.NullHandler) for h in logger.handlers)
            assert "Warning" in captured.getvalue()
        finally:
            bad_dir.chmod(0o755)

    def test_logger_has_propagate_false(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)
        assert logger.propagate is False

    def test_only_file_handler_no_stream_handler(self, tmp_path, monkeypatch):
        """T032: Logger has only FileHandler, no StreamHandler."""
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert not any(
            isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
            for h in logger.handlers
        )

    def test_no_stdout_pollution(self, tmp_path, monkeypatch):
        """T033: Debug log writes produce no stdout or stderr output."""
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_out = StringIO()
        captured_err = StringIO()
        try:
            sys.stdout = captured_out
            sys.stderr = captured_err
            logger.debug("test message", extra={"operation": "test"})
            logger.info("info message", extra={"operation": "test"})
            for h in logger.handlers:
                h.flush()
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        assert captured_out.getvalue() == ""
        assert captured_err.getvalue() == ""
