"""Tests for PyInstaller packaging helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from trellis.app.config import Config
from trellis.platforms.common.base import PlatformType
from trellis.packaging.pyinstaller import (
    PackagePlatformError,
    _write_bootstrap,
    build_single_file_executable,
)


class TestBuildSingleFileExecutable:
    """Tests for build_single_file_executable()."""

    def test_raises_on_non_macos(self, tmp_path: Path) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
        app_root = tmp_path / "app"
        app_root.mkdir()

        with (
            patch("trellis.packaging.pyinstaller.sys.platform", "linux"),
            pytest.raises(PackagePlatformError, match="macOS"),
        ):
            build_single_file_executable(config=config, app_root=app_root, output_dir=None)

    def test_runs_pyinstaller_with_onefile(self, tmp_path: Path) -> None:
        config = Config(name="myapp", module="myapp.main", platform=PlatformType.DESKTOP)
        app_root = tmp_path / "app"
        app_root.mkdir()
        dist_dir = app_root / "dist"
        dist_dir.mkdir()
        expected_output = dist_dir / "myapp"
        expected_output.write_text("binary")

        with (
            patch("trellis.packaging.pyinstaller.sys.platform", "darwin"),
            patch("trellis.packaging.pyinstaller.subprocess.run") as mock_run,
        ):
            output = build_single_file_executable(config=config, app_root=app_root, output_dir=dist_dir)

        cmd = mock_run.call_args[0][0]
        assert "--onefile" in cmd
        assert "--name" in cmd
        assert "myapp" in cmd
        assert "--distpath" in cmd
        assert str(dist_dir) in cmd
        assert "--paths" in cmd
        assert str(app_root) in cmd
        assert "--hidden-import" in cmd
        assert "myapp.main" in cmd
        assert output == expected_output

    def test_uses_derived_icon_when_available(self, tmp_path: Path) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
        app_root = tmp_path / "app"
        app_root.mkdir()
        (app_root / ".dist").mkdir()
        (app_root / ".dist" / "favicon.png").write_bytes(b"png")
        dist_dir = app_root / "dist"
        dist_dir.mkdir()
        (dist_dir / "myapp").write_text("binary")

        with (
            patch("trellis.packaging.pyinstaller.sys.platform", "darwin"),
            patch("trellis.packaging.pyinstaller.subprocess.run") as mock_run,
        ):
            build_single_file_executable(config=config, app_root=app_root, output_dir=dist_dir)

        cmd = mock_run.call_args[0][0]
        assert "--icon" in cmd
        assert str(app_root / ".dist" / "favicon.png") in cmd

    def test_bootstrap_does_not_bundle_on_startup(self, tmp_path: Path) -> None:
        config = Config(name="myapp", module="myapp.main", platform=PlatformType.DESKTOP)
        app_root = tmp_path / "app"
        app_root.mkdir()
        bootstrap_path = tmp_path / "bootstrap.py"

        _write_bootstrap(config, app_root, bootstrap_path)

        source = bootstrap_path.read_text()
        assert "apploader.bundle()" not in source
