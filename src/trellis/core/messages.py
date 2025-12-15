"""Core message types for Trellis communication.

These message types are shared across all platforms (Server, Desktop, Browser).
All platforms use the same message protocol including HelloMessage handshake.
"""

import typing as tp

import msgspec


class RenderMessage(msgspec.Struct, tag="render", tag_field="type"):
    """Tree render sent to client.

    Contains the complete serialized Element tree for initial render
    or re-render after state changes.
    """

    tree: dict[str, tp.Any]


class EventMessage(msgspec.Struct, tag="event", tag_field="type"):
    """Client event triggering a server callback."""

    callback_id: str
    args: list[tp.Any] = []


class ErrorMessage(msgspec.Struct, tag="error", tag_field="type"):
    """Error message sent to client when an exception occurs.

    Contains a formatted traceback and context about where the error occurred.
    """

    error: str  # Formatted traceback
    context: str  # "render" | "callback"


class HelloMessage(msgspec.Struct, tag="hello", tag_field="type"):
    """Client hello message sent on connection.

    All platforms use this message for session initialization.
    """

    client_id: str


class HelloResponseMessage(msgspec.Struct, tag="hello_response", tag_field="type"):
    """Server response to client hello.

    Contains session ID for tracking and server version for compatibility.
    """

    session_id: str
    server_version: str


# Union type for all messages - used by MessageHandler
Message = HelloMessage | HelloResponseMessage | RenderMessage | EventMessage | ErrorMessage
