"""Browser platform build steps."""

from __future__ import annotations

import json
from pathlib import Path

from trellis.bundler.manifest import StepManifest
from trellis.bundler.packages import get_bin
from trellis.bundler.steps import BuildContext, BuildStep, ShouldBuild
from trellis.bundler.utils import is_rebuild_needed
from trellis.bundler.wheels import (
    PYODIDE_VERSION,
    ResolvedDependencies,
    build_wheel,
    create_site_packages_zip,
    read_wheel_record,
    resolve_dependencies,
)
from trellis.bundler.workspace import node_modules_path

# Path to pyodide worker source relative to this file
_PYODIDE_WORKER_PATH = Path(__file__).parent / "client" / "src" / "pyodide.worker.ts"


class WheelBuildStep(BuildStep):
    """Build the app wheel from its pyproject.toml.

    Stores the built wheel path in ctx.generated_files["app_wheel"].

    Args:
        app_root: Directory containing pyproject.toml
    """

    def __init__(self, app_root: Path) -> None:
        self._app_root = app_root

    @property
    def name(self) -> str:
        return "wheel-build"

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if app wheel needs rebuilding based on pyproject.toml + source mtime."""
        if step_manifest is None:
            return ShouldBuild.BUILD

        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD

        # Restore context on skip
        wheel_path_str = step_manifest.metadata.get("wheel_path")
        if wheel_path_str:
            ctx.generated_files["app_wheel"] = Path(wheel_path_str)

        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        wheel_dir = ctx.workspace / "wheels"
        wheel_path = build_wheel(self._app_root, wheel_dir)
        ctx.generated_files["app_wheel"] = wheel_path

        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        for record_path in read_wheel_record(wheel_path):
            source = self._app_root / record_path
            if source.exists():
                step_manifest.source_paths.add(source)
                continue
            src_layout = self._app_root / "src" / record_path
            if src_layout.exists():
                step_manifest.source_paths.add(src_layout)
        step_manifest.source_paths.add(self._app_root / "pyproject.toml")
        step_manifest.dest_files.add(wheel_path)
        step_manifest.metadata["wheel_path"] = str(wheel_path)


class DependencyResolveStep(BuildStep):
    """Resolve dependencies for the emscripten/Pyodide target.

    Reads the app wheel from ctx.generated_files["app_wheel"] and stores
    ResolvedDependencies in ctx.build_data["resolved_deps"].
    """

    @property
    def name(self) -> str:
        return "dependency-resolve"

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if dependency resolution needs re-running based on app wheel mtime."""
        if step_manifest is None:
            return ShouldBuild.BUILD
        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD

        # Restore resolved deps from metadata
        wheel_path_strs: list[str] = step_manifest.metadata.get("wheel_paths", [])
        pyodide_packages: list[str] = step_manifest.metadata.get("pyodide_packages", [])
        python_version: str = step_manifest.metadata.get("python_version", "")
        ctx.build_data["resolved_deps"] = ResolvedDependencies(
            wheel_paths=[Path(p) for p in wheel_path_strs],
            pyodide_packages=pyodide_packages,
            python_version=python_version,
        )

        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        app_wheel = ctx.generated_files["app_wheel"]
        cache_dir = ctx.workspace / "cache"
        resolved = resolve_dependencies(app_wheel, cache_dir)
        ctx.build_data["resolved_deps"] = resolved

        # Write marker file for mtime-based staleness detection
        marker = ctx.workspace / ".dependency-resolve-marker"
        marker.touch()

        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.source_paths.add(app_wheel)
        step_manifest.dest_files.add(marker)
        step_manifest.metadata["wheel_paths"] = [str(p) for p in resolved.wheel_paths]
        step_manifest.metadata["pyodide_packages"] = resolved.pyodide_packages
        step_manifest.metadata["python_version"] = resolved.python_version


