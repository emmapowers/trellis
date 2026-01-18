"""Desktop platform using PyTauri.

Provides native desktop applications using the system webview.
Uses channel-based communication with the same message protocol as WebSocket.
"""

# Register trellis-desktop module with the bundler
from trellis.platforms.desktop import _register as _  # noqa: F401
from trellis.platforms.desktop.platform import DesktopPlatform

__all__ = ["DesktopPlatform"]
