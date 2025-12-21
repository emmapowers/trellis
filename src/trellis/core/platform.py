"""Platform abstraction for Trellis backends.

Each platform (Server, Desktop, Browser) implements this interface to provide
transport-specific functionality while sharing the core message handling logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from trellis.core.rendering import ElementNode


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
    def bundle(
        self,
        force: bool = False,
        extra_packages: dict[str, str] | None = None,
    ) -> None:
        """Build the client bundle for this platform.

        Args:
            force: Force rebuild even if sources unchanged
            extra_packages: Additional npm packages beyond platform defaults
        """
        ...

    @abstractmethod
    async def run(
        self,
        root_component: Callable[[], ElementNode],
        **kwargs: Any,
    ) -> None:
        """Start the platform and run until shutdown.

        Args:
            root_component: The root Trellis component to render
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
