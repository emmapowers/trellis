"""NPM package management using Bun."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from .bun import ensure_bun
from .utils import CACHE_DIR

# Direct dependencies only - Bun resolves transitive deps automatically
PACKAGES = {
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "@msgpack/msgpack": "3.0.0",
    # Icons
    "lucide-react": "0.468.0",
    # Charts
    "uplot": "1.6.31",
    "recharts": "3.6.0",
    # React Aria (accessibility) - umbrella packages handle sub-dependencies
    "react-aria": "3.35.0",
    "react-stately": "3.33.0",
    # Internationalization
    "@internationalized/date": "3.5.6",
}

# Additional packages for desktop platform (PyTauri)
DESKTOP_PACKAGES = {
    "@tauri-apps/api": "2.8.0",
    "tauri-plugin-pytauri-api": "0.8.0",
}


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


def ensure_packages(packages: dict[str, str] | None = None) -> Path:
    """Install packages using Bun and return node_modules path.

    Creates a workspace directory keyed by a hash of the packages.
    If the workspace already has a bun.lock, installation is skipped.

    Args:
        packages: Dict mapping package names to versions.
                  Defaults to PACKAGES if not provided.

    Returns:
        Path to the node_modules directory
    """
    packages = packages or PACKAGES
    pkg_hash = get_packages_hash(packages)

    workspace = CACHE_DIR / "workspaces" / pkg_hash
    lockfile = workspace / "bun.lock"
    node_modules = workspace / "node_modules"

    # Skip if already installed (lockfile exists)
    if lockfile.exists() and node_modules.exists():
        return node_modules

    # Ensure workspace exists
    workspace.mkdir(parents=True, exist_ok=True)

    # Write package.json
    pkg_json = generate_package_json(packages)
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
