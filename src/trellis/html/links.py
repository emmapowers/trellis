"""Link and media HTML elements.

Elements for hyperlinks and images.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering.element import ElementNode
from trellis.html.base import Style, html_element
from trellis.html.events import MouseHandler

__all__ = [
    "A",
    "Img",
]


@html_element("img")
def Img(
    *,
    src: str,
    alt: str = "",
    width: int | str | None = None,
    height: int | str | None = None,
    className: str | None = None,
    style: Style | None = None,
    onClick: MouseHandler | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An image element."""
    ...


# Hybrid element needs special handling
@html_element("a", is_container=True, name="A")
def _A(
    *,
    _text: str | None = None,
    href: str | None = None,
    target: str | None = None,
    rel: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    onClick: MouseHandler | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An anchor (link) element."""
    ...


def A(
    text: str = "",
    *,
    href: str | None = None,
    target: str | None = None,
    rel: str | None = None,
    className: str | None = None,
    style: Style | None = None,
    onClick: MouseHandler | None = None,
    key: str | None = None,
    **props: tp.Any,
) -> ElementNode:
    """An anchor (link) element.

    Can be used as text-only or as a container:
        h.A("Click here", href="/path")  # Text only
        with h.A(href="/path"):          # Container with children
            h.Img(src="icon.png")
            h.Span("Link text")
    """
    return _A(
        _text=text if text else None,
        href=href,
        target=target,
        rel=rel,
        className=className,
        style=style,
        onClick=onClick,
        key=key,
        **props,
    )
