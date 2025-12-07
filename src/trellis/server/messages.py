"""Message types for WebSocket communication using msgpack."""

import msgspec


class HelloMessage(msgspec.Struct, tag="hello", tag_field="type"):
    """Client hello message sent on connection."""

    client_id: str
    protocol_version: int = 1


class HelloResponseMessage(msgspec.Struct, tag="hello_response", tag_field="type"):
    """Server response to client hello."""

    session_id: str
    server_version: str


# Union type for all messages - enables type-safe dispatch
Message = HelloMessage | HelloResponseMessage
