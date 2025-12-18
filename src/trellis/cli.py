"""Trellis CLI utilities."""

import click


@click.group()
def trellis() -> None:
    """Trellis CLI utilities."""


@trellis.group()
def bundle() -> None:
    """Bundle management commands."""


@bundle.command()
@click.option("--force", is_flag=True, help="Force rebuild even if sources unchanged")
@click.option(
    "--platform",
    type=click.Choice(["server", "desktop", "browser", "all"]),
    default="all",
    help="Platform to build bundle for",
)
def build(force: bool, platform: str) -> None:
    """Build platform bundles."""
    from trellis.platforms.browser.serve_platform import BrowserServePlatform
    from trellis.platforms.desktop.platform import DesktopPlatform
    from trellis.platforms.server.platform import ServerPlatform

    if platform in ("server", "all"):
        ServerPlatform().bundle(force=force)
    if platform in ("desktop", "all"):
        DesktopPlatform().bundle(force=force)
    if platform in ("browser", "all"):
        BrowserServePlatform().bundle(force=force)
