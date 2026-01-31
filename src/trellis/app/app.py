"""App class and global accessors for Trellis applications."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType

from trellis.app.config import Config

ENV_VAR_APP_ROOT = "TRELLIS_APP_ROOT"


def find_app_path() -> Path:
    """Find the directory containing trellis.py by walking up from cwd.

    Searches from the current working directory toward the filesystem root,
    returning the first directory that contains a trellis.py file.

    Returns:
        Path to the directory containing trellis.py

    Raises:
        FileNotFoundError: If no trellis.py is found
    """
    current = Path.cwd().resolve()

    while True:
        if (current / "trellis.py").exists():
            return current

        parent = current.parent
        if parent == current:
            # Reached filesystem root
            raise FileNotFoundError(
                "trellis.py not found. Run 'trellis init' to create a Trellis project."
            )

        current = parent


def resolve_app_root(cli_value: Path | None = None) -> Path:
    """Resolve app root from CLI > ENV > auto-detect.

    Resolution order:
    1. If cli_value is provided, use it
    2. Else check TRELLIS_APP_ROOT environment variable
    3. Else call find_app_path() for auto-detection

    For any explicit path (CLI or ENV): if it's a file, use its parent directory.
    Always validates that the resulting directory contains trellis.py.

    Args:
        cli_value: Path from --app-root CLI option (None if not provided)

    Returns:
        Path to directory containing trellis.py

    Raises:
        FileNotFoundError: If path doesn't exist or no trellis.py found
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
        Normalized directory path containing trellis.py

    Raises:
        FileNotFoundError: If path doesn't exist or no trellis.py found
    """
    if not path.exists():
        raise FileNotFoundError(f"Path from {source} does not exist: {path}")

    # If path is a file, use its parent directory
    if path.is_file():
        path = path.parent

    # Validate trellis.py exists
    if not (path / "trellis.py").exists():
        raise FileNotFoundError(f"trellis.py not found in {path}")

    return path


class App:
    """Represents a Trellis application.

    The App class manages application configuration loaded from trellis.py.

    Attributes:
        path: Directory containing the trellis.py file
        config: Loaded configuration, or None if not yet loaded
    """

    def __init__(self, path: Path) -> None:
        """Initialize an App instance.

        Args:
            path: Directory containing the trellis.py file
        """
        self.path = path
        self.config: Config | None = None

    def load_config(self) -> None:
        """Load configuration from trellis.py.

        Executes the trellis.py file and extracts the `config` variable,
        which must be a Config instance.

        Raises:
            FileNotFoundError: If trellis.py doesn't exist at self.path
            ValueError: If `config` variable is not defined in trellis.py
            TypeError: If `config` is not a Config instance
            SyntaxError: If trellis.py has syntax errors (passed through)
            ModuleNotFoundError: If trellis.py has import errors (passed through)
        """
        trellis_file = self.path / "trellis.py"

        if not trellis_file.exists():
            raise FileNotFoundError(f"trellis.py not found at {self.path}")

        # Execute trellis.py in its own namespace
        namespace: dict[str, object] = {}
        exec(trellis_file.read_text(), namespace)

        if "config" not in namespace:
            raise ValueError(
                f"'config' variable not defined in {trellis_file}. "
                "Your trellis.py must define: config = Config(name=..., module=...)"
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


# Global singleton
_app: App | None = None


def get_app() -> App:
    """Get the global App instance.

    Returns:
        The global App instance

    Raises:
        RuntimeError: If set_app() has not been called
    """
    if _app is None:
        raise RuntimeError(
            "App not initialized. Call set_app() first, or use find_app_path() "
            "and App() to create one."
        )
    return _app


def set_app(app: App) -> None:
    """Set the global App instance.

    Args:
        app: The App instance to set as global
    """
    global _app
    _app = app
