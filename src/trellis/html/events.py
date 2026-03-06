"""Generated typed event definitions for HTML elements."""

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


@dataclass(frozen=True)
class BaseEvent:
    type: str = ""
    timestamp: float = 0.0


@dataclass(frozen=True)
class MouseEvent(BaseEvent):
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
    key: str = ""
    code: str = ""
    alt_key: bool = False
    ctrl_key: bool = False
    shift_key: bool = False
    meta_key: bool = False
    repeat: bool = False


@dataclass(frozen=True)
class FocusEvent(BaseEvent):
    pass


@dataclass(frozen=True)
class FormEvent(BaseEvent):
    pass


@dataclass(frozen=True)
class InputEvent(BaseEvent):
    data: str | None = None


@dataclass(frozen=True)
class ChangeEvent(BaseEvent):
    value: str = ""
    checked: bool = False


@dataclass(frozen=True)
class ScrollEvent(BaseEvent):
    scroll_top: float = 0.0
    scroll_left: float = 0.0
    scroll_width: float = 0.0
    scroll_height: float = 0.0
    client_width: float = 0.0
    client_height: float = 0.0


@dataclass(frozen=True)
class WheelEvent(MouseEvent):
    delta_x: float = 0.0
    delta_y: float = 0.0
    delta_z: float = 0.0
    delta_mode: int = 0


@dataclass(frozen=True)
class DragDataTransferFile:
    name: str = ""
    size: int = 0
    type: str = ""


@dataclass(frozen=True)
class DragDataTransfer:
    drop_effect: str = "none"
    effect_allowed: str = "none"
    types: list[str] = field(default_factory=list)
    files: list[DragDataTransferFile] = field(default_factory=list)


@dataclass(frozen=True)
class DragEvent(MouseEvent):
    data_transfer: DragDataTransfer | None = None


EventHandler = Callable[[], None] | Callable[[], Awaitable[None]]

MouseEventHandler = Callable[[MouseEvent], None] | Callable[[MouseEvent], Awaitable[None]]
KeyboardEventHandler = Callable[[KeyboardEvent], None] | Callable[[KeyboardEvent], Awaitable[None]]
FocusEventHandler = Callable[[FocusEvent], None] | Callable[[FocusEvent], Awaitable[None]]
FormEventHandler = Callable[[FormEvent], None] | Callable[[FormEvent], Awaitable[None]]
InputEventHandler = Callable[[InputEvent], None] | Callable[[InputEvent], Awaitable[None]]
ChangeEventHandler = Callable[[ChangeEvent], None] | Callable[[ChangeEvent], Awaitable[None]]
ScrollEventHandler = Callable[[ScrollEvent], None] | Callable[[ScrollEvent], Awaitable[None]]
WheelEventHandler = Callable[[WheelEvent], None] | Callable[[WheelEvent], Awaitable[None]]
DragEventHandler = Callable[[DragEvent], None] | Callable[[DragEvent], Awaitable[None]]

MouseHandler = EventHandler | MouseEventHandler
KeyboardHandler = EventHandler | KeyboardEventHandler
FocusHandler = EventHandler | FocusEventHandler
FormHandler = EventHandler | FormEventHandler
InputHandler = EventHandler | InputEventHandler
ChangeHandler = EventHandler | ChangeEventHandler
ScrollHandler = EventHandler | ScrollEventHandler
WheelHandler = EventHandler | WheelEventHandler
DragHandler = EventHandler | DragEventHandler


EVENT_TYPE_MAP: dict[str, type[BaseEvent]] = {
    "blur": FocusEvent,
    "change": ChangeEvent,
    "click": MouseEvent,
    "contextmenu": MouseEvent,
    "dblclick": MouseEvent,
    "drag": DragEvent,
    "dragend": DragEvent,
    "dragenter": DragEvent,
    "dragleave": DragEvent,
    "dragover": DragEvent,
    "dragstart": DragEvent,
    "drop": DragEvent,
    "focus": FocusEvent,
    "input": InputEvent,
    "keydown": KeyboardEvent,
    "keyup": KeyboardEvent,
    "mousedown": MouseEvent,
    "mouseenter": MouseEvent,
    "mouseleave": MouseEvent,
    "mousemove": MouseEvent,
    "mouseout": MouseEvent,
    "mouseover": MouseEvent,
    "mouseup": MouseEvent,
    "scroll": ScrollEvent,
    "submit": FormEvent,
    "wheel": WheelEvent,
}


def get_event_class(event_type: str) -> type[BaseEvent]:
    return EVENT_TYPE_MAP.get(event_type, BaseEvent)
