"""Unit tests for trellis.packaging.toolchain.pytauri_wheel."""

from __future__ import annotations

import importlib
import site
import subprocess
import sys
import zipfile
from importlib.metadata import EntryPoint
from pathlib import Path
from unittest.mock import patch

import pytest


def _make_entry_point(dist_name: str, value: str = "pytauri_wheel.ext_mod") -> EntryPoint:
    """Create a PyTauri entry point for testing."""
    return EntryPoint(name="ext_mod", value=value, group="pytauri")._for(dist=dist_name)


def _write_test_wheel(path: Path) -> None:
    """Create a minimal wheel archive with a pytauri entry point."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("pytauri_wheel/__init__.py", "")
        zf.writestr("pytauri_wheel/ext_mod.py", "pytauri = object()\n")
        zf.writestr(
            "pytauri_wheel-0.8.0.dist-info/entry_points.txt",
            "[pytauri]\next_mod = pytauri_wheel.ext_mod\n",
        )
        zf.writestr(
            "pytauri_wheel-0.8.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: pytauri-wheel\nVersion: 0.8.0\n",
        )


class TestEnsurePytauriRuntime:
    """Tests for the lazy PyTauri runtime provisioner."""

    def test_returns_immediately_in_standalone_mode(self) -> None:
        with patch.object(sys, "_pytauri_standalone", True, create=True):
            module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")

            with (
                patch.object(module, "_current_ext_mod_entry_points") as mock_entry_points,
                patch.object(module, "_download_wheel") as mock_download,
            ):
                module.ensure_pytauri_runtime()

        mock_entry_points.assert_not_called()
        mock_download.assert_not_called()

    def test_returns_when_runtime_provider_is_already_available(self) -> None:
        module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")

        with (
            patch.object(
                module,
                "_current_ext_mod_entry_points",
                return_value=[_make_entry_point("installed")],
            ),
            patch.object(module, "_download_wheel") as mock_download,
        ):
            module.ensure_pytauri_runtime()

        mock_download.assert_not_called()

    def test_raises_when_multiple_runtime_providers_are_visible(self) -> None:
        module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")

        providers = [
            _make_entry_point("pytauri-wheel"),
            _make_entry_point("custom-provider", value="custom.ext_mod"),
        ]
        with patch.object(module, "_current_ext_mod_entry_points", return_value=providers):
            with pytest.raises(RuntimeError, match="Exactly one `pytauri` runtime provider"):
                module.ensure_pytauri_runtime()

    def test_downloads_exact_matching_wheel_version(self, tmp_path: Path) -> None:
        module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")
        cache_dir = tmp_path / "cache"
        download_dir = cache_dir / "pytauri-wheel" / "downloads"
        download_dir.mkdir(parents=True)
        wheel_path = download_dir / "pytauri_wheel-0.8.0-cp313-cp313-macosx_14_0_arm64.whl"

        def _fake_download(version: str, destination: Path) -> Path:
            assert version == "0.8.0"
            assert destination == download_dir
            _write_test_wheel(wheel_path)
            return wheel_path

        entry_points = [[], [_make_entry_point("pytauri-wheel")]]
        with (
            patch.object(module, "CACHE_DIR", cache_dir),
            patch.object(module, "_current_ext_mod_entry_points", side_effect=entry_points),
            patch.object(module, "_installed_pytauri_version", return_value="0.8.0"),
            patch.object(module, "_download_wheel", side_effect=_fake_download) as mock_download,
            patch.object(site, "addsitedir") as mock_addsitedir,
        ):
            module.ensure_pytauri_runtime()

        mock_download.assert_called_once_with("0.8.0", download_dir)
        mock_addsitedir.assert_called_once_with(
            str(cache_dir / "pytauri-wheel" / "pytauri_wheel-0.8.0-cp313-cp313-macosx_14_0_arm64")
        )

    def test_reuses_existing_extracted_wheel(self, tmp_path: Path) -> None:
        module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")
        cache_dir = tmp_path / "cache"
        wheel_name = "pytauri_wheel-0.8.0-cp313-cp313-macosx_14_0_arm64"
        extract_dir = cache_dir / "pytauri-wheel" / wheel_name
        extract_dir.mkdir(parents=True)
        (extract_dir / "pytauri_wheel").mkdir()

        with (
            patch.object(module, "CACHE_DIR", cache_dir),
            patch.object(
                module,
                "_current_ext_mod_entry_points",
                side_effect=[[], [_make_entry_point("pytauri-wheel")]],
            ),
            patch.object(module, "_installed_pytauri_version", return_value="0.8.0"),
            patch.object(
                module, "_download_wheel", return_value=Path(f"{wheel_name}.whl")
            ) as mock_download,
            patch.object(site, "addsitedir"),
        ):
            module.ensure_pytauri_runtime()

        mock_download.assert_called_once()

    def test_raises_clear_error_when_pip_download_fails(self) -> None:
        module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")

        with (
            patch.object(module, "_current_ext_mod_entry_points", return_value=[]),
            patch.object(module, "_installed_pytauri_version", return_value="0.8.0"),
            patch.object(module, "_python_version_display", return_value="3.14"),
            patch.object(
                module,
                "_download_wheel",
                side_effect=subprocess.CalledProcessError(
                    1,
                    [sys.executable, "-m", "pip", "download"],
                    stderr="No matching distribution found",
                ),
            ),
        ):
            with pytest.raises(RuntimeError, match="Install pytauri-wheel manually"):
                module.ensure_pytauri_runtime()

    def test_download_wheel_uses_pip_download(self, tmp_path: Path) -> None:
        module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()

        def _fake_run(cmd: list[str], **_kwargs: object) -> None:
            dest = Path(cmd[cmd.index("--dest") + 1])
            (dest / "pytauri_wheel-0.8.0-cp313-cp313-macosx_14_0_arm64.whl").write_bytes(b"wheel")

        with patch.object(subprocess, "run", side_effect=_fake_run) as mock_run:
            result = module._download_wheel("0.8.0", download_dir)

        assert result.name == "pytauri_wheel-0.8.0-cp313-cp313-macosx_14_0_arm64.whl"
        cmd = mock_run.call_args[0][0]
        assert cmd[:7] == [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--only-binary=:all:",
            "--no-deps",
            "--dest",
        ]
        assert Path(cmd[7]).is_relative_to(download_dir)
        assert cmd[8] == "pytauri-wheel==0.8.0"

    def test_download_wheel_rejects_sdist_only_results(self, tmp_path: Path) -> None:
        module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        (download_dir / "pytauri_wheel-0.8.0.tar.gz").write_bytes(b"sdist")

        with patch.object(subprocess, "run"):
            with pytest.raises(RuntimeError, match="published binary wheel"):
                module._download_wheel("0.8.0", download_dir)


class TestExtractWheel:
    """Tests for wheel extraction helpers."""

    def test_extracts_wheel_safely(self, tmp_path: Path) -> None:
        module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")
        wheel_path = tmp_path / "pytauri_wheel-0.8.0-cp313-cp313-macosx_14_0_arm64.whl"
        extract_dir = tmp_path / "extract"
        _write_test_wheel(wheel_path)

        result = module._extract_wheel(wheel_path, extract_dir)

        assert result == extract_dir
        assert (extract_dir / "pytauri_wheel" / "__init__.py").exists()
        assert (extract_dir / "pytauri_wheel-0.8.0.dist-info" / "entry_points.txt").exists()

    def test_reuses_existing_extracted_directory(self, tmp_path: Path) -> None:
        module = importlib.import_module("trellis.packaging.toolchain.pytauri_wheel")
        wheel_path = tmp_path / "pytauri_wheel-0.8.0-cp313-cp313-macosx_14_0_arm64.whl"
        extract_dir = tmp_path / "extract"
        extract_dir.mkdir()

        result = module._extract_wheel(wheel_path, extract_dir)

        assert result == extract_dir
