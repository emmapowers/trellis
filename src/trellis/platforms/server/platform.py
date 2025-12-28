"""Server platform implementation using FastAPI and WebSocket."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import uvicorn

if TYPE_CHECKING:
    from trellis.core.rendering.element import Element

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from rich.console import Console

from trellis.bundler import CORE_PACKAGES, BundleConfig, build_bundle
from trellis.platforms.common import find_available_port
from trellis.platforms.common.base import Platform
from trellis.platforms.server.handler import router as ws_router
from trellis.platforms.server.middleware import RequestLoggingMiddleware
from trellis.platforms.server.routes import create_static_dir
from trellis.platforms.server.routes import router as http_router

_console = Console()


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
        root_component: Callable[[], Element],
        *,
        host: str = "127.0.0.1",
        port: int | None = None,
        static_dir: Path | None = None,
        batch_delay: float = 1.0 / 30,
        **_kwargs: Any,  # Ignore other platform args
    ) -> None:
        """Start FastAPI server with WebSocket support.

        Args:
            root_component: The root Trellis component to render
            host: Host to bind to
            port: Port to bind to (auto-find if None)
            static_dir: Custom static files directory
            batch_delay: Time between render frames in seconds (default ~33ms for 30fps)
        """
        # Create FastAPI app
        app = FastAPI()

        # Add request logging middleware
        app.add_middleware(RequestLoggingMiddleware)

        # Include routers
        app.include_router(http_router)
        app.include_router(ws_router)

        # Store top component and config in app state
        app.state.trellis_top_component = root_component
        app.state.trellis_batch_delay = batch_delay

        # Set up static file serving
        static = static_dir or create_static_dir()
        if static.exists():
            app.mount("/static", StaticFiles(directory=static), name="static")

        # Find available port if not specified
        if port is None:
            port = find_available_port(host=host)

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
