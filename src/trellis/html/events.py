"""Typed event definitions for HTML elements.

Provides React-compatible event types for use with HTML element callbacks.
Currently callbacks don't receive event data, but these types document
the expected signatures and can be extended for full event support.

Example:
    ```python
    from trellis.html.events import MouseEventHandler

    def handle_click(event: MouseEvent) -> None:
        print(f"Clicked at {event.clientX}, {event.clientY}")

    h.Div(onClick=handle_click)
    ```
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

__all__ = [
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
]


# =============================================================================
# Event data types
# =============================================================================


@dataclass(frozen=True)
class BaseEvent:
    """Base class for all events."""

    type: str
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

# Simple handler (no event data) - for backwards compatibility
EventHandler = Callable[[], None]

# Typed handlers that receive event data
MouseEventHandler = Callable[[MouseEvent], None]
KeyboardEventHandler = Callable[[KeyboardEvent], None]
FocusEventHandler = Callable[[FocusEvent], None]
FormEventHandler = Callable[[FormEvent], None]
InputEventHandler = Callable[[InputEvent], None]
ChangeEventHandler = Callable[[ChangeEvent], None]

# Union type for any mouse event handler (simple or typed)
MouseHandler = EventHandler | MouseEventHandler
KeyboardHandler = EventHandler | KeyboardEventHandler
FocusHandler = EventHandler | FocusEventHandler
FormHandler = EventHandler | FormEventHandler
InputHandler = EventHandler | InputEventHandler
ChangeHandler = EventHandler | ChangeEventHandler
