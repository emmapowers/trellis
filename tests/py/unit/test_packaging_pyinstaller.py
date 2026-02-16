"""Tests for PyInstaller packaging helpers."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from trellis.app.config import Config
from trellis.packaging.pyinstaller import (
    PackagePlatformError,
    _write_bootstrap,
    build_desktop_app_bundle,
)
from trellis.platforms.common.base import PlatformType


class TestBuildDesktopAppBundle:
    """Tests for build_desktop_app_bundle()."""

    def test_raises_on_non_macos(self, tmp_path: Path) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
        app_root = tmp_path / "app"
        app_root.mkdir()

        with (
            patch("trellis.packaging.pyinstaller.platform.system", return_value="Linux"),
            pytest.raises(PackagePlatformError, match="macOS"),
        ):
            build_desktop_app_bundle(config=config, app_root=app_root, output_dir=None)

    def test_runs_pyinstaller_with_windowed_bundle(self, tmp_path: Path) -> None:
        config = Config(name="myapp", module="myapp.main", platform=PlatformType.DESKTOP)
        app_root = tmp_path / "app"
        app_root.mkdir()
        dist_dir = app_root / "dist"
        dist_dir.mkdir()
        expected_output = dist_dir / "myapp.app"

        with (
            patch("trellis.packaging.pyinstaller.platform.system", return_value="Darwin"),
            patch(
                "trellis.packaging.pyinstaller.shutil.which", return_value="/usr/bin/pyinstaller"
            ),
            patch("trellis.packaging.pyinstaller.subprocess.run") as mock_run,
        ):
            output = build_desktop_app_bundle(config=config, app_root=app_root, output_dir=dist_dir)

        cmd = mock_run.call_args[0][0]
        assert "--windowed" in cmd
        assert "--onedir" in cmd
        assert "--onefile" not in cmd
        assert "--name" in cmd
        assert "myapp" in cmd
        assert "--distpath" in cmd
        assert str(dist_dir) in cmd
        assert "--paths" in cmd
        assert str(app_root) in cmd
        assert "--add-data" in cmd
        assert f"{app_root / '.dist'}{os.pathsep}.dist" in cmd
        assert "--hidden-import" in cmd
        assert "myapp.main" in cmd
        assert cmd.count("--hidden-import") == 2
        assert "pytauri_wheel.ext_mod" in cmd
        assert "--copy-metadata" in cmd
        assert "pytauri-wheel" in cmd
        assert "--collect-data" in cmd
        assert "trellis.platforms.desktop" in cmd
        assert output == expected_output

    def test_default_output_dir_is_package(self, tmp_path: Path) -> None:
        config = Config(name="myapp", module="myapp.main", platform=PlatformType.DESKTOP)
        app_root = tmp_path / "app"
        app_root.mkdir()

        with (
            patch("trellis.packaging.pyinstaller.platform.system", return_value="Darwin"),
            patch(
                "trellis.packaging.pyinstaller.shutil.which", return_value="/usr/bin/pyinstaller"
            ),
            patch("trellis.packaging.pyinstaller.subprocess.run") as mock_run,
        ):
            output = build_desktop_app_bundle(config=config, app_root=app_root, output_dir=None)

        cmd = mock_run.call_args[0][0]
        assert "--distpath" in cmd
        distpath_value = cmd[cmd.index("--distpath") + 1]
        assert distpath_value == str((app_root / "package").resolve())
        assert output == (app_root / "package" / "myapp.app").resolve()

    def test_uses_derived_icon_when_available(self, tmp_path: Path) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
        config.icon = tmp_path / "project.icns"
        config.icon.write_bytes(b"icns")
        app_root = tmp_path / "app"
        app_root.mkdir()
        (app_root / ".dist").mkdir()
        (app_root / ".dist" / "favicon.icns").write_bytes(b"icns")
        (app_root / ".dist" / "favicon.png").write_bytes(b"png")
        dist_dir = app_root / "dist"
        dist_dir.mkdir()

        with (
            patch("trellis.packaging.pyinstaller.platform.system", return_value="Darwin"),
            patch(
                "trellis.packaging.pyinstaller.shutil.which", return_value="/usr/bin/pyinstaller"
            ),
            patch("trellis.packaging.pyinstaller.subprocess.run") as mock_run,
        ):
            build_desktop_app_bundle(config=config, app_root=app_root, output_dir=dist_dir)

        cmd = mock_run.call_args[0][0]
        assert "--icon" in cmd
        assert str(app_root / ".dist" / "favicon.icns") in cmd

    def test_ignores_stale_derived_icon_when_no_project_icon_configured(
        self, tmp_path: Path
    ) -> None:
        config = Config(name="myapp", module="main", platform=PlatformType.DESKTOP)
        app_root = tmp_path / "app"
        app_root.mkdir()
        (app_root / ".dist").mkdir()
        (app_root / ".dist" / "favicon.icns").write_bytes(b"stale")
        dist_dir = app_root / "dist"
        dist_dir.mkdir()

        with (
            patch("trellis.packaging.pyinstaller.platform.system", return_value="Darwin"),
            patch(
                "trellis.packaging.pyinstaller.shutil.which", return_value="/usr/bin/pyinstaller"
            ),
            patch("trellis.packaging.pyinstaller.subprocess.run") as mock_run,
        ):
            build_desktop_app_bundle(config=config, app_root=app_root, output_dir=dist_dir)

        cmd = mock_run.call_args[0][0]
        assert "--icon" not in cmd

    def test_bootstrap_uses_baked_config_json(self, tmp_path: Path) -> None:
        config = Config(name="myapp", module="myapp.main", platform=PlatformType.DESKTOP)
        bootstrap_path = tmp_path / "bootstrap.py"

        _write_bootstrap(config, bootstrap_path)

        source = bootstrap_path.read_text()
        assert "apploader.bundle()" not in source
        assert "Config.from_json" in source
        assert "AppLoader.from_config" not in source
        assert "app_root = _runtime_app_root()" in source
        assert "apploader.load_config()" not in source
        assert '\\"platform\\": \\"desktop\\"' in source
