"""Integration tests for trellis.bundler module.

These tests download from npm registry and require network access.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import requires_pytauri
from trellis.app.apploader import AppLoader, get_dist_dir, get_workspace_dir, set_apploader
from trellis.bundler import registry
from trellis.bundler.metafile import get_metafile_path, read_metafile
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


@pytest.mark.network
@pytest.mark.slow
class TestServerPlatformBundle:
    """Integration tests for ServerPlatform.bundle()."""

    @pytest.fixture(autouse=True)
    def setup_apploader(self, tmp_path: Path, reset_apploader: None) -> None:
        """Set up apploader with tmp_path as app root."""
        apploader = AppLoader(tmp_path)
        set_apploader(apploader)

    def test_builds_bundle(self) -> None:
        """Builds client bundle successfully via ServerPlatform."""
        from trellis.platforms.server.platform import ServerPlatform  # noqa: PLC0415

        dist_dir = get_dist_dir()
        bundle_path = dist_dir / "bundle.js"

        platform = ServerPlatform()
        platform.bundle(force=True)

        assert bundle_path.exists()
        assert bundle_path.stat().st_size > 0

    def test_generates_metafile(self) -> None:
        """Build generates metafile.json with input/output information."""
        from trellis.platforms.server.platform import ServerPlatform  # noqa: PLC0415

        workspace = get_workspace_dir()

        platform = ServerPlatform()
        platform.bundle(force=True)

        # Metafile should exist
        metafile_path = get_metafile_path(workspace)
        assert metafile_path.exists(), "metafile.json not created"

        # Metafile should be parseable
        metafile = read_metafile(workspace)
        assert len(metafile.inputs) > 0, "Metafile should have inputs"
        assert len(metafile.outputs) > 0, "Metafile should have outputs"

        # Entry point should be in inputs
        assert any(
            p.name == "main.tsx" for p in metafile.inputs
        ), "Entry point not in metafile inputs"

        # Bundle should be in outputs
        assert any(
            p.name == "bundle.js" for p in metafile.outputs
        ), "bundle.js not in metafile outputs"


@pytest.mark.network
@pytest.mark.slow
@requires_pytauri
class TestDesktopPlatformBundle:
    """Integration tests for DesktopPlatform.bundle()."""

    @pytest.fixture(autouse=True)
    def setup_apploader(self, tmp_path: Path, reset_apploader: None) -> None:
        """Set up apploader with tmp_path as app root."""
        apploader = AppLoader(tmp_path)
        set_apploader(apploader)

    def test_builds_bundle_and_copies_html(self) -> None:
        """Builds desktop bundle and copies static index.html."""
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        dist_dir = get_dist_dir()
        bundle_path = dist_dir / "bundle.js"
        index_path = dist_dir / "index.html"

        platform = DesktopPlatform()
        platform.bundle(force=True)

        assert bundle_path.exists()
        assert bundle_path.stat().st_size > 0
        assert index_path.exists()
        # Verify HTML contains expected content
        html_content = index_path.read_text()
        assert '<div id="root" class="trellis-root"></div>' in html_content
        assert "bundle.js" in html_content
