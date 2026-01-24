"""Browser platform build steps."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from trellis.bundler.manifest import StepManifest
from trellis.bundler.packages import get_bin
from trellis.bundler.python_source import collect_package_files, find_package_root
from trellis.bundler.steps import BuildContext, BuildStep, ShouldBuild
from trellis.bundler.utils import _get_newest_mtime, is_rebuild_needed


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

    Populates manifest with worker source directory and output bundle.
    """

    @property
    def name(self) -> str:
        return "pyodide-worker-build"

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if worker bundle needs rebuilding based on source/output mtimes."""
        if step_manifest is None:
            return ShouldBuild.BUILD
        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD
        return ShouldBuild.SKIP

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

        # Populate step manifest - track source directory and output bundle
        # Track parent directory to detect any changes in worker source files
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.source_paths.add(_PYODIDE_WORKER_PATH.parent)
        step_manifest.dest_files.add(output_file)


class PythonSourceBundleStep(BuildStep):
    """Bundle Python source code into template context.

    Reads python_entry_point from BuildContext. If not set, this step is a no-op.
    Adds source_json and routing_mode to template_context for IndexHtmlRenderStep.
    Also populates manifest with Python source files/directories.
    """

    @property
    def name(self) -> str:
        return "python-source-bundle"

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if Python source bundle needs rebuilding based on source mtime."""
        if ctx.python_entry_point is None:
            return ShouldBuild.SKIP  # No-op

        if step_manifest is None:
            return ShouldBuild.BUILD

        # Get current source mtime
        package_root = find_package_root(ctx.python_entry_point)
        source_path = package_root if package_root else ctx.python_entry_point
        current_mtime = _get_newest_mtime(source_path)

        prev_mtime = step_manifest.metadata.get("source_mtime")
        if prev_mtime is None or current_mtime > prev_mtime:
            return ShouldBuild.BUILD
        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        if ctx.python_entry_point is None:
            return  # No-op if no Python entry point

        source = build_source_config(ctx.python_entry_point)

        # JSON-encode and escape </ to prevent script tag injection
        source_json = json.dumps(source).replace("</", r"<\/")

        ctx.template_context["source_json"] = source_json
        ctx.template_context["routing_mode"] = "hash_url"

        # Populate step manifest with source files and mtime
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        package_root = find_package_root(ctx.python_entry_point)
        if package_root is not None:
            # Module mode - track package directory (enables recursive mtime checking)
            step_manifest.source_paths.add(package_root)
            step_manifest.metadata["source_mtime"] = _get_newest_mtime(package_root)
        else:
            # Single file mode - track the file itself
            step_manifest.source_paths.add(ctx.python_entry_point)
            step_manifest.metadata["source_mtime"] = _get_newest_mtime(ctx.python_entry_point)


class WheelCopyStep(BuildStep):
    """Copy trellis wheel to the dist directory.

    Pyodide needs the trellis wheel to install trellis at runtime.
    This step copies the wheel from the project's dist/ directory
    to the build's dist_dir so it can be served alongside the bundle.

    Also populates manifest and implements should_build() for wheel version check.

    Args:
        wheel_dir: Directory containing the trellis wheel (project's dist/)
    """

    def __init__(self, wheel_dir: Path) -> None:
        self._wheel_dir = wheel_dir

    @property
    def name(self) -> str:
        return "wheel-copy"

    def _find_wheel(self) -> Path | None:
        """Find the most recent trellis wheel in wheel_dir.

        Returns:
            Path to wheel file, or None if not found
        """
        if not self._wheel_dir.exists():
            return None
        wheels = list(self._wheel_dir.glob("trellis-*.whl"))
        if not wheels:
            return None
        return max(wheels, key=lambda p: p.stat().st_mtime)

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if wheel has changed since last build.

        Returns SKIP if wheel unchanged, BUILD if different or no previous.
        """
        if step_manifest is None:
            return ShouldBuild.BUILD

        wheel = self._find_wheel()
        if wheel is None:
            return ShouldBuild.BUILD  # Will fail in run() with RuntimeError

        prev_wheel_name = step_manifest.metadata.get("wheel_name")
        if wheel.name != prev_wheel_name:
            return ShouldBuild.BUILD
        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        wheel = self._find_wheel()

        if wheel is None:
            raise RuntimeError(
                f"trellis wheel not found in {self._wheel_dir}. "
                "Run 'pixi run build-wheel' first."
            )

        dest = ctx.dist_dir / wheel.name
        dest.write_bytes(wheel.read_bytes())

        # Populate step manifest
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.source_paths.add(wheel)
        step_manifest.dest_files.add(dest)
        step_manifest.metadata["wheel_name"] = wheel.name
