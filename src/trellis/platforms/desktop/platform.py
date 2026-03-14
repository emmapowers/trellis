"""Desktop platform implementation for both dev and packaged runtimes."""

from __future__ import annotations

import asyncio
import importlib
import signal
import sys
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from anyio.from_thread import start_blocking_portal
from pydantic import create_model
from rich.console import Console

from trellis.app.apploader import get_dist_dir
from trellis.desktop.dialogs import _clear_dialog_runtime, _set_dialog_runtime
from trellis.platforms.common.base import Platform
from trellis.platforms.common.handler_registry import get_global_registry
from trellis.platforms.desktop.handler import PyTauriMessageHandler

if TYPE_CHECKING:
    from trellis.app.config import Config
    from trellis.bundler import BuildConfig
    from trellis.core.components.base import Component
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper

_console = Console()


def _print_startup_banner(title: str) -> None:
    """Print a colorful startup banner."""
    _console.print()
    _console.print("  [bold green]Trellis[/bold green] [dim]desktop app[/dim]")
    _console.print()
    _console.print(f"  [bold]>[/bold]  [cyan]Window:[/cyan]   {title}")
    _console.print()
    _console.print("  [dim]Press Ctrl+C or close window to exit[/dim]")
    _console.print()


def _build_tauri_config_override(
    *, dist_path: str, window_title: str, window_width: int, window_height: int
) -> dict[str, Any]:
    """Build runtime Tauri config overrides for desktop window and frontend assets."""
    return {
        "build": {"frontendDist": dist_path},
        "app": {
            "windows": [
                {
                    "title": window_title,
                    "width": window_width,
                    "height": window_height,
                    "visible": False,
                }
            ]
        },
    }


