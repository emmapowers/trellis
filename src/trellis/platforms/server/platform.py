"""Server platform implementation using FastAPI and WebSocket."""

from __future__ import annotations

import socket
from collections.abc import Callable
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from rich.console import Console

from trellis.bundler import CORE_PACKAGES, BundleConfig, build_bundle
from trellis.core.platform import Platform
from trellis.platforms.server.handler import router as ws_router
from trellis.platforms.server.middleware import RequestLoggingMiddleware
from trellis.platforms.server.routes import create_static_dir
from trellis.platforms.server.routes import router as http_router

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
            # Allow binding to TIME_WAIT ports (matches uvicorn's behavior)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available port found in range {start}-{end}")


def _print_startup_banner(host: str, port: int) -> None:
    """Print a colorful startup banner."""
    url = f"http://{host}:{port}"

    _console.print()
    _console.print("  [bold green]🌿 Trellis[/bold green] [dim]dev server running[/dim]")
    _console.print()
    _console.print(f"  [bold]➜[/bold]  [cyan]Local:[/cyan]   [underline]{url}[/underline]")
    _console.print()
    _console.print("  [dim]Press[/dim] [bold]Ctrl+C[/bold] [dim]to stop[/dim]")
    _console.print()


class ServerPlatform(Platform):
    """FastAPI/WebSocket platform implementation."""

    @property
    def name(self) -> str:
        return "server"

    def bundle(
        self,
        force: bool = False,
        extra_packages: dict[str, str] | None = None,
    ) -> None:
        """Build the server client bundle if needed.

        Output: platforms/server/client/dist/bundle.js

        The server platform serves this bundle via /static/bundle.js and returns
        HTML dynamically from routes.py (no generated index.html needed).
        """
        platforms_dir = Path(__file__).parent.parent
        common_src_dir = platforms_dir / "common" / "client" / "src"

        config = BundleConfig(
            name="server",
            src_dir=Path(__file__).parent / "client" / "src",
            dist_dir=Path(__file__).parent / "client" / "dist",
            packages=CORE_PACKAGES,
        )

        build_bundle(config, common_src_dir, force, extra_packages)

    async def run(
        self,
        root_component: Callable[[], None],
        *,
        host: str = "127.0.0.1",
        port: int | None = None,
        static_dir: Path | None = None,
        **_kwargs: Any,  # Ignore other platform args
    ) -> None:
        """Start FastAPI server with WebSocket support.

        Args:
            root_component: The root Trellis component to render
            host: Host to bind to
            port: Port to bind to (auto-find if None)
            static_dir: Custom static files directory
        """
        # Create FastAPI app
        app = FastAPI()

        # Add request logging middleware
        app.add_middleware(RequestLoggingMiddleware)

        # Include routers
        app.include_router(http_router)
        app.include_router(ws_router)

        # Store top component in app state
        app.state.trellis_top_component = root_component

        # Set up static file serving
        static = static_dir or create_static_dir()
        if static.exists():
            app.mount("/static", StaticFiles(directory=static), name="static")

        # Find available port if not specified
        if port is None:
            port = _find_available_port()

        _print_startup_banner(host, port)

        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_config=None,  # Don't override logging config
            log_level="warning",  # Suppress uvicorn's info messages
        )
        server = uvicorn.Server(config)
        await server.serve()
