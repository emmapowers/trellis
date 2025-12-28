"""Reactive state primitives for the Trellis UI framework.

This package provides:
- `Stateful`: Base class for reactive state with automatic dependency tracking
- `TrackedList`, `TrackedDict`, `TrackedSet`: Tracked collection types
- `Mutable`: Fine-grained reactive properties for complex objects
"""

from trellis.core.state.conversion import convert_to_tracked
from trellis.core.state.mutable import Mutable, callback, mutable
from trellis.core.state.stateful import Stateful
from trellis.core.state.tracked import TrackedDict, TrackedList, TrackedSet

__all__ = [
    "Mutable",
    "Stateful",
    "TrackedDict",
    "TrackedList",
    "TrackedSet",
    "callback",
    "convert_to_tracked",
    "mutable",
]
