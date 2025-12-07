"""Table HTML elements.

Elements for creating data tables.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering import ElementDescriptor
from trellis.html.base import HtmlElement, Style, auto_collect_hybrid

__all__ = [
    "Table",
    "Tbody",
    "Td",
    "Th",
    "Thead",
    "Tr",
]

# Singleton instances
_table = HtmlElement(_tag="table", name="Table", _is_container=True)
_thead = HtmlElement(_tag="thead", name="Thead", _is_container=True)
_tbody = HtmlElement(_tag="tbody", name="Tbody", _is_container=True)
_tr = HtmlElement(_tag="tr", name="Tr", _is_container=True)
_th = HtmlElement(_tag="th", name="Th", _is_container=True)  # Hybrid: text or children
_td = HtmlElement(_tag="td", name="Td", _is_container=True)  # Hybrid: text or children


def Table(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementDescriptor:
    """A table element."""
    return _table(className=className, style=style, id=id, key=key, **props)


def Thead(
    *,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementDescriptor:
    """A table header section element."""
    return _thead(className=className, style=style, key=key, **props)


def Tbody(
    *,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementDescriptor:
    """A table body section element."""
    return _tbody(className=className, style=style, key=key, **props)


def Tr(
    *,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementDescriptor:
    """A table row element."""
    return _tr(className=className, style=style, key=key, **props)


def Th(
    text: str = "",
    *,
    scope: str | None = None,
    colSpan: int | None = None,
    rowSpan: int | None = None,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementDescriptor:
    """A table header cell element.

    Can be used as text-only or as a container:
        h.Th("Column Name")  # Text only
        with h.Th():         # Container with children
            h.Span("Name")
            h.Span("*", style={"color": "red"})
    """
    desc = _th(
        _text=text if text else None,
        scope=scope,
        colSpan=colSpan,
        rowSpan=rowSpan,
        className=className,
        style=style,
        key=key,
        **props,
    )
    if text:
        auto_collect_hybrid(desc)
    return desc


def Td(
    text: str = "",
    *,
    colSpan: int | None = None,
    rowSpan: int | None = None,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementDescriptor:
    """A table data cell element.

    Can be used as text-only or as a container:
        h.Td("Cell content")  # Text only
        with h.Td():          # Container with children
            h.Strong("Bold")
            h.Span(" and normal")
    """
    desc = _td(
        _text=text if text else None,
        colSpan=colSpan,
        rowSpan=rowSpan,
        className=className,
        style=style,
        key=key,
        **props,
    )
    if text:
        auto_collect_hybrid(desc)
    return desc
