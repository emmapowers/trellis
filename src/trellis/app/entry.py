"""Unified Trellis application entry point.

The Trellis class provides a single entry point for all platforms.
It handles platform detection, CLI argument parsing, and launches
the appropriate backend.

Usage:
    from trellis import Trellis, async_main

    @async_main
    async def main():
        app = Trellis(top=MyApp)
        await app.serve()

CLI arguments:
    --platform=server|desktop|browser  Select platform explicitly
    --desktop                          Shortcut for --platform=desktop
    --browser                          Shortcut for --platform=browser
    --host=HOST                        Server bind host (server only)
    --port=PORT                        Server bind port (server only)
    --build-bundle                     Force rebuild client bundle
    --no-hot-reload                    Disable hot reload (enabled by default)
    -d/--debug CATEGORIES              Enable debug logging (comma-separated)
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from trellis.app.client_state import ClientState, ThemeMode
from trellis.app.trellis_app import TrellisApp
from trellis.core.components.base import Component
from trellis.core.components.composition import CompositionComponent
from trellis.platforms.common.base import Platform, PlatformArgumentError, PlatformType
from trellis.routing.enums import RoutingMode
from trellis.utils.debug import configure_debug, list_categories, parse_categories
from trellis.utils.log_setup import setup_logging

if TYPE_CHECKING:
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper

# Define which arguments belong to which platform
_SERVER_ARGS = {"host", "port", "static_dir"}
_DESKTOP_ARGS = {"window_title", "window_width", "window_height"}
_BROWSER_ARGS = {"host", "port"}  # Browser CLI mode also serves HTTP
# Watch mode is platform-independent (handled at Trellis level)
_WATCH_PLATFORMS = {PlatformType.SERVER, PlatformType.DESKTOP, PlatformType.BROWSER}


class _TrellisArgs:
    """Tracks configuration arguments and whether they were explicitly set."""

    def __init__(self) -> None:
        self._values: dict[str, Any] = {}
        self._explicit: set[str] = set()

    def set_default(self, key: str, value: Any) -> None:
        """Set a default value (not marked as explicit)."""
        if key not in self._values:
            self._values[key] = value

    def set(self, key: str, value: Any) -> None:
        """Set a value explicitly."""
        self._values[key] = value
        self._explicit.add(key)

    def get(self, key: str) -> Any:
        """Get a value."""
        return self._values.get(key)

    def is_explicit(self, key: str) -> bool:
        """Check if a value was explicitly set."""
        return key in self._explicit

    def to_dict(self) -> dict[str, Any]:
        """Return all values as a dictionary."""
        return dict(self._values)

    def explicit_args_for_platform(self, platform: PlatformType) -> list[str]:
        """Return list of explicit args that belong to a specific platform."""
        if platform == PlatformType.SERVER:
            platform_args = _SERVER_ARGS
        elif platform == PlatformType.DESKTOP:
            platform_args = _DESKTOP_ARGS
        else:  # BROWSER
            platform_args = _BROWSER_ARGS
        return [arg for arg in self._explicit if arg in platform_args]


def _detect_platform() -> PlatformType:
    """Auto-detect the appropriate platform.

    Detection order:
    1. Pyodide environment -> BROWSER
    2. Default -> SERVER
    """
    # Check for Pyodide (browser environment)
    if "pyodide" in sys.modules or hasattr(sys, "pyodide"):
        return PlatformType.BROWSER

    # Default to server
    return PlatformType.SERVER


def _parse_cli_args() -> tuple[PlatformType | None, dict[str, Any]]:
    """Parse CLI arguments for platform selection and configuration.

    Uses parse_known_args() to ignore app-specific arguments.

    Returns:
        Tuple of (platform_type or None, dict of other args)

    Raises:
        PlatformArgumentError: If both --desktop and --platform are provided
    """
    # Set up logging early so all apps get Rich-formatted output
    setup_logging()  # Default level=INFO

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--platform",
        choices=["server", "desktop", "browser"],
        help="Select platform",
    )
    parser.add_argument(
        "--desktop",
        action="store_true",
        help="Shortcut for --platform=desktop",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Shortcut for --platform=browser",
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Server bind host",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Server bind port",
    )
    parser.add_argument(
        "--build-bundle",
        action="store_true",
        help="Force rebuild client bundle",
    )
    parser.add_argument(
        "--no-hot-reload",
        action="store_true",
        help="Disable hot reload (enabled by default)",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch source files and rebuild bundle on changes",
    )
    parser.add_argument(
        "-d",
        "--debug",
        nargs="?",
        const="",  # When -d is passed without value
        default=None,  # When -d is not passed at all
        help="Enable debug logging (comma-separated categories, or 'all')",
    )

    # Ignore unknown args (app may have its own args)
    args, _ = parser.parse_known_args()

    # Check for conflicts between shortcuts and --platform
    shortcuts_used = sum([args.desktop, args.browser])
    if shortcuts_used > 1:
        raise PlatformArgumentError(
            "Cannot specify multiple platform shortcuts. Use only one of --desktop or --browser."
        )
    if shortcuts_used and args.platform:
        raise PlatformArgumentError(
            "Cannot specify both a shortcut (--desktop/--browser) and --platform. Use one or the other."
        )

    # Determine platform
    platform: PlatformType | None = None
    if args.desktop:
        platform = PlatformType.DESKTOP
    elif args.browser:
        platform = PlatformType.BROWSER
    elif args.platform:
        platform = PlatformType(args.platform)

    # Handle debug argument
    if args.debug is not None:
        if args.debug == "":
            # -d with no value: list categories and exit
            print(list_categories())
            sys.exit(0)
        else:
            # -d with categories: configure debug logging
            try:
                categories = parse_categories(args.debug)
                configure_debug(categories)
            except ValueError as e:
                print(f"Error: {e}", file=sys.stderr)
                print(list_categories(), file=sys.stderr)
                sys.exit(1)

    # Collect other args
    other_args: dict[str, Any] = {}
    if args.host is not None:
        other_args["host"] = args.host
    if args.port is not None:
        other_args["port"] = args.port
    if args.build_bundle:
        other_args["build_bundle"] = True
    if args.no_hot_reload:
        other_args["hot_reload"] = False
    if args.watch:
        other_args["watch"] = True

    return platform, other_args


def _is_pyodide() -> bool:
    """Check if we're running inside Pyodide."""
    return "pyodide" in sys.modules or hasattr(sys, "pyodide")


