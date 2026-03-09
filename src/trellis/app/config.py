"""Configuration dataclass for Trellis applications."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from trellis.app.configvars import (
    ConfigVar,
    cli_context,
    coerce_value,
    get_config_vars,
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
_PYTHON_PATH: ConfigVar[list[Path]] = ConfigVar(
    "python_path",
    default=[Path(".")],
    type_hint=list[Path],
    help="Python import paths relative to app root",
)
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
_ICON: ConfigVar[Path | None] = ConfigVar(
    "icon",
    default=None,
    type_hint=Path,
    help="Project icon source file used to derive platform/web icons",
)

# Browser settings (category="browser" -> TRELLIS_BROWSER_*)
_LIBRARY = ConfigVar(
    "library",
    default=False,
    category="browser",
    is_flag=True,
    help="Build as library with exports instead of standalone app",
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
_SSR = ConfigVar(
    "ssr",
    default=True,
    category="server",
    help="Enable server-side rendering",
)
_SESSION_TTL = ConfigVar(
    "session_ttl",
    default=300,
    category="server",
    help="Session time-to-live in seconds (for SSR resumption and reconnection)",
)


def _default_routing_mode(platform: PlatformType) -> RoutingMode:
    """Return the default routing mode for a platform."""
    match platform:
        case PlatformType.SERVER:
            return RoutingMode.URL
        case PlatformType.BROWSER:
            return RoutingMode.HASH
        case PlatformType.DESKTOP:
            return RoutingMode.HIDDEN
        case _:
            raise ValueError(f"No default RoutingMode for PlatformType {platform!r}")


def _resolve_python_path(value: list[Path | str] | None) -> list[Path]:
    """Resolve python_path from constructor, environment, and CLI sources."""
    return _PYTHON_PATH.resolve(cast("Any", value))


def _resolve_optional_path(
    config_var: ConfigVar[Path | None], value: Path | str | None
) -> Path | None:
    """Resolve an optional path field from constructor, environment, and CLI sources."""
    return config_var.resolve(cast("Any", value))


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

# Packaging settings (category="packaging" -> TRELLIS_PACKAGING_*)
_IDENTIFIER: ConfigVar[str | None] = ConfigVar(
    "identifier",
    default=None,
    category="packaging",
    type_hint=str,
    help="Reverse-domain identifier (e.g., 'com.example.myapp')",
)
_VERSION: ConfigVar[str | None] = ConfigVar(
    "version",
    default=None,
    category="packaging",
    type_hint=str,
    help="Application version (semver, e.g., '1.0.0')",
)
_UPDATE_URL: ConfigVar[str | None] = ConfigVar(
    "update_url",
    default=None,
    category="packaging",
    type_hint=str,
    help="Tauri updater endpoint URL",
)
_UPDATE_PUBKEY: ConfigVar[str | None] = ConfigVar(
    "update_pubkey",
    default=None,
    category="packaging",
    type_hint=str,
    help="Ed25519 public key for update signature verification",
)


@dataclass(init=False)
class Config:
    """Configuration for a Trellis application.

    Values are resolved from multiple sources in priority order:
    1. CLI arguments (highest priority)
    2. Environment variables (TRELLIS_* or TRELLIS_{CATEGORY}_*)
    3. Constructor values (passed to Config())
    4. Default values (lowest priority)

    Access via get_config() after the apploader is loaded:

        from trellis.app import get_config

        config = get_config()
        print(config.name, config.module)

    Attributes:
        name: Application name (used for build artifacts, etc.)
        module: Python module path containing the entry point
        python_path: Python import paths, typically relative to the app root
            before file-backed configs are loaded (default: ["."])
        platform: Target platform (server, desktop, browser)
        force_build: Force rebuild of client bundle even if sources unchanged
        watch: Whether to watch for file changes
        batch_delay: Delay in seconds for batching render updates
        hot_reload: Whether to enable hot reload during development
        routing_mode: URL routing strategy (standard, hash_url, embedded)
        debug: Comma-separated debug categories to enable
        assets_dir: Directory containing static assets for bundling
        icon: Project icon source file path
        title: Application title (page/window title, defaults to name)
        host: Server bind address
        port: Server port (None for auto-select)
        session_ttl: Session time-to-live in seconds (default 300)
        window_size: Desktop window size ('maximized' or 'WIDTHxHEIGHT')
        identifier: Reverse-domain bundle identifier (e.g., 'com.example.myapp')
        version: Application version string (semver)
        update_url: Tauri updater endpoint URL
        update_pubkey: Ed25519 public key for update verification
    """

    # Required fields
    name: str
    module: str

    # General settings
    python_path: list[Path] = field(default_factory=lambda: [Path(".")])
    platform: PlatformType = field(default_factory=lambda: PlatformType.SERVER)
    force_build: bool = False
    watch: bool = False
    batch_delay: float = field(default_factory=lambda: 1 / 30)
    hot_reload: bool = True
    routing_mode: RoutingMode | None = None
    debug: str = ""
    assets_dir: Path | None = None
    icon: Path | None = None
    title: str | None = None

    # Browser settings
    library: bool = False

    # Server settings
    host: str = "127.0.0.1"
    port: int | None = None
    ssr: bool = True
    session_ttl: int = 300

    # Desktop settings
    window_size: str = "maximized"

    # Packaging settings
    identifier: str | None = None
    version: str | None = None
    update_url: str | None = None
    update_pubkey: str | None = None

    def __init__(
        self,
        name: str,
        module: str,
        python_path: list[Path | str] | None = None,
        platform: PlatformType = PlatformType.SERVER,
        force_build: bool = False,
        watch: bool = False,
        batch_delay: float = 1 / 30,
        hot_reload: bool = True,
        routing_mode: RoutingMode | None = None,
        debug: str = "",
        assets_dir: Path | str | None = None,
        icon: Path | str | None = None,
        title: str | None = None,
        library: bool = False,
        host: str = "127.0.0.1",
        port: int | None = None,
        ssr: bool = True,
        session_ttl: int = 300,
        window_size: str = "maximized",
        identifier: str | None = None,
        version: str | None = None,
        update_url: str | None = None,
        update_pubkey: str | None = None,
    ) -> None:
        """Resolve all fields through ConfigVar system and validate."""
        self.name = name
        self.module = module

        # Validate required fields
        if not self.name:
            raise TypeError("Config() missing required argument: 'name'")
        if not self.module:
            raise TypeError("Config() missing required argument: 'module'")

        # Resolve each field through CLI > ENV > constructor_value > default
        # General settings
        self.python_path = _resolve_python_path(python_path)
        self.platform = _PLATFORM.resolve(platform)
        self.force_build = _FORCE_BUILD.resolve(force_build)
        self.watch = _WATCH.resolve(watch)
        self.batch_delay = _BATCH_DELAY.resolve(batch_delay)
        self.hot_reload = _HOT_RELOAD.resolve(hot_reload)
        self.routing_mode = _ROUTING_MODE.resolve(routing_mode)
        if self.routing_mode is None:
            self.routing_mode = _default_routing_mode(self.platform)
        self.debug = _DEBUG.resolve(debug)
        self.assets_dir = _resolve_optional_path(_ASSETS_DIR, assets_dir)
        self.icon = _resolve_optional_path(_ICON, icon)
        self.title = _TITLE.resolve(title)
        if self.title is None:
            self.title = self.name

        # Browser settings
        self.library = _LIBRARY.resolve(library)

        # Server settings
        self.host = _HOST.resolve(host)
        self.port = _PORT.resolve(port)
        self.ssr = _SSR.resolve(ssr)
        self.session_ttl = _SESSION_TTL.resolve(session_ttl)

        # Desktop settings
        self.window_size = _WINDOW_SIZE.resolve(window_size)

        # Packaging settings
        self.identifier = _IDENTIFIER.resolve(identifier)
        self.version = _VERSION.resolve(version)
        self.update_url = _UPDATE_URL.resolve(update_url)
        self.update_pubkey = _UPDATE_PUBKEY.resolve(update_pubkey)

    def to_json(self) -> str:
        """Serialize this Config to a JSON string.

        Enums are serialized as their string values, Paths as strings,
        lists of Paths as lists of strings.

        Returns:
            JSON string representation of the config
        """
        data: dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, StrEnum):
                data[f.name] = value.value
            elif isinstance(value, Path):
                data[f.name] = value.as_posix()
            elif isinstance(value, list):
                data[f.name] = [
                    item.as_posix() if isinstance(item, Path) else item for item in value
                ]
            else:
                data[f.name] = value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> Config:
        """Deserialize a JSON string to a Config instance.

        Uses cli_context to inject values so __post_init__ validation runs.

        Args:
            json_str: JSON string representation of a config

        Returns:
            A new Config instance

        Raises:
            json.JSONDecodeError: If json_str is not valid JSON
            TypeError: If required fields (name, module) are missing
            ValueError: If field values fail validation
        """
        data = json.loads(json_str)
        name = data.get("name", "")
        module = data.get("module", "")

        configvar_names = {cv.name for cv in get_config_vars()}
        cli_args: dict[str, Any] = {}

        for key, value in data.items():
            if key in ("name", "module") or value is None:
                continue
            if key in configvar_names:
                cli_args[key] = coerce_value(key, value) if isinstance(value, str) else value

        with cli_context(cli_args):
            return cls(name=name, module=module)
