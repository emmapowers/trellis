"""Typed event definitions for HTML elements.

Provides React-compatible event types for use with HTML element callbacks.
Event data is automatically serialized from JavaScript and converted to
appropriate dataclasses on the Python side.

Example:
    ```python
    from trellis.html.events import MouseEvent, ChangeEvent

    def handle_click(event: MouseEvent) -> None:
        print(f"Clicked at {event.client_x}, {event.client_y}")

    def handle_change(event: ChangeEvent) -> None:
        print(f"New value: {event.value}")

    h.Div(on_click=handle_click)
    h.Input(on_change=handle_change)
    ```
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

__all__ = [
    "EVENT_TYPE_MAP",
    "BaseEvent",
    "ChangeEvent",
    "ChangeEventHandler",
    "ChangeHandler",
    "DragDataTransfer",
    "DragDataTransferFile",
    "DragEvent",
    "DragEventHandler",
    "DragHandler",
    "EventHandler",
    "FocusEvent",
    "FocusEventHandler",
    "FocusHandler",
    "FormEvent",
    "FormEventHandler",
    "FormHandler",
    "InputEvent",
    "InputEventHandler",
    "InputHandler",
    "KeyboardEvent",
    "KeyboardEventHandler",
    "KeyboardHandler",
    "MouseEvent",
    "MouseEventHandler",
    "MouseHandler",
    "ScrollEvent",
    "ScrollEventHandler",
    "ScrollHandler",
    "WheelEvent",
    "WheelEventHandler",
    "WheelHandler",
    "get_event_class",
]


# =============================================================================
# Event data types
# =============================================================================


@dataclass(frozen=True)
class BaseEvent:
    """Base class for all events."""

    type: str = ""
    """The type of event (e.g., 'click', 'keydown')."""

    timestamp: float = 0.0
    """Time when the event was created (milliseconds since epoch)."""


@dataclass(frozen=True)
class MouseEvent(BaseEvent):
    """Mouse event data matching React's MouseEvent."""

    client_x: int = 0
    client_y: int = 0
    screen_x: int = 0
    screen_y: int = 0
    button: int = 0
    buttons: int = 0
    alt_key: bool = False
    ctrl_key: bool = False
    shift_key: bool = False
    meta_key: bool = False


@dataclass(frozen=True)
class KeyboardEvent(BaseEvent):
    """Keyboard event data matching React's KeyboardEvent."""

    key: str = ""
    code: str = ""
    alt_key: bool = False
    ctrl_key: bool = False
    shift_key: bool = False
    meta_key: bool = False
    repeat: bool = False


@dataclass(frozen=True)
class FocusEvent(BaseEvent):
    """Focus event data matching React's FocusEvent."""

    pass


@dataclass(frozen=True)
class FormEvent(BaseEvent):
    """Form event data for on_submit."""

    pass


@dataclass(frozen=True)
class InputEvent(BaseEvent):
    """Input event data for on_input."""

    data: str | None = None
    """The inserted characters (for insertions)."""


@dataclass(frozen=True)
class ChangeEvent(BaseEvent):
    """Change event data for on_change."""

    value: str = ""
    checked: bool = False


@dataclass(frozen=True)
class ScrollEvent(BaseEvent):
    """Scroll event data from scrollable containers."""

    scroll_top: float = 0.0
    scroll_left: float = 0.0
    scroll_width: float = 0.0
    scroll_height: float = 0.0
    client_width: float = 0.0
    client_height: float = 0.0


@dataclass(frozen=True)
class WheelEvent(MouseEvent):
    """Wheel event data (extends MouseEvent with delta fields)."""

    delta_x: float = 0.0
    delta_y: float = 0.0
    delta_z: float = 0.0
    delta_mode: int = 0


@dataclass(frozen=True)
class DragDataTransferFile:
    """File metadata from a drag/drop data_transfer payload."""

    name: str = ""
    size: int = 0
    type: str = ""


