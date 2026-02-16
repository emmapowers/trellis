"""Desktop platform implementation using PyTauri."""

from __future__ import annotations

import asyncio
import importlib
import json
import webbrowser
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, assert_never
from urllib.parse import urlparse

from anyio.from_thread import start_blocking_portal
from pydantic import BaseModel
from pytauri import AppHandle, Commands
from pytauri.ipc import Channel, JavaScriptChannelId  # noqa: TC002 - runtime for pytauri
from pytauri.webview import WebviewWindow  # noqa: TC002 - runtime for pytauri
from pytauri_wheel.lib import builder_factory, context_factory
from rich.console import Console

from trellis.app.apploader import get_dist_dir
from trellis.bundler import (
    BuildConfig,
    BundleBuildStep,
    IconAssetStep,
    IndexHtmlRenderStep,
    PackageInstallStep,
    RegistryGenerationStep,
    StaticFileCopyStep,
)
from trellis.desktop.dialogs import _clear_dialog_runtime, _set_dialog_runtime
from trellis.platforms.common.base import Platform
from trellis.platforms.common.handler_registry import get_global_registry
from trellis.platforms.desktop.e2e import (
    DesktopE2EConfig,
    DesktopE2EScenario,
    build_probe_script,
    load_desktop_e2e_config_from_env,
)
from trellis.platforms.desktop.handler import PyTauriMessageHandler
from trellis.utils.hot_reload import get_or_create_hot_reload

if TYPE_CHECKING:
    from trellis.app.config import Config
    from trellis.core.components.base import Component
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper

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


def _build_tauri_config_override(
    *, dist_path: str, window_title: str, window_width: int, window_height: int
) -> dict[str, Any]:
    """Build runtime Tauri config overrides for desktop window and frontend assets."""
    return {
        "build": {"frontendDist": dist_path},
        "app": {
            "windows": [{"title": window_title, "width": window_width, "height": window_height}]
        },
    }


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


class OpenExternalRequest(BaseModel):
    """Request to open a URL in the system default browser."""

    url: str


