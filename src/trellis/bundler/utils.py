"""Shared utilities and constants for the bundler."""

from __future__ import annotations

import os
import sys
import tarfile
from collections.abc import Iterable
from pathlib import Path

BUN_VERSION = "1.3.5"


def _get_cache_dir() -> Path:
    """Get platform-specific cache directory for trellis."""
    if sys.platform == "win32":
        # Windows: %LOCALAPPDATA%\trellis
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        # macOS: ~/Library/Caches/trellis
        base = Path.home() / "Library" / "Caches"
    else:
        # Linux/Unix: $XDG_CACHE_HOME/trellis or ~/.cache/trellis
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "trellis"


CACHE_DIR = _get_cache_dir()
BIN_DIR = CACHE_DIR / "bin"


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
        # Reject device files and FIFOs
        if member.ischr() or member.isblk() or member.isfifo():
            raise ValueError(f"Tarball contains device/fifo entry: {member.name}")
        member_path = (dest / member.name).resolve()
        if not member_path.is_relative_to(dest):
            raise ValueError(f"Tarball contains path traversal: {member.name}")
    tar.extractall(dest, filter="data")


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

    # No outputs means nothing exists yet - rebuild needed
    if not output_list:
        return True

    # Check all outputs exist
    for output in output_list:
        if not output.exists():
            return True

    # Find oldest output mtime
    oldest_output = min(output.stat().st_mtime for output in output_list)

    # Check if any input (file or directory contents) is newer than oldest output
    for input_path in input_list:
        if not input_path.exists():
            return True  # Missing input forces rebuild
        newest_input = _get_newest_mtime(input_path)
        if newest_input > oldest_output:
            return True

    return False
