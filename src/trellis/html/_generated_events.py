"""Generated typed event definitions for HTML elements.

Generated at: 2026-03-07T23:17:37.126Z
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

__all__ = [
    "EVENT_TYPE_MAP",
    "DataTransfer",
    "DragEvent",
    "DragEventHandler",
    "Event",
    "EventHandler",
    "File",
    "FocusEvent",
    "FocusEventHandler",
    "InputEvent",
    "InputEventHandler",
    "KeyboardEvent",
    "KeyboardEventHandler",
    "MouseEvent",
    "MouseEventHandler",
    "SubmitEvent",
    "SubmitEventHandler",
    "UIEvent",
    "UIEventHandler",
    "WheelEvent",
    "WheelEventHandler",
    "get_event_class",
]


@dataclass(frozen=True)
class Event:
    type: str = ""
    time_stamp: float = 0.0
    bubbles: bool = False
    cancelable: bool = False
    default_prevented: bool = False
    event_phase: int = 0
    is_trusted: bool = False


@dataclass(frozen=True)
class UIEvent(Event):
    detail: int = 0


@dataclass(frozen=True)
class MouseEvent(UIEvent):
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
class KeyboardEvent(UIEvent):
    key: str = ""
    code: str = ""
    location: int = 0
    alt_key: bool = False
    ctrl_key: bool = False
    shift_key: bool = False
    meta_key: bool = False
    repeat: bool = False
    is_composing: bool = False


@dataclass(frozen=True)
class FocusEvent(Event):
    pass


@dataclass(frozen=True)
class SubmitEvent(Event):
    pass


@dataclass(frozen=True)
class InputEvent(Event):
    data: str | None = None
    is_composing: bool = False
    input_type: str = ""


@dataclass(frozen=True)
class WheelEvent(MouseEvent):
    delta_x: float = 0.0
    delta_y: float = 0.0
    delta_z: float = 0.0
    delta_mode: int = 0


@dataclass(frozen=True)
class File:
    name: str = ""
    size: int = 0
    type: str = ""


@dataclass(frozen=True)
class DataTransfer:
    drop_effect: str = "none"
    effect_allowed: str = "none"
    types: list[str] = field(default_factory=list)
    files: list[File] = field(default_factory=list)


@dataclass(frozen=True)
class DragEvent(MouseEvent):
    data_transfer: DataTransfer | None = None


EventHandler = Callable[[Event], None] | Callable[[Event], Awaitable[None]]
UIEventHandler = Callable[[UIEvent], None] | Callable[[UIEvent], Awaitable[None]]
MouseEventHandler = Callable[[MouseEvent], None] | Callable[[MouseEvent], Awaitable[None]]
KeyboardEventHandler = Callable[[KeyboardEvent], None] | Callable[[KeyboardEvent], Awaitable[None]]
FocusEventHandler = Callable[[FocusEvent], None] | Callable[[FocusEvent], Awaitable[None]]
SubmitEventHandler = Callable[[SubmitEvent], None] | Callable[[SubmitEvent], Awaitable[None]]
InputEventHandler = Callable[[InputEvent], None] | Callable[[InputEvent], Awaitable[None]]
WheelEventHandler = Callable[[WheelEvent], None] | Callable[[WheelEvent], Awaitable[None]]
DragEventHandler = Callable[[DragEvent], None] | Callable[[DragEvent], Awaitable[None]]


EVENT_TYPE_MAP: dict[str, type[Event]] = {
    "blur": FocusEvent,
    "change": Event,
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
    "scroll": UIEvent,
    "submit": SubmitEvent,
    "wheel": WheelEvent,
}


def get_event_class(event_type: str) -> type[Event]:
    return EVENT_TYPE_MAP.get(event_type, Event)
