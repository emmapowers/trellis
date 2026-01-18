"""Shared utilities and constants for the bundler."""

from __future__ import annotations

import tarfile
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
