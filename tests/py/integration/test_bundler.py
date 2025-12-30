"""Integration tests for trellis.bundler module.

These tests download from npm registry and require network access.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class TestEnsureEsbuild:
    def test_downloads_esbuild_binary(self) -> None:
        """Downloads esbuild binary from npm registry."""
        from trellis.bundler import (
            BIN_DIR,
            ESBUILD_VERSION,
            _get_platform,
            ensure_esbuild,
        )

        plat = _get_platform()
        binary_name = "esbuild.exe" if plat.startswith("win32") else "esbuild"
        expected_path = (
            BIN_DIR / f"esbuild-{ESBUILD_VERSION}-{plat}" / "package" / "bin" / binary_name
        )

        result = ensure_esbuild()

        assert result.exists()
        assert result == expected_path
        assert result.stat().st_mode & 0o111  # Is executable


class TestEnsurePackages:
    def test_downloads_core_packages(self) -> None:
        """Downloads core npm packages from registry."""
        from trellis.bundler import CORE_PACKAGES, PACKAGES_DIR, ensure_packages

        result = ensure_packages()

        assert result == PACKAGES_DIR
        for name in CORE_PACKAGES:
            if name.startswith("@"):
                scope, pkg = name.split("/", 1)
                pkg_dir = PACKAGES_DIR / scope / pkg
            else:
                pkg_dir = PACKAGES_DIR / name
            assert pkg_dir.exists(), f"Package {name} not found"
            assert (pkg_dir / "package.json").exists()


class TestServerPlatformBundle:
    def test_builds_bundle(self) -> None:
        """Builds client bundle successfully via ServerPlatform."""
        from trellis.platforms.server.platform import ServerPlatform

        # Bundle is now at platforms/server/client/dist/
        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        bundle_path = platforms_dir / "server" / "client" / "dist" / "bundle.js"

        # Force rebuild
        platform = ServerPlatform()
        platform.bundle(force=True)

        assert bundle_path.exists()
        assert bundle_path.stat().st_size > 0


class TestDesktopPlatformBundle:
    def test_builds_bundle_and_copies_html(self) -> None:
        """Builds desktop bundle and copies static index.html."""
        pytest = __import__("pytest")
        try:
            from trellis.platforms.desktop.platform import DesktopPlatform
        except ImportError:
            pytest.skip("pytauri not installed")

        # Bundle is at platforms/desktop/client/dist/
        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        dist_dir = platforms_dir / "desktop" / "client" / "dist"
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
        assert '<div id="root"></div>' in html_content
        assert "bundle.js" in html_content


class TestBundleBuildCli:
    """Tests for the `trellis bundle build` CLI command."""

    def test_bundle_build_server_succeeds(self) -> None:
        """Running `trellis bundle build --platform server --force` succeeds."""
        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        server_bundle = platforms_dir / "server" / "client" / "dist" / "bundle.js"

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

    def test_bundle_build_browser_succeeds(self) -> None:
        """Running `trellis bundle build --platform browser --force` succeeds."""
        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        browser_bundle = platforms_dir / "browser" / "client" / "dist" / "bundle.js"

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

    def test_bundle_build_desktop_succeeds(self) -> None:
        """Running `trellis bundle build --platform desktop --force` succeeds."""
        pytest = __import__("pytest")
        try:
            import pytauri  # noqa: F401
        except ImportError:
            pytest.skip("pytauri not installed")

        platforms_dir = Path(__file__).parent.parent.parent.parent / "src" / "trellis" / "platforms"
        desktop_bundle = platforms_dir / "desktop" / "client" / "dist" / "bundle.js"

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
