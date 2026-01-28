"""Unit tests for trellis.bundler.packages module (Bun-based installation)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from trellis.bundler.packages import (
    SYSTEM_PACKAGES,
    ensure_packages,
    generate_package_json,
    get_bin,
)


class TestGeneratePackageJson:
    """Tests for generate_package_json function."""

    def test_creates_valid_json_structure(self) -> None:
        """Returns a valid package.json dict structure."""
        packages = {"react": "18.3.1", "react-dom": "18.3.1"}
        result = generate_package_json(packages)

        assert result["name"] == "trellis-client"
        assert result["private"] is True
        assert "dependencies" in result

    def test_includes_all_packages_as_dependencies(self) -> None:
        """All packages appear in dependencies with correct versions."""
        packages = {
            "react": "18.3.1",
            "react-dom": "18.3.1",
            "@msgpack/msgpack": "3.0.0",
        }
        result = generate_package_json(packages)

        assert result["dependencies"] == packages

    def test_empty_packages_creates_empty_dependencies(self) -> None:
        """Empty packages dict creates empty dependencies."""
        result = generate_package_json({})

        assert result["dependencies"] == {}

    def test_scoped_packages_handled_correctly(self) -> None:
        """Scoped packages like @scope/name are handled."""
        packages = {
            "@react-aria/button": "3.10.0",
            "@tauri-apps/api": "2.8.0",
        }
        result = generate_package_json(packages)

        assert result["dependencies"]["@react-aria/button"] == "3.10.0"
        assert result["dependencies"]["@tauri-apps/api"] == "2.8.0"


class TestEnsurePackages:
    """Tests for ensure_packages function using Bun."""

    def test_requires_workspace_parameter(self, tmp_path: Path) -> None:
        """ensure_packages requires a workspace parameter."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
            mock_bun.return_value = tmp_path / "bun"
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                # Should accept workspace parameter and return None
                result = ensure_packages({"react": "18.3.1"}, workspace)

                assert result is None

    def test_installs_in_provided_workspace(self, tmp_path: Path) -> None:
        """Installs packages directly in the provided workspace."""
        workspace = tmp_path / "my_workspace"
        workspace.mkdir()

        with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
            mock_bun.return_value = tmp_path / "bun"
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                ensure_packages({"react": "18.3.1"}, workspace)

                # Should run bun install in the provided workspace
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs["cwd"] == workspace

    def test_returns_none(self, tmp_path: Path) -> None:
        """Returns None (caller constructs node_modules path from workspace)."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
            mock_bun.return_value = tmp_path / "bun"
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = ensure_packages({"react": "18.3.1"}, workspace)

        assert result is None

    def test_skips_install_if_package_json_unchanged(self, tmp_path: Path) -> None:
        """Skips bun install if package.json already has same content."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        packages = {"react": "18.3.1"}
        all_packages = {**SYSTEM_PACKAGES, **packages}

        # Pre-create package.json with same content
        pkg_json = {
            "name": "trellis-client",
            "private": True,
            "dependencies": all_packages,
        }
        (workspace / "package.json").write_text(json.dumps(pkg_json, indent=2))
        (workspace / "bun.lock").touch()
        (workspace / "node_modules").mkdir()

        with patch("subprocess.run") as mock_run:
            ensure_packages(packages, workspace)

        # Should NOT have called subprocess (bun install)
        mock_run.assert_not_called()

    def test_runs_install_if_package_json_differs(self, tmp_path: Path) -> None:
        """Runs bun install if package.json has different content."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Pre-create package.json with different content
        (workspace / "package.json").write_text('{"dependencies": {"old": "1.0.0"}}')
        (workspace / "bun.lock").touch()
        (workspace / "node_modules").mkdir()

        with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
            mock_bun.return_value = tmp_path / "bun"
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                ensure_packages({"react": "18.3.1"}, workspace)

        # Should have called bun install
        mock_run.assert_called_once()

    def test_runs_install_if_no_lockfile(self, tmp_path: Path) -> None:
        """Runs bun install if no bun.lock exists."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
            mock_bun.return_value = tmp_path / "bun"
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                ensure_packages({"react": "18.3.1"}, workspace)

        # Should have called bun install
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "install" in cmd

    def test_writes_package_json_before_install(self, tmp_path: Path) -> None:
        """Writes package.json to workspace before running bun install."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        packages = {"react": "18.3.1", "lodash": "4.17.21"}
        expected_packages = {**SYSTEM_PACKAGES, **packages}

        with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
            mock_bun.return_value = tmp_path / "bun"

            with patch("subprocess.run") as mock_run:

                def verify_package_json(*args, **kwargs):
                    # Verify package.json was written before install
                    pkg_json = workspace / "package.json"
                    assert pkg_json.exists(), "package.json should exist before bun install"
                    content = json.loads(pkg_json.read_text())
                    # Should include both user packages and SYSTEM_PACKAGES
                    assert content["dependencies"] == expected_packages
                    return MagicMock(returncode=0)

                mock_run.side_effect = verify_package_json

                ensure_packages(packages, workspace)

    def test_uses_correct_bun_command(self, tmp_path: Path) -> None:
        """Runs bun install with correct arguments."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        bun_path = tmp_path / "bin" / "bun"

        with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
            mock_bun.return_value = bun_path

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                ensure_packages({"react": "18.3.1"}, workspace)

            call_args = mock_run.call_args
            cmd = call_args[0][0]
            kwargs = call_args[1]

            assert cmd[0] == str(bun_path)
            assert "install" in cmd
            assert kwargs["cwd"] == workspace


