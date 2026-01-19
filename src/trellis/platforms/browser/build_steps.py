"""Browser platform build steps."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from trellis.bundler.packages import get_bin
from trellis.bundler.python_source import collect_package_files, find_package_root
from trellis.bundler.steps import BuildContext, BuildStep


def build_source_config(entry_path: Path, module_name: str | None = None) -> dict[str, Any]:
    """Build source config dict for Pyodide.

    This is browser-platform specific - it creates the config structure
    that the Pyodide worker expects for loading Python source code.

    Args:
        entry_path: Path to the Python entry point file
        module_name: Optional module name override. If not provided, inferred from path.

    Returns:
        Source config dict:
        - {"type": "code", "code": "..."} for single files
        - {"type": "module", "files": {...}, "moduleName": "..."} for packages
    """
    package_root = find_package_root(entry_path)

    if package_root is None:
        # Single file mode
        return {"type": "code", "code": entry_path.read_text()}

    # Module mode - collect all package files
    files = collect_package_files(package_root)

    # Determine module name
    if module_name is None:
        if entry_path.name == "__main__.py":
            # __main__.py: module name is the package directory path
            # e.g., myapp/__main__.py -> "myapp", myapp/sub/__main__.py -> "myapp.sub"
            rel_path = entry_path.parent.relative_to(package_root.parent)
            module_name = str(rel_path).replace("/", ".").replace("\\", ".")
        else:
            # Regular .py file: module name includes the filename (without .py)
            # e.g., myapp/cli.py -> "myapp.cli"
            rel_path = entry_path.relative_to(package_root.parent)
            module_name = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")

    return {"type": "module", "files": files, "moduleName": module_name}


# Path to pyodide worker source relative to this file
_PYODIDE_WORKER_PATH = Path(__file__).parent / "client" / "src" / "pyodide.worker.ts"


class PyodideWorkerBuildStep(BuildStep):
    """Build the Pyodide worker as an IIFE bundle inlined as text.

    Builds the pyodide.worker.ts file as an IIFE bundle and adds an alias
    so the main bundle can import it as text via:

        import WORKER_CODE from "@trellis/browser/pyodide.worker-bundle";
        new Worker(URL.createObjectURL(new Blob([WORKER_CODE])));
    """

    @property
    def name(self) -> str:
        return "pyodide-worker-build"

    def run(self, ctx: BuildContext) -> None:
        if ctx.node_modules is None:
            raise RuntimeError("PyodideWorkerBuildStep requires node_modules")

        esbuild = get_bin(ctx.node_modules, "esbuild")
        output_file = ctx.workspace / "pyodide.worker-bundle"

        cmd = [
            str(esbuild),
            str(_PYODIDE_WORKER_PATH),
            "--bundle",
            f"--outfile={output_file}",
            "--format=iife",
            "--platform=browser",
            "--target=es2022",
            "--loader:.ts=ts",
        ]

        subprocess.run(cmd, check=True, env={**ctx.env})

        # Add loader and alias so the main bundle can import the worker as text
        ctx.esbuild_args.append("--loader:.worker-bundle=text")
        ctx.esbuild_args.append(f"--alias:@trellis/browser/pyodide.worker-bundle={output_file}")


class PythonSourceBundleStep(BuildStep):
    """Bundle Python source code into template context.

    Reads python_entry_point from BuildContext. If not set, this step is a no-op.
    Adds source_json and routing_mode to template_context for IndexHtmlRenderStep.
    """

    @property
    def name(self) -> str:
        return "python-source-bundle"

    def run(self, ctx: BuildContext) -> None:
        if ctx.python_entry_point is None:
            return  # No-op if no Python entry point

        source = build_source_config(ctx.python_entry_point)

        # JSON-encode and escape </ to prevent script tag injection
        source_json = json.dumps(source).replace("</", r"<\/")

        ctx.template_context["source_json"] = source_json
        ctx.template_context["routing_mode"] = "hash_url"


class WheelCopyStep(BuildStep):
    """Copy trellis wheel to the dist directory.

    Pyodide needs the trellis wheel to install trellis at runtime.
    This step copies the wheel from the project's dist/ directory
    to the build's dist_dir so it can be served alongside the bundle.

    Args:
        wheel_dir: Directory containing the trellis wheel (project's dist/)
    """

    def __init__(self, wheel_dir: Path) -> None:
        self._wheel_dir = wheel_dir

    @property
    def name(self) -> str:
        return "wheel-copy"

    def run(self, ctx: BuildContext) -> None:
        wheels: list[Path] = []
        if self._wheel_dir.exists():
            wheels = list(self._wheel_dir.glob("trellis-*.whl"))

        if not wheels:
            raise RuntimeError(
                f"trellis wheel not found in {self._wheel_dir}. "
                "Run 'pixi run build-wheel' first."
            )

        # Use the most recently modified wheel
        wheel = max(wheels, key=lambda p: p.stat().st_mtime)

        dest = ctx.dist_dir / wheel.name
        dest.write_bytes(wheel.read_bytes())
