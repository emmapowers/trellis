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


# New structural elements


@html_element("blockquote", is_container=True, name="Blockquote")
def _Blockquote(
    *,
    _text: str | None = None,
    cite: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A blockquote element."""
    ...


@overload
def Blockquote(
    text: str,
    /,
    *,
    cite: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Blockquote(
    *,
    cite: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Blockquote(
    text: str = "",
    /,
    *,
    cite: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A blockquote element."""
    return _Blockquote(
        _text=text if text else None,
        cite=cite,
        className=className,
        style=style,
        id=id,
        **props,
    )


@html_element("address", is_container=True)
def Address(
    *,
    className: str | None = None,
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
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A details disclosure element."""
    ...


@html_element("summary", is_container=True, name="Summary")
def _Summary(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A summary element for use within Details."""
    ...


@overload
def Summary(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Summary(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Summary(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A summary element for use within Details."""
    return _Summary(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@html_element("figure", is_container=True)
def Figure(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A figure element for self-contained content."""
    ...


@html_element("figcaption", is_container=True, name="Figcaption")
def _Figcaption(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A figcaption element."""
    ...


@overload
def Figcaption(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Figcaption(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Figcaption(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A figcaption element."""
    return _Figcaption(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )
