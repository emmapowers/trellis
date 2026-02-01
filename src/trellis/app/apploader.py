"""AppLoader class and global accessors for Trellis applications."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from trellis.app.app import App
from trellis.app.config import Config
from trellis.platforms.common.base import PlatformType

if TYPE_CHECKING:
    from trellis.platforms.common.base import Platform

ENV_VAR_APP_ROOT = "TRELLIS_APP_ROOT"


def _is_pyodide() -> bool:
    """Check if running inside Pyodide.

    Uses sys.platform == 'emscripten' as recommended by Pyodide docs.
    See: https://pyodide.org/en/stable/usage/faq.html
    """
    return sys.platform == "emscripten"


def find_app_path() -> Path:
    """Find the directory containing trellis_config.py by walking up from cwd.

    Searches from the current working directory toward the filesystem root,
    returning the first directory that contains a trellis_config.py file.

    Returns:
        Path to the directory containing trellis_config.py

    Raises:
        FileNotFoundError: If no trellis_config.py is found
    """
    current = Path.cwd().resolve()

    while True:
        if (current / "trellis_config.py").exists():
            return current

        parent = current.parent
        if parent == current:
            # Reached filesystem root
            raise FileNotFoundError(
                "trellis_config.py not found. Run 'trellis init' to create a Trellis project."
            )

        current = parent


def resolve_app_root(cli_value: Path | None = None) -> Path:
    """Resolve app root from CLI > ENV > auto-detect.

    Resolution order:
    1. If cli_value is provided, use it
    2. Else check TRELLIS_APP_ROOT environment variable
    3. Else call find_app_path() for auto-detection

    For any explicit path (CLI or ENV): if it's a file, use its parent directory.
    Always validates that the resulting directory contains trellis_config.py.

    Args:
        cli_value: Path from --app-root CLI option (None if not provided)

    Returns:
        Path to directory containing trellis_config.py

    Raises:
        FileNotFoundError: If path doesn't exist or no trellis_config.py found
    """
    # Try CLI value first
    if cli_value is not None:
        return _validate_app_root(cli_value, source="CLI")

    # Try environment variable
    env_value = os.environ.get(ENV_VAR_APP_ROOT, "").strip()
    if env_value:
        return _validate_app_root(Path(env_value), source="TRELLIS_APP_ROOT")

    # Fall back to auto-detection
    return find_app_path()


def _validate_app_root(path: Path, source: str) -> Path:
    """Validate and normalize an explicit app root path.

    Args:
        path: The path to validate
        source: Description of where the path came from (for error messages)

    Returns:
        Normalized directory path containing trellis_config.py

    Raises:
        FileNotFoundError: If path doesn't exist or no trellis_config.py found
    """
    if not path.exists():
        raise FileNotFoundError(f"Path from {source} does not exist: {path}")

    # If path is a file, use its parent directory
    if path.is_file():
        path = path.parent

    # Validate trellis_config.py exists
    if not (path / "trellis_config.py").exists():
        raise FileNotFoundError(f"trellis_config.py not found in {path}")

    return path


class AppLoader:
    """Loads and manages a Trellis application.

    The AppLoader class manages application configuration loaded from trellis_config.py.

    Attributes:
        path: Directory containing the trellis_config.py file
        config: Loaded configuration, or None if not yet loaded
    """

    def __init__(self, path: Path) -> None:
        """Initialize an AppLoader instance.

        Args:
            path: Directory containing the trellis_config.py file
        """
        self.path = path
        self.config: Config | None = None
        self.app: App | None = None
        self._platform: Platform | None = None

    def load_config(self) -> None:
        """Load configuration from trellis_config.py.

        Executes the trellis_config.py file and extracts the `config` variable,
        which must be a Config instance.

        Raises:
            FileNotFoundError: If trellis_config.py doesn't exist at self.path
            ValueError: If `config` variable is not defined in trellis_config.py
            TypeError: If `config` is not a Config instance
            SyntaxError: If trellis_config.py has syntax errors (passed through)
            ModuleNotFoundError: If trellis_config.py has import errors (passed through)
        """
        trellis_file = self.path / "trellis_config.py"

        if not trellis_file.exists():
            raise FileNotFoundError(f"trellis_config.py not found at {self.path}")

        # Execute trellis_config.py in its own namespace
        namespace: dict[str, object] = {}
        exec(trellis_file.read_text(), namespace)

        if "config" not in namespace:
            raise ValueError(
                f"'config' variable not defined in {trellis_file}. "
                "Your trellis_config.py must define: config = Config(name=..., module=...)"
            )

        config = namespace["config"]
        if not isinstance(config, Config):
            raise TypeError(
                f"'config' must be a Config instance, got {type(config).__name__}. "
                "Use: config = Config(name=..., module=...)"
            )

        self.config = config

    def import_module(self) -> ModuleType:
        """Import the application module specified in config.module.

        Attempts to import the module directly first. If that fails with
        ModuleNotFoundError, adds the app's path to sys.path and retries.

        Returns:
            The imported module object

        Raises:
            RuntimeError: If load_config() has not been called first
            ModuleNotFoundError: If the module cannot be found
            SyntaxError: If the module has syntax errors (passed through)
            ImportError: If the module has import errors (passed through)
        """
        if self.config is None:
            raise RuntimeError(
                "Config not loaded. Call load_config() first before import_module()."
            )

        module_name = self.config.module

        # Try importing directly first
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError:
            pass

        # Add app path to sys.path and retry
        app_path_str = str(self.path)
        if app_path_str not in sys.path:
            sys.path.insert(0, app_path_str)
            importlib.invalidate_caches()

        return importlib.import_module(module_name)

    def load_app(self) -> None:
        """Load the App instance from the application module.

        Imports the module via import_module() and extracts the `app` variable.
        Requires load_config() to have been called first.

        Raises:
            RuntimeError: If load_config() has not been called first
            ValueError: If `app` variable is not defined in the module
            TypeError: If `app` is not an App instance
        """
        if self.config is None:
            raise RuntimeError("Config not loaded. Call load_config() first before load_app().")

        module = self.import_module()

        if not hasattr(module, "app"):
            raise ValueError(
                f"'app' variable not defined in {self.config.module}. "
                "Your module must define: app = App(YourRootComponent)"
            )

        app = module.app
        if not isinstance(app, App):
            raise TypeError(
                f"'app' must be an App instance, got {type(app).__name__}. "
                "Use: app = App(YourRootComponent)"
            )

        self.app = app

    @property
    def platform(self) -> Platform:
        """Get the platform instance for this application.

        Lazily imports and instantiates the platform based on config.platform.
        For browser platform, returns BrowserPlatform if running in Pyodide,
        otherwise returns BrowserServePlatform.

        Returns:
            The platform instance

        Raises:
            RuntimeError: If config has not been loaded
        """
        if self._platform is not None:
            return self._platform

        if self.config is None:
            raise RuntimeError(
                "Config not loaded. Call load_config() first before accessing platform."
            )

        platform_type = self.config.platform

        # Lazy imports to avoid circular dependencies and load platform deps only when needed
        if platform_type == PlatformType.SERVER:
            from trellis.platforms.server import ServerPlatform  # noqa: PLC0415

            self._platform = ServerPlatform()
        elif platform_type == PlatformType.DESKTOP:
            from trellis.platforms.desktop import DesktopPlatform  # noqa: PLC0415

            self._platform = DesktopPlatform()
        elif platform_type == PlatformType.BROWSER:
            if _is_pyodide():
                from trellis.platforms.browser import BrowserPlatform  # noqa: PLC0415

                self._platform = BrowserPlatform()
            else:
                from trellis.platforms.browser.serve_platform import (  # noqa: PLC0415
                    BrowserServePlatform,
                )

                self._platform = BrowserServePlatform()
        else:
            raise ValueError(f"Unknown platform: {platform_type}")

        return self._platform


# Global singleton
_apploader: AppLoader | None = None


def get_apploader() -> AppLoader:
    """Get the global AppLoader instance.

    Returns:
        The global AppLoader instance

    Raises:
        RuntimeError: If set_apploader() has not been called
    """
    if _apploader is None:
        raise RuntimeError(
            "AppLoader not initialized. Call set_apploader() first, or use find_app_path() "
            "and AppLoader() to create one."
        )
    return _apploader


def set_apploader(apploader: AppLoader) -> None:
    """Set the global AppLoader instance.

    Args:
        apploader: The AppLoader instance to set as global
    """
    global _apploader
    _apploader = apploader


def get_config() -> Config | None:
    """Get the config from the global AppLoader.

    Returns:
        The Config from the global AppLoader, or None if not loaded

    Raises:
        RuntimeError: If set_apploader() has not been called
    """
    return get_apploader().config


def get_app() -> App | None:
    """Get the app from the global AppLoader.

    Returns:
        The App from the global AppLoader, or None if not loaded

    Raises:
        RuntimeError: If set_apploader() has not been called
    """
    return get_apploader().app


def get_app_root() -> Path:
    """Get the app root path from the global AppLoader.

    Returns:
        The path to the directory containing trellis_config.py

    Raises:
        RuntimeError: If set_apploader() has not been called
    """
    return get_apploader().path
