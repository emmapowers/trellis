"""Trellis CLI utilities."""

import asyncio
from pathlib import Path

import click

from trellis.platforms.common.base import WatchConfig


@click.group()
def trellis() -> None:
    """Trellis CLI utilities."""


@trellis.group()
def bundle() -> None:
    """Bundle management commands."""


@bundle.command()
@click.option("--force", is_flag=True, help="Force rebuild even if sources unchanged")
@click.option("--watch", is_flag=True, help="Watch source files and rebuild on changes")
@click.option(
    "--platform",
    type=click.Choice(["server", "desktop", "browser", "all"]),
    default="all",
    help="Platform to build bundle for",
)
@click.option(
    "--dest",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for build artifacts (default: cache directory)",
)
@click.option(
    "--library",
    is_flag=True,
    help="Build as library with exports (vs app that renders to DOM)",
)
@click.option(
    "--app",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Python app entry point for browser platform (embeds source in bundle)",
)
def build(
    force: bool, watch: bool, platform: str, dest: Path | None, library: bool, app: Path | None
) -> None:
    """Build platform bundles."""
    # Collect platforms to build
    platforms: list[tuple[str, WatchConfig | None]] = []

    if platform in ("server", "all"):
        from trellis.platforms.server.platform import ServerPlatform  # noqa: PLC0415

        server = ServerPlatform()
        server.bundle(force=force, dest=dest, library=library)
        platforms.append(("server", server.get_watch_config()))

    if platform in ("desktop", "all"):
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        desktop = DesktopPlatform()
        desktop.bundle(force=force, dest=dest, library=library)
        platforms.append(("desktop", desktop.get_watch_config()))

    if platform in ("browser", "all"):
        from trellis.platforms.browser.serve_platform import BrowserServePlatform  # noqa: PLC0415

        browser = BrowserServePlatform()
        browser.bundle(force=force, dest=dest, library=library, python_entry_point=app)
        platforms.append(("browser", browser.get_watch_config()))

    # Start watch mode if enabled
    if watch:
        from trellis.bundler.watch import watch_and_rebuild  # noqa: PLC0415

        async def watch_all() -> None:
            """Watch all platforms concurrently."""
            tasks = []
            for name, config in platforms:
                if config is not None:
                    click.echo(f"Watching {name} bundle for changes...")
                    tasks.append(
                        asyncio.create_task(
                            watch_and_rebuild(
                                config.registry,
                                config.entry_point,
                                config.workspace,
                                config.steps,
                            )
                        )
                    )
            if tasks:
                await asyncio.gather(*tasks)

        try:
            asyncio.run(watch_all())
        except KeyboardInterrupt:
            click.echo("\nWatch mode stopped.")
