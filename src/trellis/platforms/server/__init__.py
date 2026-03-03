"""Server platform - FastAPI + WebSocket.

This is the default platform for Trellis applications.
"""

from trellis.platforms.server.platform import ServerPlatform
from trellis.registry import registry

# Register the trellis-server module
registry.register("trellis-server")

__all__ = ["ServerPlatform"]