class DesktopPlatform(Platform):
    """Desktop platform using PyTauri.

    Provides a native desktop application using the system webview.
    Uses channel-based communication with the same message protocol
    as the WebSocket server platform.
    """

    _root_component: Component | None
    _app_wrapper: AppWrapper | None
    _handler: PyTauriMessageHandler | None
    _handler_task: asyncio.Task[None] | None
    _batch_delay: float
    _e2e_config: DesktopE2EConfig | None
    _e2e_result_event: asyncio.Event
    _e2e_connected_event: asyncio.Event
    _e2e_finished: bool
    _e2e_external_url: str | None
    _e2e_probe_task: asyncio.Task[None] | None
    _e2e_watch_task: asyncio.Task[None] | None

    def __init__(self) -> None:
        self._root_component = None
        self._app_wrapper = None
        self._handler = None
        self._handler_task = None
        self._batch_delay = 1.0 / 30
        self._e2e_config = load_desktop_e2e_config_from_env()
        self._e2e_result_event = asyncio.Event()
        self._e2e_connected_event = asyncio.Event()
        self._e2e_finished = False
        self._e2e_external_url = None
        self._e2e_probe_task = None
        self._e2e_watch_task = None

    @property
    def name(self) -> str:
        return "desktop"

    def get_build_config(self, config: Config) -> BuildConfig:
        """Get build configuration for this platform.

        Args:
            config: Application configuration

        Returns:
            BuildConfig with entry point and build steps
        """
        entry_point = Path(__file__).parent / "client" / "src" / "main.tsx"
        template_path = Path(__file__).parent / "client" / "src" / "index.html.j2"
        return BuildConfig(
            entry_point=entry_point,
            steps=[
                PackageInstallStep(),
                RegistryGenerationStep(),
                BundleBuildStep(output_name="bundle"),
                StaticFileCopyStep(),
                IconAssetStep(icon_path=config.icon),
                IndexHtmlRenderStep(template_path, {"title": config.title}),
            ],
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

            if self._e2e_config is not None:
                self._e2e_connected_event.set()
                self._start_e2e_probe(webview_window, app_handle)
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

        @commands.command()
        async def trellis_open_external(body: OpenExternalRequest) -> None:
            """Open a URL in the user's default browser."""
            parsed = urlparse(body.url)
            allowed_schemes = {"http", "https", "mailto", "tel"}
            if parsed.scheme not in allowed_schemes:
                raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
            if parsed.scheme in {"http", "https"} and not parsed.netloc:
                raise ValueError("External URL must include a host")
            if self._e2e_config is not None:
                self._e2e_external_url = body.url
                self._e2e_result_event.set()
                return
            webbrowser.open(body.url)

        return commands

    def _start_e2e_probe(self, webview_window: WebviewWindow, app_handle: AppHandle) -> None:
        """Start desktop E2E probe and timeout watcher."""
        e2e_config = self._e2e_config
        if e2e_config is None:
            return

        async def run_probe() -> None:
            await asyncio.sleep(e2e_config.initial_delay_seconds)
            webview_window.run_on_main_thread(
                lambda: webview_window.eval(build_probe_script(e2e_config))
            )

        async def watch_result() -> None:
            try:
                await asyncio.wait_for(
                    self._e2e_result_event.wait(), timeout=e2e_config.timeout_seconds
                )
            except TimeoutError:
                self._finish_e2e(
                    app_handle=app_handle,
                    success=False,
                    reason="timeout",
                    details={
                        "scenario": e2e_config.scenario,
                        "external_url": self._e2e_external_url,
                    },
                )
                return

            match e2e_config.scenario:
                case DesktopE2EScenario.MARKDOWN_EXTERNAL_LINK:
                    expected_urls = {
                        "https://github.com/emmapowers/trellis",
                        "https://github.com/emmapowers/trellis/",
                    }
                    if self._e2e_external_url in expected_urls:
                        self._finish_e2e(
                            app_handle=app_handle,
                            success=True,
                            reason="ok",
                            details={
                                "scenario": e2e_config.scenario,
                                "external_url": self._e2e_external_url,
                            },
                        )
                        return

                    self._finish_e2e(
                        app_handle=app_handle,
                        success=False,
                        reason="unexpected_url",
                        details={
                            "scenario": e2e_config.scenario,
                            "external_url": self._e2e_external_url,
                            "expected_urls": sorted(expected_urls),
                        },
                    )
                    return
                case _:
                    assert_never(e2e_config.scenario)

        self._e2e_probe_task = asyncio.create_task(run_probe())
        self._e2e_watch_task = asyncio.create_task(watch_result())

    async def _watch_e2e_global_timeout(self, app_handle: AppHandle) -> None:
        """Fail fast when desktop E2E flow does not complete."""
        if self._e2e_config is None:
            return

        total_timeout = (
            self._e2e_config.initial_delay_seconds + self._e2e_config.timeout_seconds + 2
        )
        try:
            await asyncio.wait_for(self._e2e_result_event.wait(), timeout=total_timeout)
        except TimeoutError:
            reason = "not_connected" if not self._e2e_connected_event.is_set() else "timeout"
            self._finish_e2e(
                app_handle=app_handle,
                success=False,
                reason=reason,
                details={
                    "scenario": self._e2e_config.scenario,
                    "external_url": self._e2e_external_url,
                },
            )

    def _finish_e2e(
        self,
        *,
        app_handle: AppHandle,
        success: bool,
        reason: str,
        details: dict[str, Any],
    ) -> None:
        """Emit E2E result line and terminate desktop app."""
        if self._e2e_finished:
            return
        self._e2e_finished = True
        payload = {"success": success, "reason": reason, **details}
        print(f"TRELLIS_DESKTOP_E2E_RESULT={json.dumps(payload, sort_keys=True)}", flush=True)
        exit_code = 0 if success else 1
        app_handle.run_on_main_thread(lambda: app_handle.exit(exit_code))

    async def run(
        self,
        root_component: Callable[[], Element],
        app_wrapper: AppWrapper,
        *,
        window_title: str = "Trellis App",
        window_width: int = 1024,
        window_height: int = 768,
        batch_delay: float = 1.0 / 30,
        hot_reload: bool = True,
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
            hot_reload: Enable hot reload (default True)
        """
        # Store root component and config for handler access
        self._root_component = root_component  # type: ignore[assignment]
        self._app_wrapper = app_wrapper
        self._batch_delay = batch_delay
        self._e2e_result_event = asyncio.Event()
        self._e2e_connected_event = asyncio.Event()
        self._e2e_finished = False
        self._e2e_external_url = None
        self._e2e_probe_task = None
        self._e2e_watch_task = None

        # Create commands with registered handlers
        commands = self._create_commands()

        _print_startup_banner(window_title)

        # Load Tauri configuration with dist path
        config_dir = Path(__file__).parent / "config"
        dist_path = str(get_dist_dir())

        # Override frontendDist and window metadata with runtime app config.
        config_override = _build_tauri_config_override(
            dist_path=dist_path,
            window_title=window_title,
            window_width=window_width,
            window_height=window_height,
        )

        # PyTauri runs its own event loop on main thread (app.run_return).
        # start_blocking_portal creates an asyncio event loop in a background thread,
        # allowing async command handlers to run while PyTauri blocks the main thread.
        # The portal bridges sync PyTauri commands to async Trellis handlers.
        with start_blocking_portal("asyncio") as portal:
            # Start hot reload with the portal's event loop (not the main thread's loop)
            if hot_reload:
                # portal.call runs the function in the portal's async context
                loop = portal.call(asyncio.get_running_loop)
                hr = get_or_create_hot_reload(loop)
                hr.start()

            app = builder_factory().build(
                context=context_factory(config_dir, tauri_config=config_override),
                invoke_handler=commands.generate_handler(portal),
            )
            dialog_plugin: Any = importlib.import_module("pytauri_plugins.dialog")
            app.handle().plugin(dialog_plugin.init())

            if self._e2e_config is not None:
                portal.start_task_soon(self._watch_e2e_global_timeout, app.handle())

            # Run until window is closed
            try:
                exit_code = app.run_return()
                if exit_code != 0:
                    raise RuntimeError(f"Desktop app exited with code {exit_code}")
            finally:
                _clear_dialog_runtime()


__all__ = ["DesktopPlatform"]
