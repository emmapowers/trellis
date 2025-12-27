"""Protocols and shared types for the Trellis core module.

This module provides type definitions and protocols that are shared across
multiple modules in trellis.core.

Types:
    - ElementKind: Enum for element types (REACT_COMPONENT, JSX_ELEMENT, TEXT)
    - FrozenProps: Immutable props tuple type

Protocols:
    - IComponent: Interface for all components

Functions:
    - freeze_props: Convert dict to FrozenProps
    - unfreeze_props: Convert FrozenProps back to dict
"""

from __future__ import annotations

import typing as tp
from enum import StrEnum

__all__ = [
    "ElementKind",
    "FrozenProps",
    "IComponent",
    "freeze_props",
    "unfreeze_props",
]


class ElementKind(StrEnum):
    """Kind of element in the render tree.

    Used by the client to determine how to render each node:
    - REACT_COMPONENT: Custom React component (Button, Slider, etc.)
    - JSX_ELEMENT: Intrinsic HTML element (div, span, p)
    - TEXT: Raw text node

    Values are explicit strings for stable wire format (serialized to client).
    """

    REACT_COMPONENT = "react_component"
    JSX_ELEMENT = "jsx_element"
    TEXT = "text"


# Immutable props type for ElementNode - tuple of (key, value) pairs
type FrozenProps = tuple[tuple[str, tp.Any], ...]


def freeze_props(props: dict[str, tp.Any]) -> FrozenProps:
    """Convert a props dictionary to an immutable tuple for comparison.

    Props are frozen so that ElementNode can be immutable and props
    can be compared for equality to determine if re-execution is needed.

    Args:
        props: Dictionary of component properties

    Returns:
        Sorted tuple of (key, value) pairs
    """
    return tuple(sorted(props.items()))


def unfreeze_props(frozen: FrozenProps) -> dict[str, tp.Any]:
    """Convert frozen props back to a mutable dictionary.

    Args:
        frozen: Immutable tuple of (key, value) pairs

    Returns:
        Mutable dictionary of props
    """
    return dict(frozen)


# Forward reference for ElementNode (defined in rendering.py)
if tp.TYPE_CHECKING:
    from trellis.core.rendering import ElementNode


class IComponent(tp.Protocol):
    """Protocol defining the component interface.

    All components (functional or class-based) must implement this protocol.
    Components are callable and return ElementNodes when invoked.
    """

    name: str
    """Human-readable name of the component (used for debugging)."""

    @property
    def element_kind(self) -> ElementKind:
        """The kind of element (REACT_COMPONENT, JSX_ELEMENT, or TEXT)."""
        ...

    @property
    def element_name(self) -> str:
        """The element type name used to render this on the client.

        For REACT_COMPONENT: The React component name (e.g., "Button")
        For JSX_ELEMENT: The HTML tag name (e.g., "div")
        For TEXT: A special marker (e.g., "__text__")
        """
        ...

    @property
    def _has_children_param(self) -> bool:
        """Whether this component accepts children via `with` block."""
        ...

    def __call__(self, /, **props: tp.Any) -> ElementNode:
        """Create a node for this component with the given props.

        This does NOT render the component - it only creates a description
        of what should be rendered. Rendering happens later during reconciliation.

        Args:
            **props: Properties to pass to the component

        Returns:
            An ElementNode describing this component invocation
        """
        ...

    def render(self, /, **props: tp.Any) -> None:
        """Render the component to produce child nodes.

        Called by RenderSession when this component needs to render.
        The component should create child nodes by calling other
        components or using `with` blocks for containers.

        Args:
            **props: Properties passed to the component
        """
        ...
