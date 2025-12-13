"""Text HTML elements.

Elements for displaying and formatting text content.
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis.core.react_component import ReactComponentBase
from trellis.core.rendering import ElementKind, ElementNode
from trellis.html.base import HtmlElement, Style

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


@dataclass(kw_only=True)
class TextNode(ReactComponentBase):
    """Special component for raw text nodes.

    Unlike HtmlElement which renders as an intrinsic JSX element, TextNode
    renders as a raw text node in React (just a string child).
    """

    @property
    def element_kind(self) -> ElementKind:
        """Text nodes have their own kind for special client handling."""
        return ElementKind.TEXT

    @property
    def element_name(self) -> str:
        """Special marker for text nodes."""
        return "__text__"


# Singleton instances
_p = HtmlElement(_tag="p", name="P")
_h1 = HtmlElement(_tag="h1", name="H1")
_h2 = HtmlElement(_tag="h2", name="H2")
_h3 = HtmlElement(_tag="h3", name="H3")
_h4 = HtmlElement(_tag="h4", name="H4")
_h5 = HtmlElement(_tag="h5", name="H5")
_h6 = HtmlElement(_tag="h6", name="H6")
_strong = HtmlElement(_tag="strong", name="Strong")
_em = HtmlElement(_tag="em", name="Em")
_code = HtmlElement(_tag="code", name="Code")
_pre = HtmlElement(_tag="pre", name="Pre")
_text_node = TextNode(name="Text")


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
    return _p(
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
    return _h1(
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
    return _h2(
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
    return _h3(
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
    return _h4(
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
    return _h5(
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
    return _h6(
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
    return _strong(
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
    return _em(
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
    return _code(
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
    return _pre(
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
