"""Platform abstraction for Trellis backends.

Each platform (Server, Desktop, Browser) implements this interface to provide
transport-specific functionality while sharing the core message handling logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from trellis.bundler.registry import ModuleRegistry
    from trellis.bundler.steps import BuildStep
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper


class PlatformType(StrEnum):
    """Available platform types."""

    SERVER = auto()
    DESKTOP = auto()
    BROWSER = auto()


@dataclass
class WatchConfig:
    """Configuration for watch mode.

    Returned by platforms that support automatic rebuilding on file changes.
    """

    registry: ModuleRegistry
    """Module registry with registered modules."""

    entry_point: Path
    """Path to the entry point file."""

    workspace: Path
    """Workspace directory for staging and output."""

    steps: list[BuildStep]
    """Build steps to execute on rebuild."""


class Platform(ABC):
    """Abstract base class for platform implementations.

    Platforms handle the transport layer and application lifecycle.
    They create MessageHandler instances for each session/connection.

    Example:
        class ServerPlatform(Platform):
            @property
            def name(self) -> str:
                return "server"

            async def run(self, root_component, **kwargs):
                # Set up FastAPI, create WebSocket handler, etc.
                ...
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform identifier (e.g., 'server', 'desktop', 'browser')."""
        ...

    @abstractmethod
    def bundle(
        self,
        force: bool = False,
        dest: Path | None = None,
        library: bool = False,
        app_static_dir: Path | None = None,
    ) -> None:
        """Build the client bundle for this platform.

        Args:
            force: Force rebuild even if sources unchanged
            dest: Custom output directory (default: cache directory)
            library: Build as library with exports (vs app that renders to DOM)
            app_static_dir: App-level static files directory to copy to dist
        """
        ...

    @abstractmethod
    async def run(
        self,
        root_component: Callable[[], Element],
        app_wrapper: AppWrapper,
        **kwargs: Any,
    ) -> None:
        """Start the platform and run until shutdown.

        Args:
            root_component: The root Trellis component to render
            app_wrapper: Callback to wrap component with TrellisApp
            **kwargs: Platform-specific configuration (host, port, etc.)
        """
        ...

    def get_watch_config(self) -> WatchConfig | None:
        """Get configuration for watch mode.

        Override in platforms that support automatic rebuilding on file changes.
        Returns None by default (watch not supported).

        Returns:
            WatchConfig if watch is supported, None otherwise
        """
        return None


class PlatformArgumentError(Exception):
    """Raised when a platform-specific argument is used with wrong platform."""

    pass


__all__ = [
    "Platform",
    "PlatformArgumentError",
    "PlatformType",
    "WatchConfig",
]
