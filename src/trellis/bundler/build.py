"""Bundle building with esbuild."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from trellis.bundler.steps import BuildContext

from .registry import SUPPORTED_SOURCE_TYPES

if TYPE_CHECKING:
    from trellis.bundler.registry import CollectedModules, ModuleRegistry
    from trellis.bundler.steps import BuildStep

logger = logging.getLogger(__name__)


def is_rebuild_needed(inputs: Iterable[Path], outputs: Iterable[Path]) -> bool:
    """Check if outputs are stale relative to inputs.

    Returns True if any output is missing or older than any input.

    Args:
        inputs: Source files to check
        outputs: Output files that should be newer than inputs

    Returns:
        True if rebuild is needed, False if outputs are up to date
    """
    input_list = list(inputs)
    output_list = list(outputs)

    # No inputs means nothing to rebuild from
    if not input_list:
        return False

    # Check all outputs exist
    for output in output_list:
        if not output.exists():
            return True

    # Find oldest output mtime
    oldest_output = min(output.stat().st_mtime for output in output_list)

    # Check if any input is newer than oldest output
    for input_file in input_list:
        if input_file.exists() and input_file.stat().st_mtime > oldest_output:
            return True

    return False


def _collect_input_files(entry_point: Path, collected: CollectedModules) -> list[Path]:
    """Collect all input files for cache checking.

    Args:
        entry_point: Main entry point file
        collected: Collected modules from registry

    Returns:
        List of input file paths
    """
    inputs = [entry_point]

    # Add source files from all modules with base paths
    for module in collected.modules:
        if module._base_path and module._base_path.exists():
            # Add all source files in module directory
            for ext in SUPPORTED_SOURCE_TYPES:
                inputs.extend(module._base_path.rglob(f"*{ext}"))

    return inputs


def build(
    registry: ModuleRegistry,
    entry_point: Path,
    workspace: Path,
    steps: list[BuildStep],
    *,
    force: bool = False,
    output_dir: Path | None = None,
) -> None:
    """Run a build pipeline with the given steps.

    Args:
        registry: Module registry with registered modules
        entry_point: Path to entry point file (e.g., main.tsx)
        workspace: Workspace directory for generated files
        steps: List of build steps to execute in order
        force: Force rebuild even if up to date
        output_dir: Custom output directory (default: workspace/dist)
    """

    collected = registry.collect()
    dist_dir = output_dir or (workspace / "dist")

    # Check if rebuild is needed (skip if outputs up to date)
    if not force:
        inputs = _collect_input_files(entry_point, collected)
        # esbuild produces bundle.js and optionally bundle.css when CSS is imported.
        # We only check bundle.js for cache invalidation since it's always produced.
        outputs = [dist_dir / "bundle.js"]

        if not is_rebuild_needed(inputs, outputs):
            logger.debug("Skipping build: outputs up to date")
            return

    dist_dir.mkdir(parents=True, exist_ok=True)

    # Create build context with system environment so subprocess tools can find node
    ctx = BuildContext(
        registry=registry,
        entry_point=entry_point,
        workspace=workspace,
        collected=collected,
        dist_dir=dist_dir,
        env=os.environ.copy(),
    )

    for step in steps:
        logger.debug("Running step: %s", step.name)
        step.run(ctx)