class TestSystemPackages:
    """Tests for SYSTEM_PACKAGES constant."""

    def test_system_packages_exists(self) -> None:
        """SYSTEM_PACKAGES constant is defined."""
        assert isinstance(SYSTEM_PACKAGES, dict)

    def test_system_packages_includes_esbuild(self) -> None:
        """SYSTEM_PACKAGES includes esbuild."""
        assert "esbuild" in SYSTEM_PACKAGES
        # Version should be a string like "0.27.2"
        assert isinstance(SYSTEM_PACKAGES["esbuild"], str)

    def test_system_packages_includes_typescript(self) -> None:
        """SYSTEM_PACKAGES includes typescript."""
        assert "typescript" in SYSTEM_PACKAGES
        assert isinstance(SYSTEM_PACKAGES["typescript"], str)

    def test_ensure_packages_includes_system_packages(self, tmp_path: Path) -> None:
        """ensure_packages automatically includes SYSTEM_PACKAGES."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        user_packages = {"react": "18.3.1"}

        with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
            mock_bun.return_value = tmp_path / "bun"

            written_packages: dict[str, str] = {}

            def capture_and_create(*args, **kwargs):
                # Read the package.json that was written
                ws = kwargs.get("cwd")
                if ws:
                    pkg_json = Path(ws) / "package.json"
                    if pkg_json.exists():
                        content = json.loads(pkg_json.read_text())
                        written_packages.update(content.get("dependencies", {}))
                return MagicMock(returncode=0)

            with patch("subprocess.run", side_effect=capture_and_create):
                ensure_packages(user_packages, workspace)

        # Should include both user packages and system packages
        assert "react" in written_packages
        for pkg in SYSTEM_PACKAGES:
            assert pkg in written_packages, f"SYSTEM_PACKAGES[{pkg}] missing"


class TestGetBin:
    """Tests for get_bin() function to locate bun-installed binaries."""

    def test_get_bin_returns_path_to_binary(self, tmp_path: Path) -> None:
        """get_bin returns path to binary in node_modules/.bin/."""
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        bin_dir = node_modules / ".bin"
        bin_dir.mkdir()

        result = get_bin(node_modules, "esbuild")

        assert result == node_modules / ".bin" / "esbuild"

    def test_get_bin_works_for_any_tool(self, tmp_path: Path) -> None:
        """get_bin works for any tool name (tsc, esbuild, etc)."""
        node_modules = tmp_path / "node_modules"

        assert get_bin(node_modules, "tsc") == node_modules / ".bin" / "tsc"
        assert get_bin(node_modules, "esbuild") == node_modules / ".bin" / "esbuild"
        assert get_bin(node_modules, "prettier") == node_modules / ".bin" / "prettier"

    @pytest.mark.skipif(sys.platform == "win32", reason="Windows uses .cmd extension")
    def test_get_bin_unix_path(self, tmp_path: Path) -> None:
        """On Unix, get_bin returns path without extension."""
        node_modules = tmp_path / "node_modules"
        result = get_bin(node_modules, "tsc")

        assert result.name == "tsc"
        assert ".cmd" not in str(result)

    def test_finds_cmd_extension_on_windows(self, tmp_path: Path) -> None:
        """get_bin finds .cmd extension when it exists."""
        node_modules = tmp_path / "node_modules"
        bin_dir = node_modules / ".bin"
        bin_dir.mkdir(parents=True)
        # Create only the .cmd version (simulating Windows npm install)
        (bin_dir / "esbuild.cmd").touch()

        result = get_bin(node_modules, "esbuild")

        assert result == bin_dir / "esbuild.cmd"

    def test_finds_exe_extension(self, tmp_path: Path) -> None:
        """get_bin finds .exe extension when it exists."""
        node_modules = tmp_path / "node_modules"
        bin_dir = node_modules / ".bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "tsc.exe").touch()

        result = get_bin(node_modules, "tsc")

        assert result == bin_dir / "tsc.exe"

    def test_prefers_no_extension_when_exists(self, tmp_path: Path) -> None:
        """get_bin prefers bare name when it exists (Unix behavior)."""
        node_modules = tmp_path / "node_modules"
        bin_dir = node_modules / ".bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "esbuild").touch()
        (bin_dir / "esbuild.cmd").touch()

        result = get_bin(node_modules, "esbuild")

        assert result == bin_dir / "esbuild"

    def test_returns_bare_name_when_nothing_exists(self, tmp_path: Path) -> None:
        """get_bin falls back to bare name when no extension exists."""
        node_modules = tmp_path / "node_modules"
        bin_dir = node_modules / ".bin"
        bin_dir.mkdir(parents=True)
        # Nothing exists

        result = get_bin(node_modules, "missing")

        assert result == bin_dir / "missing"
