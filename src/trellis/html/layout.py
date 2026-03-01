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
    "Article",
    "Aside",
    "Div",
    "Footer",
    "Header",
    "Main",
    "Nav",
    "Section",
    "Span",
]


@html_element("div", is_container=True)
def Div(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onClick: MouseHandler | None = None,
    onDoubleClick: MouseHandler | None = None,
    onContextMenu: MouseHandler | None = None,
    onMouseEnter: MouseHandler | None = None,
    onMouseLeave: MouseHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    onScroll: ScrollHandler | None = None,
    onWheel: WheelHandler | None = None,
    onDragStart: DragHandler | None = None,
    onDrag: DragHandler | None = None,
    onDragEnd: DragHandler | None = None,
    onDragEnter: DragHandler | None = None,
    onDragOver: DragHandler | None = None,
    onDragLeave: DragHandler | None = None,
    onDrop: DragHandler | None = None,
    **props: tp.Any,
) -> Element:
    """A div container element."""
    ...


@html_element("span", is_container=True, name="Span")
def _Span(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onClick: MouseHandler | None = None,
    onDoubleClick: MouseHandler | None = None,
    onContextMenu: MouseHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    **props: tp.Any,
) -> Element:
    """An inline span element."""
    ...


@overload
def Span(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onClick: MouseHandler | None = None,
    onDoubleClick: MouseHandler | None = None,
    onContextMenu: MouseHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Span(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onClick: MouseHandler | None = None,
    onDoubleClick: MouseHandler | None = None,
    onContextMenu: MouseHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Span(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onClick: MouseHandler | None = None,
    onDoubleClick: MouseHandler | None = None,
    onContextMenu: MouseHandler | None = None,
    onKeyDown: KeyboardHandler | None = None,
    onKeyUp: KeyboardHandler | None = None,
    **props: tp.Any,
) -> Element:
    """An inline span element."""
    return _Span(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        onClick=onClick,
        onDoubleClick=onDoubleClick,
        onContextMenu=onContextMenu,
        onKeyDown=onKeyDown,
        onKeyUp=onKeyUp,
        **props,
    )


@html_element("section", is_container=True)
def Section(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onScroll: ScrollHandler | None = None,
    **props: tp.Any,
) -> Element:
    """A section element for grouping content."""
    ...


@html_element("article", is_container=True)
def Article(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onScroll: ScrollHandler | None = None,
    **props: tp.Any,
) -> Element:
    """An article element for self-contained content."""
    ...


@html_element("header", is_container=True)
def Header(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A header element."""
    ...


@html_element("footer", is_container=True)
def Footer(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A footer element."""
    ...


@html_element("nav", is_container=True)
def Nav(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A navigation element."""
    ...


@html_element("main", is_container=True)
def Main(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onScroll: ScrollHandler | None = None,
    **props: tp.Any,
) -> Element:
    """A main content element."""
    ...


@html_element("aside", is_container=True)
def Aside(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onScroll: ScrollHandler | None = None,
    **props: tp.Any,
) -> Element:
    """An aside element for tangential content."""
    ...
