"""Logging configuration for Revision Forge.

All loggers live under the 'revision_forge' parent so application output can
be filtered away from third-party library noise.
"""

import logging
import sys
from pathlib import Path

_PARENT = "revision_forge"
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging(level: str = "INFO", log_file: str | None = None, console: bool = True) -> None:
    """Set up logging handlers. Safe to call more than once."""
    parent = logging.getLogger(_PARENT)
    parent.setLevel(getattr(logging, level.upper(), logging.INFO))
    parent.handlers.clear()

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(_FORMAT))
        parent.addHandler(console_handler)

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(_FORMAT))
        parent.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger namespaced under the application parent."""
    return logging.getLogger(f"{_PARENT}.{name}")
