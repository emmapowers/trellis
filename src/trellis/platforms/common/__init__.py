"""Common utilities shared across platforms."""

from trellis.bundler.registry import registry
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
from trellis.platforms.common.serialization import parse_callback_id, serialize_element

# Register the trellis-core module
registry.register(
    "trellis-core",
    packages={
        "react": "18.3.1",
        "react-dom": "18.3.1",
        "@types/react": "18.3.23",
        "@types/react-dom": "18.3.7",
        "@msgpack/msgpack": "3.0.0",
        "lucide-react": "0.468.0",
        "uplot": "1.6.31",
        "recharts": "3.6.0",
        "react-aria": "3.35.0",
        "react-stately": "3.33.0",
        "@internationalized/date": "3.5.6",
    },
)

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
    "serialize_element",
]
