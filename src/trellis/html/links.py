"""Handwritten public wrappers for link-oriented HTML elements.

This module holds Trellis-specific behavior that intentionally sits on top of
the generated HTML bindings, primarily router-aware anchors.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from trellis.core.rendering.element import Element
from trellis.html._generated_runtime import Img
from trellis.html._generated_runtime import _A
from trellis.routing.state import router

__all__ = [
    "A",
    "Img",
]

DataValue = str | int | float | bool | None

# Schemes that always bypass the client-side router. We check a known set
# rather than using urlparse because urlparse treats any "word:rest" as a
# scheme (e.g. "localhost:3000" parses as scheme="localhost").
_NON_RELATIVE_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "javascript:",
    "data:",
    "file:",
    "ftp://",
)


def _has_uri_scheme(href: str) -> bool:
    """Detect arbitrary URI schemes (e.g. ``tauri://``, ``custom:``)."""
    colon_pos = href.find(":")
    if colon_pos <= 0:
        return False
    before_colon = href[:colon_pos]
    if not (
        before_colon.isascii()
        and before_colon.replace("+", "").replace("-", "").replace(".", "").isalnum()
    ):
        return False
    after_colon = href[colon_pos + 1 :]
    return after_colon.startswith("//") or not after_colon[:1].isdigit()


def _is_relative_url(href: str) -> bool:
    """Check if a URL is relative (no host/protocol)."""
    if href.startswith(("//", "#", "?")):
        return False
    if href.startswith(_NON_RELATIVE_PREFIXES):
        return False
    if _has_uri_scheme(href):
        return False
    return True


def _resolve_router_navigation(
    props: dict[str, object],
    use_router: bool,
) -> None:
    """Conditionally inject router navigation into *props*."""
    href = props.get("href")
    if not (
        href
        and props.get("on_click") is None
        and use_router
        and props.get("target") != "_blank"
        and (props.get("download") is None or props.get("download") is False)
        and _is_relative_url(str(href))
    ):
        return

    nav_href = str(href)

    async def router_click(_event: object) -> None:
        await router().navigate(nav_href)

    props["on_click"] = router_click

    existing_data = props.get("data")
    existing_mapping = existing_data if isinstance(existing_data, Mapping) else None
    effective_data: dict[str, DataValue] = (
        dict(existing_mapping) if existing_mapping is not None else {}
    )
    effective_data["trellis-router-link"] = "true"
    props["data"] = effective_data


def A(
    inner_text: object | None = None,
    /,
    *,
    use_router: bool = True,
    **kwargs: object,
) -> Element:
    """Render an anchor element.

    Wraps the standard HTML ``<a>`` element and adds Trellis router navigation
    for relative links by default. Absolute URLs, fragment links, and special
    schemes use normal browser navigation.

    Can be used as text-only or as a container:
        h.A("Click here", href="/path")  # Text only
        with h.A(href="/path"):          # Container with children
            h.Img(src="icon.png")
            h.Span("Link text")

    Args:
        inner_text: Text content for the link
        href: URL to navigate to. Relative URLs use router, absolute use browser.
        target: Target window/frame (e.g., "_blank")
        rel: Relationship to linked document (e.g., "noopener")
        class_name: CSS class name
        style: Inline styles
        on_click: Custom click handler (overrides auto-routing for relative URLs)
        use_router: Whether to use client-side router for relative URLs (default True).
            Set to False to force browser navigation for relative URLs.
        data: Custom data-* attributes keyed by DOM suffix (e.g. ``{"test-id": "x"}``)
    """
    props: dict[str, object] = dict(kwargs)
    _resolve_router_navigation(props, use_router)

    if inner_text is None:
        return _A(**props)
    return _A(inner_text, **props)
