"""Generated runtime-aligned HTML wrappers.

This module is intentionally scoped to the first generated HTML slice:
A, Div, Img, and Input.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, overload

from trellis.core.rendering.element import ContainerElement, Element
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
from trellis.routing.state import router

__all__ = [
    "A",
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


def _is_relative_url(href: str) -> bool:
    """Check if a URL should use client-side router navigation."""
    if href.startswith(("//", "#", "?")):
        return False

    non_relative_prefixes = (
        "http://",
        "https://",
        "mailto:",
        "tel:",
        "javascript:",
        "data:",
        "file:",
        "ftp://",
    )
    if href.startswith(non_relative_prefixes):
        return False

    colon_pos = href.find(":")
    if colon_pos > 0:
        before_colon = href[:colon_pos]
        if (
            before_colon.isascii()
            and before_colon.replace("+", "").replace("-", "").replace(".", "").isalnum()
        ):
            after_colon = href[colon_pos + 1 :]
            if after_colon.startswith("//") or not after_colon[:1].isdigit():
                return False

    return True


@html_element("img")
def Img(
    *,
    src: str,
    alt: str = "",
    width: int | str | None = None,
    height: int | str | None = None,
    loading: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseHandler | None = None,
    on_double_click: MouseHandler | None = None,
    on_context_menu: MouseHandler | None = None,
    data: Mapping[str, DataValue] | None = None,
) -> Element:
    """A generated image element."""
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
    """A generated div element."""
    ...


@html_element("input")
def Input(
    *,
    type: InputType = "text",
    value: str | None = None,
    placeholder: str | None = None,
    disabled: bool = False,
    read_only: bool = False,
    name: str | None = None,
    checked: bool | None = None,
    required: bool = False,
    min: str | int | float | None = None,
    max: str | int | float | None = None,
    step: str | int | float | None = None,
    pattern: str | None = None,
    max_length: int | None = None,
    auto_complete: str | None = None,
    auto_focus: bool = False,
    accept: str | None = None,
    multiple: bool = False,
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
    """A generated input element."""
    ...


@html_element("a", is_container=True, name="A")
def _A(
    *,
    _text: str | None = None,
    href: str | None = None,
    target: str | None = None,
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
    """A generated anchor element."""
    ...


def _make_a(
    text: str | None,
    *,
    href: str | None,
    target: str | None,
    rel: str | None,
    download: str | bool | None,
    class_name: str | None,
    style: Style | None,
    id: str | None,
    on_click: MouseHandler | None,
    on_double_click: MouseHandler | None,
    on_context_menu: MouseHandler | None,
    on_key_down: KeyboardHandler | None,
    on_key_up: KeyboardHandler | None,
    use_router: bool,
    data: Mapping[str, DataValue] | None,
) -> Element:
    """Shared implementation for generated A() overloads."""
    effective_onclick = on_click
    effective_data = dict(data) if data is not None else None
    if (
        href
        and on_click is None
        and use_router
        and target != "_blank"
        and (download is None or download is False)
        and _is_relative_url(href)
    ):
        nav_href = href

        async def router_click(_event: object) -> None:
            await router().navigate(nav_href)

        effective_onclick = router_click
        if effective_data is None:
            effective_data = {}
        effective_data["trellis-router-link"] = "true"

    return _A(
        _text=text,
        href=href,
        target=target,
        rel=rel,
        download=download,
        class_name=class_name,
        style=style,
        id=id,
        on_click=effective_onclick,
        on_double_click=on_double_click,
        on_context_menu=on_context_menu,
        on_key_down=on_key_down,
        on_key_up=on_key_up,
        data=effective_data,
    )


@overload
def A(
    text: str,
    /,
    *,
    href: str | None = None,
    target: str | None = None,
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
    use_router: bool = True,
    data: Mapping[str, DataValue] | None = None,
) -> Element: ...


@overload
def A(
    *,
    href: str | None = None,
    target: str | None = None,
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
    use_router: bool = True,
    data: Mapping[str, DataValue] | None = None,
) -> ContainerElement: ...


def A(
    text: str | None = None,
    /,
    *,
    href: str | None = None,
    target: str | None = None,
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
    use_router: bool = True,
    data: Mapping[str, DataValue] | None = None,
) -> Element | ContainerElement:
    """A generated anchor element with router-aware relative href handling."""
    return _make_a(
        text,
        href=href,
        target=target,
        rel=rel,
        download=download,
        class_name=class_name,
        style=style,
        id=id,
        on_click=on_click,
        on_double_click=on_double_click,
        on_context_menu=on_context_menu,
        on_key_down=on_key_down,
        on_key_up=on_key_up,
        use_router=use_router,
        data=data,
    )
