"""Desktop platform using PyTauri.

Provides native desktop applications using the system webview.
Uses channel-based communication with the same message protocol as WebSocket.
"""

from trellis.platforms.desktop.platform import DesktopPlatform

__all__ = ["DesktopPlatform"]