class WheelBundleStep(BuildStep):
    """Create site-packages zip and wheel manifest for the worker.

    Reads ResolvedDependencies from ctx.build_data["resolved_deps"].
    Writes zip and manifest JSON to workspace, stores paths in ctx.generated_files.

    Args:
        config_json: Serialized Config JSON string (from config.to_json())
    """

    def __init__(self, config_json: str) -> None:
        self._config_json = config_json

    @property
    def name(self) -> str:
        return "wheel-bundle"

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if wheel bundle needs rebuilding based on source/output mtimes."""
        if step_manifest is None:
            return ShouldBuild.BUILD
        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD

        # Restore generated_files from metadata
        wheel_bundle_str = step_manifest.metadata.get("wheel_bundle")
        wheel_manifest_str = step_manifest.metadata.get("wheel_manifest")
        if wheel_bundle_str:
            ctx.generated_files["wheel_bundle"] = Path(wheel_bundle_str)
        if wheel_manifest_str:
            ctx.generated_files["wheel_manifest"] = Path(wheel_manifest_str)

        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        resolved: ResolvedDependencies = ctx.build_data["resolved_deps"]

        # Create the site-packages zip
        zip_path = ctx.workspace / "site-packages.wheel-bundle"
        create_site_packages_zip(resolved.wheel_paths, zip_path)

        # Write the manifest JSON with config and pyodide package info
        config_data: dict[str, object] = json.loads(self._config_json)
        entry_module = config_data.get("module", "")
        manifest_data = {
            "entryModule": entry_module,
            "pyodidePackages": resolved.pyodide_packages,
            "configJson": self._config_json,
        }
        manifest_path = ctx.workspace / "wheel-manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))

        ctx.generated_files["wheel_bundle"] = zip_path
        ctx.generated_files["wheel_manifest"] = manifest_path

        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        for wp in resolved.wheel_paths:
            step_manifest.source_paths.add(wp)
        step_manifest.dest_files.add(zip_path)
        step_manifest.dest_files.add(manifest_path)
        step_manifest.metadata["wheel_bundle"] = str(zip_path)
        step_manifest.metadata["wheel_manifest"] = str(manifest_path)


class PyodideWorkerBuildStep(BuildStep):
    """Build the Pyodide worker as an IIFE bundle inlined as text.

    Builds pyodide.worker.ts as an IIFE bundle. Includes esbuild flags for:
    - Worker bundle as text import
    - Wheel bundle as binary import (if present in generated_files)
    - Wheel manifest as JSON alias (if present in generated_files)

    Populates manifest with worker source directory and output bundle.
    """

    @property
    def name(self) -> str:
        return "pyodide-worker-build"

    def _get_python_version(self, ctx: BuildContext) -> str:
        """Get the Pyodide Python version (major.minor) from resolved dependencies."""
        resolved: ResolvedDependencies = ctx.build_data["resolved_deps"]
        return resolved.python_version

    def _get_esbuild_args(self, ctx: BuildContext) -> list[str]:
        """Compute the esbuild args this step adds to context."""
        output_file = ctx.workspace / "pyodide.worker-bundle"
        return [
            "--loader:.worker-bundle=text",
            f"--alias:@trellis/trellis-browser/pyodide.worker-bundle={output_file}",
        ]

    def _get_wheel_esbuild_args(self, ctx: BuildContext) -> list[str]:
        """Compute esbuild args for wheel bundle/manifest aliases."""
        args: list[str] = []
        wheel_bundle = ctx.generated_files.get("wheel_bundle")
        wheel_manifest = ctx.generated_files.get("wheel_manifest")
        if wheel_bundle:
            args.append(f"--alias:@trellis/wheel-bundle={wheel_bundle}")
        if wheel_manifest:
            args.append(f"--alias:@trellis/wheel-manifest={wheel_manifest}")
        return args

    def should_build(
        self, ctx: BuildContext, step_manifest: StepManifest | None
    ) -> ShouldBuild | None:
        """Check if worker bundle needs rebuilding based on source/output mtimes.

        When skipping, restores context fields that run() would have set.
        """
        if step_manifest is None:
            return ShouldBuild.BUILD
        if not step_manifest.source_paths or not step_manifest.dest_files:
            return ShouldBuild.BUILD
        if is_rebuild_needed(step_manifest.source_paths, step_manifest.dest_files):
            return ShouldBuild.BUILD

        # Restore context fields that run() would have set
        ctx.esbuild_args.extend(self._get_esbuild_args(ctx))
        ctx.esbuild_args.extend(self._get_wheel_esbuild_args(ctx))

        return ShouldBuild.SKIP

    def run(self, ctx: BuildContext) -> None:
        esbuild = get_bin(node_modules_path(ctx.workspace), "esbuild")
        output_file = ctx.workspace / "pyodide.worker-bundle"

        # Build the esbuild command for the worker
        cmd = [
            str(esbuild),
            str(_PYODIDE_WORKER_PATH),
            "--bundle",
            f"--outfile={output_file}",
            "--format=iife",
            "--platform=browser",
            "--target=es2022",
            "--loader:.ts=ts",
            f'--define:PYODIDE_VERSION="{PYODIDE_VERSION}"',
            f'--define:PYODIDE_PYTHON_VERSION="{self._get_python_version(ctx)}"',
        ]

        # Add wheel bundle/manifest as esbuild aliases for the worker build
        wheel_bundle = ctx.generated_files.get("wheel_bundle")
        wheel_manifest = ctx.generated_files.get("wheel_manifest")
        if wheel_bundle:
            cmd.append("--loader:.wheel-bundle=binary")
            cmd.append(f"--alias:@trellis/wheel-bundle={wheel_bundle}")
        if wheel_manifest:
            cmd.append(f"--alias:@trellis/wheel-manifest={wheel_manifest}")

        ctx.exec_in_build_env(cmd)

        # Add loader and alias so the main bundle can import the worker as text
        ctx.esbuild_args.extend(self._get_esbuild_args(ctx))
        ctx.esbuild_args.extend(self._get_wheel_esbuild_args(ctx))

        # Populate step manifest
        step_manifest = ctx.manifest.steps.setdefault(self.name, StepManifest())
        step_manifest.source_paths.add(_PYODIDE_WORKER_PATH.parent)
        if wheel_bundle:
            step_manifest.source_paths.add(wheel_bundle)
        if wheel_manifest:
            step_manifest.source_paths.add(wheel_manifest)
        step_manifest.dest_files.add(output_file)
