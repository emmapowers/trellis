"""Package command for Trellis CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from trellis.app import AppLoader, resolve_app_root, set_apploader
from trellis.app.configvars import cli_context, get_config_vars
from trellis.cli import CliContext, pass_cli_context, trellis
from trellis.cli.options import configvar_options
from trellis.packaging.tauri import build_desktop_app_bundle
from trellis.platforms.common.base import PlatformType

_console = Console()

_cli_config_vars = [v for v in get_config_vars() if not v.hidden]

_PLATFORM_HELP = {
    "darwin": "Default: .app bundle. With --installer: .dmg disk image.",
    "win32": "Default: portable .exe. With --installer: installer .exe with Start Menu shortcut.",
    "linux": "Default: AppImage. With --installer: .deb package.",
}


@trellis.command(name="package")
@click.option(
    "--dest",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for the packaged app bundle (default: {app_root}/dist)",
)
@click.option(
    "--installer",
    is_flag=True,
    default=False,
    help="Build installer bundle instead of portable. " + _PLATFORM_HELP.get(sys.platform, ""),
)
@click.option(
    "--bundles",
    type=str,
    default=None,
    help="Comma-separated Tauri bundle types (e.g. nsis, rpm). Cannot be combined with --installer.",
)
@pass_cli_context
@configvar_options(_cli_config_vars)
def package_app(
    ctx: CliContext,
    /,
    dest: Path | None = None,
    installer: bool = False,
    bundles: str | None = None,
    **cli_kwargs: Any,
) -> None:
    """Build a desktop app bundle with Tauri."""
    if bundles is not None and installer:
        raise click.UsageError("--bundles and --installer cannot be used together.")

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

        # Packaging always produces a desktop app regardless of the
        # platform set in trellis_config.py.
        config.platform = PlatformType.DESKTOP

        try:
            apploader.load_app()
        except (ValueError, TypeError) as e:
            raise click.UsageError(str(e)) from None

        click.echo(f"Packaging {config.name} for desktop...")
        apploader.bundle()

        try:
            bundle_types = [b.strip() for b in bundles.split(",")] if bundles else None
            output_path = build_desktop_app_bundle(
                config=config,
                app_root=resolved_path,
                output_dir=dest,
                installer=installer,
                bundles=bundle_types,
            )
        except (
            RuntimeError,
            ValueError,
            subprocess.CalledProcessError,
        ) as e:
            raise click.UsageError(str(e)) from None

        _print_package_complete(config.name, output_path)


def _print_package_complete(name: str, output_dir: Path) -> None:
    """Print a summary banner listing the built artifacts."""
    if output_dir.is_dir():
        artifacts = sorted(
            p.name for p in output_dir.iterdir() if p.is_file() or p.suffix == ".app"
        )
    else:
        artifacts = []

    _console.print()
    _console.print("  [bold green]Trellis[/bold green] [dim]package complete[/dim]")
    _console.print()
    _console.print(f"  [bold]>[/bold]  [cyan]App:[/cyan]      {name}")
    _console.print(f"  [bold]>[/bold]  [cyan]Output:[/cyan]   {output_dir}")
    if artifacts:
        _console.print()
        for artifact in artifacts:
            _console.print(f"     [dim]-[/dim]  {artifact}")
    _console.print()
