"""Wires one rotating-file + console logger shared by the CLI and the FastAPI server, so every agent trace, LLM call, and HTTP request lands in a single logs/ file (console-only on Lambda, where CloudWatch captures stdout)."""

from __future__ import annotations

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

_LOG_DIR = Path(__file__).resolve().parent / "logs"
_configured: set[str] = set()


def _file_handler(log_file: str, fmt: logging.Formatter) -> Optional[logging.Handler]:
    """Build the rotating file handler, or None if this environment can't write one.

    On Lambda the task directory is read-only (only /tmp is writable) and stdout
    is already captured by CloudWatch, so a log file is both impossible and
    pointless there - the console handler alone is the right answer.
    """
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return None
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            _LOG_DIR / log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(fmt)
        return handler
    except OSError:
        # Read-only or otherwise unwritable filesystem: degrade to console only
        # rather than taking the whole app down over logging setup.
        return None


def setup_logging(log_file: str = "backend.log", level: int = logging.INFO) -> Optional[Path]:
    """Route every agent/orchestrator trace and uvicorn request log to one rotating file.

    Safe to call more than once (e.g. on module reload) - repeat calls for the
    same log_file are a no-op so handlers are never attached twice. Returns the
    log file path, or None when logging to the console only.
    """
    if log_file in _configured:
        return _LOG_DIR / log_file

    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = _file_handler(log_file, fmt)

    # All of this package's loggers are children of "clubapply_strands"
    # (their __name__ is e.g. "clubapply_strands.agents.website_agent"), so
    # configuring the package logger once catches every agent/tool/orchestrator
    # trace without touching each module's logger individually.
    app_logger = logging.getLogger("clubapply_strands")
    app_logger.setLevel(level)
    if file_handler:
        app_logger.addHandler(file_handler)
    if not any(isinstance(h, logging.StreamHandler) for h in app_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)
        app_logger.addHandler(console_handler)
    app_logger.propagate = False

    # Uvicorn logs startup/error lines on "uvicorn.error" (which propagates up
    # to "uvicorn") and access lines on "uvicorn.access" (which does not
    # propagate). Attach directly to both leaf loggers, and not to the bare
    # "uvicorn" parent, so nothing is missed and nothing double-writes.
    if file_handler:
        for name in ("uvicorn.error", "uvicorn.access"):
            logging.getLogger(name).addHandler(file_handler)

    _configured.add(log_file)
    return (_LOG_DIR / log_file) if file_handler else None
