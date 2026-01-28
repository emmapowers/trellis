"""Integration tests for trellis.bundler module.

These tests download from npm registry and require network access.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.helpers import HAS_PYTAURI, requires_pytauri
from trellis.bundler import registry
from trellis.bundler.metafile import get_metafile_path, read_metafile
from trellis.bundler.packages import SYSTEM_PACKAGES, ensure_packages, get_bin
from trellis.bundler.workspace import get_project_workspace
from trellis.platforms.server import platform as server_platform_module

# Desktop requires pytauri which isn't available in CI
if HAS_PYTAURI:
    from trellis.platforms.desktop import platform as desktop_platform_module
from trellis.platforms.server.platform import ServerPlatform


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
    def test_builds_bundle(self) -> None:
        """Builds client bundle successfully via ServerPlatform."""
        # Bundle is now in the cache workspace
        server_dir = Path(server_platform_module.__file__).parent
        entry_point = server_dir / "client" / "src" / "main.tsx"
        workspace = get_project_workspace(entry_point)
        bundle_path = workspace / "dist" / "bundle.js"

        # Force rebuild
        platform = ServerPlatform()
        platform.bundle(force=True)

        assert bundle_path.exists()
        assert bundle_path.stat().st_size > 0

    def test_generates_metafile(self) -> None:
        """Build generates metafile.json with input/output information."""
        server_dir = Path(server_platform_module.__file__).parent
        entry_point = server_dir / "client" / "src" / "main.tsx"
        workspace = get_project_workspace(entry_point)

        # Force rebuild
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
class TestDesktopPlatformBundle:
    @requires_pytauri
    def test_builds_bundle_and_copies_html(self) -> None:
        """Builds desktop bundle and copies static index.html."""
        # Desktop import requires pytauri which isn't available in CI
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        # Bundle is now in the cache workspace
        desktop_dir = Path(desktop_platform_module.__file__).parent
        entry_point = desktop_dir / "client" / "src" / "main.tsx"
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


@pytest.mark.network
@pytest.mark.slow
class TestBundleBuildCli:
    """Tests for the `trellis bundle build` CLI command."""

    def test_bundle_build_server_succeeds(self) -> None:
        """Running `trellis bundle build --platform server --force` succeeds."""
        server_dir = Path(server_platform_module.__file__).parent
        entry_point = server_dir / "client" / "src" / "main.tsx"
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

    def test_bundle_build_browser_requires_library_or_app(self) -> None:
        """Browser build without --library or --app shows helpful error."""
        result = subprocess.run(
            ["trellis", "bundle", "build", "--platform", "browser", "--force"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode != 0, "Should fail without --library or --app"
        assert "Browser app mode requires a Python entry point" in result.stderr
        assert "--app" in result.stderr
        assert "--library" in result.stderr

    def test_bundle_build_browser_library_mode(self, tmp_path: Path) -> None:
        """Browser library mode builds successfully with --library flag."""
        dest = tmp_path / "lib_output"

        result = subprocess.run(
            [
                "trellis",
                "bundle",
                "build",
                "--platform",
                "browser",
                "--library",
                "--force",
                "--dest",
                str(dest),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, f"Build failed:\n{result.stderr}"
        assert (dest / "index.js").exists(), "index.js not created"
        assert (dest / "index.css").exists(), "index.css not created"
        assert (dest / "index.d.ts").exists(), "TypeScript declarations not created"
        assert not (dest / "index.html").exists(), "Library mode should not create HTML"

    def test_bundle_build_browser_app_with_package(self, tmp_path: Path) -> None:
        """Browser app mode builds a Python package with --app flag."""
        # Create test package
        pkg_dir = tmp_path / "myapp"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "__main__.py").write_text(
            "from trellis import component\n"
            "from trellis.html import Div\n"
            "@component\n"
            "def App():\n"
            "    Div()\n"
        )

        dest = tmp_path / "app_output"
        result = subprocess.run(
            [
                "trellis",
                "bundle",
                "build",
                "--platform",
                "browser",
                "--app",
                str(pkg_dir / "__main__.py"),
                "--force",
                "--dest",
                str(dest),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, f"Build failed:\n{result.stderr}"
        assert (dest / "bundle.js").exists(), "bundle.js not created"
        assert (dest / "index.html").exists(), "index.html not created"

        html = (dest / "index.html").read_text()
        assert "window.__TRELLIS_CONFIG__" in html, "Config not embedded in HTML"

    def test_bundle_build_browser_app_with_single_file(self, tmp_path: Path) -> None:
        """Browser app mode builds a standalone .py file (not in a package)."""
        # Create standalone file (no __init__.py nearby)
        app_file = tmp_path / "standalone_app.py"
        app_file.write_text(
            "from trellis import component\n"
            "from trellis.html import Div\n"
            "@component\n"
            "def App():\n"
            "    Div()\n"
        )

        dest = tmp_path / "standalone_output"
        result = subprocess.run(
            [
                "trellis",
                "bundle",
                "build",
                "--platform",
                "browser",
                "--app",
                str(app_file),
                "--force",
                "--dest",
                str(dest),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, f"Build failed:\n{result.stderr}"
        assert (dest / "bundle.js").exists(), "bundle.js not created"
        assert (dest / "index.html").exists(), "index.html not created"

    @requires_pytauri
    def test_bundle_build_desktop_succeeds(self) -> None:
        """Running `trellis bundle build --platform desktop --force` succeeds."""
        desktop_dir = Path(desktop_platform_module.__file__).parent
        entry_point = desktop_dir / "client" / "src" / "main.tsx"
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
