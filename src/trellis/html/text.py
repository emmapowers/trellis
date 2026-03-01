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
    "Code",
    "Em",
    "P",
    "Pre",
    "Strong",
    "Text",
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
