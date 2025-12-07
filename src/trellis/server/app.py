"""Main App class for Trellis server."""

import socket
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from rich.console import Console
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from trellis.bundler import build_client
from trellis.server.routes import create_static_dir, router

_console = Console()

_DEFAULT_PORT_START = 8000
_DEFAULT_PORT_END = 8100


def _find_available_port(start: int = _DEFAULT_PORT_START, end: int = _DEFAULT_PORT_END) -> int:
    """Find an available port in the given range.

    Args:
        start: First port to try
        end: Last port to try (exclusive)

    Returns:
        An available port number

    Raises:
        RuntimeError: If no port is available in the range
    """
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found in range {start}-{end}")


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


@dataclass
class Trellis:
    """Trellis application server.

    Usage:
        app = Trellis(top=MyRootComponent, port=8080)
        await app.serve()

    If port is None, the first available port starting at 8000 is used.
    """

    top: Callable[[], None] | None = None
    host: str = "127.0.0.1"
    port: int | None = None
    static_dir: Path | None = None
    _fastapi: FastAPI = field(default_factory=FastAPI, repr=False)

    def __post_init__(self) -> None:
        """Set up FastAPI app with routes."""
        # Build client bundle if needed
        build_client()

        # Add request logging middleware
        self._fastapi.add_middleware(RequestLoggingMiddleware)

        self._fastapi.include_router(router)

        # Store top component in app state for routes to access
        self._fastapi.state.top_component = self.top

        # Set up static file serving
        static = self.static_dir or create_static_dir()
        if static.exists():
            self._fastapi.mount("/static", StaticFiles(directory=static), name="static")

    def _print_startup_banner(self) -> None:
        """Print a colorful startup banner."""
        console = Console()
        url = f"http://{self.host}:{self.port}"

        console.print()
        console.print("  [bold green]🌿 Trellis[/bold green] [dim]dev server running[/dim]")
        console.print()
        console.print(f"  [bold]➜[/bold]  [cyan]Local:[/cyan]   [underline]{url}[/underline]")
        console.print()
        console.print("  [dim]Press[/dim] [bold]Ctrl+C[/bold] [dim]to stop[/dim]")
        console.print()

    async def serve(self) -> None:
        """Start the server."""
        # Find available port if not specified
        if self.port is None:
            self.port = _find_available_port()

        self._print_startup_banner()

        config = uvicorn.Config(
            self._fastapi,
            host=self.host,
            port=self.port,
            log_config=None,  # Don't override logging config
            log_level="warning",  # Suppress uvicorn's info messages
        )
        server = uvicorn.Server(config)
        await server.serve()