class _WatchThread:
    """Background thread for watching files and rebuilding bundles."""

    def __init__(self, workspace: Path, rebuild: Callable[[], None]) -> None:
        self._workspace = workspace
        self._rebuild = rebuild
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._background_tasks: set[asyncio.Task[None]] = set()

    def start(self) -> None:
        """Start the watch thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the watch thread and wait for it to finish."""
        self._stop_event.set()
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    def _run(self) -> None:
        """Run the watch loop in a new event loop."""
        # Import watch module lazily to avoid loading watchfiles in browser
        from trellis.bundler.watch import watch_and_rebuild  # noqa: PLC0415
        from trellis.platforms.common.handler_registry import get_global_registry  # noqa: PLC0415
        from trellis.platforms.common.messages import ReloadMessage  # noqa: PLC0415

        def on_rebuild() -> None:
            """Broadcast reload message to all connected clients."""
            registry = get_global_registry()
            if len(registry) > 0:
                # Schedule broadcast on the watch thread's event loop
                # This is safe because we're already in the watch thread
                # Task reference stored to prevent garbage collection during execution
                task = asyncio.create_task(registry.broadcast(ReloadMessage()))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.create_task(
                watch_and_rebuild(
                    self._workspace,
                    self._rebuild,
                    on_rebuild=on_rebuild,
                )
            )
            self._loop.run_forever()
        finally:
            self._loop.close()


def _get_platform(platform_type: PlatformType) -> Platform:
    """Get platform instance by type.

    Args:
        platform_type: The type of platform to instantiate

    Returns:
        Platform instance

    Raises:
        ImportError: If platform dependencies not available
        ValueError: If platform type is unknown
    """
    if platform_type == PlatformType.SERVER:
        from trellis.platforms.server import ServerPlatform  # noqa: PLC0415

        return ServerPlatform()
    if platform_type == PlatformType.DESKTOP:
        from trellis.platforms.desktop import DesktopPlatform  # noqa: PLC0415

        return DesktopPlatform()
    if platform_type == PlatformType.BROWSER:
        # Browser platform has two implementations:
        # - BrowserPlatform: Runs inside Pyodide (WebAssembly). Minimal dependencies,
        #   communicates with JS via the trellis_browser_bridge module.
        # - BrowserServePlatform: Runs on CLI side. Serves static files (bundle.js,
        #   wheel, HTML with embedded source) via HTTP for the browser to load.
        if _is_pyodide():
            from trellis.platforms.browser import BrowserPlatform  # noqa: PLC0415

            return BrowserPlatform()
        from trellis.platforms.browser.serve_platform import BrowserServePlatform  # noqa: PLC0415

        return BrowserServePlatform()
    raise ValueError(f"Unknown platform: {platform_type}")


