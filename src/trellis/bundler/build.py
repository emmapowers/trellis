"""Bundle building with esbuild."""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from trellis.bundler.metafile import read_metafile
from trellis.bundler.steps import BuildContext

if TYPE_CHECKING:
    from trellis.bundler.registry import ModuleRegistry
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


def _collect_input_files(workspace: Path) -> list[Path]:
    """Collect all input files for cache checking from metafile.

    Args:
        workspace: Workspace directory containing metafile.json

    Returns:
        List of input file paths from metafile

    Raises:
        FileNotFoundError: If metafile.json doesn't exist
    """
    return read_metafile(workspace).inputs


def build(
    registry: ModuleRegistry,
    entry_point: Path,
    workspace: Path,
    steps: list[BuildStep],
    *,
    force: bool = False,
    output_dir: Path | None = None,
    app_static_dir: Path | None = None,
) -> None:
    """Run a build pipeline with the given steps.

    Args:
        registry: Module registry with registered modules
        entry_point: Path to entry point file (e.g., main.tsx)
        workspace: Workspace directory for generated files
        steps: List of build steps to execute in order
        force: Force rebuild even if up to date
        output_dir: Custom output directory (default: workspace/dist)
        app_static_dir: App-level static files directory to copy to dist
    """

    collected = registry.collect()
    dist_dir = output_dir or (workspace / "dist")

    # Check if rebuild is needed (skip if outputs up to date)
    if not force:
        try:
            inputs = _collect_input_files(workspace)
        except FileNotFoundError:
            # No metafile from previous build - need to build
            logger.debug("No metafile found, forcing rebuild")
        else:
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
        app_static_dir=app_static_dir,
        env=os.environ.copy(),
    )

    for step in steps:
        logger.debug("Running step: %s", step.name)
        step.run(ctx)
