"""Package command for Trellis CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import click

from trellis.app import AppLoader, resolve_app_root, set_apploader
from trellis.app.configvars import cli_context, get_config_vars
from trellis.cli import CliContext, pass_cli_context, trellis
from trellis.cli.options import configvar_options
from trellis.packaging.pyinstaller import (
    PackagePlatformError,
    build_desktop_app_bundle,
)
from trellis.platforms.common.base import PlatformType

_cli_config_vars = [v for v in get_config_vars() if not v.hidden]


@trellis.command(name="package")
@click.option(
    "--dest",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for the packaged app bundle (default: {app_root}/package)",
)
@pass_cli_context
@configvar_options(_cli_config_vars)
def package_app(ctx: CliContext, /, dest: Path | None = None, **cli_kwargs: Any) -> None:
    """Build a desktop app bundle with PyInstaller."""
    if "platform" in cli_kwargs:
        cli_kwargs["platform"] = PlatformType(cli_kwargs["platform"])

    try:
        resolved_path = resolve_app_root(ctx.app_root)
    except FileNotFoundError as e:
        raise click.UsageError(str(e)) from None

    with cli_context(cli_kwargs):
        apploader = AppLoader(resolved_path)
        apploader.load_config()
        set_apploader(apploader)

        config = apploader.config
        assert config is not None
        if config.platform != PlatformType.DESKTOP:
            raise click.UsageError(
                "trellis package currently supports desktop apps only. "
                "Set platform=desktop in trellis_config.py or pass --platform desktop."
            )

        try:
            apploader.load_app()
        except (ValueError, TypeError) as e:
            raise click.UsageError(str(e)) from None

        click.echo(f"Packaging {config.name} for desktop...")
        apploader.bundle()

        try:
            executable_path = build_desktop_app_bundle(
                config=config,
                app_root=resolved_path,
                output_dir=dest,
            )
        except (
            PackagePlatformError,
            RuntimeError,
            ValueError,
            subprocess.CalledProcessError,
        ) as e:
            raise click.UsageError(str(e)) from None

        click.echo(f"Package complete: {executable_path}")
