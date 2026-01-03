"""Core message types for Trellis communication.

These message types are shared across all platforms (Server, Desktop, Browser).
All platforms use the same message protocol including HelloMessage handshake.
"""

import typing as tp
from typing import Literal

import msgspec

# ============================================================================
# Patch types for incremental updates
# ============================================================================


class UpdatePatch(msgspec.Struct, tag="update", tag_field="op"):
    """Update an existing element's props and/or children order."""

    id: str
    props: dict[str, tp.Any] | None = None  # Changed props only
    children: list[str] | None = None  # New children order


class RemovePatch(msgspec.Struct, tag="remove", tag_field="op"):
    """Remove an element from the tree."""

    id: str


class AddPatch(msgspec.Struct, tag="add", tag_field="op"):
    """Add a new element to the tree."""

    parent_id: str | None
    children: list[str]  # Parent's new children list
    element: dict[str, tp.Any]  # Full subtree for the new element


Patch = UpdatePatch | RemovePatch | AddPatch


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


class PatchMessage(msgspec.Struct, tag="patch", tag_field="type"):
    """Incremental update sent to client.

    Contains a list of patches to apply to the client-side tree.
    See Patch type for the three patch operations (add, update, remove).
    """

    patches: list[Patch]


class HelloMessage(msgspec.Struct, tag="hello", tag_field="type"):
    """Client hello message sent on connection.

    All platforms use this message for session initialization.
    """

    client_id: str
    system_theme: Literal["light", "dark"] = "light"  # Detected from OS preference
    theme_mode: Literal["system", "light", "dark"] | None = None  # Host-controlled override


class DebugConfig(msgspec.Struct):
    """Debug configuration sent to client.

    Contains the list of enabled debug categories so the client
    can mirror the server's debug logging configuration.
    """

    categories: list[str]


class HelloResponseMessage(msgspec.Struct, tag="hello_response", tag_field="type"):
    """Server response to client hello.

    Contains session ID for tracking and server version for compatibility.
    Optionally includes debug configuration for client-side logging.
    """

    session_id: str
    server_version: str
    debug: DebugConfig | None = None


# Union type for all messages - used by MessageHandler
Message = HelloMessage | HelloResponseMessage | PatchMessage | EventMessage | ErrorMessage