class DesktopPlatform(Platform):
    """Desktop platform for both development and packaged applications."""

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

    @property
    def is_standalone(self) -> bool:
        """Whether this runtime is running inside a packaged standalone app."""
        return getattr(sys, "_pytauri_standalone", False)

    def get_build_config(self, config: Config) -> BuildConfig:
        """Get build configuration for this platform.

        Args:
            config: Application configuration

        Returns:
            BuildConfig with entry point and build steps
        """
        if self.is_standalone:
            raise NotImplementedError(
                "DesktopPlatform build config is unavailable in standalone mode."
            )

        # Bundler imports are local to this method so importing DesktopPlatform
        # does not pull in the entire bundler module tree.
        from trellis.bundler import (  # noqa: PLC0415
            BuildConfig,
            BundleBuildStep,
            IconAssetStep,
            IndexHtmlRenderStep,
            PackageInstallStep,
            RegistryGenerationStep,
            StaticFileCopyStep,
        )

        entry_point = Path(__file__).parent / "client" / "src" / "main.tsx"
        template_path = Path(__file__).parent / "client" / "src" / "index.html.j2"
        return BuildConfig(
            entry_point=entry_point,
            steps=[
                PackageInstallStep(),
                RegistryGenerationStep(),
                BundleBuildStep(output_name="bundle"),
                StaticFileCopyStep(),
                IconAssetStep(icon_path=config.icon, include_icns=sys.platform == "darwin"),
                IndexHtmlRenderStep(template_path, {"title": config.title}),
            ],
        )

    def _get_config_override(self, **kwargs: Any) -> dict[str, Any] | None:
        """Return Tauri config overrides for dev mode (frontendDist + window metadata)."""
        if self.is_standalone:
            return None

        dist_dir = get_dist_dir()
        if sys.platform == "win32":
            # Tauri misinterprets absolute Windows paths (C:/...) as URLs.
            # Create a junction next to the config dir so we can use a relative path.
            config_dir = Path(__file__).parent / "config"
            dist_link = config_dir / "dist"
            if not dist_link.exists():
                import _winapi  # noqa: PLC0415

                _winapi.CreateJunction(str(dist_dir.resolve()), str(dist_link))
            dist_path = "./dist"
        else:
            dist_path = str(dist_dir)
        return _build_tauri_config_override(
            dist_path=dist_path,
            window_title=kwargs.get("window_title", "Trellis App"),
            window_width=kwargs.get("window_width", 1024),
            window_height=kwargs.get("window_height", 768),
        )

    def _load_pytauri_runtime(self) -> SimpleNamespace:
        """Load PyTauri runtime objects, provisioning the dev wheel when needed."""
        if not self.is_standalone:
            from trellis.toolchain.pytauri_wheel import ensure_pytauri_runtime  # noqa: PLC0415

            ensure_pytauri_runtime()

        from pytauri import (  # noqa: PLC0415
            AppHandle,
            Commands,
            Manager,
            builder_factory,
            context_factory,
        )
        from pytauri.ipc import Channel, JavaScriptChannelId  # noqa: PLC0415
        from pytauri.webview import WebviewWindow  # noqa: PLC0415

        return SimpleNamespace(
            AppHandle=AppHandle,
            Channel=Channel,
            Commands=Commands,
            JavaScriptChannelId=JavaScriptChannelId,
            Manager=Manager,
            WebviewWindow=WebviewWindow,
            builder_factory=builder_factory,
            context_factory=context_factory,
        )

    def _create_commands(self, runtime: SimpleNamespace) -> Any:
        """Create PyTauri commands with access to platform state via closure."""
        Commands = runtime.Commands
        ConnectRequest = create_model(
            "ConnectRequest",
            channel_id=(runtime.JavaScriptChannelId, ...),
        )
        SendRequest = create_model("SendRequest", data=(list[int], ...))
        LogRequest = create_model(
            "LogRequest",
            level=(str, ...),
            message=(str, ...),
        )

        commands = Commands()

        async def trellis_connect(body: Any, webview_window: Any, app_handle: Any) -> str:
            channel = body.channel_id.channel_on(webview_window.as_ref_webview())
            _set_dialog_runtime(app_handle)
            handler = PyTauriMessageHandler(
                self._root_component,  # type: ignore[arg-type]
                self._app_wrapper,  # type: ignore[arg-type]
                channel,
                batch_delay=self._batch_delay,
            )
            self._handler = handler
            get_global_registry().register(handler)

            def _on_handler_done(task: asyncio.Task[None]) -> None:
                get_global_registry().unregister(handler)
                if self._handler is handler:
                    self._handler = None
                    _clear_dialog_runtime()

            self._handler_task = asyncio.create_task(handler.run())
            self._handler_task.add_done_callback(_on_handler_done)
            return "ok"

        async def trellis_send(body: Any) -> None:
            if self._handler is None:
                raise RuntimeError("Not connected - call trellis_connect first")
            self._handler.enqueue(bytes(body.data))

        async def trellis_log(body: Any) -> None:
            print(f"[JS {body.level}] {body.message}", flush=True)

        trellis_connect.__annotations__ = {
            "body": ConnectRequest,
            "webview_window": runtime.WebviewWindow,
            "app_handle": runtime.AppHandle,
            "return": str,
        }
        trellis_send.__annotations__ = {"body": SendRequest, "return": type(None)}
        trellis_log.__annotations__ = {"body": LogRequest, "return": type(None)}

        commands.set_command("trellis_connect", trellis_connect)
        commands.set_command("trellis_send", trellis_send)
        commands.set_command("trellis_log", trellis_log)

        return commands

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
        """Start the desktop application in either dev or standalone mode."""
        if not self.is_standalone:
            _print_startup_banner(window_title)

        self._root_component = root_component  # type: ignore[assignment]
        self._app_wrapper = app_wrapper
        self._batch_delay = batch_delay

        runtime = self._load_pytauri_runtime()
        commands = self._create_commands(runtime)

        config_dir = Path(__file__).parent / "config"
        config_override = self._get_config_override(
            window_title=window_title,
            window_width=window_width,
            window_height=window_height,
        )

        with start_blocking_portal("asyncio") as portal:
            if hot_reload and not self.is_standalone:
                from trellis.utils.hot_reload import get_or_create_hot_reload  # noqa: PLC0415

                loop = portal.call(asyncio.get_running_loop)
                hr = get_or_create_hot_reload(loop)
                hr.start()

            app = runtime.builder_factory().build(
                context=runtime.context_factory(config_dir, tauri_config=config_override),
                invoke_handler=commands.generate_handler(portal),
            )
            dialog_plugin: Any = importlib.import_module("pytauri_plugins.dialog")
            app.handle().plugin(dialog_plugin.init())

            window_state_plugin: Any = importlib.import_module("pytauri_plugins.window_state")
            app.handle().plugin(window_state_plugin.Builder.build())

            opener_plugin: Any = importlib.import_module("pytauri_plugins.opener")
            app.handle().plugin(opener_plugin.init())

            handle = app.handle()
            prev_sigint = signal.getsignal(signal.SIGINT)

            def _on_run_event(app_handle: Any, event: object) -> None:
                pass

            def _sigint_handler(signum: int, frame: Any) -> None:
                for window in runtime.Manager.webview_windows(handle).values():
                    window.close()

            signal.signal(signal.SIGINT, _sigint_handler)

            try:
                exit_code = app.run_return(_on_run_event)
                if exit_code != 0:
                    raise RuntimeError(f"Desktop app exited with code {exit_code}")
            finally:
                signal.signal(signal.SIGINT, prev_sigint)
                _clear_dialog_runtime()


__all__ = ["DesktopPlatform"]
