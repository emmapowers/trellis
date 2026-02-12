"""Bundle command for Trellis CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from trellis.app import AppLoader, resolve_app_root, set_apploader
from trellis.app.configvars import cli_context, get_config_vars
from trellis.cli import CliContext, pass_cli_context, trellis
from trellis.cli.options import configvar_options
from trellis.platforms.common.base import PlatformType

_cli_config_vars = [v for v in get_config_vars() if not v.hidden]


@trellis.command()
@click.option(
    "--dest",
    type=click.Path(path_type=Path),
    default=None,
    help="Custom output directory (default: {app_root}/.dist)",
)
@pass_cli_context
@configvar_options(_cli_config_vars)
def bundle(ctx: CliContext, /, dest: Path | None = None, **cli_kwargs: Any) -> None:
    """Build the client bundle for the configured platform."""
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

        # Import the app module to trigger @react decorator registration
        apploader.import_module()

        click.echo(f"Bundling {config.name} for {config.platform.value}...")
        apploader.bundle(dest=dest)
        click.echo("Bundle complete.")
