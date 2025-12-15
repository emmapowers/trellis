"""HTTP middleware for server platform."""

from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING

from rich.console import Console
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

if TYPE_CHECKING:
    from fastapi import Request
    from starlette.responses import Response

_console = Console()


def _get_status_color(status: int) -> str:
    """Return a color name based on HTTP status code."""
    if status < 300:  # noqa: PLR2004
        return "green"
    if status < 400:  # noqa: PLR2004
        return "cyan"
    if status < 500:  # noqa: PLR2004
        return "yellow"
    return "red"


def _format_duration(duration_ms: float) -> str:
    """Format duration in human-readable form."""
    if duration_ms < 1:
        return f"{duration_ms * 1000:.0f}µs"
    if duration_ms < 1000:  # noqa: PLR2004
        return f"{duration_ms:.0f}ms"
    return f"{duration_ms / 1000:.2f}s"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs HTTP requests with colors."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - start) * 1000

        method = request.method
        path = request.url.path
        status = response.status_code

        # Color the method
        method_colors = {
            "GET": "green",
            "POST": "yellow",
            "PUT": "blue",
            "DELETE": "red",
            "PATCH": "magenta",
        }
        method_color = method_colors.get(method, "white")

        # Color the status code
        status_color = _get_status_color(status)

        # Format duration
        duration_str = _format_duration(duration_ms)

        _console.print(
            f"  [{method_color} bold]{method:7}[/{method_color} bold] "
            f"[{status_color} bold]{status}[/{status_color} bold] "
            f"{path} "
            f"[bright_black]{duration_str}[/bright_black]"
        )

        return response
