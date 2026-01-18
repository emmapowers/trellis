"""Unit tests for trellis.bundler.packages module (Bun-based installation)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGeneratePackageJson:
    """Tests for generate_package_json function."""

    def test_creates_valid_json_structure(self) -> None:
        """Returns a valid package.json dict structure."""
        from trellis.bundler.packages import generate_package_json

        packages = {"react": "18.3.1", "react-dom": "18.3.1"}
        result = generate_package_json(packages)

        assert result["name"] == "trellis-client"
        assert result["private"] is True
        assert "dependencies" in result

    def test_includes_all_packages_as_dependencies(self) -> None:
        """All packages appear in dependencies with correct versions."""
        from trellis.bundler.packages import generate_package_json

        packages = {
            "react": "18.3.1",
            "react-dom": "18.3.1",
            "@msgpack/msgpack": "3.0.0",
        }
        result = generate_package_json(packages)

        assert result["dependencies"] == packages

    def test_empty_packages_creates_empty_dependencies(self) -> None:
        """Empty packages dict creates empty dependencies."""
        from trellis.bundler.packages import generate_package_json

        result = generate_package_json({})

        assert result["dependencies"] == {}

    def test_scoped_packages_handled_correctly(self) -> None:
        """Scoped packages like @scope/name are handled."""
        from trellis.bundler.packages import generate_package_json

        packages = {
            "@react-aria/button": "3.10.0",
            "@tauri-apps/api": "2.8.0",
        }
        result = generate_package_json(packages)

        assert result["dependencies"]["@react-aria/button"] == "3.10.0"
        assert result["dependencies"]["@tauri-apps/api"] == "2.8.0"


class TestGetPackagesHash:
    """Tests for get_packages_hash function."""

    def test_same_packages_same_hash(self) -> None:
        """Identical packages produce identical hash."""
        from trellis.bundler.packages import get_packages_hash

        packages = {"react": "18.3.1", "react-dom": "18.3.1"}

        hash1 = get_packages_hash(packages)
        hash2 = get_packages_hash(packages)

        assert hash1 == hash2

    def test_different_packages_different_hash(self) -> None:
        """Different packages produce different hash."""
        from trellis.bundler.packages import get_packages_hash

        hash1 = get_packages_hash({"react": "18.3.1"})
        hash2 = get_packages_hash({"react": "18.3.0"})

        assert hash1 != hash2

    def test_order_independent(self) -> None:
        """Package order doesn't affect hash."""
        from trellis.bundler.packages import get_packages_hash

        # Different insertion order, same content
        packages1 = {"a": "1.0.0", "b": "2.0.0"}
        packages2 = {"b": "2.0.0", "a": "1.0.0"}

        assert get_packages_hash(packages1) == get_packages_hash(packages2)

    def test_returns_hex_string(self) -> None:
        """Returns a valid hex string."""
        from trellis.bundler.packages import get_packages_hash

        result = get_packages_hash({"react": "18.3.1"})

        assert isinstance(result, str)
        # Should be valid hex (no exception)
        int(result, 16)


