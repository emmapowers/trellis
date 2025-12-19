"""Feedback and alert widgets for Trellis.

Provides widgets for displaying feedback, alerts, and collapsible content.
"""

from __future__ import annotations

import typing as tp
from typing import Literal

from trellis.core.mutable import Mutable
from trellis.core.react_component import react_component_base
from trellis.core.rendering import ElementNode

if tp.TYPE_CHECKING:
    from collections.abc import Callable


@react_component_base("Collapsible", has_children=True)
def Collapsible(
    *,
    title: str = "",
    expanded: bool | Mutable[bool] = True,
    icon: str | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Collapsible content section.

    Args:
        title: Section title
        expanded: Whether content is visible. Use mutable(state.prop) for two-way binding.
        icon: Optional icon for the header
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...


@react_component_base("Callout", has_children=True)
def Callout(
    *,
    title: str | None = None,
    intent: Literal["info", "success", "warning", "error"] = "info",
    icon: str | None = None,
    dismissible: bool = False,
    on_dismiss: Callable[[], None] | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Prominent status message or alert.

    Args:
        title: Optional title for the callout
        intent: Visual intent/severity
        icon: Optional icon (defaults based on intent if not provided)
        dismissible: Whether to show dismiss button
        on_dismiss: Callback when dismissed
        class_name: Additional CSS classes
        style: Inline styles
        key: Unique key for reconciliation
    """
    ...
