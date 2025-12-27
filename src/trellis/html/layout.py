"""Layout HTML elements.

Container elements for structuring page content.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering.element import ElementNode
from trellis.html.base import Style, html_element
from trellis.html.events import MouseHandler

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
    onMouseEnter: MouseHandler | None = None,
    onMouseLeave: MouseHandler | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A div container element."""
    ...


@html_element("span", name="Span")
def _Span(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onClick: MouseHandler | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An inline span element."""
    ...


def Span(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    onClick: MouseHandler | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An inline span element."""
    return _Span(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        onClick=onClick,
        key=key,
        **props,
    )


@html_element("section", is_container=True)
def Section(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A section element for grouping content."""
    ...


@html_element("article", is_container=True)
def Article(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An article element for self-contained content."""
    ...


@html_element("header", is_container=True)
def Header(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A header element."""
    ...


@html_element("footer", is_container=True)
def Footer(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A footer element."""
    ...


@html_element("nav", is_container=True)
def Nav(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A navigation element."""
    ...


@html_element("main", is_container=True)
def Main(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A main content element."""
    ...


@html_element("aside", is_container=True)
def Aside(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An aside element for tangential content."""
    ...