class TestEnsurePackages:
    """Tests for ensure_packages function using Bun."""

    def test_returns_node_modules_path(self, tmp_path: Path) -> None:
        """Returns path to node_modules directory."""
        from trellis.bundler.packages import ensure_packages

        workspace = tmp_path / "workspace"
        node_modules = workspace / "node_modules"
        node_modules.mkdir(parents=True)

        with patch("trellis.bundler.packages.CACHE_DIR", tmp_path):
            with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
                with patch("subprocess.run") as mock_run:
                    mock_bun.return_value = Path("/fake/bun")
                    mock_run.return_value = MagicMock(returncode=0)

                    # Pre-create the workspace structure
                    with patch(
                        "trellis.bundler.packages.get_packages_hash",
                        return_value="abc123",
                    ):
                        ws = tmp_path / "workspaces" / "abc123"
                        ws.mkdir(parents=True)
                        (ws / "node_modules").mkdir()
                        (ws / "bun.lock").touch()

                        result = ensure_packages({"react": "18.3.1"})

        assert result.name == "node_modules"

    def test_skips_install_if_lockfile_exists(self, tmp_path: Path) -> None:
        """Skips bun install if bun.lock already exists."""
        from trellis.bundler.packages import ensure_packages

        with patch("trellis.bundler.packages.CACHE_DIR", tmp_path):
            with patch("trellis.bundler.packages.get_packages_hash", return_value="cached123"):
                # Pre-create cached workspace with lockfile
                ws = tmp_path / "workspaces" / "cached123"
                ws.mkdir(parents=True)
                (ws / "bun.lock").touch()
                (ws / "node_modules").mkdir()

                with patch("subprocess.run") as mock_run:
                    ensure_packages({"react": "18.3.1"})

                # Should NOT have called subprocess (bun install)
                mock_run.assert_not_called()

    def test_runs_bun_install_if_no_lockfile(self, tmp_path: Path) -> None:
        """Runs bun install if no bun.lock exists."""
        from trellis.bundler.packages import ensure_packages

        with patch("trellis.bundler.packages.CACHE_DIR", tmp_path):
            with patch("trellis.bundler.packages.get_packages_hash", return_value="new123"):
                with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
                    mock_bun.return_value = tmp_path / "bun"

                    with patch("subprocess.run") as mock_run:
                        mock_run.return_value = MagicMock(returncode=0)

                        # Create node_modules that bun install would create
                        ws = tmp_path / "workspaces" / "new123"

                        def create_node_modules(*args, **kwargs):
                            ws.mkdir(parents=True, exist_ok=True)
                            (ws / "node_modules").mkdir(exist_ok=True)
                            (ws / "bun.lock").touch()
                            return MagicMock(returncode=0)

                        mock_run.side_effect = create_node_modules

                        ensure_packages({"react": "18.3.1"})

                # Should have called bun install
                mock_run.assert_called_once()
                call_args = mock_run.call_args
                cmd = call_args[0][0]
                assert "install" in cmd

    def test_writes_package_json_before_install(self, tmp_path: Path) -> None:
        """Writes package.json to workspace before running bun install."""
        from trellis.bundler.packages import SYSTEM_PACKAGES, ensure_packages

        packages = {"react": "18.3.1", "lodash": "4.17.21"}
        expected_packages = {**SYSTEM_PACKAGES, **packages}

        with patch("trellis.bundler.packages.CACHE_DIR", tmp_path):
            with patch("trellis.bundler.packages.get_packages_hash", return_value="write123"):
                with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
                    mock_bun.return_value = tmp_path / "bun"

                    with patch("subprocess.run") as mock_run:
                        ws = tmp_path / "workspaces" / "write123"

                        def create_artifacts(*args, **kwargs):
                            # Verify package.json was written before install
                            pkg_json = ws / "package.json"
                            assert pkg_json.exists(), "package.json should exist before bun install"
                            content = json.loads(pkg_json.read_text())
                            # Should include both user packages and SYSTEM_PACKAGES
                            assert content["dependencies"] == expected_packages
                            (ws / "node_modules").mkdir(exist_ok=True)
                            (ws / "bun.lock").touch()
                            return MagicMock(returncode=0)

                        mock_run.side_effect = create_artifacts

                        ensure_packages(packages)

    def test_uses_correct_bun_command(self, tmp_path: Path) -> None:
        """Runs bun install with correct arguments."""
        from trellis.bundler.packages import ensure_packages

        bun_path = tmp_path / "bin" / "bun"

        with patch("trellis.bundler.packages.CACHE_DIR", tmp_path):
            with patch("trellis.bundler.packages.get_packages_hash", return_value="cmd123"):
                with patch("trellis.bundler.packages.ensure_bun") as mock_bun:
                    mock_bun.return_value = bun_path

                    with patch("subprocess.run") as mock_run:
                        ws = tmp_path / "workspaces" / "cmd123"

                        def create_artifacts(*args, **kwargs):
                            ws.mkdir(parents=True, exist_ok=True)
                            (ws / "node_modules").mkdir(exist_ok=True)
                            (ws / "bun.lock").touch()
                            return MagicMock(returncode=0)

                        mock_run.side_effect = create_artifacts

                        ensure_packages({"react": "18.3.1"})

                call_args = mock_run.call_args
                cmd = call_args[0][0]
                kwargs = call_args[1]

                assert cmd[0] == str(bun_path)
                assert "install" in cmd
                # Should run in workspace directory
                assert kwargs.get("cwd") is not None


