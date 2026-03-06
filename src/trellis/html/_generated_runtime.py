"""Generated runtime-aligned HTML wrappers.

This module is intentionally scoped to the first generated HTML slice:
_A, Div, Img, and Input.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from trellis.core.rendering.element import Element
from trellis.html.base import Style, html_element
from trellis.html.events import (
    ChangeHandler,
    DragHandler,
    FocusHandler,
    InputHandler,
    KeyboardHandler,
    MouseHandler,
    ScrollHandler,
    WheelHandler,
)

__all__ = [
    "_A",
    "Div",
    "Img",
    "Input",
]

DataValue = str | int | float | bool | None
InputType = Literal[
    "button",
    "checkbox",
    "color",
    "date",
    "datetime-local",
    "email",
    "file",
    "hidden",
    "image",
    "month",
    "number",
    "password",
    "radio",
    "range",
    "reset",
    "search",
    "submit",
    "tel",
    "text",
    "time",
    "url",
    "week",
]


@html_element("a", is_container=True, name="A")
def _A(
    *,
    _text: str | None = None,
    href: str | None = None,
    target: Literal["_self", "_blank", "_parent", "_top"] | None = None,
    rel: str | None = None,
    download: str | bool | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseHandler | None = None,
    on_double_click: MouseHandler | None = None,
    on_context_menu: MouseHandler | None = None,
    on_key_down: KeyboardHandler | None = None,
    on_key_up: KeyboardHandler | None = None,
    data: Mapping[str, DataValue] | None = None,
) -> Element:
    """Generated raw a binding."""
    ...


@html_element("div", is_container=True)
def Div(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseHandler | None = None,
    on_double_click: MouseHandler | None = None,
    on_context_menu: MouseHandler | None = None,
    on_mouse_enter: MouseHandler | None = None,
    on_mouse_leave: MouseHandler | None = None,
    on_key_down: KeyboardHandler | None = None,
    on_key_up: KeyboardHandler | None = None,
    on_scroll: ScrollHandler | None = None,
    on_wheel: WheelHandler | None = None,
    on_drag_start: DragHandler | None = None,
    on_drag: DragHandler | None = None,
    on_drag_end: DragHandler | None = None,
    on_drag_enter: DragHandler | None = None,
    on_drag_over: DragHandler | None = None,
    on_drag_leave: DragHandler | None = None,
    on_drop: DragHandler | None = None,
    data: Mapping[str, DataValue] | None = None,
) -> Element:
    """Generated raw div binding."""
    ...


@html_element("img")
def Img(
    *,
    src: str,
    alt: str | None = None,
    width: int | float | str | None = None,
    height: int | float | str | None = None,
    loading: Literal["eager", "lazy"] | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseHandler | None = None,
    on_double_click: MouseHandler | None = None,
    on_context_menu: MouseHandler | None = None,
    data: Mapping[str, DataValue] | None = None,
) -> Element:
    """Generated raw img binding."""
    ...


@html_element("input")
def Input(
    *,
    type: InputType = "text",
    value: str | list[str] | int | float | None = None,
    placeholder: str | None = None,
    disabled: bool | None = None,
    read_only: bool | None = None,
    name: str | None = None,
    checked: bool | None = None,
    required: bool | None = None,
    min: int | float | str | None = None,
    max: int | float | str | None = None,
    step: int | float | str | None = None,
    pattern: str | None = None,
    max_length: int | float | None = None,
    auto_complete: Literal["", "off", "on"] | None = None,
    auto_focus: bool | None = None,
    accept: str | None = None,
    multiple: bool | None = None,
    on_change: ChangeHandler | None = None,
    on_input: InputHandler | None = None,
    on_focus: FocusHandler | None = None,
    on_blur: FocusHandler | None = None,
    on_key_down: KeyboardHandler | None = None,
    on_key_up: KeyboardHandler | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    data: Mapping[str, DataValue] | None = None,
) -> Element:
    """Generated raw input binding."""
    ...
