"""Tests for the trellis package CLI command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from tests.conftest import WriteApp
from trellis.app.apploader import AppLoader
from trellis.cli import trellis


def test_package_command_exists() -> None:
    runner = CliRunner()
    result = runner.invoke(trellis, ["package", "--help"])

    assert result.exit_code == 0
    assert "--dest PATH" in result.output
    assert "--platform [server|desktop|browser]" in result.output


def test_package_rejects_non_desktop_platform(write_app: WriteApp) -> None:
    app_root = write_app(name="server-app", module="main", platform="SERVER")
    runner = CliRunner()

    result = runner.invoke(trellis, ["--app-root", str(app_root), "package"])

    assert result.exit_code != 0
    assert "desktop" in result.output.lower()


def test_package_builds_bundle_and_invokes_pyinstaller(
    write_app: WriteApp,
    reset_apploader: None,
) -> None:
    app_root = write_app(name="desktop-app", module="main", platform="DESKTOP")
    expected_path = app_root / "package" / "desktop-app.app"
    runner = CliRunner()

    with (
        patch.object(AppLoader, "bundle") as mock_bundle,
        patch(
            "trellis.cli.package.build_desktop_app_bundle", return_value=expected_path
        ) as mock_build,
    ):
        result = runner.invoke(trellis, ["--app-root", str(app_root), "package"])

    assert result.exit_code == 0, result.output
    assert "desktop-app" in result.output
    mock_bundle.assert_called_once_with()
    mock_build.assert_called_once()


def test_package_accepts_platform_override_and_bakes_desktop_config(
    write_app: WriteApp,
    reset_apploader: None,
) -> None:
    app_root = write_app(name="override-app", module="main", platform="SERVER")
    expected_path = app_root / "package" / "override-app.app"
    runner = CliRunner()

    with (
        patch.object(AppLoader, "bundle"),
        patch(
            "trellis.cli.package.build_desktop_app_bundle", return_value=expected_path
        ) as mock_build,
    ):
        result = runner.invoke(
            trellis,
            ["--app-root", str(app_root), "package", "--platform", "desktop"],
        )

    assert result.exit_code == 0, result.output
    called_config = mock_build.call_args.kwargs["config"]
    assert called_config.platform.value == "desktop"
