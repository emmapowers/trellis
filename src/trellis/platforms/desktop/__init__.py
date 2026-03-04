"""Desktop platform using PyTauri.

Provides native desktop applications using the system webview.
Uses channel-based communication with the same message protocol as WebSocket.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from trellis.registry import registry

if TYPE_CHECKING:
    from trellis.platforms.desktop.platform import DesktopPlatform
    from trellis.platforms.desktop.standalone_platform import DesktopStandalonePlatform

# Register the trellis-desktop module
registry.register(
    "trellis-desktop",
    packages={
        "@tauri-apps/api": "2.8.0",
        "tauri-plugin-pytauri-api": "0.8.0",
        "@tauri-apps/plugin-opener": "2.5.3",
    },
)


def __getattr__(name: str) -> Any:
    if name == "DesktopPlatform":
        # Lazy import keeps pytauri-only runtime dependencies out of non-desktop imports.
        from trellis.platforms.desktop.platform import DesktopPlatform  # noqa: PLC0415

        return DesktopPlatform
    if name == "DesktopStandalonePlatform":
        from trellis.platforms.desktop.standalone_platform import (  # noqa: PLC0415
            DesktopStandalonePlatform,
        )

        return DesktopStandalonePlatform
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["DesktopPlatform", "DesktopStandalonePlatform"]
