"""Shared utilities and constants for the bundler."""

from __future__ import annotations

import tarfile
from collections.abc import Iterable
from pathlib import Path

BUN_VERSION = "1.3.5"
CACHE_DIR = Path.home() / ".cache" / "trellis"
BIN_DIR = CACHE_DIR / "bin"


def find_project_root(entry_point: Path) -> Path:
    """Find the project root directory by walking up from the entry point.

    Looks for project markers in this priority order:
    1. pyproject.toml
    2. .git (file or directory - handles worktrees)

    Falls back to the entry point's parent directory if no markers found.

    Args:
        entry_point: Path to the project's entry point file

    Returns:
        Path to the project root directory
    """
    current = entry_point.resolve().parent

    while True:
        # Check for pyproject.toml first (highest priority)
        if (current / "pyproject.toml").exists():
            return current

        # Check for .git (file for worktrees, directory for normal repos)
        if (current / ".git").exists():
            return current

        # Move up to parent
        parent = current.parent
        if parent == current:
            # Reached filesystem root, fallback to entry point's parent
            return entry_point.resolve().parent

        current = parent


def safe_extract(tar: tarfile.TarFile, dest: Path) -> None:
    """Safely extract a tarball, preventing path traversal attacks.

    Validates that all extracted paths stay within the destination directory.
    This prevents malicious tarballs from writing files outside the intended
    directory via paths like "../../../etc/passwd".

    Args:
        tar: The tarfile to extract
        dest: The destination directory

    Raises:
        ValueError: If any member would extract outside the destination
    """
    dest = dest.resolve()
    for member in tar.getmembers():
        # Reject symlinks and hardlinks to prevent link-based escapes
        if member.issym() or member.islnk():
            raise ValueError(f"Tarball contains link entry: {member.name}")
        member_path = (dest / member.name).resolve()
        if not member_path.is_relative_to(dest):
            raise ValueError(f"Tarball contains path traversal: {member.name}")
    tar.extractall(dest)


def _get_newest_mtime(path: Path) -> float:
    """Get the newest modification time for a path.

    For files, returns the file's mtime.
    For directories, recursively walks all files and returns the newest mtime
    found (including the directory itself).

    Args:
        path: File or directory path

    Returns:
        Modification time as float timestamp
    """
    if path.is_file():
        return path.stat().st_mtime

    # For directories, find the newest mtime among all contents
    newest = path.stat().st_mtime
    for item in path.rglob("*"):
        try:
            item_mtime = item.stat().st_mtime
            newest = max(newest, item_mtime)
        except OSError:
            # File may have been deleted during walk
            continue
    return newest


def is_rebuild_needed(inputs: Iterable[Path], outputs: Iterable[Path]) -> bool:
    """Check if outputs are stale relative to inputs.

    Returns True if any output is missing or older than any input.
    For directory inputs, recursively checks all files in the directory.

    Args:
        inputs: Source files or directories to check
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

    # Check if any input (file or directory contents) is newer than oldest output
    for input_path in input_list:
        if input_path.exists():
            newest_input = _get_newest_mtime(input_path)
            if newest_input > oldest_output:
                return True

    return False
