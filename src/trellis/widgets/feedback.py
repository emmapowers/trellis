"""Feedback and alert widgets for Trellis.

Provides widgets for displaying feedback, alerts, and collapsible content.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.components.react import react
from trellis.core.components.style_props import Margin, Padding, Width
from trellis.core.state.mutable import Mutable

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react("client/Collapsible.tsx", is_container=True)
def Collapsible(
    *,
    title: str = "",
    expanded: bool | Mutable[bool] = True,
    icon: str | None = None,
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
    """Collapsible content section.

    Args:
        title: Section title
        expanded: Whether content is visible. Use mutable(state.prop) for two-way binding.
        icon: Optional icon for the header
        padding: Padding inside the collapsible (Padding dataclass or int for all sides).
        margin: Margin around the collapsible (Margin dataclass).
        width: Width of the collapsible (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    pass


@react("client/Callout.tsx", is_container=True)
def Callout(
    *,
    title: str | None = None,
    intent: Literal["info", "success", "warning", "error"] = "info",
    icon: str | None = None,
    dismissible: bool = False,
    on_dismiss: Callable[[], None] | None = None,
    padding: Padding | int | None = None,
    margin: Margin | None = None,
    width: Width | int | str | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
) -> None:
    """Prominent status message or alert.

    Args:
        title: Optional title for the callout
        intent: Visual intent/severity
        icon: Optional icon (defaults based on intent if not provided)
        dismissible: Whether to show dismiss button
        on_dismiss: Callback when dismissed
        padding: Padding inside the callout (Padding dataclass or int for all sides).
        margin: Margin around the callout (Margin dataclass).
        width: Width of the callout (Width dataclass, int for pixels, or str for CSS).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    pass
