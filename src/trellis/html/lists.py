"""List HTML elements.

Elements for creating ordered and unordered lists.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering.element import Element
from trellis.html.base import Style, html_element

__all__ = [
    "Li",
    "Ol",
    "Ul",
]


@html_element("ul", is_container=True)
def Ul(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An unordered list element."""
    ...


@html_element("ol", is_container=True)
def Ol(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    start: int | None = None,
    **props: tp.Any,
) -> Element:
    """An ordered list element."""
    ...


# Hybrid element needs special handling
@html_element("li", is_container=True, name="Li")
def _Li(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A list item element."""
    ...


def Li(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A list item element.

    Can be used as text-only or as a container:
        h.Li("Simple text")  # Text only
        with h.Li():         # Container with children
            h.Strong("Bold")
    """
    return _Li(
        _text=text if text else None,
        className=className,
        style=style,
        **props,
    )
