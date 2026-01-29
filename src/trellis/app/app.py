"""App class and global accessors for Trellis applications."""

from __future__ import annotations

from pathlib import Path

from trellis.app.config import Config


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
