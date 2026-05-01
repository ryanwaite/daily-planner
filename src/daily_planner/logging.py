"""Debug logging infrastructure — JSONL formatter, setup, and truncation helper."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date, datetime
from pathlib import Path

_MAX_PAYLOAD_LENGTH = 5000
_TRUNCATION_SUFFIX = "...[truncated]"


def truncate_payload(
    data: object,
    max_length: int = _MAX_PAYLOAD_LENGTH,
) -> object:
    """Recursively truncate string values in dicts/lists.

    Returns a new structure without mutating the input. Strings exceeding
    *max_length* are cut and suffixed with ``...[truncated]``.
    """
    if isinstance(data, dict):
        return {k: truncate_payload(v, max_length) for k, v in data.items()}
    if isinstance(data, list):
        return [truncate_payload(item, max_length) for item in data]
    if isinstance(data, str) and len(data) > max_length:
        return data[:max_length] + _TRUNCATION_SUFFIX
    return data


def _json_default(obj: object) -> str:
    """Handle non-serializable types for ``json.dumps``."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)


class JsonlFormatter(logging.Formatter):
    """Format each log record as a single-line JSON object (JSONL)."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "operation": getattr(record, "operation", "unknown"),
            "message": record.getMessage(),
        }

        direction = getattr(record, "direction", None)
        if direction is not None:
            entry["direction"] = direction

        data = getattr(record, "data", None)
        if data is not None:
            entry["data"] = truncate_payload(data)

        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms

        if record.exc_info and record.exc_info[0] is not None:
            entry["traceback"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=_json_default)


def setup_debug_logging(output_dir: str | Path) -> logging.Logger:
    """Configure and return the debug logger.

    Behaviour depends on the ``DAILY_PLANNER_DEBUG`` environment variable:

    * **Set to a truthy value** – creates a :class:`logging.FileHandler`
      writing JSONL to *output_dir*, attaches :class:`JsonlFormatter`.
    * **Unset or empty** – attaches a :class:`logging.NullHandler` (no-op).

    If *output_dir* is not writable the function prints a warning to
    *stderr* and falls back to the NullHandler path.

    The returned logger has ``propagate=False`` so that log records
    **never** bubble to the root logger.  This is critical for MCP
    transport safety — stdout must remain reserved for the MCP protocol.
    """
    logger = logging.getLogger("daily_planner.debug")
    logger.propagate = False  # CRITICAL: prevents stdout pollution via root logger

    env_value = os.environ.get("DAILY_PLANNER_DEBUG", "").strip()
    if not env_value:
        logger.addHandler(logging.NullHandler())
        return logger

    output_path = Path(output_dir).expanduser().resolve()
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(
            f"Warning: Cannot create debug log directory {output_path}: {exc}",
            file=sys.stderr,
        )
        logger.addHandler(logging.NullHandler())
        return logger

    now = datetime.now()
    filename = f"debug_{now.strftime('%Y-%m-%d_%H%M%S')}_{os.getpid()}.jsonl"
    log_file = output_path / filename

    try:
        handler = logging.FileHandler(str(log_file), mode="a", encoding="utf-8")
    except OSError as exc:
        print(
            f"Warning: Cannot create debug log file {log_file}: {exc}",
            file=sys.stderr,
        )
        logger.addHandler(logging.NullHandler())
        return logger

    handler.setFormatter(JsonlFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger
