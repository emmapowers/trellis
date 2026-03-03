"""Layout HTML elements.

Container elements for structuring page content.
"""

from __future__ import annotations

import typing as tp
from typing import overload

from trellis.core.rendering.element import ContainerElement, Element
from trellis.html.base import Style, html_element
from trellis.html.events import (
    DragHandler,
    KeyboardHandler,
    MouseHandler,
    ScrollHandler,
    WheelHandler,
)

__all__ = [
    "Address",
    "Article",
    "Aside",
    "Blockquote",
    "Details",
    "Div",
    "Figcaption",
    "Figure",
    "Footer",
    "Header",
    "Main",
    "Nav",
    "Section",
    "Span",
    "Summary",
]


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
    **props: tp.Any,
) -> Element:
    """A div container element."""
    ...


@overload
def Span(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseHandler | None = None,
    on_double_click: MouseHandler | None = None,
    on_context_menu: MouseHandler | None = None,
    on_key_down: KeyboardHandler | None = None,
    on_key_up: KeyboardHandler | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Span(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseHandler | None = None,
    on_double_click: MouseHandler | None = None,
    on_context_menu: MouseHandler | None = None,
    on_key_down: KeyboardHandler | None = None,
    on_key_up: KeyboardHandler | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("span", is_container=True)
def Span(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseHandler | None = None,
    on_double_click: MouseHandler | None = None,
    on_context_menu: MouseHandler | None = None,
    on_key_down: KeyboardHandler | None = None,
    on_key_up: KeyboardHandler | None = None,
    **props: tp.Any,
) -> Element:
    """An inline span element."""
    ...


@html_element("section", is_container=True)
def Section(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_scroll: ScrollHandler | None = None,
    **props: tp.Any,
) -> Element:
    """A section element for grouping content."""
    ...


@html_element("article", is_container=True)
def Article(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_scroll: ScrollHandler | None = None,
    **props: tp.Any,
) -> Element:
    """An article element for self-contained content."""
    ...


@html_element("header", is_container=True)
def Header(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A header element."""
    ...


@html_element("footer", is_container=True)
def Footer(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A footer element."""
    ...


@html_element("nav", is_container=True)
def Nav(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A navigation element."""
    ...


@html_element("main", is_container=True)
def Main(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_scroll: ScrollHandler | None = None,
    **props: tp.Any,
) -> Element:
    """A main content element."""
    ...


@html_element("aside", is_container=True)
def Aside(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_scroll: ScrollHandler | None = None,
    **props: tp.Any,
) -> Element:
    """An aside element for tangential content."""
    ...


# Structural elements


@overload
def Blockquote(
    text: str,
    /,
    *,
    cite: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Blockquote(
    *,
    cite: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("blockquote", is_container=True)
def Blockquote(
    text: str | None = None,
    /,
    *,
    cite: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A blockquote element."""
    ...


@html_element("address", is_container=True)
def Address(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An address element for contact information."""
    ...


@html_element("details", is_container=True)
def Details(
    *,
    open: bool = False,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A details disclosure element."""
    ...


@overload
def Summary(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Summary(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("summary", is_container=True)
def Summary(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A summary element for use within Details."""
    ...


@html_element("figure", is_container=True)
def Figure(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A figure element for self-contained content."""
    ...


@overload
def Figcaption(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Figcaption(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("figcaption", is_container=True)
def Figcaption(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A figcaption element."""
    ...
