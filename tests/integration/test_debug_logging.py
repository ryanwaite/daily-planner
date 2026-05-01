"""Integration tests for debug logging — file creation, content, edge cases."""

from __future__ import annotations

import json
import logging
import re

from daily_planner.logging import setup_debug_logging


class TestDebugLogFileCreation:
    """T021: With DAILY_PLANNER_DEBUG=1, verify log file is created with valid JSONL."""

    def test_log_file_created_with_correct_pattern(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)

        logger.debug("hello", extra={"operation": "test"})

        # Flush handlers
        for h in logger.handlers:
            h.flush()

        files = list(tmp_path.glob("debug_*.jsonl"))
        assert len(files) == 1
        assert re.match(r"debug_\d{4}-\d{2}-\d{2}_\d{6}_\d+\.jsonl", files[0].name)

    def test_log_file_contains_valid_jsonl(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)

        logger.debug("msg1", extra={"operation": "op1", "direction": "request"})
        logger.debug(
            "msg2",
            extra={"operation": "op2", "direction": "response", "data": {"k": "v"}},
        )
        logger.info("msg3", extra={"operation": "op3"})

        for h in logger.handlers:
            h.flush()

        files = list(tmp_path.glob("debug_*.jsonl"))
        lines = files[0].read_text().strip().splitlines()
        assert len(lines) == 3

        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "level" in entry
            assert "operation" in entry
            assert "message" in entry

    def test_required_fields_present(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)

        logger.debug(
            "tool start",
            extra={
                "operation": "get_today_tasks",
                "direction": "request",
                "data": {"date": "2025-01-15"},
                "duration_ms": 42.5,
            },
        )

        for h in logger.handlers:
            h.flush()

        files = list(tmp_path.glob("debug_*.jsonl"))
        entry = json.loads(files[0].read_text().strip())

        assert entry["operation"] == "get_today_tasks"
        assert entry["direction"] == "request"
        assert entry["data"] == {"date": "2025-01-15"}
        assert entry["duration_ms"] == 42.5
        assert entry["level"] == "DEBUG"

    def teardown_method(self):
        """Clean up the logger between tests to avoid handler accumulation."""
        logger = logging.getLogger("daily_planner.debug")
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)


class TestDebugLogDisabled:
    """T022: With DAILY_PLANNER_DEBUG unset, verify no log file is created."""

    def test_no_log_file_when_env_unset(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DAILY_PLANNER_DEBUG", raising=False)
        logger = setup_debug_logging(tmp_path)

        logger.debug("should not appear", extra={"operation": "test"})

        for h in logger.handlers:
            h.flush()

        files = list(tmp_path.glob("debug_*.jsonl"))
        assert len(files) == 0

    def test_logger_uses_null_handler_when_disabled(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DAILY_PLANNER_DEBUG", raising=False)
        logger = setup_debug_logging(tmp_path)

        assert any(isinstance(h, logging.NullHandler) for h in logger.handlers)
        assert not any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def teardown_method(self):
        logger = logging.getLogger("daily_planner.debug")
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)


class TestErrorLogging:
    """T029: Verify error-level log entries contain traceback and context."""

    def test_error_entry_contains_traceback(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)

        try:
            raise ValueError("something broke")
        except ValueError:
            logger.error(
                "simulated failure",
                exc_info=True,
                extra={
                    "operation": "test.error",
                    "data": {"input": "bad_value"},
                },
            )

        for h in logger.handlers:
            h.flush()

        files = list(tmp_path.glob("debug_*.jsonl"))
        entry = json.loads(files[0].read_text().strip())

        assert entry["level"] == "ERROR"
        assert entry["operation"] == "test.error"
        assert "traceback" in entry
        assert "ValueError" in entry["traceback"]
        assert entry["data"] == {"input": "bad_value"}

    def teardown_method(self):
        logger = logging.getLogger("daily_planner.debug")
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)


class TestDurationMs:
    """T030: Verify duration_ms is present and positive on response entries."""

    def test_duration_ms_is_positive_number(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)

        logger.debug(
            "tool done",
            extra={
                "operation": "test.tool",
                "direction": "response",
                "duration_ms": 15.7,
            },
        )

        for h in logger.handlers:
            h.flush()

        files = list(tmp_path.glob("debug_*.jsonl"))
        entry = json.loads(files[0].read_text().strip())

        assert "duration_ms" in entry
        assert isinstance(entry["duration_ms"], (int, float))
        assert entry["duration_ms"] > 0

    def teardown_method(self):
        logger = logging.getLogger("daily_planner.debug")
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)


class TestStdoutIsolation:
    """T034: Debug log content does not appear in captured stdout."""

    def test_log_content_not_in_stdout(self, tmp_path, monkeypatch):
        import sys
        from io import StringIO

        monkeypatch.setenv("DAILY_PLANNER_DEBUG", "1")
        logger = setup_debug_logging(tmp_path)

        captured = StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured
            for i in range(10):
                logger.debug(
                    f"entry {i}",
                    extra={"operation": f"test.op{i}", "data": {"i": i}},
                )
            for h in logger.handlers:
                h.flush()
        finally:
            sys.stdout = old_stdout

        assert captured.getvalue() == ""

        # Verify the log file does have content
        files = list(tmp_path.glob("debug_*.jsonl"))
        assert len(files) == 1
        lines = files[0].read_text().strip().splitlines()
        assert len(lines) == 10

    def teardown_method(self):
        logger = logging.getLogger("daily_planner.debug")
        for h in logger.handlers[:]:
            h.close()
            logger.removeHandler(h)
