"""Platform abstraction for Trellis backends.

Each platform (Server, Desktop, Browser) implements this interface to provide
transport-specific functionality while sharing the core message handling logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import StrEnum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from trellis.app.config import Config
    from trellis.bundler.build_config import BuildConfig
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper


class PlatformType(StrEnum):
    """Available platform types."""

    SERVER = auto()
    DESKTOP = auto()
    BROWSER = auto()


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
    def get_build_config(self, config: Config) -> BuildConfig:
        """Get build configuration for this platform.

        Args:
            config: Application configuration

        Returns:
            BuildConfig with entry point and build steps
        """
        ...

    @abstractmethod
    def bundle(
        self,
        force: bool = False,
        dest: Path | None = None,
        library: bool = False,
        assets_dir: Path | None = None,
    ) -> Path:
        """Build the client bundle for this platform.

        Args:
            force: Force rebuild even if sources unchanged
            dest: Custom output directory (default: cache directory)
            library: Build as library with exports (vs app that renders to DOM)
            assets_dir: App-level static files directory to copy to dist

        Returns:
            The workspace Path used for the build
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


class PlatformArgumentError(Exception):
    """Raised when a platform-specific argument is used with wrong platform."""

    pass


__all__ = [
    "Platform",
    "PlatformArgumentError",
    "PlatformType",
]
