"""Link and media HTML elements.

Elements for hyperlinks and images.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering.element import Element
from trellis.html.base import Style, html_element
from trellis.html.events import MouseHandler
from trellis.routing.state import router

__all__ = [
    "A",
    "Img",
]


def _is_relative_url(href: str) -> bool:
    """Check if a URL is relative (no host/protocol).

    Relative URLs should use client-side router navigation.
    Absolute URLs (http://, https://, //) and special schemes (mailto:, tel:, etc.)
    should use browser navigation.

    Fragment-only (#section) and query-only (?foo=bar) URLs also bypass the router
    since they modify the current page rather than navigating to a new route.

    Args:
        href: The URL to check

    Returns:
        True if the URL is relative (should use router), False if absolute or special scheme
    """
    # Absolute URLs, protocol-relative URLs, and special schemes should bypass router
    if href.startswith(
        (
            "http://",
            "https://",
            "//",
            "mailto:",
            "tel:",
            "javascript:",
            "data:",
            "file:",
            "#",  # Fragment-only: scroll to element
            "?",  # Query-only: modify query params on current page
        )
    ):
        return False
    return True


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
    **props: tp.Any,
) -> Element:
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
    **props: tp.Any,
) -> Element:
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
    use_router: bool = True,
    **props: tp.Any,
) -> Element:
    """An anchor (link) element.

    For relative URLs (paths without http://, https://, or //), automatically
    uses client-side router navigation instead of full page reload. This
    enables SPA-style navigation when used within a RouterState context.

    For absolute URLs, uses normal browser navigation.

    Can be used as text-only or as a container:
        h.A("Click here", href="/path")  # Text only
        with h.A(href="/path"):          # Container with children
            h.Img(src="icon.png")
            h.Span("Link text")

    Args:
        text: Text content for the link
        href: URL to navigate to. Relative URLs use router, absolute use browser.
        target: Target window/frame (e.g., "_blank")
        rel: Relationship to linked document (e.g., "noopener")
        className: CSS class name
        style: Inline styles
        onClick: Custom click handler (overrides auto-routing for relative URLs)
        use_router: Whether to use client-side router for relative URLs (default True).
            Set to False to force browser navigation for relative URLs.
        **props: Additional HTML attributes
    """
    # For relative URLs without custom onClick, add router navigation
    effective_onclick = onClick
    if href and onClick is None and use_router and target != "_blank" and _is_relative_url(href):
        # Capture href in closure for the async callback
        nav_href = href

        async def router_click(_event: object) -> None:
            await router().navigate(nav_href)

        effective_onclick = router_click

    return _A(
        _text=text if text else None,
        href=href,
        target=target,
        rel=rel,
        className=className,
        style=style,
        onClick=effective_onclick,
        **props,
    )
