"""Bundle building with esbuild."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from trellis.bundler.manifest import BuildManifest, load_manifest, save_manifest
from trellis.bundler.steps import BuildContext, ShouldBuild
from trellis.bundler.workspace import node_modules_path

if TYPE_CHECKING:
    from trellis.bundler.registry import ModuleRegistry
    from trellis.bundler.steps import BuildStep

logger = logging.getLogger(__name__)


def build(
    registry: ModuleRegistry,
    entry_point: Path,
    workspace: Path,
    steps: list[BuildStep],
    *,
    force: bool = False,
    output_dir: Path,
    assets_dir: Path | None = None,
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
        output_dir: Output directory for built artifacts
        assets_dir: App-level static files directory to copy to dist
    """
    collected = registry.collect()
    dist_dir = output_dir.resolve()

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
        assets_dir=assets_dir,
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
