"""Shared utilities and constants for the bundler."""

from __future__ import annotations

import tarfile
from pathlib import Path

BUN_VERSION = "1.3.5"
CACHE_DIR = Path.home() / ".cache" / "trellis"
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
        member_path = (dest / member.name).resolve()
        if not member_path.is_relative_to(dest):
            raise ValueError(f"Tarball contains path traversal: {member.name}")
    tar.extractall(dest)
