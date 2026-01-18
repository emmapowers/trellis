"""Server platform - FastAPI + WebSocket.

This is the default platform for Trellis applications.
"""

# Register trellis-server module with the bundler
from trellis.platforms.server import _register as _  # noqa: F401
from trellis.platforms.server.platform import ServerPlatform

__all__ = ["ServerPlatform"]
