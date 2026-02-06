"""Server platform implementation using FastAPI and WebSocket."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import uvicorn

if TYPE_CHECKING:
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from rich.console import Console

from trellis.app.apploader import get_dist_dir, get_workspace_dir
from trellis.bundler import (
    BuildStep,
    BundleBuildStep,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
    build,
    registry,
)
from trellis.platforms.common import find_available_port
from trellis.platforms.common.base import Platform
from trellis.platforms.server.handler import router as ws_router
from trellis.platforms.server.middleware import RequestLoggingMiddleware
from trellis.platforms.server.routes import create_static_dir, register_spa_fallback
from trellis.platforms.server.routes import router as http_router
from trellis.utils.hot_reload import get_or_create_hot_reload

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

    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        return "server"

    def _get_build_steps(self) -> list[BuildStep]:
        """Get build steps for this platform."""
        template_path = Path(__file__).parent / "client" / "src" / "index.html.j2"
        return [
            PackageInstallStep(),
            RegistryGenerationStep(),
            BundleBuildStep(output_name="bundle"),
            StaticFileCopyStep(),
            IndexHtmlRenderStep(template_path, {"static_path": "/static"}),
        ]

    def bundle(
        self,
        force: bool = False,
        dest: Path | None = None,
        library: bool = False,
        assets_dir: Path | None = None,
    ) -> Path:
        """Build the server client bundle if needed.

        Uses the registry-based build system. The bundle is stored in a
        cache workspace (or dest if specified) and served via /static/.

        Returns:
            The workspace Path used for the build
        """
        entry_point = Path(__file__).parent / "client" / "src" / "main.tsx"
        workspace = get_workspace_dir()

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=self._get_build_steps(),
            force=force,
            output_dir=dest or get_dist_dir(),
            assets_dir=assets_dir,
        )
        return workspace

    async def run(
        self,
        root_component: Callable[[], Element],
        app_wrapper: AppWrapper,
        *,
        host: str = "127.0.0.1",
        port: int | None = None,
        static_dir: Path | None = None,
        batch_delay: float = 1.0 / 30,
        hot_reload: bool = True,
        **_kwargs: Any,  # Ignore other platform args
    ) -> None:
        """Start FastAPI server with WebSocket support.

        Args:
            root_component: The root Trellis component to render
            app_wrapper: Callback to wrap component with TrellisApp
            host: Host to bind to
            port: Port to bind to (auto-find if None)
            static_dir: Custom static files directory
            batch_delay: Time between render frames in seconds (default ~33ms for 30fps)
            hot_reload: Enable hot reload (default True)
        """
        # Start hot reload if enabled
        if hot_reload:
            hr = get_or_create_hot_reload(asyncio.get_running_loop())
            hr.start()

        # Create FastAPI app
        app = FastAPI()

        # Add request logging middleware
        app.add_middleware(RequestLoggingMiddleware)

        # Include routers
        app.include_router(http_router)
        app.include_router(ws_router)

        # Store top component and config in app state
        app.state.trellis_top_component = root_component
        app.state.trellis_app_wrapper = app_wrapper
        app.state.trellis_batch_delay = batch_delay

        # Set up static file serving
        static = static_dir or create_static_dir()
        if static.exists():
            app.mount("/static", StaticFiles(directory=static), name="static")

        # Register SPA fallback for client-side routing (must be after static files)
        register_spa_fallback(app)

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
