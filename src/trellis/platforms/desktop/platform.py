"""Desktop platform implementation using PyTauri."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from anyio.from_thread import start_blocking_portal
from pydantic import BaseModel
from pytauri import Commands
from pytauri.ipc import Channel, JavaScriptChannelId  # noqa: TC002 - runtime for pytauri
from pytauri.webview import WebviewWindow  # noqa: TC002 - runtime for pytauri
from pytauri_wheel.lib import builder_factory, context_factory
from rich.console import Console

from trellis.bundler import CORE_PACKAGES, DESKTOP_PACKAGES, BundleConfig, build_bundle
from trellis.core.platform import Platform
from trellis.platforms.desktop.handler import PyTauriMessageHandler

if TYPE_CHECKING:
    from trellis.core.rendering import ElementNode, IComponent

_console = Console()


def _print_startup_banner(title: str) -> None:
    """Print a colorful startup banner."""
    _console.print()
    _console.print("  [bold green]🌿 Trellis[/bold green] [dim]desktop app[/dim]")
    _console.print()
    _console.print(f"  [bold]➜[/bold]  [cyan]Window:[/cyan]   {title}")
    _console.print()
    _console.print("  [dim]Close window to exit[/dim]")
    _console.print()


# PyTauri command request models


class ConnectRequest(BaseModel):
    """Request to establish channel connection."""

    channel_id: JavaScriptChannelId


class SendRequest(BaseModel):
    """Request to send a message."""

    data: list[int]  # msgpack bytes as list


class LogRequest(BaseModel):
    """Request to log a message."""

    level: str
    message: str


class DesktopPlatform(Platform):
    """Desktop platform using PyTauri.

    Provides a native desktop application using the system webview.
    Uses channel-based communication with the same message protocol
    as the WebSocket server platform.
    """

    _root_component: IComponent | None
    _handler: PyTauriMessageHandler | None
    _handler_task: asyncio.Task[None] | None

    def __init__(self) -> None:
        self._root_component = None
        self._handler = None
        self._handler_task = None

    @property
    def name(self) -> str:
        return "desktop"

    def bundle(
        self,
        force: bool = False,
        extra_packages: dict[str, str] | None = None,
    ) -> None:
        """Build the desktop client bundle if needed.

        Output: platforms/desktop/client/dist/bundle.js + index.html
        """
        platforms_dir = Path(__file__).parent.parent
        common_src_dir = platforms_dir / "common" / "client" / "src"
        client_dir = Path(__file__).parent / "client"
        dist_dir = client_dir / "dist"
        index_path = dist_dir / "index.html"

        config = BundleConfig(
            name="desktop",
            src_dir=client_dir / "src",
            dist_dir=dist_dir,
            packages={**CORE_PACKAGES, **DESKTOP_PACKAGES},
            static_files={"index.html": client_dir / "src" / "index.html"},
            extra_outputs=[index_path],
        )

        build_bundle(config, common_src_dir, force, extra_packages)

    def _create_commands(self) -> Commands:
        """Create PyTauri commands with access to platform state via closure."""
        commands = Commands()

        @commands.command()
        async def trellis_connect(body: ConnectRequest, webview_window: WebviewWindow) -> str:
            """Establish channel connection with frontend."""
            channel: Channel = body.channel_id.channel_on(webview_window.as_ref_webview())
            self._handler = PyTauriMessageHandler(self._root_component, channel)  # type: ignore[arg-type]
            self._handler_task = asyncio.create_task(self._handler.run())
            return "ok"

        @commands.command()
        async def trellis_send(body: SendRequest) -> None:
            """Receive message from frontend."""
            if self._handler is None:
                raise RuntimeError("Not connected - call trellis_connect first")
            self._handler.enqueue(bytes(body.data))

        @commands.command()
        async def trellis_log(body: LogRequest) -> None:
            """Log a message from frontend to stdout."""
            print(f"[JS {body.level}] {body.message}", flush=True)

        return commands

    async def run(
        self,
        root_component: Callable[[], ElementNode],
        *,
        window_title: str = "Trellis App",
        window_width: int = 1024,
        window_height: int = 768,
        **_kwargs: Any,
    ) -> None:
        """Start PyTauri desktop application.

        Args:
            root_component: The root Trellis component to render
            window_title: Title for the application window
            window_width: Initial window width in pixels
            window_height: Initial window height in pixels
        """
        # Store root component for handler access
        self._root_component = root_component  # type: ignore[assignment]

        # Create commands with registered handlers
        commands = self._create_commands()

        _print_startup_banner(window_title)

        # Load Tauri configuration
        config_dir = Path(__file__).parent / "config"

        # PyTauri runs its own event loop on main thread (app.run_return).
        # start_blocking_portal creates an asyncio event loop in a background thread,
        # allowing async command handlers to run while PyTauri blocks the main thread.
        # The portal bridges sync PyTauri commands to async Trellis handlers.
        with start_blocking_portal("asyncio") as portal:
            app = builder_factory().build(
                context=context_factory(config_dir),
                invoke_handler=commands.generate_handler(portal),
            )

            # Run until window is closed
            exit_code = app.run_return()
            if exit_code != 0:
                raise RuntimeError(f"Desktop app exited with code {exit_code}")


__all__ = ["DesktopPlatform"]
