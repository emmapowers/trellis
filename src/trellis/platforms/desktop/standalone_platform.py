"""Standalone desktop platform runtime for packaged applications.

Contains the core PyTauri runtime logic shared between dev and packaged
desktop apps. DesktopPlatform inherits from this and adds dev features
(build config, hot reload, startup banner).
"""

from __future__ import annotations

import asyncio
import importlib
import signal
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from anyio.from_thread import start_blocking_portal
from pydantic import BaseModel
from pytauri import AppHandle, Commands, Manager
from pytauri.ipc import Channel, JavaScriptChannelId  # noqa: TC002 - runtime for pytauri
from pytauri.webview import WebviewWindow  # noqa: TC002 - runtime for pytauri
from pytauri_wheel.lib import builder_factory, context_factory

from trellis.desktop.dialogs import _clear_dialog_runtime, _set_dialog_runtime
from trellis.platforms.common.base import Platform
from trellis.platforms.common.handler_registry import get_global_registry
from trellis.platforms.desktop.handler import PyTauriMessageHandler

if TYPE_CHECKING:
    from trellis.app.config import Config
    from trellis.core.components.base import Component
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper


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


class DesktopStandalonePlatform(Platform):
    """Standalone desktop platform runtime for packaged applications.

    Provides the core PyTauri event loop, command registration, and plugin
    loading. Used directly in packaged apps (via sys._pytauri_standalone)
    and as the base class for DesktopPlatform in dev mode.
    """

    _root_component: Component | None
    _app_wrapper: AppWrapper | None
    _handler: PyTauriMessageHandler | None
    _handler_task: asyncio.Task[None] | None
    _batch_delay: float

    def __init__(self) -> None:
        self._root_component = None
        self._app_wrapper = None
        self._handler = None
        self._handler_task = None
        self._batch_delay = 1.0 / 30

    @property
    def name(self) -> str:
        return "desktop"

    def get_build_config(self, config: Config) -> Any:
        raise NotImplementedError(
            "DesktopStandalonePlatform does not support build config. "
            "Use DesktopPlatform for development builds."
        )

    def _create_commands(self) -> Commands:
        """Create PyTauri commands with access to platform state via closure."""
        commands = Commands()

        @commands.command()
        async def trellis_connect(
            body: ConnectRequest, webview_window: WebviewWindow, app_handle: AppHandle
        ) -> str:
            """Establish channel connection with frontend."""
            channel: Channel = body.channel_id.channel_on(webview_window.as_ref_webview())
            _set_dialog_runtime(app_handle)
            self._handler = PyTauriMessageHandler(
                self._root_component,  # type: ignore[arg-type]
                self._app_wrapper,  # type: ignore[arg-type]
                channel,
                batch_delay=self._batch_delay,
            )
            # Register handler for broadcast (e.g., reload messages)
            get_global_registry().register(self._handler)

            def _on_handler_done(task: asyncio.Task[None]) -> None:
                if self._handler is not None:
                    get_global_registry().unregister(self._handler)
                _clear_dialog_runtime()

            self._handler_task = asyncio.create_task(self._handler.run())
            self._handler_task.add_done_callback(_on_handler_done)
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

    def _get_config_override(self, **kwargs: Any) -> dict[str, Any] | None:
        """Return Tauri config overrides. None in standalone (baked-in config)."""
        return None

    async def run(
        self,
        root_component: Callable[[], Element],
        app_wrapper: AppWrapper,
        *,
        window_title: str = "Trellis App",
        window_width: int = 1024,
        window_height: int = 768,
        batch_delay: float = 1.0 / 30,
        hot_reload: bool = False,
        **_kwargs: Any,
    ) -> None:
        """Start PyTauri desktop application.

        Args:
            root_component: The root Trellis component to render
            app_wrapper: Callback to wrap component with TrellisApp
            window_title: Title for the application window
            window_width: Initial window width in pixels
            window_height: Initial window height in pixels
            batch_delay: Time between render frames in seconds (default ~33ms for 30fps)
            hot_reload: Enable hot reload (default False in standalone)
        """
        self._root_component = root_component  # type: ignore[assignment]
        self._app_wrapper = app_wrapper
        self._batch_delay = batch_delay

        commands = self._create_commands()

        config_dir = Path(__file__).parent / "config"
        config_override = self._get_config_override(
            window_title=window_title,
            window_width=window_width,
            window_height=window_height,
        )

        # PyTauri runs its own event loop on main thread (app.run_return).
        # start_blocking_portal creates an asyncio event loop in a background thread,
        # allowing async command handlers to run while PyTauri blocks the main thread.
        # The portal bridges sync PyTauri commands to async Trellis handlers.
        with start_blocking_portal("asyncio") as portal:
            if hot_reload:
                # Lazy import: only needed in dev mode
                from trellis.utils.hot_reload import get_or_create_hot_reload  # noqa: PLC0415

                loop = portal.call(asyncio.get_running_loop)
                hr = get_or_create_hot_reload(loop)
                hr.start()

            app = builder_factory().build(
                context=context_factory(config_dir, tauri_config=config_override),
                invoke_handler=commands.generate_handler(portal),
            )
            # Keep these runtime-only imports local so non-desktop environments do not
            # require desktop plugin modules during normal import/CI workflows.
            dialog_plugin: Any = importlib.import_module("pytauri_plugins.dialog")
            app.handle().plugin(dialog_plugin.init())

            window_state_plugin: Any = importlib.import_module("pytauri_plugins.window_state")
            app.handle().plugin(window_state_plugin.Builder.build())

            opener_plugin: Any = importlib.import_module("pytauri_plugins.opener")
            app.handle().plugin(opener_plugin.init())

            # Replace asyncio's SIGINT handler (which raises KeyboardInterrupt)
            # with one that closes all windows to trigger a clean exit.
            #
            # Why close windows instead of calling handle.exit()?
            # handle.exit() sends a message via the tao event loop proxy, but
            # the signal handler fires inside the run callback (the only time
            # Python has the GIL).  tao's macOS event loop guards against
            # re-entrant processing (in_callback flag), so the exit message
            # sits in the channel unprocessed and run_return never returns.
            # Closing windows dispatches OS-level events that bypass this guard.
            #
            # The callback (_on_run_event) is still needed even though it's a
            # no-op: without it, pytauri uses a Rust-only noop that never
            # acquires the GIL, so Python signals are never delivered.
            handle = app.handle()
            prev_sigint = signal.getsignal(signal.SIGINT)

            def _on_run_event(app_handle: AppHandle, event: object) -> None:
                pass

            def _sigint_handler(signum: int, frame: Any) -> None:
                for window in Manager.webview_windows(handle).values():
                    window.close()

            signal.signal(signal.SIGINT, _sigint_handler)

            try:
                exit_code = app.run_return(_on_run_event)
                if exit_code != 0:
                    raise RuntimeError(f"Desktop app exited with code {exit_code}")
            finally:
                signal.signal(signal.SIGINT, prev_sigint)
                _clear_dialog_runtime()


__all__ = ["ConnectRequest", "DesktopStandalonePlatform", "LogRequest", "SendRequest"]
