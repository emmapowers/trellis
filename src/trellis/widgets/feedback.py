"""Feedback and alert widgets for Trellis.

Provides widgets for displaying feedback, alerts, and collapsible content.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.components.react import react
from trellis.core.state.mutable import Mutable
from trellis.html._style_runtime import SpacingInput, StyleInput, WidthInput

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react("client/Collapsible.tsx", is_container=True)
def Collapsible(
    *,
    title: str = "",
    expanded: bool | Mutable[bool] = True,
    icon: str | None = None,
    padding: SpacingInput | None = None,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Collapsible content section.

    Args:
        title: Section title
        expanded: Whether content is visible. Use mutable(state.prop) for two-way binding.
        icon: Optional icon for the header
        padding: Padding inside the collapsible (CSS padding value).
        margin: Margin around the collapsible (CSS margin value).
        width: Width of the collapsible (CSS width value).
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
    padding: SpacingInput | None = None,
    margin: SpacingInput | None = None,
    width: WidthInput | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: StyleInput | None = None,
) -> None:
    """Prominent status message or alert.

    Args:
        title: Optional title for the callout
        intent: Visual intent/severity
        icon: Optional icon (defaults based on intent if not provided)
        dismissible: Whether to show dismiss button
        on_dismiss: Callback when dismissed
        padding: Padding inside the callout (CSS padding value).
        margin: Margin around the callout (CSS margin value).
        width: Width of the callout (CSS width value).
        flex: Flex grow/shrink value.
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    pass
