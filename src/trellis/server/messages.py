"""WebSocket-specific message types for session management.

Core message types (RenderMessage, EventMessage) are in trellis.core.messages.
"""

import msgspec

# Re-export core messages for convenience
from trellis.core.messages import EventMessage, RenderMessage


class HelloMessage(msgspec.Struct, tag="hello", tag_field="type"):
    """Client hello message sent on WebSocket connection."""

    client_id: str
    protocol_version: int = 1


class HelloResponseMessage(msgspec.Struct, tag="hello_response", tag_field="type"):
    """Server response to client hello."""

    session_id: str
    server_version: str


# Union type for all WebSocket messages - includes hello handshake
Message = HelloMessage | HelloResponseMessage | RenderMessage | EventMessage
