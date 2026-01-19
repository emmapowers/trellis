"""Desktop platform using PyTauri.

Provides native desktop applications using the system webview.
Uses channel-based communication with the same message protocol as WebSocket.
"""

from pathlib import Path

from trellis.bundler import registry
from trellis.platforms.desktop.platform import DesktopPlatform

_CLIENT_SRC = Path(__file__).parent / "client" / "src"

# Register the trellis-desktop module
registry.register(
    "trellis-desktop",
    packages={
        "@tauri-apps/api": "2.8.0",
        "tauri-plugin-pytauri-api": "0.8.0",
    },
    static_files={"index.html": _CLIENT_SRC / "index.html"},
)

__all__ = ["DesktopPlatform"]
