"""List HTML elements.

Elements for creating ordered and unordered lists.
"""

from __future__ import annotations

import typing as tp
from typing import overload

from trellis.core.rendering.element import ContainerElement, Element
from trellis.html.base import Style, html_element

__all__ = [
    "Dd",
    "Dl",
    "Dt",
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
    reversed: bool = False,
    type: str | None = None,
    **props: tp.Any,
) -> Element:
    """An ordered list element."""
    ...


@overload
def Li(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Li(
    *,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("li", is_container=True)
def Li(
    text: str | None = None,
    /,
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
    ...


# Definition list elements


@html_element("dl", is_container=True)
def Dl(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A description list element."""
    ...


@overload
def Dt(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Dt(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("dt", is_container=True)
def Dt(
    text: str | None = None,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A description term element."""
    ...


@overload
def Dd(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Dd(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("dd", is_container=True)
def Dd(
    text: str | None = None,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A description details element."""
    ...
