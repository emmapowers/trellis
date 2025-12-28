"""Logging setup with colorized output via Rich."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text


class TerseRichHandler(RichHandler):
    """RichHandler with terse formatting and level-based colors."""

    def render_message(self, record: logging.LogRecord, message: str) -> Text:
        """Apply level-based styling: faded debug, orange warning, red error."""
        if record.levelno == logging.DEBUG:
            # Debug: light gray with file:line prefix
            location = f"{record.filename}:{record.lineno}"
            text = Text()
            text.append(f"{location} ", style="grey50")
            text.append(message, style="grey70")
            return text
        if record.levelno == logging.WARNING:
            return Text.from_markup(f"[orange3]Warning:[/orange3] {message}")
        if record.levelno >= logging.ERROR:
            return Text.from_markup(f"[red]Error:[/red] {message}")

        return Text.from_markup(message)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging with colorized Rich output.

    Args:
        level: The logging level (default: INFO)

    Log format is terse:
    - DEBUG: faded/dim text
    - INFO: plain text
    - WARNING: "Warning: <message>" in orange
    - ERROR/CRITICAL: "Error: <message>" in red

    Rich markup is supported in log messages for inline colors:
        logger.info("[red]Error count:[/red] %d", count)

    Also configures uvicorn/fastapi loggers to use the same handler.
    """
    console = Console(stderr=True)

    handler = TerseRichHandler(
        console=console,
        show_time=False,
        show_level=False,
        show_path=False,
        markup=True,
    )

    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=[handler],
        format="%(message)s",
        force=True,
    )

    # Uvicorn adds its own handlers by default, which would bypass our Rich handler
    # and produce duplicate or differently-formatted output. Clear them and propagate
    # to root so all logs go through our unified Rich formatting.
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
