"""Generated runtime-aligned HTML wrappers.

This module is intentionally scoped to the first generated HTML slice:
_A, Div, Img, and Input.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, overload

from trellis.core.rendering.element import Element
from trellis.html.base import HtmlContainerElement, Style, html_element
from trellis.html.events import (
    DragEventHandler,
    EventHandler,
    FocusEventHandler,
    InputEventHandler,
    KeyboardEventHandler,
    MouseEventHandler,
    UIEventHandler,
    WheelEventHandler,
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


@overload
def _A(
    internal_text: str,
    /,
    *,
    href: str | None = None,
    target: Literal["_self", "_blank", "_parent", "_top"] | None = None,
    rel: str | None = None,
    download: str | bool | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    data: Mapping[str, DataValue] | None = None,
) -> Element: ...


@overload
def _A(
    *,
    href: str | None = None,
    target: Literal["_self", "_blank", "_parent", "_top"] | None = None,
    rel: str | None = None,
    download: str | bool | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    data: Mapping[str, DataValue] | None = None,
) -> HtmlContainerElement: ...


@html_element("a", is_container=True, name="A")
def _A(
    internal_text: str | None = None,
    /,
    *,
    href: str | None = None,
    target: Literal["_self", "_blank", "_parent", "_top"] | None = None,
    rel: str | None = None,
    download: str | bool | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
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
    on_click: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_mouse_enter: MouseEventHandler | None = None,
    on_mouse_leave: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    on_scroll: UIEventHandler | None = None,
    on_wheel: WheelEventHandler | None = None,
    on_drag_start: DragEventHandler | None = None,
    on_drag: DragEventHandler | None = None,
    on_drag_end: DragEventHandler | None = None,
    on_drag_enter: DragEventHandler | None = None,
    on_drag_over: DragEventHandler | None = None,
    on_drag_leave: DragEventHandler | None = None,
    on_drop: DragEventHandler | None = None,
    data: Mapping[str, DataValue] | None = None,
) -> HtmlContainerElement:
    """Generated raw div binding."""
    ...


@html_element("img")
def Img(
    *,
    src: str | None = None,
    alt: str | None = None,
    width: int | float | str | None = None,
    height: int | float | str | None = None,
    loading: Literal["eager", "lazy"] | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
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
    on_change: EventHandler | None = None,
    on_input: InputEventHandler | None = None,
    on_focus: FocusEventHandler | None = None,
    on_blur: FocusEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    data: Mapping[str, DataValue] | None = None,
) -> Element:
    """Generated raw input binding."""
    ...