@dataclass(frozen=True)
class DragDataTransfer:
    """Typed subset of browser data_transfer payload for drag events."""

    drop_effect: str = "none"
    effect_allowed: str = "none"
    types: list[str] = field(default_factory=list)
    files: list[DragDataTransferFile] = field(default_factory=list)


@dataclass(frozen=True)
class DragEvent(MouseEvent):
    """Drag event data (extends MouseEvent with data_transfer)."""

    data_transfer: DragDataTransfer | None = None


# =============================================================================
# Handler type aliases
# =============================================================================

# Simple handler (no event data) - sync or async
EventHandler = Callable[[], None] | Callable[[], Awaitable[None]]

# Typed handlers that receive event data - sync or async
MouseEventHandler = Callable[[MouseEvent], None] | Callable[[MouseEvent], Awaitable[None]]
KeyboardEventHandler = Callable[[KeyboardEvent], None] | Callable[[KeyboardEvent], Awaitable[None]]
FocusEventHandler = Callable[[FocusEvent], None] | Callable[[FocusEvent], Awaitable[None]]
FormEventHandler = Callable[[FormEvent], None] | Callable[[FormEvent], Awaitable[None]]
InputEventHandler = Callable[[InputEvent], None] | Callable[[InputEvent], Awaitable[None]]
ChangeEventHandler = Callable[[ChangeEvent], None] | Callable[[ChangeEvent], Awaitable[None]]
ScrollEventHandler = Callable[[ScrollEvent], None] | Callable[[ScrollEvent], Awaitable[None]]
WheelEventHandler = Callable[[WheelEvent], None] | Callable[[WheelEvent], Awaitable[None]]
DragEventHandler = Callable[[DragEvent], None] | Callable[[DragEvent], Awaitable[None]]

# Union type for any event handler (simple or typed, sync or async)
MouseHandler = EventHandler | MouseEventHandler
KeyboardHandler = EventHandler | KeyboardEventHandler
FocusHandler = EventHandler | FocusEventHandler
FormHandler = EventHandler | FormEventHandler
InputHandler = EventHandler | InputEventHandler
ChangeHandler = EventHandler | ChangeEventHandler
ScrollHandler = EventHandler | ScrollEventHandler
WheelHandler = EventHandler | WheelEventHandler
DragHandler = EventHandler | DragEventHandler


# =============================================================================
# Event type mapping
# =============================================================================

# Map DOM event type strings to their corresponding dataclasses
EVENT_TYPE_MAP: dict[str, type[BaseEvent]] = {
    # Mouse events
    "click": MouseEvent,
    "dblclick": MouseEvent,
    "mousedown": MouseEvent,
    "mouseup": MouseEvent,
    "mousemove": MouseEvent,
    "mouseenter": MouseEvent,
    "mouseleave": MouseEvent,
    "mouseover": MouseEvent,
    "mouseout": MouseEvent,
    "contextmenu": MouseEvent,
    # Keyboard events
    "keydown": KeyboardEvent,
    "keyup": KeyboardEvent,
    # Form events
    "change": ChangeEvent,
    "input": InputEvent,
    "focus": FocusEvent,
    "blur": FocusEvent,
    "submit": FormEvent,
    # Scroll/wheel events
    "scroll": ScrollEvent,
    "wheel": WheelEvent,
    # Drag events
    "dragstart": DragEvent,
    "drag": DragEvent,
    "dragend": DragEvent,
    "dragenter": DragEvent,
    "dragover": DragEvent,
    "dragleave": DragEvent,
    "drop": DragEvent,
}


def get_event_class(event_type: str) -> type[BaseEvent]:
    """Get the event class for a DOM event type.

    Args:
        event_type: DOM event type string (e.g., "click", "keydown")

    Returns:
        The corresponding event dataclass, or BaseEvent if unknown
    """
    return EVENT_TYPE_MAP.get(event_type, BaseEvent)
