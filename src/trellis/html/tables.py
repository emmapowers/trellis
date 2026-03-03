"""Table HTML elements.

Elements for creating data tables.
"""

from __future__ import annotations

import typing as tp
from typing import overload

from trellis.core.rendering.element import ContainerElement, Element
from trellis.html.base import Style, html_element

__all__ = [
    "Caption",
    "Table",
    "Tbody",
    "Td",
    "Tfoot",
    "Th",
    "Thead",
    "Tr",
]


@html_element("table", is_container=True)
def Table(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A table element."""
    ...


@html_element("thead", is_container=True)
def Thead(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table header section element."""
    ...


@html_element("tbody", is_container=True)
def Tbody(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table body section element."""
    ...


@html_element("tr", is_container=True)
def Tr(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element:
    """A table row element."""
    ...


@overload
def Th(
    text: str,
    /,
    *,
    scope: str | None = None,
    col_span: int | None = None,
    row_span: int | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Th(
    *,
    scope: str | None = None,
    col_span: int | None = None,
    row_span: int | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("th", is_container=True)
def Th(
    text: str | None = None,
    /,
    *,
    scope: str | None = None,
    col_span: int | None = None,
    row_span: int | None = None,
    class_name: str | None = None,
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
    ...


@overload
def Td(
    text: str,
    /,
    *,
    col_span: int | None = None,
    row_span: int | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Td(
    *,
    col_span: int | None = None,
    row_span: int | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("td", is_container=True)
def Td(
    text: str | None = None,
    /,
    *,
    col_span: int | None = None,
    row_span: int | None = None,
    class_name: str | None = None,
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
    ...


@html_element("tfoot", is_container=True)
def Tfoot(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A table footer section element."""
    ...


@overload
def Caption(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Caption(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


@html_element("caption", is_container=True)
def Caption(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A table caption element."""
    ...
