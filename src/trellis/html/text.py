"""Text HTML elements.

Elements for displaying and formatting text content.
"""

from __future__ import annotations

import typing as tp
from typing import overload

from trellis.core.components.base import Component, ElementKind
from trellis.core.rendering.element import ContainerElement, Element
from trellis.html.base import Style, html_element

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


# Text elements use decorators but need wrappers for positional text args
@html_element("p", is_container=True, name="P")
def _P(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A paragraph element."""
    ...


@html_element("h1", is_container=True, name="H1")
def _H1(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 1 heading."""
    ...


@html_element("h2", is_container=True, name="H2")
def _H2(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 2 heading."""
    ...


@html_element("h3", is_container=True, name="H3")
def _H3(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 3 heading."""
    ...


@html_element("h4", is_container=True, name="H4")
def _H4(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 4 heading."""
    ...


@html_element("h5", is_container=True, name="H5")
def _H5(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 5 heading."""
    ...


@html_element("h6", is_container=True, name="H6")
def _H6(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 6 heading."""
    ...


@html_element("strong", is_container=True, name="Strong")
def _Strong(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A strong (bold) text element."""
    ...


@html_element("em", is_container=True, name="Em")
def _Em(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An emphasis (italic) text element."""
    ...


@html_element("code", is_container=True, name="Code")
def _Code(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An inline code element."""
    ...


@html_element("pre", is_container=True, name="Pre")
def _Pre(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A preformatted text element."""
    ...


# Void elements (no children, no text)
@html_element("br")
def Br(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A line break element."""
    ...


@html_element("hr")
def Hr(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A horizontal rule element."""
    ...


# Additional hybrid text elements
@html_element("small", is_container=True, name="Small")
def _Small(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A small text element."""
    ...


@html_element("mark", is_container=True, name="Mark")
def _Mark(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A marked/highlighted text element."""
    ...


@html_element("sub", is_container=True, name="Sub")
def _Sub(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A subscript text element."""
    ...


@html_element("sup", is_container=True, name="Sup")
def _Sup(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A superscript text element."""
    ...


@html_element("abbr", is_container=True, name="Abbr")
def _Abbr(
    *,
    _text: str | None = None,
    title: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An abbreviation element."""
    ...


@html_element("time", is_container=True, name="Time")
def _Time(
    *,
    _text: str | None = None,
    dateTime: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A time element."""
    ...


# Text node singleton
_text_node = TextNode("Text")


# Public API with positional text parameter support and @overload for hybrid behavior


@overload
def P(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def P(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def P(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A paragraph element."""
    return _P(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def H1(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H1(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def H1(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 1 heading."""
    return _H1(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def H2(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H2(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def H2(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 2 heading."""
    return _H2(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def H3(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H3(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def H3(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 3 heading."""
    return _H3(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def H4(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H4(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def H4(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 4 heading."""
    return _H4(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def H5(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H5(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def H5(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 5 heading."""
    return _H5(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def H6(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def H6(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def H6(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A level 6 heading."""
    return _H6(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Strong(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Strong(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Strong(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A strong (bold) text element."""
    return _Strong(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Em(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Em(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Em(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An emphasis (italic) text element."""
    return _Em(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Code(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Code(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Code(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An inline code element."""
    return _Code(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Pre(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Pre(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Pre(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A preformatted text element."""
    return _Pre(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Small(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Small(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Small(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A small text element."""
    return _Small(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Mark(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Mark(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Mark(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A marked/highlighted text element."""
    return _Mark(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Sub(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Sub(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Sub(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A subscript text element."""
    return _Sub(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Sup(
    text: str,
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Sup(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Sup(
    text: str = "",
    /,
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A superscript text element."""
    return _Sup(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Abbr(
    text: str,
    /,
    *,
    title: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Abbr(
    *,
    title: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Abbr(
    text: str = "",
    /,
    *,
    title: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """An abbreviation element."""
    return _Abbr(
        _text=text if text else None,
        title=title,
        className=className,
        style=style,
        id=id,
        **props,
    )


@overload
def Time(
    text: str,
    /,
    *,
    dateTime: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element: ...


@overload
def Time(
    *,
    dateTime: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> ContainerElement: ...


def Time(
    text: str = "",
    /,
    *,
    dateTime: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    **props: tp.Any,
) -> Element:
    """A time element."""
    return _Time(
        _text=text if text else None,
        dateTime=dateTime,
        className=className,
        style=style,
        id=id,
        **props,
    )


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
