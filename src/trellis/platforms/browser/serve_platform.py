"""Browser serve platform for CLI mode.

This platform builds and serves browser apps from the command line.
It's used when running `python app.py --browser` outside of Pyodide.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import uvicorn
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

if TYPE_CHECKING:
    from starlette.requests import Request

from trellis.bundler import CORE_PACKAGES, BundleConfig, build_bundle
from trellis.core.platform import Platform
from trellis.platforms.common import find_available_port

# Jinja2 environment for HTML templates
_TEMPLATE_DIR = Path(__file__).parent / "client" / "src"
_jinja_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=False)

__all__ = ["BrowserServePlatform"]

_console = Console()

# No additional npm packages needed - Pyodide is loaded from CDN
BROWSER_PACKAGES: dict[str, str] = {}


def _print_startup_banner(url: str) -> None:
    """Print a colorful startup banner for CLI mode."""
    _console.print()
    _console.print("  [bold green]🌿 Trellis[/bold green] [dim]browser app[/dim]")
    _console.print()
    _console.print(f"  [bold]➜[/bold]  [cyan]Local:[/cyan]   {url}")
    _console.print()
    _console.print("  [dim]Press Ctrl+C to stop[/dim]")
    _console.print()


def _find_package_root(source_path: Path) -> Path | None:
    """Find the root directory of a Python package containing the source file.

    Walks up from source_path looking for __init__.py files.
    Returns the topmost package directory, or None if not in a package.

    Args:
        source_path: Path to the source file

    Returns:
        Path to package root directory, or None if not a package
    """
    current = source_path.parent
    package_root = None

    # Walk up looking for __init__.py
    while (current / "__init__.py").exists():
        package_root = current
        current = current.parent

    return package_root


def _collect_package_files(package_dir: Path) -> dict[str, str]:
    """Collect all Python files in a package directory.

    Args:
        package_dir: Root directory of the package

    Returns:
        Dict mapping relative paths to file contents
    """
    files: dict[str, str] = {}

    for py_file in package_dir.rglob("*.py"):
        # Get path relative to package parent (so package name is included)
        rel_path = py_file.relative_to(package_dir.parent)
        files[str(rel_path)] = py_file.read_text()

    return files


def _detect_entry_point() -> tuple[Path, str | None]:
    """Detect the actual entry point from the __main__ module.

    This matches Python's execution semantics:
    - `python script.py` -> (script_path, None)
    - `python -m pkg` (pkg has __main__.py) -> (__main__.py path, "pkg")
    - `python -m pkg.module` -> (module.py path, "pkg.module")

    Returns:
        Tuple of (entry_file_path, module_name_if_run_as_module)
    """
    main_module = sys.modules.get("__main__")
    if main_module is None:
        raise RuntimeError("Cannot detect entry point: __main__ not found")

    entry_file = getattr(main_module, "__file__", None)
    if entry_file is None:
        raise RuntimeError("Cannot detect entry point: __main__.__file__ not set")

    entry_path = Path(entry_file)

    # Check if run as module (python -m)
    spec = getattr(main_module, "__spec__", None)
    module_name = spec.name if spec else None

    return entry_path, module_name


def _find_wheel() -> Path:
    """Find the trellis wheel for serving to Pyodide.

    Searches in order:
    1. dist/ directory (from pixi run build-wheel)
    2. Build on demand using pip wheel

    Returns:
        Path to the wheel file

    Raises:
        RuntimeError: If wheel cannot be found or built
    """
    # Check dist/ directory first
    dist_dir = Path.cwd() / "dist"
    if dist_dir.exists():
        wheels = list(dist_dir.glob("trellis-*.whl"))
        if wheels:
            return wheels[0]

    # Try to build the wheel
    _console.print("  [dim]Building trellis wheel...[/dim]")
    try:
        subprocess.run(
            ["pip", "wheel", ".", "-w", "dist", "--no-deps"],
            check=True,
            capture_output=True,
        )
        wheels = list(dist_dir.glob("trellis-*.whl"))
        if wheels:
            return wheels[0]
    except subprocess.CalledProcessError:
        pass

    raise RuntimeError("Could not find or build trellis wheel. Run 'pixi run build-wheel' first.")


class BrowserServePlatform(Platform):
    """Platform for serving browser apps from CLI.

    This platform:
    - Builds the browser client bundle
    - Packages the app source code
    - Serves everything via HTTP for the browser to load
    """

    @property
    def name(self) -> str:
        return "browser-serve"

    def bundle(
        self,
        force: bool = False,
        extra_packages: dict[str, str] | None = None,
    ) -> None:
        """Build the browser client bundle if needed.

        Output: platforms/browser/client/dist/bundle.js + index.html

        The pyodide worker is built separately and inlined into the main bundle
        via the worker_entries config (imported as text).
        """
        platforms_dir = Path(__file__).parent.parent
        common_src_dir = platforms_dir / "common" / "client" / "src"
        client_dir = Path(__file__).parent / "client"
        src_dir = client_dir / "src"
        dist_dir = client_dir / "dist"
        index_path = dist_dir / "index.html"

        config = BundleConfig(
            name="browser",
            src_dir=src_dir,
            dist_dir=dist_dir,
            packages={**CORE_PACKAGES, **BROWSER_PACKAGES},
            static_files={"index.html": src_dir / "index.html"},
            extra_outputs=[index_path],
            worker_entries={"pyodide": src_dir / "pyodide.worker.ts"},
        )

        build_bundle(config, common_src_dir, force, extra_packages)

    async def run(
        self,
        root_component: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        """Build and serve static files for browser testing.

        This is for development/testing with `python app.py --browser`.
        """
        # Detect the actual entry point (not the component location)
        entry_path, module_name = _detect_entry_point()

        # Check if source is part of a package (has __init__.py)
        package_dir = _find_package_root(entry_path)

        # Get paths
        client_dir = Path(__file__).parent / "client"
        dist_dir = client_dir / "dist"
        bundle_path = dist_dir / "bundle.js"

        # Ensure bundle exists (worker is inlined)
        if not bundle_path.exists():
            raise RuntimeError(
                f"Browser bundle not found at {bundle_path}. "
                "Run 'trellis bundle build --platform browser' first."
            )

        # Find the trellis wheel
        wheel_path = _find_wheel()

        # Create a temp directory for serving
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Copy bundle.js (worker is inlined)
            (temp_path / "bundle.js").write_bytes(bundle_path.read_bytes())

            # Copy wheel for Pyodide to install
            (temp_path / wheel_path.name).write_bytes(wheel_path.read_bytes())

            # Generate index.html with embedded config
            if package_dir:
                # Module mode - use runpy.run_module() for proper __name__ handling
                files = _collect_package_files(package_dir)

                if module_name:
                    # Run as module (python -m)
                    exec_module = module_name
                else:
                    # Run as script in package - convert path to module
                    rel_path = entry_path.relative_to(package_dir.parent)
                    exec_module = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")

                source = {"type": "module", "files": files, "moduleName": exec_module}
            else:
                # Single file mode
                source = {"type": "code", "code": entry_path.read_text()}
            html_content = _generate_html(source)
            (temp_path / "index.html").write_text(html_content)

            # Create Starlette app
            async def index(request: Request) -> HTMLResponse:
                return HTMLResponse(html_content)

            app = Starlette(
                routes=[
                    Route("/", index),
                    Mount("/", StaticFiles(directory=temp_path), name="static"),
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


def _generate_html(source: dict[str, Any]) -> str:
    """Generate the HTML page with embedded source config.

    Uses the index.html jinja2 template from the browser client.

    Args:
        source: Source config dict, e.g.:
            - {"type": "code", "code": "..."}
            - {"type": "module", "files": {...}, "moduleName": "..."}
    """
    # JSON-encode the source config for embedding in JavaScript
    # Escape </ to prevent script tag injection (e.g., </script> in code)
    source_json = json.dumps(source).replace("</", r"<\/")

    template = _jinja_env.get_template("index.html")
    return template.render(source_json=source_json)
