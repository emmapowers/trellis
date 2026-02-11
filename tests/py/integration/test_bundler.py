"""Integration tests for trellis.bundler module.

These tests download from npm registry and require network access.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from trellis.bundler import registry
from trellis.bundler.packages import SYSTEM_PACKAGES, ensure_packages, get_bin


@pytest.mark.network
@pytest.mark.slow
class TestEnsurePackages:
    def test_installs_system_packages_including_esbuild(self, tmp_path: Path) -> None:
        """SYSTEM_PACKAGES (esbuild, typescript) are automatically installed."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Empty user packages - only system packages will be installed
        ensure_packages({}, workspace)
        node_modules = workspace / "node_modules"

        # esbuild binary should be accessible
        esbuild = get_bin(node_modules, "esbuild")
        assert esbuild.exists(), f"esbuild binary not found at {esbuild}"
        assert esbuild.stat().st_mode & 0o111, "esbuild should be executable"

        # tsc binary should be accessible
        tsc = get_bin(node_modules, "tsc")
        assert tsc.exists(), f"tsc binary not found at {tsc}"

        # All system packages should be in node_modules
        for pkg in SYSTEM_PACKAGES:
            pkg_dir = node_modules / pkg
            assert pkg_dir.exists(), f"System package {pkg} not found"

    def test_installs_packages_with_bun(self, tmp_path: Path) -> None:
        """Installs packages using Bun and creates node_modules."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Get packages from registry (common platform registers them)
        collected = registry.collect()
        packages = collected.packages

        ensure_packages(packages, workspace)
        node_modules = workspace / "node_modules"

        # node_modules should exist
        assert node_modules.exists()

        # Check that direct dependencies are installed
        for name in packages:
            if name.startswith("@"):
                scope, pkg = name.split("/", 1)
                pkg_dir = node_modules / scope / pkg
            else:
                pkg_dir = node_modules / name
            assert pkg_dir.exists(), f"Package {name} not found"
            assert (pkg_dir / "package.json").exists()

        # Check that a lockfile was created
        assert (workspace / "bun.lock").exists()
        assert (workspace / "package.json").exists()
