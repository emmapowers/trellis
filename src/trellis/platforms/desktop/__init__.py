"""Desktop platform using PyTauri.

Provides native desktop applications using the system webview.
Uses channel-based communication with the same message protocol as WebSocket.
"""

from trellis.bundler import registry
from trellis.platforms.desktop.platform import DesktopPlatform

# Register the trellis-desktop module
registry.register(
    "trellis-desktop",
    packages={
        "@tauri-apps/api": "2.8.0",
        "tauri-plugin-pytauri-api": "0.8.0",
    },
)

__all__ = ["DesktopPlatform"]
