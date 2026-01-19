"""NPM package management using Bun."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from trellis.bundler.bun import ensure_bun

# System packages always installed with every build
SYSTEM_PACKAGES: dict[str, str] = {
    "esbuild": "0.27.2",
    "typescript": "5.7.3",
}


def get_bin(node_modules: Path, name: str) -> Path:
    """Get path to a binary installed in node_modules.

    Args:
        node_modules: Path to node_modules directory
        name: Name of the binary (e.g., "esbuild", "tsc")

    Returns:
        Path to the binary in node_modules/.bin/
    """
    return node_modules / ".bin" / name


def generate_package_json(packages: dict[str, str]) -> dict[str, object]:
    """Generate a package.json dict from packages.

    Args:
        packages: Dict mapping package names to versions

    Returns:
        A dict suitable for writing as package.json
    """
    return {
        "name": "trellis-client",
        "private": True,
        "dependencies": packages,
    }


def _is_install_needed(workspace: Path, pkg_json_content: str) -> bool:
    """Check if bun install is needed.

    Install is needed if:
    - package.json doesn't exist or has different content
    - bun.lock doesn't exist
    - node_modules doesn't exist

    Args:
        workspace: Path to workspace directory
        pkg_json_content: Expected package.json content

    Returns:
        True if bun install should be run
    """
    pkg_json_path = workspace / "package.json"
    lockfile = workspace / "bun.lock"
    node_modules = workspace / "node_modules"

    # Check all required files exist
    if not lockfile.exists() or not node_modules.exists():
        return True

    # Check package.json content matches
    if not pkg_json_path.exists():
        return True

    existing_content = pkg_json_path.read_text()
    return existing_content != pkg_json_content


def ensure_packages(packages: dict[str, str], workspace: Path) -> None:
    """Install packages using Bun into the specified workspace.

    If the workspace already has a matching package.json and bun.lock,
    installation is skipped.

    Args:
        packages: Dict mapping package names to versions.
        workspace: Path to the workspace directory for installation.
    """
    # Merge system packages with user packages (user can override versions)
    all_packages = {**SYSTEM_PACKAGES, **packages}

    # Generate package.json content
    pkg_json = generate_package_json(all_packages)
    pkg_json_content = json.dumps(pkg_json, indent=2)

    # Skip if already installed with same packages
    if not _is_install_needed(workspace, pkg_json_content):
        return

    # Ensure workspace exists
    workspace.mkdir(parents=True, exist_ok=True)

    # Write package.json
    pkg_json_path = workspace / "package.json"
    pkg_json_path.write_text(pkg_json_content)

    # Run bun install
    bun = ensure_bun()
    subprocess.run(
        [str(bun), "install"],
        cwd=workspace,
        check=True,
    )
