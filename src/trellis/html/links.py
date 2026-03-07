"""Link and media HTML elements.

Elements for hyperlinks and images.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, overload

from trellis.core.rendering.element import Element
from trellis.html._generated_runtime import _A, Img
from trellis.html.base import HtmlContainerElement, Style
from trellis.html.events import KeyboardEventHandler, MouseEventHandler
from trellis.routing.state import router

__all__ = [
    "A",
    "Img",
]

DataValue = str | int | float | bool | None
AnchorTarget = Literal["_self", "_blank", "_parent", "_top"]


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
    # Protocol-relative, fragment-only, and query-only URLs bypass the router.
    if href.startswith(("//", "#", "?")):
        return False

    # Explicit schemes bypass the router. We check a known set rather than using
    # urlparse because urlparse treats any "word:rest" as a scheme (e.g.
    # "localhost:3000" parses as scheme="localhost").
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
    if href.startswith(_NON_RELATIVE_PREFIXES):
        return False

    # Catch any other URI scheme pattern (e.g. "tauri://...", "custom:...")
    # by checking for "word:" where the word contains only valid scheme chars.
    colon_pos = href.find(":")
    if colon_pos > 0:
        before_colon = href[:colon_pos]
        if (
            before_colon.isascii()
            and before_colon.replace("+", "").replace("-", "").replace(".", "").isalnum()
        ):
            # Looks like a URI scheme — but exclude port-like patterns (e.g. "localhost:3000")
            after_colon = href[colon_pos + 1 :]
            if after_colon.startswith("//") or not after_colon[:1].isdigit():
                return False

    return True


def _make_a(
    internal_text: str | None,
    *,
    href: str | None,
    target: AnchorTarget | None,
    rel: str | None,
    download: str | bool | None,
    class_name: str | None,
    style: Style | None,
    id: str | None,
    on_click: MouseEventHandler | None,
    on_double_click: MouseEventHandler | None,
    on_context_menu: MouseEventHandler | None,
    on_key_down: KeyboardEventHandler | None,
    on_key_up: KeyboardEventHandler | None,
    use_router: bool,
    data: Mapping[str, DataValue] | None,
) -> Element:
    """Shared implementation for A() overloads."""
    # For relative URLs without custom on_click, add router navigation
    effective_onclick = on_click
    effective_data = dict(data) if data is not None else None
    if (
        href
        and on_click is None
        and use_router
        and target != "_blank"
        and (download is None or download is False)
        and _is_relative_url(href)
    ):
        # Capture href in closure for the async callback
        nav_href = href

        async def router_click(_event: object) -> None:
            await router().navigate(nav_href)

        effective_onclick = router_click
        if effective_data is None:
            effective_data = {}
        effective_data["trellis-router-link"] = "true"

    if internal_text is None:
        return _A(
            href=href,
            target=target,
            rel=rel,
            download=download,
            class_name=class_name,
            style=style,
            id=id,
            on_click=effective_onclick,
            on_double_click=on_double_click,
            on_context_menu=on_context_menu,
            on_key_down=on_key_down,
            on_key_up=on_key_up,
            data=effective_data,
        )
    return _A(
        internal_text,
        href=href,
        target=target,
        rel=rel,
        download=download,
        class_name=class_name,
        style=style,
        id=id,
        on_click=effective_onclick,
        on_double_click=on_double_click,
        on_context_menu=on_context_menu,
        on_key_down=on_key_down,
        on_key_up=on_key_up,
        data=effective_data,
    )


@overload
def A(
    internal_text: str,
    /,
    *,
    href: str | None = None,
    target: AnchorTarget | None = None,
    rel: str | None = None,
    download: str | bool | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    use_router: bool = True,
    data: Mapping[str, DataValue] | None = None,
) -> Element: ...


@overload
def A(
    *,
    href: str | None = None,
    target: AnchorTarget | None = None,
    rel: str | None = None,
    download: str | bool | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    use_router: bool = True,
    data: Mapping[str, DataValue] | None = None,
) -> HtmlContainerElement: ...


def A(
    internal_text: str | None = None,
    /,
    *,
    href: str | None = None,
    target: AnchorTarget | None = None,
    rel: str | None = None,
    download: str | bool | None = None,
    class_name: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    on_click: MouseEventHandler | None = None,
    on_double_click: MouseEventHandler | None = None,
    on_context_menu: MouseEventHandler | None = None,
    on_key_down: KeyboardEventHandler | None = None,
    on_key_up: KeyboardEventHandler | None = None,
    use_router: bool = True,
    data: Mapping[str, DataValue] | None = None,
) -> Element | HtmlContainerElement:
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
        internal_text: Text content for the link
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
    return _make_a(
        internal_text,
        href=href,
        target=target,
        rel=rel,
        download=download,
        class_name=class_name,
        style=style,
        id=id,
        on_click=on_click,
        on_double_click=on_double_click,
        on_context_menu=on_context_menu,
        on_key_down=on_key_down,
        on_key_up=on_key_up,
        use_router=use_router,
        data=data,
    )
