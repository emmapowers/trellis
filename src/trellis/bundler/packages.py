"""NPM package management using Bun."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from .bun import ensure_bun
from .utils import CACHE_DIR

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


def get_packages_hash(packages: dict[str, str]) -> str:
    """Generate a hash of packages for cache keying.

    The hash is order-independent to ensure consistent caching
    regardless of dict iteration order.

    Args:
        packages: Dict mapping package names to versions

    Returns:
        Hex string hash of the packages
    """
    # Sort for order independence
    sorted_items = sorted(packages.items())
    content = json.dumps(sorted_items, separators=(",", ":"))
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def ensure_packages(packages: dict[str, str]) -> Path:
    """Install packages using Bun and return node_modules path.

    Creates a workspace directory keyed by a hash of the packages.
    If the workspace already has a bun.lock, installation is skipped.

    Args:
        packages: Dict mapping package names to versions.

    Returns:
        Path to the node_modules directory
    """
    # Merge system packages with user packages (user can override versions)
    all_packages = {**SYSTEM_PACKAGES, **packages}
    pkg_hash = get_packages_hash(all_packages)

    workspace = CACHE_DIR / "workspaces" / pkg_hash
    lockfile = workspace / "bun.lock"
    node_modules = workspace / "node_modules"

    # Skip if already installed (lockfile exists)
    if lockfile.exists() and node_modules.exists():
        return node_modules

    # Ensure workspace exists
    workspace.mkdir(parents=True, exist_ok=True)

    # Write package.json
    pkg_json = generate_package_json(all_packages)
    pkg_json_path = workspace / "package.json"
    pkg_json_path.write_text(json.dumps(pkg_json, indent=2))

    # Run bun install
    bun = ensure_bun()
    subprocess.run(
        [str(bun), "install"],
        cwd=workspace,
        check=True,
    )

    return node_modules
