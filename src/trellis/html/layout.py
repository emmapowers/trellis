"""Layout HTML elements.

Container elements for structuring page content.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering import ElementNode
from trellis.html.base import HtmlElement, Style
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

# Singleton instances
_div = HtmlElement(_tag="div", name="Div", _is_container=True)
_span = HtmlElement(_tag="span", name="Span")  # Inline, usually has text
_section = HtmlElement(_tag="section", name="Section", _is_container=True)
_article = HtmlElement(_tag="article", name="Article", _is_container=True)
_header = HtmlElement(_tag="header", name="Header", _is_container=True)
_footer = HtmlElement(_tag="footer", name="Footer", _is_container=True)
_nav = HtmlElement(_tag="nav", name="Nav", _is_container=True)
_main = HtmlElement(_tag="main", name="Main", _is_container=True)
_aside = HtmlElement(_tag="aside", name="Aside", _is_container=True)


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
    return _div(
        className=className,
        style=style,
        id=id,
        onClick=onClick,
        onMouseEnter=onMouseEnter,
        onMouseLeave=onMouseLeave,
        key=key,
        **props,
    )


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
    return _span(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        onClick=onClick,
        key=key,
        **props,
    )


def Section(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A section element for grouping content."""
    return _section(className=className, style=style, id=id, key=key, **props)


def Article(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An article element for self-contained content."""
    return _article(className=className, style=style, id=id, key=key, **props)


def Header(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A header element."""
    return _header(className=className, style=style, id=id, key=key, **props)


def Footer(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A footer element."""
    return _footer(className=className, style=style, id=id, key=key, **props)


def Nav(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A navigation element."""
    return _nav(className=className, style=style, id=id, key=key, **props)


def Main(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A main content element."""
    return _main(className=className, style=style, id=id, key=key, **props)


def Aside(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An aside element for tangential content."""
    return _aside(className=className, style=style, id=id, key=key, **props)
