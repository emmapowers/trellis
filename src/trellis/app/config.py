"""Configuration dataclass for Trellis applications."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from trellis.app.configvars import (
    ConfigVar,
    validate_batch_delay,
    validate_debug_categories,
    validate_port_or_none,
    validate_window_size,
)
from trellis.platforms.common.base import PlatformType
from trellis.routing.enums import RoutingMode

# ============================================================================
# ConfigVar Definitions
# ============================================================================

# General settings
_PLATFORM = ConfigVar(
    "platform",
    default=PlatformType.SERVER,
    help="Target platform (server, desktop, browser)",
)
_FORCE_BUILD = ConfigVar(
    "force_build",
    default=False,
    help="Force rebuild of client bundle even if sources unchanged",
)
_WATCH = ConfigVar(
    "watch",
    default=False,
    is_flag=True,
    short_name="w",
    help="Watch for file changes and reload",
)
_BATCH_DELAY = ConfigVar(
    "batch_delay",
    default=1 / 30,
    validator=validate_batch_delay,
    help="Delay in seconds for batching render updates",
)
_HOT_RELOAD = ConfigVar(
    "hot_reload",
    default=True,
    help="Enable/disable hot reload during development",
)
_ROUTING_MODE: ConfigVar[RoutingMode | None] = ConfigVar(
    "routing_mode",
    default=None,
    type_hint=RoutingMode,
    help="URL routing strategy (standard, hash_url, embedded)",
)
_DEBUG = ConfigVar(
    "debug",
    default="",
    validator=validate_debug_categories,
    short_name="d",
    help="Debug categories (comma-separated: render,state,all)",
)
_ASSETS_DIR: ConfigVar[Path | None] = ConfigVar(
    "assets_dir",
    default=Path("./assets/"),
    type_hint=Path,
    help="Directory containing static assets for bundling",
)

# Server settings (category="server" -> TRELLIS_SERVER_*)
_HOST = ConfigVar(
    "host",
    default="127.0.0.1",
    category="server",
    help="Server host to bind to",
)
_PORT: ConfigVar[int | None] = ConfigVar(
    "port",
    default=None,
    category="server",
    type_hint=int,
    validator=validate_port_or_none,
    short_name="p",
    help="Server port to bind to",
)


def _default_routing_mode(platform: PlatformType) -> RoutingMode:
    """Return the default routing mode for a platform."""
    match platform:
        case PlatformType.SERVER:
            return RoutingMode.STANDARD
        case PlatformType.BROWSER:
            return RoutingMode.HASH_URL
        case PlatformType.DESKTOP:
            return RoutingMode.EMBEDDED


# Title (global - used for page title on server/browser, window title on desktop)
_TITLE: ConfigVar[str | None] = ConfigVar(
    "title",
    default=None,
    type_hint=str,
    help="Application title (page title for server/browser, window title for desktop)",
)

# Desktop settings (category="desktop" -> TRELLIS_DESKTOP_*)
_WINDOW_SIZE = ConfigVar(
    "window_size",
    default="maximized",
    category="desktop",
    validator=validate_window_size,
    help="Desktop window size: 'maximized' or 'WIDTHxHEIGHT' (e.g., '1024x768')",
)


@dataclass
class Config:
    """Configuration for a Trellis application.

    Values are resolved from multiple sources in priority order:
    1. CLI arguments (highest priority)
    2. Environment variables (TRELLIS_* or TRELLIS_{CATEGORY}_*)
    3. Constructor values (passed to Config())
    4. Default values (lowest priority)

    Access via get_app().config after the app is loaded:

        from trellis.app import get_app

        config = get_app().config
        print(config.name, config.module)

    Attributes:
        name: Application name (used for build artifacts, etc.)
        module: Python module path containing the entry point
        platform: Target platform (server, desktop, browser)
        force_build: Force rebuild of client bundle even if sources unchanged
        watch: Whether to watch for file changes
        batch_delay: Delay in seconds for batching render updates
        hot_reload: Whether to enable hot reload during development
        routing_mode: URL routing strategy (standard, hash_url, embedded)
        debug: Comma-separated debug categories to enable
        assets_dir: Directory containing static assets for bundling
        title: Application title (page/window title, defaults to name)
        host: Server bind address
        port: Server port (None for auto-select)
        window_size: Desktop window size ('maximized' or 'WIDTHxHEIGHT')
    """

    # Required fields
    name: str
    module: str

    # General settings
    platform: PlatformType = field(default_factory=lambda: PlatformType.SERVER)
    force_build: bool = False
    watch: bool = False
    batch_delay: float = field(default_factory=lambda: 1 / 30)
    hot_reload: bool = True
    routing_mode: RoutingMode | None = None
    debug: str = ""
    assets_dir: Path | None = None
    title: str | None = None

    # Server settings
    host: str = "127.0.0.1"
    port: int | None = None

    # Desktop settings
    window_size: str = "maximized"

    def __post_init__(self) -> None:
        """Resolve all fields through ConfigVar system and validate."""
        # Validate required fields
        if not self.name:
            raise TypeError("Config() missing required argument: 'name'")
        if not self.module:
            raise TypeError("Config() missing required argument: 'module'")

        # Resolve each field through CLI > ENV > constructor_value > default
        # General settings
        self.platform = _PLATFORM.resolve(self.platform)
        self.force_build = _FORCE_BUILD.resolve(self.force_build)
        self.watch = _WATCH.resolve(self.watch)
        self.batch_delay = _BATCH_DELAY.resolve(self.batch_delay)
        self.hot_reload = _HOT_RELOAD.resolve(self.hot_reload)
        self.routing_mode = _ROUTING_MODE.resolve(self.routing_mode)
        if self.routing_mode is None:
            self.routing_mode = _default_routing_mode(self.platform)
        self.debug = _DEBUG.resolve(self.debug)
        self.assets_dir = _ASSETS_DIR.resolve(self.assets_dir)
        self.title = _TITLE.resolve(self.title)
        if self.title is None:
            self.title = self.name

        # Server settings
        self.host = _HOST.resolve(self.host)
        self.port = _PORT.resolve(self.port)

        # Desktop settings
        self.window_size = _WINDOW_SIZE.resolve(self.window_size)
