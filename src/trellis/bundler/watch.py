"""Watch mode for automatic bundle rebuilding.

This module provides file watching functionality to automatically rebuild
bundles when source files change.

Note: This module should NOT be imported in the browser platform runtime
since watchfiles is not available in Pyodide.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from .build import build

if TYPE_CHECKING:
    from .registry import CollectedModules, ModuleRegistry
    from .steps import BuildStep

logger = logging.getLogger(__name__)


def get_watch_paths(entry_point: Path, collected: CollectedModules) -> set[Path]:
    """Get all file paths that should trigger a rebuild when changed.

    This includes:
    - The entry point file
    - All module source files
    - All static file sources

    Snippets are NOT included since they are inline code, not files.

    Args:
        entry_point: Path to the entry point file
        collected: Collected modules from the registry

    Returns:
        Set of paths to watch
    """
    paths: set[Path] = {entry_point.resolve()}

    for module in collected.modules:
        # Add module source files
        if module._base_path:
            for file_path in module.files:
                paths.add((module._base_path / file_path).resolve())

        # Add static file sources
        for src_path in module.static_files.values():
            paths.add(src_path.resolve())

    return paths


def get_watch_directories(entry_point: Path, collected: CollectedModules) -> set[Path]:
    """Get directories to watch for file changes.

    Returns parent directories of all watchable files. This is useful for
    file watchers that work at the directory level.

    Args:
        entry_point: Path to the entry point file
        collected: Collected modules from the registry

    Returns:
        Set of directories to watch
    """
    paths = get_watch_paths(entry_point, collected)
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
    """
    # Import watchfiles here to avoid loading it when not needed
    # (especially important for browser platform where it's unavailable)
    import watchfiles

    # Get collected modules for watch paths
    collected = registry.collect()
    watch_dirs = get_watch_directories(entry_point, collected)
    watch_paths = get_watch_paths(entry_point, collected)

    logger.info("Watch mode enabled, monitoring %d files", len(watch_paths))

    # Watch the directories
    async for changes in watchfiles.awatch(*watch_dirs):
        # Filter to only changes in our watched files
        relevant_changes = [
            (change_type, path) for change_type, path in changes if Path(path) in watch_paths
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

                # Notify caller of successful rebuild
                if on_rebuild is not None:
                    on_rebuild()
            except Exception:
                logger.exception("Bundle rebuild failed")


def start_watch_task(
    registry: ModuleRegistry,
    entry_point: Path,
    workspace: Path,
    steps: list[BuildStep],
) -> asyncio.Task[None]:
    """Start a background task to watch and rebuild.

    Returns a task that can be cancelled to stop watching.

    Args:
        registry: Module registry with registered modules
        entry_point: Path to entry point file
        workspace: Workspace directory for staging and output
        steps: Build steps to execute on rebuild

    Returns:
        Asyncio task running the watch loop
    """
    return asyncio.create_task(
        watch_and_rebuild(registry, entry_point, workspace, steps),
        name="bundle-watcher",
    )
