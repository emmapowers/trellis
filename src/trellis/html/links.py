"""Link and media HTML elements.

Elements for hyperlinks and images.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering import ElementNode
from trellis.html.base import HtmlElement, Style, auto_collect_hybrid
from trellis.html.events import MouseHandler

__all__ = [
    "A",
    "Img",
]

# Singleton instances
_a = HtmlElement(_tag="a", name="A", _is_container=True)  # Hybrid: text or children
_img = HtmlElement(_tag="img", name="Img")


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
    desc = _a(
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
    if text:
        auto_collect_hybrid(desc)
    return desc


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
    return _img(
        src=src,
        alt=alt,
        width=width,
        height=height,
        className=className,
        style=style,
        onClick=onClick,
        key=key,
        **props,
    )
