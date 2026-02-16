"""Markdown widget."""

from __future__ import annotations

from trellis.core.components.react import react
from trellis.core.components.style_props import Margin, Width

_MARKDOWN_PACKAGES = {
    "dompurify": "3.3.0",
    "markdown-it": "14.1.0",
}


@react("client/Markdown.tsx", packages=_MARKDOWN_PACKAGES)
def Markdown(
    content: str = "",
    *,
    base_path: str | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    class_name: str | None = None,
    style: dict[str, object] | None = None,
) -> None:
    """Render markdown content in an isolated shadow DOM container.

    Args:
        content: Markdown source to render.
        base_path: Optional local path allowlist root for local resources.
        margin: Margin around the widget.
        width: Width of the widget.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
    """
    pass
