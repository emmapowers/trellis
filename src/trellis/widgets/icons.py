"""Icon widget for rendering Lucide icons."""

from __future__ import annotations

import typing as tp

from trellis.core.react_component import react_component_base
from trellis.core.rendering import ElementNode
from trellis.icons import IconName


@react_component_base("Icon")
def Icon(
    name: IconName | str,
    *,
    size: int = 16,
    color: str | None = None,
    stroke_width: float = 2,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Render a Lucide icon.

    Args:
        name: Icon name from IconName enum or string (e.g., IconName.CHECK or "check").
        size: Icon size in pixels. Defaults to 16.
        color: Icon color (CSS color string). Defaults to theme text color.
        stroke_width: Stroke width for the icon. Defaults to 2.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Icon component.

    Example:
        from trellis.icons import IconName

        Icon(name=IconName.CHECK, size=24, color="green")
        Icon(name=IconName.ALERT_TRIANGLE, color="#d97706")
    """
    ...
