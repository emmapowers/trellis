"""Text HTML elements.

Elements for displaying and formatting text content.
"""

from __future__ import annotations

import typing as tp
from typing import overload

from trellis.core.components.base import Component, ElementKind
from trellis.core.rendering.element import Element
from trellis.html.base import HtmlContainerElement, Style, html_element

__all__ = [
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "Abbr",
    "Br",
    "Code",
    "Em",
    "Hr",
    "Mark",
    "P",
    "Pre",
    "Small",
    "Strong",
    "Sub",
    "Sup",
    "Text",
    "Time",
]


class TextNode(Component):
    """Special component for raw text nodes.

    Unlike HtmlElement which renders as an intrinsic JSX element, TextNode
    renders as a raw text node in React (just a string child).

    TextNode extends Component directly (like HtmlElement) but with
    a special element_kind for text handling.
    """

    @property
    def is_container(self) -> bool:
        """Text nodes don't accept children."""
        return False

    @property
    def element_kind(self) -> ElementKind:
        """Text nodes have their own kind for special client handling."""
        return ElementKind.TEXT

    @property
    def element_name(self) -> str:
        """Special marker for text nodes."""
        return "__text__"

    def execute(self, /, **props: tp.Any) -> None:
        """Text nodes are leaf nodes - no rendering needed."""
        pass


# Void elements (no children, no text)
@html_element("br")
def Br(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A line break element."""
    ...


@html_element("hr")
def Hr(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A horizontal rule element."""
    ...


# Text node singleton
_text_node = TextNode("Text")


# Public API with positional text parameter support and @overload for hybrid behavior


@overload
def P(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def P(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("p", is_container=True)
def P(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A paragraph element."""
    ...


@overload
def H1(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H1(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("h1", is_container=True)
def H1(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 1 heading."""
    ...


@overload
def H2(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H2(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("h2", is_container=True)
def H2(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 2 heading."""
    ...


@overload
def H3(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H3(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("h3", is_container=True)
def H3(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 3 heading."""
    ...


@overload
def H4(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H4(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("h4", is_container=True)
def H4(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 4 heading."""
    ...


@overload
def H5(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H5(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("h5", is_container=True)
def H5(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 5 heading."""
    ...


@overload
def H6(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H6(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("h6", is_container=True)
def H6(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 6 heading."""
    ...


@overload
def Strong(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Strong(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("strong", is_container=True)
def Strong(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A strong (bold) text element."""
    ...


@overload
def Em(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Em(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("em", is_container=True)
def Em(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An emphasis (italic) text element."""
    ...


@overload
def Code(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Code(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("code", is_container=True)
def Code(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An inline code element."""
    ...


@overload
def Pre(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Pre(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("pre", is_container=True)
def Pre(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A preformatted text element."""
    ...


@overload
def Small(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Small(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("small", is_container=True)
def Small(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A small text element."""
    ...


@overload
def Mark(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Mark(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("mark", is_container=True)
def Mark(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A marked/highlighted text element."""
    ...


@overload
def Sub(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Sub(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("sub", is_container=True)
def Sub(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A subscript text element."""
    ...


@overload
def Sup(
    text: str,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Sup(
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("sup", is_container=True)
def Sup(
    text: str | None = None,
    /,
    *,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A superscript text element."""
    ...


@overload
def Abbr(
    text: str,
    /,
    *,
    title: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Abbr(
    *,
    title: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("abbr", is_container=True)
def Abbr(
    text: str | None = None,
    /,
    *,
    title: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An abbreviation element."""
    ...


@overload
def Time(
    text: str,
    /,
    *,
    date_time: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Time(
    *,
    date_time: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> HtmlContainerElement: ...


@html_element("time", is_container=True)
def Time(
    text: str | None = None,
    /,
    *,
    date_time: str | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A time element."""
    ...


def Text(
    value: tp.Any,
) -> Element:
    """A plain text node without any wrapper element.

    Use this to insert raw text into the DOM without wrapping it
    in a span or other element.

    Args:
        value: Any value to display (will be converted to string)
    """
    return _text_node(_text=str(value))
