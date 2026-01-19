"""Watch mode for automatic bundle rebuilding.

This module provides file watching functionality to automatically rebuild
bundles when source files change.

Note: This module should NOT be imported in the browser platform runtime
since watchfiles is not available in Pyodide.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from trellis.bundler.build import build
from trellis.bundler.metafile import read_metafile

if TYPE_CHECKING:
    from trellis.bundler.registry import ModuleRegistry
    from trellis.bundler.steps import BuildStep

logger = logging.getLogger(__name__)


def get_watch_paths(workspace: Path) -> set[Path]:
    """Get all paths that should trigger a rebuild when changed.

    Reads the metafile from a previous build to get the exact list of
    input files that were used in the bundle.

    Args:
        workspace: Workspace directory containing metafile.json

    Returns:
        Set of resolved absolute paths to watch

    Raises:
        FileNotFoundError: If metafile.json doesn't exist
    """
    metafile = read_metafile(workspace)
    return {p.resolve() for p in metafile.inputs}


def get_watch_directories(workspace: Path) -> set[Path]:
    """Get directories to watch for file changes.

    Returns parent directories of all watch paths. This is needed because
    watchfiles monitors directories, not individual files.

    Args:
        workspace: Workspace directory containing metafile.json

    Returns:
        Set of directories to watch

    Raises:
        FileNotFoundError: If metafile.json doesn't exist
    """
    paths = get_watch_paths(workspace)
    return {p.parent for p in paths}


async def watch_and_rebuild(
    registry: ModuleRegistry,
    entry_point: Path,
    workspace: Path,
    steps: list[BuildStep],
    on_rebuild: Callable[[], None] | None = None,
) -> None:
    """Watch source files and rebuild when they change.

    This function runs indefinitely, watching for file changes and
    triggering rebuilds. It should be run as a background task.

    Args:
        registry: Module registry with registered modules
        entry_point: Path to entry point file
        workspace: Workspace directory for staging and output
        steps: Build steps to execute on rebuild
        on_rebuild: Optional callback invoked after successful rebuild

    Raises:
        FileNotFoundError: If metafile.json doesn't exist (build must run first)
    """
    # Import watchfiles here to avoid loading it when not needed
    # (especially important for browser platform where it's unavailable)
    import watchfiles  # noqa: PLC0415

    # Get watch paths from metafile (requires build to have run first)
    watch_paths = get_watch_paths(workspace)
    watch_dirs = get_watch_directories(workspace)

    logger.info("Watch mode enabled, monitoring %d files", len(watch_paths))

    # Watch the directories
    async for changes in watchfiles.awatch(*watch_dirs):
        # Filter to only changes in our watched paths (exact file matches)
        relevant_changes = [
            (change_type, path)
            for change_type, path in changes
            if Path(path).resolve() in watch_paths
        ]

        if relevant_changes:
            changed_files = [Path(path).name for _, path in relevant_changes]
            logger.info("Detected changes in: %s", ", ".join(changed_files))

            try:
                # Force rebuild
                build(
                    registry=registry,
                    entry_point=entry_point,
                    workspace=workspace,
                    steps=steps,
                    force=True,
                )
                logger.info("Bundle rebuilt successfully")

                # Update watch paths from new metafile
                watch_paths = get_watch_paths(workspace)
                new_dirs = get_watch_directories(workspace)
                if new_dirs != watch_dirs:
                    # Directories changed - need to restart watcher
                    # For now, just log it. Full restart would require restructuring.
                    logger.info("Watch directories changed, some changes may be missed")
                    watch_dirs = new_dirs

                # Notify caller of successful rebuild
                if on_rebuild is not None:
                    on_rebuild()
            except Exception:
                logger.exception("Bundle rebuild failed")
