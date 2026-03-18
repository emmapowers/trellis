"""Server platform implementation using FastAPI and WebSocket."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import uvicorn

if TYPE_CHECKING:
    from trellis.app.config import Config
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from rich.console import Console

from trellis.bundler import (
    BuildConfig,
    BundleBuildStep,
    IconAssetStep,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    SSRBundleBuildStep,
    StaticFileCopyStep,
)
from trellis.platforms.common import find_available_port
from trellis.platforms.common.base import Platform
from trellis.platforms.server.handler import router as ws_router
from trellis.platforms.server.middleware import RequestLoggingMiddleware
from trellis.platforms.server.routes import create_static_dir, register_spa_fallback
from trellis.platforms.server.routes import router as http_router
from trellis.platforms.server.session_store import SessionStore
from trellis.platforms.server.ssr import SSROrchestrator
from trellis.platforms.server.ssr_renderer import SSRRenderer
from trellis.utils.hot_reload import get_or_create_hot_reload

logger = logging.getLogger(__name__)

_console = Console()


def _print_startup_banner(host: str, port: int) -> None:
    """Print a colorful startup banner."""
    url = f"http://{host}:{port}"

    _console.print()
    _console.print("  [bold green]Trellis[/bold green] [dim]dev server running[/dim]")
    _console.print()
    _console.print(f"  [bold]>[/bold]  [cyan]Local:[/cyan]   [underline]{url}[/underline]")
    _console.print()
    _console.print("  [dim]Press[/dim] [bold]Ctrl+C[/bold] [dim]to stop[/dim]")
    _console.print()


def _setup_ssr(
    app: FastAPI,
    *,
    root_component: Any,
    app_wrapper: Any,
    static_dir: Path | None,
    session_ttl: int,
    ssr_enabled: bool,
    hot_reload: bool,
) -> tuple[SessionStore, SSRRenderer | None]:
    """Set up SSR infrastructure: session store, renderer, and orchestrator."""
    ssr_renderer: SSRRenderer | None = None
    session_store = SessionStore(ttl_seconds=session_ttl)
    app.state.trellis_session_store = session_store

    if ssr_enabled:
        static = static_dir or create_static_dir()
        ssr_bundle = static / "ssr.js"
        if ssr_bundle.exists():
            ssr_renderer = SSRRenderer(ssr_bundle)
            try:
                ssr_renderer.start()
            except Exception:
                logger.warning("SSR renderer failed to start, falling back to CSR")
                ssr_renderer = None

        orchestrator = SSROrchestrator(
            root_component=root_component,
            app_wrapper=app_wrapper,
            session_store=session_store,
            ssr_renderer=ssr_renderer,
        )
        app.state.trellis_ssr = orchestrator

        if hot_reload:
            hr = get_or_create_hot_reload()
            hr.add_on_reload_callback(orchestrator.invalidate_cache)
    else:
        app.state.trellis_ssr = None

    return session_store, ssr_renderer


class ServerPlatform(Platform):
    """FastAPI/WebSocket platform implementation."""

    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        return "server"

    def get_build_config(self, config: Config) -> BuildConfig:
        """Get build configuration for this platform.

        Args:
            config: Application configuration

        Returns:
            BuildConfig with entry point and build steps
        """
        entry_point = Path(__file__).parent / "client" / "src" / "main.tsx"
        template_path = Path(__file__).parent / "client" / "src" / "index.html.j2"
        ssr_enabled = config.ssr

        steps = [
            PackageInstallStep(),
            RegistryGenerationStep(),
            BundleBuildStep(output_name="bundle"),
        ]
        if ssr_enabled:
            steps.append(SSRBundleBuildStep())
        steps.extend(
            [
                StaticFileCopyStep(),
                IconAssetStep(icon_path=config.icon),
                IndexHtmlRenderStep(
                    template_path, {"title": config.title, "static_path": "/static"}
                ),
            ]
        )

        return BuildConfig(
            entry_point=entry_point,
            steps=steps,
        )

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
        ssr: bool = True,
        session_ttl: int = 300,
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
            ssr: Enable server-side rendering (default True)
            session_ttl: Session time-to-live in seconds (default 300)
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

        session_store, ssr_renderer = _setup_ssr(
            app,
            root_component=root_component,
            app_wrapper=app_wrapper,
            static_dir=static_dir,
            session_ttl=session_ttl,
            ssr_enabled=ssr,
            hot_reload=hot_reload,
        )

        # Periodic cleanup of expired sessions
        cleanup_task = asyncio.create_task(
            _session_cleanup_loop(session_store, interval=session_ttl)
        )

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
        try:
            await server.serve()
        finally:
            cleanup_task.cancel()
            if ssr_renderer is not None:
                ssr_renderer.stop()


async def _session_cleanup_loop(store: SessionStore, interval: float) -> None:
    """Periodically remove expired sessions from the store."""
    while True:
        await asyncio.sleep(interval)
        store.cleanup_expired()
