"""Browser serve platform for CLI mode.

This platform builds and serves browser apps from the command line.
It bundles Python apps at build time and serves them via HTTP.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import uvicorn
from rich.console import Console
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

if TYPE_CHECKING:
    from starlette.requests import Request

    from trellis.app.config import Config
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper

from trellis.app.apploader import get_app_root, get_dist_dir
from trellis.bundler import (
    BuildConfig,
    BundleBuildStep,
    DeclarationStep,
    IconAssetStep,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
    TsconfigStep,
)
from trellis.platforms.browser.build_steps import (
    DependencyResolveStep,
    PyodideWorkerBuildStep,
    WheelBuildStep,
    WheelBundleStep,
)
from trellis.platforms.common import find_available_port
from trellis.platforms.common.base import Platform

__all__ = ["BrowserServePlatform"]

_console = Console()


def _print_startup_banner(url: str) -> None:
    """Print a colorful startup banner for CLI mode."""
    _console.print()
    _console.print("  [bold green]🌿 Trellis[/bold green] [dim]browser app[/dim]")
    _console.print()
    _console.print(f"  [bold]➜[/bold]  [cyan]Local:[/cyan]   {url}")
    _console.print()
    _console.print("  [dim]Press Ctrl+C to stop[/dim]")
    _console.print()


class BrowserServePlatform(Platform):
    """Platform for building and serving browser apps from CLI.

    This platform:
    - Builds the browser client bundle with wheel-based Python packaging
    - Serves the pre-built bundle via HTTP
    """

    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        return "browser-serve"

    def get_build_config(self, config: Config) -> BuildConfig:
        """Get build configuration for this platform.

        Args:
            config: Application configuration

        Returns:
            BuildConfig with entry point and build steps.
            Library mode produces an ES module with type declarations.
            App mode produces a standalone bundle with embedded wheel data.
        """
        client_src = Path(__file__).parent / "client" / "src"
        app_root = get_app_root()

        if config.library:
            return BuildConfig(
                entry_point=client_src / "index.ts",
                steps=[
                    PackageInstallStep(),
                    RegistryGenerationStep(),
                    TsconfigStep(),
                    WheelBuildStep(app_root),
                    DependencyResolveStep(),
                    WheelBundleStep(config_json=config.to_json()),
                    PyodideWorkerBuildStep(),
                    BundleBuildStep(output_name="index"),
                    DeclarationStep(),
                    StaticFileCopyStep(),
                ],
            )

        # App mode
        template_path = client_src / "index.html.j2"
        return BuildConfig(
            entry_point=client_src / "main.tsx",
            steps=[
                PackageInstallStep(),
                RegistryGenerationStep(),
                WheelBuildStep(app_root),
                DependencyResolveStep(),
                WheelBundleStep(config_json=config.to_json()),
                PyodideWorkerBuildStep(),
                BundleBuildStep(output_name="bundle"),
                StaticFileCopyStep(),
                IconAssetStep(icon_path=config.icon),
                IndexHtmlRenderStep(template_path, {"title": config.title, "routing_mode": "hash"}),
            ],
        )

    async def run(
        self,
        root_component: Callable[[], Element],
        app_wrapper: AppWrapper,
        *,
        hot_reload: bool = True,
        **kwargs: Any,
    ) -> None:
        """Serve the pre-built browser bundle.

        Note: root_component and app_wrapper are accepted for signature compatibility
        but not used here - the app runs in Pyodide from the pre-built bundle.
        """
        if hot_reload:
            _console.print(
                "  [yellow]⚠[/yellow]  [dim]Hot reload not supported for browser platform[/dim]"
            )
            _console.print()

        # Get paths from dist directory
        dist_dir = get_dist_dir()
        index_path = dist_dir / "index.html"

        # Read the pre-built HTML (bundle must have been run first)
        html_content = index_path.read_text()

        # Create Starlette app - serve directly from dist
        async def index(request: Request) -> HTMLResponse:
            return HTMLResponse(html_content)

        app = Starlette(
            routes=[
                Route("/", index),
                Mount("/", StaticFiles(directory=dist_dir), name="static"),
            ]
        )

        # Get host/port from kwargs (with defaults)
        host: str = str(kwargs.get("host", "127.0.0.1"))
        port_arg = kwargs.get("port")
        port: int
        if port_arg is None:
            port = find_available_port(host=host)
        elif isinstance(port_arg, int):
            port = port_arg
        else:
            port = int(port_arg)

        _print_startup_banner(f"http://{host}:{port}")

        # Run the server
        config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        server = uvicorn.Server(config)
        await server.serve()
