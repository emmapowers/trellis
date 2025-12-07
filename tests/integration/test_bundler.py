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
        expected_path = BIN_DIR / f"esbuild-{ESBUILD_VERSION}-{plat}" / "package" / "bin" / binary_name

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


class TestBuildClient:
    def test_builds_bundle(self) -> None:
        """Builds client bundle successfully."""
        from trellis.bundler import build_client

        client_dir = Path(__file__).parent.parent.parent / "src" / "trellis" / "client"
        bundle_path = client_dir / "dist" / "bundle.js"

        # Force rebuild
        build_client(force=True)

        assert bundle_path.exists()
        assert bundle_path.stat().st_size > 0
