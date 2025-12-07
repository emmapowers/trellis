"""Message types for WebSocket communication using msgpack."""

import typing as tp

import msgspec


class HelloMessage(msgspec.Struct, tag="hello", tag_field="type"):
    """Client hello message sent on connection."""

    client_id: str
    protocol_version: int = 1


class HelloResponseMessage(msgspec.Struct, tag="hello_response", tag_field="type"):
    """Server response to client hello."""

    session_id: str
    server_version: str


class RenderMessage(msgspec.Struct, tag="render", tag_field="type"):
    """Full tree render sent to client.

    Contains the complete serialized Element tree for initial render
    or full re-render.
    """

    tree: dict[str, tp.Any]


# Union type for all messages - enables type-safe dispatch
Message = HelloMessage | HelloResponseMessage | RenderMessage
