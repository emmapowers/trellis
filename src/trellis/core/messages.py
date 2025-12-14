"""Core message types for Trellis communication.

These message types are shared across all backends (WebSocket, Tauri IPC, Playground).
Transport-specific messages (like WebSocket hello handshake) live in their respective
backend modules.
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


# Union type for core messages - used by MessageHandler
Message = RenderMessage | EventMessage
