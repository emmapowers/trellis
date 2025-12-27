"""Text HTML elements.

Elements for displaying and formatting text content.
"""

from __future__ import annotations

import typing as tp

from trellis.core.component import Component, ElementKind
from trellis.core.element_node import ElementNode
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
    def _has_children_param(self) -> bool:
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

    def render(self, /, **props: tp.Any) -> None:
        """Text nodes are leaf nodes - no rendering needed."""
        pass


# Text elements use decorators but need wrappers for positional text args
@html_element("p", name="P")
def _P(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A paragraph element."""
    ...


@html_element("h1", name="H1")
def _H1(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 1 heading."""
    ...


@html_element("h2", name="H2")
def _H2(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 2 heading."""
    ...


@html_element("h3", name="H3")
def _H3(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 3 heading."""
    ...


@html_element("h4", name="H4")
def _H4(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 4 heading."""
    ...


@html_element("h5", name="H5")
def _H5(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 5 heading."""
    ...


@html_element("h6", name="H6")
def _H6(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 6 heading."""
    ...


@html_element("strong", name="Strong")
def _Strong(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A strong (bold) text element."""
    ...


@html_element("em", name="Em")
def _Em(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An emphasis (italic) text element."""
    ...


@html_element("code", name="Code")
def _Code(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An inline code element."""
    ...


@html_element("pre", name="Pre")
def _Pre(
    *,
    _text: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A preformatted text element."""
    ...


# Text node singleton
_text_node = TextNode("Text")


# Public API with positional text parameter support
def P(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A paragraph element."""
    return _P(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


def H1(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 1 heading."""
    return _H1(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


def H2(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 2 heading."""
    return _H2(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


def H3(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 3 heading."""
    return _H3(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


def H4(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 4 heading."""
    return _H4(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


def H5(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 5 heading."""
    return _H5(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


def H6(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A level 6 heading."""
    return _H6(
        _text=text if text else None,
        className=className,
        style=style,
        id=id,
        key=key,
        **props,
    )


def Strong(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A strong (bold) text element."""
    return _Strong(
        _text=text if text else None,
        className=className,
        style=style,
        key=key,
        **props,
    )


def Em(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An emphasis (italic) text element."""
    return _Em(
        _text=text if text else None,
        className=className,
        style=style,
        key=key,
        **props,
    )


def Code(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An inline code element."""
    return _Code(
        _text=text if text else None,
        className=className,
        style=style,
        key=key,
        **props,
    )


def Pre(
    text: str = "",
    *,
    className: str | None = None,
    style: Style | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """A preformatted text element."""
    return _Pre(
        _text=text if text else None,
        className=className,
        style=style,
        key=key,
        **props,
    )


def Text(
    value: tp.Any,
    *,
    key: str | None = None,
) -> ElementNode:
    """A plain text node without any wrapper element.

    Use this to insert raw text into the DOM without wrapping it
    in a span or other element.

    Args:
        value: Any value to display (will be converted to string)
        key: Optional key for reconciliation
    """
    return _text_node(_text=str(value), key=key)
