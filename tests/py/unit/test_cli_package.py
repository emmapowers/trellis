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


def test_package_overrides_platform_to_desktop(
    write_app: WriteApp,
    reset_apploader: None,
) -> None:
    app_root = write_app(name="server-app", module="main", platform="SERVER")
    expected_path = app_root / "package" / "server-app"
    runner = CliRunner()

    with (
        patch.object(AppLoader, "bundle"),
        patch(
            "trellis.cli.package.build_desktop_app_bundle",
            return_value=(expected_path, ["fake.app"]),
        ) as mock_build,
    ):
        result = runner.invoke(trellis, ["--app-root", str(app_root), "package"])

    assert result.exit_code == 0, result.output
    called_config = mock_build.call_args.kwargs["config"]
    assert called_config.platform.value == "desktop"


def test_package_builds_bundle_and_invokes_tauri(
    write_app: WriteApp,
    reset_apploader: None,
) -> None:
    app_root = write_app(name="desktop-app", module="main", platform="DESKTOP")
    expected_path = app_root / "package" / "desktop-app"
    runner = CliRunner()

    with (
        patch.object(AppLoader, "bundle") as mock_bundle,
        patch(
            "trellis.cli.package.build_desktop_app_bundle",
            return_value=(expected_path, ["fake.app"]),
        ) as mock_build,
    ):
        result = runner.invoke(trellis, ["--app-root", str(app_root), "package"])

    assert result.exit_code == 0, result.output
    assert "desktop-app" in result.output
    mock_bundle.assert_called_once_with()
    mock_build.assert_called_once()


def test_package_rejects_bundles_with_installer(write_app: WriteApp) -> None:
    app_root = write_app(name="desktop-app", module="main", platform="DESKTOP")
    runner = CliRunner()

    result = runner.invoke(
        trellis,
        ["--app-root", str(app_root), "package", "--bundles", "nsis", "--installer"],
    )

    assert result.exit_code != 0
    assert "cannot be used together" in result.output.lower()


def test_package_passes_bundles_to_build(
    write_app: WriteApp,
    reset_apploader: None,
) -> None:
    app_root = write_app(name="desktop-app", module="main", platform="DESKTOP")
    expected_path = app_root / "package" / "desktop-app"
    runner = CliRunner()

    with (
        patch.object(AppLoader, "bundle"),
        patch(
            "trellis.cli.package.build_desktop_app_bundle",
            return_value=(expected_path, ["fake.app"]),
        ) as mock_build,
    ):
        result = runner.invoke(
            trellis,
            ["--app-root", str(app_root), "package", "--bundles", "nsis,rpm"],
        )

    assert result.exit_code == 0, result.output
    mock_build.assert_called_once()
    assert mock_build.call_args.kwargs["bundles"] == ["nsis", "rpm"]
