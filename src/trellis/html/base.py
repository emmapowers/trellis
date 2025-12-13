"""Base classes and helpers for HTML elements.

This module provides the HtmlElement class that powers all native HTML
element wrappers, plus helper functions for hybrid element behavior.
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass, field

from trellis.core.react_component import ReactComponentBase
from trellis.core.rendering import ElementKind, ElementNode, get_active_render_tree

__all__ = [
    "HtmlElement",
    "Style",
    "auto_collect_hybrid",
]

# Type alias for inline styles
Style = dict[str, str | int | float]


@dataclass(kw_only=True)
class HtmlElement(ReactComponentBase):
    """Base class for native HTML elements.

    Unlike regular ReactComponentBase which maps to custom React components,
    HtmlElement returns JSX_ELEMENT kind and the HTML tag name as its element_name,
    causing React to render it as a native DOM element.

    Attributes:
        _tag: The HTML tag name (e.g., "div", "span")
        _is_container: Whether this element can contain children via `with` block
    """

    _tag: str = field(default="div", repr=False)
    _is_container: bool = field(default=False, repr=False)

    # Class-level default - overridden by instance property
    _has_children: tp.ClassVar[bool] = False

    @property
    def _has_children_param(self) -> bool:
        """Whether this specific instance accepts children via with block."""
        return self._is_container

    @property
    def element_kind(self) -> ElementKind:
        """HTML elements are JSX intrinsic elements."""
        return ElementKind.JSX_ELEMENT

    @property
    def element_name(self) -> str:
        """Return the HTML tag name for native DOM rendering."""
        return self._tag


def auto_collect_hybrid(descriptor: ElementNode) -> ElementNode:
    """Auto-collect a hybrid element descriptor when text is provided.

    Hybrid elements (like Td, Li, A) can work either as:
    - Text-only: h.Td("text") - auto-collected
    - Container: with h.Td(): ... - collected via with block

    This helper enables auto-collection for containers when text is provided.

    Args:
        descriptor: The element descriptor to auto-collect

    Returns:
        The same descriptor, for chaining
    """
    ctx = get_active_render_tree()
    if ctx is not None and ctx.has_active_frame():
        ctx.add_to_current_frame(descriptor)
        object.__setattr__(descriptor, "_auto_collected", True)
    return descriptor
