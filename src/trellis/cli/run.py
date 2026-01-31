"""Run command for Trellis CLI."""

from typing import Any

import click

from trellis.app import App, resolve_app_root
from trellis.app.configvars import cli_context, get_config_vars
from trellis.cli import CliContext, pass_cli_context, trellis
from trellis.cli.options import configvar_options
from trellis.platforms.common.base import PlatformType

# Get all visible (non-hidden) ConfigVars for CLI options
_cli_config_vars = [v for v in get_config_vars() if not v.hidden]


@trellis.command()
@pass_cli_context
@configvar_options(_cli_config_vars)
def run(
    ctx: CliContext,
    /,
    **cli_kwargs: Any,
) -> None:
    """Run a Trellis application.

    Uses --app-root global option or TRELLIS_APP_ROOT environment variable.
    If neither is specified, searches upward from the current directory.
    """
    # Convert platform string to enum if present
    if "platform" in cli_kwargs:
        cli_kwargs["platform"] = PlatformType(cli_kwargs["platform"])

    # Resolve app root from CLI > ENV > auto-detect
    try:
        resolved_path = resolve_app_root(ctx.app_root)
    except FileNotFoundError as e:
        raise click.UsageError(str(e)) from None

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
