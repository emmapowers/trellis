"""Integration tests for trellis.bundler module.

These tests download from npm registry and require network access.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.helpers import requires_pytauri
from trellis.bundler.workspace import get_project_workspace


class TestEnsurePackages:
    def test_installs_system_packages_including_esbuild(self, tmp_path: Path) -> None:
        """SYSTEM_PACKAGES (esbuild, typescript) are automatically installed."""
        from trellis.bundler.packages import SYSTEM_PACKAGES, ensure_packages, get_bin

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
        from trellis.bundler import registry
        from trellis.bundler.packages import ensure_packages

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


class TestServerPlatformBundle:
    def test_builds_bundle(self) -> None:
        """Builds client bundle successfully via ServerPlatform."""
        from trellis.platforms.server.platform import ServerPlatform

        # Bundle is now in the cache workspace
        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        entry_point = platforms_dir / "server" / "client" / "src" / "main.tsx"
        workspace = get_project_workspace(entry_point)
        bundle_path = workspace / "dist" / "bundle.js"

        # Force rebuild
        platform = ServerPlatform()
        platform.bundle(force=True)

        assert bundle_path.exists()
        assert bundle_path.stat().st_size > 0


class TestDesktopPlatformBundle:
    @requires_pytauri
    def test_builds_bundle_and_copies_html(self) -> None:
        """Builds desktop bundle and copies static index.html."""
        from trellis.platforms.desktop.platform import DesktopPlatform

        # Bundle is now in the cache workspace
        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        entry_point = platforms_dir / "desktop" / "client" / "src" / "main.tsx"
        workspace = get_project_workspace(entry_point)
        dist_dir = workspace / "dist"
        bundle_path = dist_dir / "bundle.js"
        index_path = dist_dir / "index.html"

        # Force rebuild
        platform = DesktopPlatform()
        platform.bundle(force=True)

        assert bundle_path.exists()
        assert bundle_path.stat().st_size > 0
        assert index_path.exists()
        # Verify HTML contains expected content
        html_content = index_path.read_text()
        assert '<div id="root" class="trellis-root"></div>' in html_content
        assert "bundle.js" in html_content


class TestBundleBuildCli:
    """Tests for the `trellis bundle build` CLI command."""

    def test_bundle_build_server_succeeds(self) -> None:
        """Running `trellis bundle build --platform server --force` succeeds."""
        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        entry_point = platforms_dir / "server" / "client" / "src" / "main.tsx"
        workspace = get_project_workspace(entry_point)
        server_bundle = workspace / "dist" / "bundle.js"

        mtime_before = server_bundle.stat().st_mtime if server_bundle.exists() else None

        result = subprocess.run(
            ["trellis", "bundle", "build", "--platform", "server", "--force"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, f"Bundle build failed:\n{result.stderr}"
        assert server_bundle.exists(), "Server bundle not created"
        assert server_bundle.stat().st_size > 0
        if mtime_before is not None:
            assert server_bundle.stat().st_mtime > mtime_before, "Bundle was not regenerated"

    @pytest.mark.xfail(reason="Browser platform broken - worker generation not yet implemented")
    def test_bundle_build_browser_succeeds(self) -> None:
        """Running `trellis bundle build --platform browser --force` succeeds."""
        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        entry_point = platforms_dir / "browser" / "client" / "src" / "main.tsx"
        workspace = get_project_workspace(entry_point)
        browser_bundle = workspace / "dist" / "bundle.js"

        mtime_before = browser_bundle.stat().st_mtime if browser_bundle.exists() else None

        result = subprocess.run(
            ["trellis", "bundle", "build", "--platform", "browser", "--force"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, f"Bundle build failed:\n{result.stderr}"
        assert browser_bundle.exists(), "Browser bundle not created"
        assert browser_bundle.stat().st_size > 0
        if mtime_before is not None:
            assert browser_bundle.stat().st_mtime > mtime_before, "Bundle was not regenerated"

    @requires_pytauri
    def test_bundle_build_desktop_succeeds(self) -> None:
        """Running `trellis bundle build --platform desktop --force` succeeds."""
        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        entry_point = platforms_dir / "desktop" / "client" / "src" / "main.tsx"
        workspace = get_project_workspace(entry_point)
        desktop_bundle = workspace / "dist" / "bundle.js"

        mtime_before = desktop_bundle.stat().st_mtime if desktop_bundle.exists() else None

        result = subprocess.run(
            ["trellis", "bundle", "build", "--platform", "desktop", "--force"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, f"Bundle build failed:\n{result.stderr}"
        assert desktop_bundle.exists(), "Desktop bundle not created"
        assert desktop_bundle.stat().st_size > 0
        if mtime_before is not None:
            assert desktop_bundle.stat().st_mtime > mtime_before, "Bundle was not regenerated"

    def test_bundle_build_with_dest_option(self, tmp_path: Path) -> None:
        """Running `trellis bundle build --dest <path>` outputs to specified directory."""
        dest_dir = tmp_path / "custom_output"

        result = subprocess.run(
            [
                "trellis",
                "bundle",
                "build",
                "--platform",
                "server",
                "--force",
                "--dest",
                str(dest_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, f"Bundle build failed:\n{result.stderr}"

        # Bundle should be directly in dest_dir
        bundle_path = dest_dir / "bundle.js"
        assert bundle_path.exists(), f"Bundle not found at {bundle_path}"
        assert bundle_path.stat().st_size > 0
