"""Trellis CLI utilities."""

import asyncio
from pathlib import Path

import click


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
    from collections.abc import Callable  # noqa: PLC0415
    from typing import Any  # noqa: PLC0415

    from trellis.platforms.common.base import Platform  # noqa: PLC0415

    # Rebuild callback type - returns Path but callers ignore it
    RebuildCallback = Callable[[], Any]

    # Helper to create rebuild callbacks with proper closure
    def make_rebuild(
        plat: Platform, d: Path | None, lib: bool, entry: Path | None = None
    ) -> RebuildCallback:
        """Create a typed rebuild callback."""
        if entry is not None:
            # Browser platform with python entry point - use Any to allow extra param
            browser_plat: Any = plat
            return lambda: browser_plat.bundle(dest=d, library=lib, python_entry_point=entry)
        return lambda: plat.bundle(dest=d, library=lib)

    # Collect platforms to build: (name, workspace, rebuild_callback)
    platforms: list[tuple[str, Path, RebuildCallback]] = []

    if platform in ("server", "all"):
        from trellis.platforms.server.platform import ServerPlatform  # noqa: PLC0415

        server = ServerPlatform()
        workspace = server.bundle(force=force, dest=dest, library=library)
        platforms.append(("server", workspace, make_rebuild(server, dest, library)))

    if platform in ("desktop", "all"):
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        desktop = DesktopPlatform()
        workspace = desktop.bundle(force=force, dest=dest, library=library)
        platforms.append(("desktop", workspace, make_rebuild(desktop, dest, library)))

    if platform in ("browser", "all"):
        from trellis.platforms.browser.serve_platform import (  # noqa: PLC0415
            BrowserServePlatform,
            MissingEntryPointError,
        )

        browser = BrowserServePlatform()
        try:
            workspace = browser.bundle(
                force=force, dest=dest, library=library, python_entry_point=app
            )
        except MissingEntryPointError:
            raise click.UsageError(
                "Browser app mode requires a Python entry point.\n"
                "Use --app <path> to specify your app, or --library for library mode."
            ) from None
        platforms.append(("browser", workspace, make_rebuild(browser, dest, library, app)))

    # Start watch mode if enabled
    if watch:
        from trellis.bundler.watch import watch_and_rebuild  # noqa: PLC0415

        async def watch_all() -> None:
            """Watch all platforms concurrently."""
            tasks = []
            for name, ws, rebuild in platforms:
                click.echo(f"Watching {name} bundle for changes...")
                tasks.append(asyncio.create_task(watch_and_rebuild(ws, rebuild)))
            if tasks:
                await asyncio.gather(*tasks)

        try:
            asyncio.run(watch_all())
        except KeyboardInterrupt:
            click.echo("\nWatch mode stopped.")
