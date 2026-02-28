"""
Logging setup for autonomous-test-agent.

Usage:
    from src.core.logger import setup_logger, log_crash

    logger = setup_logger("my_module")
"""
from __future__ import annotations

import logging
import os
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path("logs")
_CRASH_DIR = _LOG_DIR / "crashes"

# Track which loggers have already been configured to avoid duplicate handlers.
_configured: set[str] = set()


def setup_logger(name: str = "app") -> logging.Logger:
    """
    Return a configured logger for *name*.

    Handlers are added only once per logger name, so calling this function
    multiple times with the same name is safe.
    """
    logger = logging.getLogger(name)

    if name in _configured:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler — INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler — DEBUG and above
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        _LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _configured.add(name)
    return logger


def log_crash(e: Exception, context: str = "") -> str:
    """
    Write a full crash report to a timestamped file under *logs/crashes/*.

    Returns the absolute path of the report file.
    """
    _CRASH_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = _CRASH_DIR / f"crash_{timestamp}.txt"

    with filepath.open("w") as f:
        f.write(f"Timestamp : {datetime.now()}\n")
        f.write(f"Context   : {context}\n")
        f.write(f"Exception : {e}\n")
        f.write("-" * 60 + "\n")
        f.write(traceback.format_exc())

    return str(filepath)
