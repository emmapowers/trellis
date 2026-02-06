"""Browser serve platform for CLI mode.

This platform builds and serves browser apps from the command line.
It bundles Python apps at build time and serves them via HTTP.
"""

from __future__ import annotations

import sys
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

    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper

from trellis.bundler import (
    BuildStep,
    BundleBuildStep,
    DeclarationStep,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
    TsconfigStep,
    build,
    registry,
)
from trellis.bundler.workspace import get_dist_dir, get_workspace_dir
from trellis.platforms.browser.build_steps import (
    PyodideWorkerBuildStep,
    PythonSourceBundleStep,
    WheelCopyStep,
)
from trellis.platforms.common import find_available_port
from trellis.platforms.common.base import Platform

__all__ = ["BrowserServePlatform", "MissingEntryPointError"]


class MissingEntryPointError(Exception):
    """Raised when browser app mode is used without a Python entry point."""

    pass


_console = Console()


def _detect_entry_point() -> Path | None:
    """Detect the Python entry point from the __main__ module.

    Used for auto-detecting the app entry point when running with
    `python -m app --browser` or `python app.py --browser`.

    Returns:
        Path to the entry point file, or None if not detectable.
        Returns None if the detected file is not a .py file (e.g., when
        running from a CLI entry script like `trellis bundle build`).
    """
    main_module = sys.modules.get("__main__")
    if main_module is None:
        return None

    entry_file = getattr(main_module, "__file__", None)
    if entry_file is None:
        return None

    path = Path(entry_file)

    # CLI entry scripts (like `trellis`) are not .py files
    if path.suffix != ".py":
        return None

    return path


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
    - Builds the browser client bundle with embedded Python app source
    - Serves the pre-built bundle via HTTP
    """

    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        return "browser-serve"

    def _get_build_steps(self, *, output_name: str = "bundle") -> list[BuildStep]:
        """Get build steps for this platform.

        Args:
            output_name: Name for output files (default "bundle")
        """
        # Wheel is expected in project's dist/ directory (from pixi run build-wheel)
        wheel_dir = Path.cwd() / "dist"

        return [
            PackageInstallStep(),
            RegistryGenerationStep(),
            PyodideWorkerBuildStep(),
            BundleBuildStep(output_name=output_name),
            StaticFileCopyStep(),
            WheelCopyStep(wheel_dir),
        ]

    def bundle(
        self,
        force: bool = False,
        dest: Path | None = None,
        library: bool = False,
        assets_dir: Path | None = None,
        python_entry_point: Path | None = None,
    ) -> Path:
        """Build the browser client bundle if needed.

        Uses the registry-based build system. The bundle is stored in a
        cache workspace (or dest if specified).

        Args:
            force: Force rebuild even if sources unchanged
            dest: Custom output directory (default: cache directory)
            library: If True, build as library exporting TrellisApp (uses index.ts).
                     If False, build as app that renders to DOM (uses main.tsx).
            assets_dir: App-level static files directory to copy to dist
            python_entry_point: Python app entry point to embed in bundle.
                If None in app mode, auto-detects from __main__ module.

        Returns:
            The workspace Path used for the build
        """
        # Use index.ts for library mode, main.tsx for app mode
        entry_name = "index.ts" if library else "main.tsx"
        entry_point = Path(__file__).parent / "client" / "src" / entry_name
        workspace = get_workspace_dir()

        # Determine output name based on mode
        output_name = "index" if library else "bundle"

        # Path to index.html.j2 template
        template_path = Path(__file__).parent / "client" / "src" / "index.html.j2"

        if library:
            # Library mode adds type generation steps
            steps: list[BuildStep] = [
                PackageInstallStep(),
                RegistryGenerationStep(),
                TsconfigStep(),
                PyodideWorkerBuildStep(),
                BundleBuildStep(output_name=output_name),
                DeclarationStep(),
                StaticFileCopyStep(),
            ]
        else:
            steps = self._get_build_steps(output_name=output_name)

            # Auto-detect entry point if not provided (for python -m app --browser flow)
            if python_entry_point is None:
                python_entry_point = _detect_entry_point()

            # Error if still no entry point
            if python_entry_point is None:
                raise MissingEntryPointError("Browser app mode requires a Python entry point.")

            # Add Python source bundling and HTML rendering
            steps.append(PythonSourceBundleStep())
            steps.append(IndexHtmlRenderStep(template_path))

        build(
            registry=registry,
            entry_point=entry_point,
            workspace=workspace,
            steps=steps,
            force=force,
            output_dir=dest or get_dist_dir(),
            assets_dir=assets_dir,
            python_entry_point=python_entry_point,
        )
        return workspace

    async def run(
        self,
        root_component: Callable[[], Element],
        app_wrapper: AppWrapper,
        *,
        hot_reload: bool = True,
        **kwargs: Any,
    ) -> None:
        """Serve the pre-built browser bundle.

        Requires bundle to be built first with:
            trellis bundle build --platform browser --app <entry.py>

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

        # Ensure pre-built bundle exists
        if not index_path.exists():
            raise RuntimeError(
                f"Browser bundle index.html not found at {index_path}. "
                "Run 'trellis bundle build --platform browser --app <entry.py>' first."
            )

        # Read the pre-built HTML
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
