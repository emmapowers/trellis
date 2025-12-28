"""Common utilities shared across platforms."""

from trellis.platforms.common.base import Platform, PlatformArgumentError, PlatformType
from trellis.platforms.common.handler import MessageHandler
from trellis.platforms.common.messages import (
    AddPatch,
    DebugConfig,
    ErrorMessage,
    EventMessage,
    HelloMessage,
    HelloResponseMessage,
    Message,
    Patch,
    PatchMessage,
    RemovePatch,
    UpdatePatch,
)
from trellis.platforms.common.ports import find_available_port
from trellis.platforms.common.serialization import parse_callback_id, serialize_node

__all__ = [
    "AddPatch",
    "DebugConfig",
    "ErrorMessage",
    "EventMessage",
    "HelloMessage",
    "HelloResponseMessage",
    "Message",
    "MessageHandler",
    "Patch",
    "PatchMessage",
    "Platform",
    "PlatformArgumentError",
    "PlatformType",
    "RemovePatch",
    "UpdatePatch",
    "find_available_port",
    "parse_callback_id",
    "serialize_node",
]
