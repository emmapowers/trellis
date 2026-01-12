"""Typed event definitions for HTML elements.

Provides React-compatible event types for use with HTML element callbacks.
Event data is automatically serialized from JavaScript and converted to
the appropriate dataclass on the Python side.

Example:
    ```python
    from trellis.html.events import MouseEvent, ChangeEvent

    def handle_click(event: MouseEvent) -> None:
        print(f"Clicked at {event.clientX}, {event.clientY}")

    def handle_change(event: ChangeEvent) -> None:
        print(f"New value: {event.value}")

    h.Div(onClick=handle_click)
    h.Input(onChange=handle_change)
    ```
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

__all__ = [
    "EVENT_TYPE_MAP",
    "BaseEvent",
    "ChangeEvent",
    "ChangeEventHandler",
    "EventHandler",
    "FocusEvent",
    "FocusEventHandler",
    "FormEvent",
    "FormEventHandler",
    "InputEvent",
    "InputEventHandler",
    "KeyboardEvent",
    "KeyboardEventHandler",
    "MouseEvent",
    "MouseEventHandler",
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
    """Mouse event data matching React's MouseEvent.

    Attributes:
        clientX: X coordinate relative to viewport
        clientY: Y coordinate relative to viewport
        button: Which button was pressed (0=left, 1=middle, 2=right)
        altKey: Whether Alt key was held
        ctrlKey: Whether Ctrl key was held
        shiftKey: Whether Shift key was held
        metaKey: Whether Meta/Cmd key was held
    """

    clientX: int = 0
    clientY: int = 0
    screenX: int = 0
    screenY: int = 0
    button: int = 0
    buttons: int = 0
    altKey: bool = False
    ctrlKey: bool = False
    shiftKey: bool = False
    metaKey: bool = False


@dataclass(frozen=True)
class KeyboardEvent(BaseEvent):
    """Keyboard event data matching React's KeyboardEvent.

    Attributes:
        key: The key value (e.g., 'Enter', 'a', 'ArrowUp')
        code: Physical key code (e.g., 'KeyA', 'Enter')
        altKey: Whether Alt key was held
        ctrlKey: Whether Ctrl key was held
        shiftKey: Whether Shift key was held
        metaKey: Whether Meta/Cmd key was held
        repeat: Whether key is being held down (auto-repeat)
    """

    key: str = ""
    code: str = ""
    altKey: bool = False
    ctrlKey: bool = False
    shiftKey: bool = False
    metaKey: bool = False
    repeat: bool = False


@dataclass(frozen=True)
class FocusEvent(BaseEvent):
    """Focus event data matching React's FocusEvent."""

    pass


@dataclass(frozen=True)
class FormEvent(BaseEvent):
    """Form event data for onSubmit."""

    pass


@dataclass(frozen=True)
class InputEvent(BaseEvent):
    """Input event data for onInput."""

    data: str | None = None
    """The inserted characters (for insertions)."""


@dataclass(frozen=True)
class ChangeEvent(BaseEvent):
    """Change event data for onChange.

    Attributes:
        value: The new value of the input element
        checked: For checkboxes/radios, whether it's checked
    """

    value: str = ""
    checked: bool = False


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

# Union type for any event handler (simple or typed, sync or async)
MouseHandler = EventHandler | MouseEventHandler
KeyboardHandler = EventHandler | KeyboardEventHandler
FocusHandler = EventHandler | FocusEventHandler
FormHandler = EventHandler | FormEventHandler
InputHandler = EventHandler | InputEventHandler
ChangeHandler = EventHandler | ChangeEventHandler


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
    "keypress": KeyboardEvent,
    # Form events
    "change": ChangeEvent,
    "input": InputEvent,
    "focus": FocusEvent,
    "blur": FocusEvent,
    "submit": FormEvent,
}


def get_event_class(event_type: str) -> type[BaseEvent]:
    """Get the event class for a DOM event type.

    Args:
        event_type: DOM event type string (e.g., "click", "keydown")

    Returns:
        The corresponding event dataclass, or BaseEvent if unknown
    """
    return EVENT_TYPE_MAP.get(event_type, BaseEvent)
