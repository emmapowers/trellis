"""Run command for Trellis CLI."""

from __future__ import annotations

import asyncio
from typing import Any

import click

from trellis.app import AppLoader, resolve_app_root, set_apploader
from trellis.app.config import Config
from trellis.app.configvars import cli_context, get_config_vars
from trellis.cli import CliContext, pass_cli_context, trellis
from trellis.cli.options import configvar_options
from trellis.platforms.common.base import PlatformType

_cli_config_vars = [v for v in get_config_vars() if not v.hidden]


def _build_run_kwargs(config: Config) -> dict[str, Any]:
    """Extract platform-specific kwargs from config for platform.run()."""
    kwargs: dict[str, Any] = {
        "host": config.host,
        "port": config.port,
        "batch_delay": config.batch_delay,
        "hot_reload": config.hot_reload,
    }
    if config.platform == PlatformType.DESKTOP:
        kwargs["window_title"] = config.title
        if config.window_size != "maximized":
            parts = config.window_size.split("x")
            kwargs["window_width"] = int(parts[0])
            kwargs["window_height"] = int(parts[1])
    return kwargs


@trellis.command()
@click.option(
    "--server", "platform_shortcut", flag_value="server", help="Shortcut for --platform server"
)
@click.option(
    "--desktop", "platform_shortcut", flag_value="desktop", help="Shortcut for --platform desktop"
)
@click.option(
    "--browser", "platform_shortcut", flag_value="browser", help="Shortcut for --platform browser"
)
@pass_cli_context
@configvar_options(_cli_config_vars)
def run(
    ctx: CliContext,
    /,
    platform_shortcut: str | None = None,
    **cli_kwargs: Any,
) -> None:
    """Run a Trellis application.

    Uses --app-root global option or TRELLIS_APP_ROOT environment variable.
    If neither is specified, searches upward from the current directory.
    """
    if platform_shortcut:
        if "platform" in cli_kwargs:
            raise click.UsageError(f"--{platform_shortcut} cannot be used with --platform")
        cli_kwargs["platform"] = platform_shortcut

    if "platform" in cli_kwargs:
        cli_kwargs["platform"] = PlatformType(cli_kwargs["platform"])

    try:
        resolved_path = resolve_app_root(ctx.app_root)
    except FileNotFoundError as e:
        raise click.UsageError(str(e)) from None

    with cli_context(cli_kwargs):
        apploader = AppLoader(resolved_path)
        apploader.load_config()

        config = apploader.config
        assert config is not None

        try:
            apploader.load_app()
        except (ValueError, TypeError) as e:
            raise click.UsageError(str(e)) from None

        set_apploader(apploader)

        click.echo(f"Running {config.name} on {config.platform.value}...")

        apploader.bundle()

        app = apploader.app
        assert app is not None

        run_kwargs = _build_run_kwargs(config)

        # Adapt App.get_wrapped_top to AppWrapper signature.
        # AppWrapper takes (component, system_theme, theme_mode) but
        # get_wrapped_top already knows its root component via self.top.
        def app_wrapper(_component: Any, system_theme: str, theme_mode: str | None) -> Any:
            return app.get_wrapped_top(system_theme, theme_mode)

        asyncio.run(apploader.platform.run(app.top, app_wrapper, **run_kwargs))
