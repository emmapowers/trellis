"""Table HTML elements.

Elements for creating data tables.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering.element import Element
from trellis.html.base import Style, html_element

__all__ = [
    "Table",
    "Tbody",
    "Td",
    "Th",
    "Thead",
    "Tr",
]


@html_element("table", is_container=True)
def Table(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A table element."""
    ...


@html_element("thead", is_container=True)
def Thead(
    *,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table header section element."""
    ...


@html_element("tbody", is_container=True)
def Tbody(
    *,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table body section element."""
    ...


@html_element("tr", is_container=True)
def Tr(
    *,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table row element."""
    ...


# Hybrid elements need special handling
@html_element("th", is_container=True, name="Th")
def _Th(
    *,
    _text: str | None = None,
    scope: str | None = None,
    colSpan: int | None = None,
    rowSpan: int | None = None,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table header cell element."""
    ...


@html_element("td", is_container=True, name="Td")
def _Td(
    *,
    _text: str | None = None,
    colSpan: int | None = None,
    rowSpan: int | None = None,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table data cell element."""
    ...


def Th(
    text: str = "",
    *,
    scope: str | None = None,
    colSpan: int | None = None,
    rowSpan: int | None = None,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table header cell element.

    Can be used as text-only or as a container:
        h.Th("Column Name")  # Text only
        with h.Th():         # Container with children
            h.Span("Name")
            h.Span("*", style={"color": "red"})
    """
    return _Th(
        _text=text if text else None,
        scope=scope,
        colSpan=colSpan,
        rowSpan=rowSpan,
        className=className,
        style=style,
        **props,
    )


def Td(
    text: str = "",
    *,
    colSpan: int | None = None,
    rowSpan: int | None = None,
    className: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table data cell element.

    Can be used as text-only or as a container:
        h.Td("Cell content")  # Text only
        with h.Td():          # Container with children
            h.Strong("Bold")
            h.Span(" and normal")
    """
    return _Td(
        _text=text if text else None,
        colSpan=colSpan,
        rowSpan=rowSpan,
        className=className,
        style=style,
        **props,
    )