class TestSystemPackages:
    """Tests for SYSTEM_PACKAGES constant."""

    def test_system_packages_exists(self) -> None:
        """SYSTEM_PACKAGES constant is defined."""
        from trellis.bundler.packages import SYSTEM_PACKAGES

        assert isinstance(SYSTEM_PACKAGES, dict)

    def test_system_packages_includes_esbuild(self) -> None:
        """SYSTEM_PACKAGES includes esbuild."""
        from trellis.bundler.packages import SYSTEM_PACKAGES

        assert "esbuild" in SYSTEM_PACKAGES
        # Version should be a string like "0.27.2"
        assert isinstance(SYSTEM_PACKAGES["esbuild"], str)

    def test_system_packages_includes_typescript(self) -> None:
        """SYSTEM_PACKAGES includes typescript."""
        from trellis.bundler.packages import SYSTEM_PACKAGES

        assert "typescript" in SYSTEM_PACKAGES
        assert isinstance(SYSTEM_PACKAGES["typescript"], str)

    def test_ensure_packages_includes_system_packages(self, tmp_path: Path) -> None:
        """ensure_packages automatically includes SYSTEM_PACKAGES."""
        from trellis.bundler.packages import SYSTEM_PACKAGES, ensure_packages

        user_packages = {"react": "18.3.1"}

        with patch("trellis.bundler.packages.CACHE_DIR", tmp_path):
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
                    # Create artifacts
                    Path(ws).mkdir(parents=True, exist_ok=True)
                    (Path(ws) / "node_modules").mkdir(exist_ok=True)
                    (Path(ws) / "bun.lock").touch()
                    return MagicMock(returncode=0)

                with patch("subprocess.run", side_effect=capture_and_create):
                    ensure_packages(user_packages)

        # Should include both user packages and system packages
        assert "react" in written_packages
        for pkg in SYSTEM_PACKAGES:
            assert pkg in written_packages, f"SYSTEM_PACKAGES[{pkg}] missing"


class TestGetBin:
    """Tests for get_bin() function to locate bun-installed binaries."""

    def test_get_bin_returns_path_to_binary(self, tmp_path: Path) -> None:
        """get_bin returns path to binary in node_modules/.bin/."""
        from trellis.bundler.packages import get_bin

        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        bin_dir = node_modules / ".bin"
        bin_dir.mkdir()

        result = get_bin(node_modules, "esbuild")

        assert result == node_modules / ".bin" / "esbuild"

    def test_get_bin_works_for_any_tool(self, tmp_path: Path) -> None:
        """get_bin works for any tool name (tsc, esbuild, etc)."""
        from trellis.bundler.packages import get_bin

        node_modules = tmp_path / "node_modules"

        assert get_bin(node_modules, "tsc") == node_modules / ".bin" / "tsc"
        assert get_bin(node_modules, "esbuild") == node_modules / ".bin" / "esbuild"
        assert get_bin(node_modules, "prettier") == node_modules / ".bin" / "prettier"

    @pytest.mark.skipif(sys.platform == "win32", reason="Windows uses .cmd extension")
    def test_get_bin_unix_path(self, tmp_path: Path) -> None:
        """On Unix, get_bin returns path without extension."""
        from trellis.bundler.packages import get_bin

        node_modules = tmp_path / "node_modules"
        result = get_bin(node_modules, "tsc")

        assert result.name == "tsc"
        assert ".cmd" not in str(result)
