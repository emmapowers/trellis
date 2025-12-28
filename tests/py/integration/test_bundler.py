"""Integration tests for trellis.bundler module.

These tests download from npm registry and require network access.
"""

from __future__ import annotations

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
