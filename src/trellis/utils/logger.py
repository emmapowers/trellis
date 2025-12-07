"""Module-level logger that returns a logger for the importing module.

Usage:
    from trellis.utils.logger import logger

    logger.info("This logs with the importing module's __name__")
"""

from __future__ import annotations

import inspect
import logging
import typing as tp


def __getattr__(name: str) -> tp.Any:
    """Return a logger for the calling module when 'logger' is accessed."""
    if name == "logger":
        frame = inspect.currentframe()
        if frame is not None and frame.f_back is not None:
            caller_globals = frame.f_back.f_globals
            module_name = caller_globals.get("__name__", __name__)
            return logging.getLogger(module_name)
        return logging.getLogger(__name__)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
