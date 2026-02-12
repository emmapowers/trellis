"""Common utilities shared across platforms."""

from pathlib import Path

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

# Register the trellis-core module with base_path pointing to the TypeScript
# source directory so @trellis/trellis-core/* aliases resolve correctly.
registry.register(
    "trellis-core",
    packages={
        "react": "18.3.1",
        "react-dom": "18.3.1",
        "@types/react": "18.3.23",
        "@types/react-dom": "18.3.7",
        "@msgpack/msgpack": "3.0.0",
    },
    base_path=Path(__file__).parent.resolve() / "client" / "src",
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
