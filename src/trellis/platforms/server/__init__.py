"""Server platform - FastAPI + WebSocket.

This is the default platform for Trellis applications.
"""

from trellis.bundler import registry
from trellis.platforms.server.platform import ServerPlatform

# Register the trellis-server module
registry.register("trellis-server")

__all__ = ["ServerPlatform"]
