"""Python source collection utilities for bundling.

Provides functions to collect Python source files for bundling.
"""

from __future__ import annotations

from pathlib import Path


def find_package_root(source_path: Path) -> Path | None:
    """Find the root directory of a Python package containing the source file.

    Walks up from source_path looking for __init__.py files.
    Returns the topmost package directory, or None if not in a package.

    Args:
        source_path: Path to the source file

    Returns:
        Path to package root directory, or None if not a package
    """
    current = source_path.parent
    package_root = None

    # Walk up looking for __init__.py, stopping at filesystem root
    while current != current.parent and (current / "__init__.py").exists():
        package_root = current
        current = current.parent

    return package_root


def collect_package_files(package_dir: Path) -> dict[str, str]:
    """Collect all Python files in a package directory.

    Args:
        package_dir: Root directory of the package

    Returns:
        Dict mapping relative paths (including package name) to file contents
    """
    files: dict[str, str] = {}

    for py_file in package_dir.rglob("*.py"):
        # Skip __pycache__ and hidden directories
        if "__pycache__" in py_file.parts:
            continue
        if any(part.startswith(".") for part in py_file.parts):
            continue

        # Get path relative to package parent (so package name is included)
        rel_path = py_file.relative_to(package_dir.parent)
        files[str(rel_path)] = py_file.read_text()

    return files
