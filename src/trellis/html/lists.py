"""List HTML elements.

Elements for creating ordered and unordered lists.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering import ElementDescriptor
from trellis.html.base import HtmlElement, Style, auto_collect_hybrid

__all__ = [
    "Li",
    "Ol",
    "Ul",
]

# Singleton instances
_ul = HtmlElement(_tag="ul", name="Ul", _is_container=True)
_ol = HtmlElement(_tag="ol", name="Ol", _is_container=True)
_li = HtmlElement(_tag="li", name="Li", _is_container=True)  # Hybrid: text or children


def Ul(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementDescriptor:
    """An unordered list element."""
    return _ul(className=className, style=style, id=id, key=key, **props)


def Ol(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    start: int | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementDescriptor:
    """An ordered list element."""
    return _ol(className=className, style=style, id=id, start=start, key=key, **props)


def Li(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementDescriptor:
    """A list item element.

    Can be used as text-only or as a container:
        h.Li("Simple text")  # Text only
        with h.Li():         # Container with children
            h.Strong("Bold")
    """
    desc = _li(
        _text=text if text else None,
        className=className,
        style=style,
        key=key,
        **props,
    )
    if text:
        auto_collect_hybrid(desc)
    return desc
