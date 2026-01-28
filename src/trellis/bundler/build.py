"""Bundle building with esbuild."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from trellis.bundler.manifest import BuildManifest, load_manifest, save_manifest
from trellis.bundler.python_source import find_package_root
from trellis.bundler.steps import BuildContext, ShouldBuild
from trellis.bundler.workspace import node_modules_path

if TYPE_CHECKING:
    from trellis.bundler.registry import ModuleRegistry
    from trellis.bundler.steps import BuildStep

logger = logging.getLogger(__name__)


def _import_entry_point(entry_point: Path) -> None:
    """Import a Python entry point file to trigger module registrations.

    This ensures any module registrations (like @registry.register decorators)
    in the entry point are executed before registry.collect() is called.

    For packages (detected by __init__.py), adds the package parent to sys.path
    and imports using runpy to support relative imports.

    Args:
        entry_point: Path to the Python entry point file
    """
    package_root = find_package_root(entry_point)

    if package_root is not None:
        # Package mode - add parent to sys.path and run as module
        package_parent = str(package_root.parent)
        if package_parent not in sys.path:
            sys.path.insert(0, package_parent)

        # Determine module name
        if entry_point.name == "__main__.py":
            module_name = package_root.name
        else:
            rel_path = entry_point.relative_to(package_root.parent)
            # Strip .py extension for module name (pkg/module.py -> pkg.module)
            module_name = str(rel_path.with_suffix("")).replace("/", ".").replace("\\", ".")

        # Skip if already imported (e.g., BrowserServer platform doesn't need this)
        if module_name in sys.modules:
            return

        importlib.import_module(module_name)
    else:
        # Single file mode
        spec = importlib.util.spec_from_file_location("__entry_point__", entry_point)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load entry point: {entry_point}")
        module = importlib.util.module_from_spec(spec)
        # Register module in sys.modules so decorators like @dataclass can resolve types
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)


def build(
    registry: ModuleRegistry,
    entry_point: Path,
    workspace: Path,
    steps: list[BuildStep],
    *,
    force: bool = False,
    output_dir: Path | None = None,
    app_static_dir: Path | None = None,
    python_entry_point: Path | None = None,
) -> None:
    """Run a build pipeline with the given steps.

    Each step decides whether to run via should_build():
    - SKIP: Step is up to date, copy old manifest section to new
    - BUILD/None: Step needs to run

    Args:
        registry: Module registry with registered modules
        entry_point: Path to entry point file (e.g., main.tsx)
        workspace: Workspace directory for generated files
        steps: List of build steps to execute in order
        force: Force rebuild even if up to date
        output_dir: Custom output directory (default: workspace/dist)
        app_static_dir: App-level static files directory to copy to dist
        python_entry_point: Python app entry point for browser bundling (optional)
    """
    # Import Python entry point to trigger module registrations before collect()
    if python_entry_point is not None:
        _import_entry_point(python_entry_point)

    collected = registry.collect()
    dist_dir = (output_dir or (workspace / "dist")).resolve()

    # Load previous manifest for per-step staleness check
    previous_manifest = load_manifest(workspace)

    # Create fresh manifest for this build (steps write directly to ctx.manifest.steps)
    manifest = BuildManifest()

    # Create build context with system environment so subprocess tools can find node
    ctx = BuildContext(
        registry=registry,
        entry_point=entry_point,
        workspace=workspace,
        collected=collected,
        dist_dir=dist_dir,
        manifest=manifest,
        app_static_dir=app_static_dir,
        python_entry_point=python_entry_point,
        env={
            **os.environ,
            "NODE_PATH": str(node_modules_path(workspace)),
        },
    )

    # Ensure directories exist
    workspace.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Single pass: evaluate and run each step in order
    for step in steps:
        prev_step_manifest = previous_manifest.steps.get(step.name) if previous_manifest else None

        # Run step if: forced or no previous manifest
        if force or prev_step_manifest is None:
            logger.debug("Running step: %s", step.name)
            step.run(ctx)
        else:
            # Check if step needs to rebuild
            decision = step.should_build(ctx, prev_step_manifest)
            if decision is None or decision == ShouldBuild.BUILD:
                logger.debug("Running step: %s", step.name)
                step.run(ctx)
            else:
                logger.debug("Skipping step: %s", step.name)
                ctx.manifest.steps[step.name] = prev_step_manifest

    # Save manifest for next build
    save_manifest(workspace, ctx.manifest)
