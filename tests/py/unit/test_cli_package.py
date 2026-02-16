"""Tests for the trellis package CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from tests.conftest import WriteApp
from trellis.app.apploader import AppLoader
from trellis.cli import trellis


class TestPackageCommandBasics:
    """Basic command and help behavior."""

    def test_package_command_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(trellis, ["package", "--help"])
        assert result.exit_code == 0

    def test_package_rejects_non_desktop_platform(self, write_app: WriteApp) -> None:
        app_root = write_app(name="server-app", module="main", platform="SERVER")
        runner = CliRunner()
        result = runner.invoke(trellis, ["--app-root", str(app_root), "package"])

        assert result.exit_code != 0
        assert "desktop" in result.output.lower()


class TestPackageCommandExecution:
    """Happy-path packaging behavior."""

    def test_package_builds_bundle_and_invokes_pyinstaller(
        self,
        write_app: WriteApp,
        reset_apploader: None,
    ) -> None:
        app_root = write_app(name="desktop-app", module="main", platform="DESKTOP")
        expected_path = app_root / "dist" / "desktop-app"

        runner = CliRunner()
        with (
            patch.object(AppLoader, "bundle"),
            patch("trellis.cli.package.build_single_file_executable", return_value=expected_path),
        ):
            result = runner.invoke(trellis, ["--app-root", str(app_root), "package"])

        assert result.exit_code == 0, result.output
        assert "desktop-app" in result.output