class Trellis:
    """Trellis application - unified entry point for all platforms.

    Usage:
        # Auto-detect platform (server by default)
        app = Trellis(top=MyApp)
        await app.serve()

        # Explicit platform selection
        app = Trellis(top=MyApp, platform="desktop")
        await app.serve()

        # Platform-specific args
        app = Trellis(top=MyApp, host="0.0.0.0", port=8080)
        await app.serve()

    CLI args (when ignore_cli=False):
        --platform=server|desktop|browser
        --desktop (shortcut for --platform=desktop)
        --host=HOST (server only)
        --port=PORT (server only)

    Attributes:
        platform_type: The selected platform type
        top: The root component to render
    """

    platform_type: PlatformType
    top: Callable[[], Element] | None
    _platform: Platform
    _args: _TrellisArgs

    def __init__(
        self,
        top: Callable[[], Element] | None = None,
        *,
        platform: PlatformType | str | None = None,
        ignore_cli: bool = False,
        build_bundle: bool = False,
        watch: bool = False,
        batch_delay: float | None = None,
        hot_reload: bool | None = None,
        routing_mode: RoutingMode | None = None,
        static_files: Path | str | None = None,
        # Server args
        host: str | None = None,
        port: int | None = None,
        static_dir: Path | None = None,
        # Desktop args (future)
        window_title: str | None = None,
        window_width: int | None = None,
        window_height: int | None = None,
    ) -> None:
        """Initialize Trellis application.

        Args:
            top: Root component to render
            platform: Target platform (auto-detect if None)
            ignore_cli: If True, ignore CLI arguments
            build_bundle: Force rebuild client bundle
            watch: Watch source files and rebuild bundle on changes
            batch_delay: Time between render frames in seconds (default ~33ms for 30fps)
            hot_reload: Enable hot reload (default True, disable with --no-hot-reload)
            routing_mode: How the router handles browser history and URLs.
                Desktop forces EMBEDDED. Browser defaults to HASH_URL. Server uses STANDARD.
            static_files: Directory containing static files to copy to dist during build
            host: Server bind host (server only)
            port: Server bind port (server only)
            static_dir: Custom static files directory (server only)
            window_title: Window title (desktop only)
            window_width: Window width (desktop only)
            window_height: Window height (desktop only)

        Raises:
            PlatformArgumentError: If platform-specific arg used with wrong platform
        """
        self.top = top
        self._static_files = Path(static_files) if isinstance(static_files, str) else static_files

        # Build args with defaults
        self._args = _TrellisArgs()

        # Set defaults for all platforms
        self._args.set_default("platform", _detect_platform())
        self._args.set_default("build_bundle", False)
        self._args.set_default("watch", False)
        self._args.set_default("batch_delay", 1.0 / 30)
        self._args.set_default("hot_reload", True)
        self._args.set_default("routing_mode", RoutingMode.HASH_URL)
        self._args.set_default("host", "127.0.0.1")
        self._args.set_default("port", None)
        self._args.set_default("static_dir", None)
        self._args.set_default("window_title", "Trellis App")
        self._args.set_default("window_width", 1024)
        self._args.set_default("window_height", 768)

        # Override with constructor args (if provided)
        if build_bundle:
            self._args.set("build_bundle", build_bundle)
        if watch:
            self._args.set("watch", watch)
        if batch_delay is not None:
            self._args.set("batch_delay", batch_delay)
        if hot_reload is not None:
            self._args.set("hot_reload", hot_reload)
        if routing_mode is not None:
            self._args.set("routing_mode", routing_mode)
        if host is not None:
            self._args.set("host", host)
        if port is not None:
            self._args.set("port", port)
        if static_dir is not None:
            self._args.set("static_dir", static_dir)
        if window_title is not None:
            self._args.set("window_title", window_title)
        if window_width is not None:
            self._args.set("window_width", window_width)
        if window_height is not None:
            self._args.set("window_height", window_height)

        # Parse CLI args (if enabled)
        if not ignore_cli:
            cli_platform, cli_args = _parse_cli_args()
            if cli_platform is not None:
                self._args.set("platform", cli_platform)
            # Override with CLI args (only if not already set by constructor)
            for key, value in cli_args.items():
                if not self._args.is_explicit(key):
                    self._args.set(key, value)

        # Constructor platform arg has highest priority
        if platform is not None:
            if isinstance(platform, str):
                platform = PlatformType(platform)
            self._args.set("platform", platform)

        self.platform_type = self._args.get("platform")

        # Desktop always uses embedded mode (no URL bar)
        if self.platform_type == PlatformType.DESKTOP:
            self._args.set("routing_mode", RoutingMode.EMBEDDED)

        # Validate: check for explicit args from wrong platforms
        self._validate_platform_args()

        # Get platform implementation
        self._platform = _get_platform(self.platform_type)

    def _validate_platform_args(self) -> None:
        """Validate that explicit args match the selected platform.

        Raises:
            PlatformArgumentError: If explicit args from wrong platform
        """
        # Get current platform's allowed args
        current_args = self._args.explicit_args_for_platform(self.platform_type)
        current_args_set = set(current_args)

        # Check each other platform's args
        for check_platform in [PlatformType.SERVER, PlatformType.DESKTOP, PlatformType.BROWSER]:
            if check_platform == self.platform_type:
                continue
            wrong_args = self._args.explicit_args_for_platform(check_platform)
            # Exclude args that also belong to current platform
            wrong_args = [arg for arg in wrong_args if arg not in current_args_set]
            if wrong_args:
                raise PlatformArgumentError(
                    f"{check_platform.value.title()} arguments {wrong_args} "
                    f"cannot be used with platform '{self.platform_type}'"
                )

    @property
    def platform(self) -> Platform:
        """The platform instance."""
        return self._platform

    def _create_app_wrapper(self) -> AppWrapper:
        """Create the app wrapper callback for platforms.

        The wrapper handles:
        - Converting string theme data to enums
        - Creating ClientState with detected theme
        - Wrapping the component with TrellisApp

        Returns:
            A callback that takes (component, system_theme, theme_mode) and
            returns a wrapped Component ready for RenderSession.
        """

        def wrapper(
            component: Component,
            system_theme: str,
            theme_mode: str | None,
        ) -> Component:
            # Convert strings to enums
            sys_theme = ThemeMode.DARK if system_theme == "dark" else ThemeMode.LIGHT
            mode = ThemeMode(theme_mode) if theme_mode else ThemeMode.SYSTEM

            client_state = ClientState(theme_setting=mode, system_theme=sys_theme)

            def wrapped_app() -> None:
                TrellisApp(app=component, client_state=client_state)

            return CompositionComponent(name="TrellisRoot", render_func=wrapped_app)

        # Type assertion for clarity
        result: AppWrapper = wrapper
        return result

    async def serve(self) -> None:
        """Start the application on the selected platform.

        This method runs until the application is shut down.

        Raises:
            ValueError: If no top component specified
        """
        if self.top is None:
            raise ValueError("No top component specified")

        # Build client bundle if needed
        workspace = self._platform.bundle(
            force=self._args.get("build_bundle"),
            app_static_dir=self._static_files,
        )

        # Start watch in background thread if enabled
        # Using a thread keeps rebuilds off the main event loop and works
        # uniformly across all platforms (including desktop which blocks main thread)
        watch_thread: _WatchThread | None = None
        if self._args.get("watch"):

            def rebuild() -> None:
                self._platform.bundle(app_static_dir=self._static_files)

            watch_thread = _WatchThread(workspace, rebuild)
            watch_thread.start()

        try:
            await self._platform.run(
                root_component=self.top,
                app_wrapper=self._create_app_wrapper(),
                **self._args.to_dict(),
            )
        finally:
            if watch_thread is not None:
                watch_thread.stop()


__all__ = ["Trellis"]
