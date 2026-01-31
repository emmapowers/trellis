"""Run command for Trellis CLI."""

from pathlib import Path
from typing import Any

import click

from trellis.app import App, find_app_path
from trellis.app.configvars import cli_context, get_config_vars
from trellis.cli import trellis
from trellis.cli.options import configvar_options
from trellis.platforms.common.base import PlatformType

# Get all visible (non-hidden) ConfigVars for CLI options
_cli_config_vars = [v for v in get_config_vars() if not v.hidden]


@trellis.command()
@click.argument("app_path", type=click.Path(exists=True, path_type=Path), required=False)
@configvar_options(_cli_config_vars)
def run(
    app_path: Path | None,
    **cli_kwargs: Any,
) -> None:
    """Run a Trellis application.

    APP_PATH is the path to a trellis.py file or directory containing one.
    If not specified, searches upward from the current directory.
    """
    # Convert platform string to enum if present
    if "platform" in cli_kwargs:
        cli_kwargs["platform"] = PlatformType(cli_kwargs["platform"])

    # Find or validate app path
    if app_path is None:
        try:
            resolved_path = find_app_path()
        except FileNotFoundError as e:
            raise click.UsageError(str(e)) from None
    else:
        resolved_path = app_path if app_path.is_dir() else app_path.parent

    # Load and run with CLI context
    with cli_context(cli_kwargs):
        app = App(resolved_path)
        app.load_config()
        config = app.config
        assert config is not None  # load_config sets this

        click.echo(f"Running {config.name} on {config.platform.value}...")

        # TODO: Actually run the platform
        # For now, just show what would happen
        if config.port:
            click.echo(f"  Port: {config.port}")
        if config.host != "127.0.0.1":
            click.echo(f"  Host: {config.host}")
        if config.debug:
            click.echo(f"  Debug: {config.debug}")
