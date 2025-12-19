"""Base classes and helpers for HTML elements.

This module provides the HtmlElement class that powers all native HTML
element wrappers, plus the @html_element decorator for defining elements.
"""

from __future__ import annotations

import functools
import typing as tp
from collections.abc import Callable
from typing import ParamSpec

from trellis.core.base import ElementKind
from trellis.core.base_component import Component
from trellis.core.rendering import ElementNode, get_active_render_tree

__all__ = [
    "HtmlElement",
    "Style",
    "auto_collect_hybrid",
    "html_element",
]

# Type alias for inline styles
Style = dict[str, str | int | float]

# ParamSpec for preserving function signatures through the decorator
P = ParamSpec("P")


class HtmlElement(Component):
    """Base class for native HTML elements like div, span, button, etc.

    HtmlElement provides type-safe wrappers around standard HTML tags. Elements
    are rendered directly as native DOM nodes on the client (not as React
    components), enabling full HTML/CSS capabilities with Python type hints.

    Use the `@html_element` decorator to define elements rather than
    subclassing directly. See `trellis.html` for pre-defined elements.

    Example:
        ```python
        from trellis import html as h

        # Leaf element
        h.Button("Click me", onClick=handler)

        # Container element
        with h.Div(className="card", style={"padding": "20px"}):
            h.H1("Title")
            h.P("Content")
        ```
    """

    # Subclasses must set this
    _tag: tp.ClassVar[str] = ""

    # Whether this component accepts children via `with` block (class var)
    _is_container: tp.ClassVar[bool] = False

    @property
    def _has_children_param(self) -> bool:
        """Whether this element accepts children via with block."""
        return self.__class__._is_container

    @property
    def element_kind(self) -> ElementKind:
        """HTML elements are JSX intrinsic elements."""
        return ElementKind.JSX_ELEMENT

    @property
    def element_name(self) -> str:
        """Return the HTML tag name for native DOM rendering."""
        if not self.__class__._tag:
            raise NotImplementedError(f"{self.__class__.__name__} must set _tag class attribute")
        return self.__class__._tag

    def render(self, /, **props: tp.Any) -> None:
        """Render this element.

        For leaf elements (no children), this is a no-op.
        For container elements, this mounts the children.

        Args:
            **props: Properties including `children` for containers
        """
        # If this is a container, mount the children
        children = props.get("children")
        if children:
            for child in children:
                child()


def html_element(
    tag: str,
    *,
    is_container: bool = False,
    name: str | None = None,
) -> Callable[[Callable[P, tp.Any]], Callable[P, ElementNode]]:
    """Decorator to create an HtmlElement from a function signature.

    This is the standard way to define HTML elements. The function body is
    ignored; only the signature is used for documentation and type hints.
    Internally, a singleton HtmlElement instance is created.

    Args:
        tag: The HTML tag name (e.g., "div", "span", "button")
        is_container: Whether this element accepts children via `with` block
        name: Optional name override (defaults to function name). Useful for
            internal functions prefixed with underscore.

    Returns:
        A decorator that creates a callable returning ElementNodes

    Example:
        ```python
        @html_element("div", is_container=True)
        def Div(
            *,
            className: str | None = None,
            style: Style | None = None,
        ) -> ElementNode:
            '''A div container element.'''
            ...  # Body ignored

        # Use like a regular function
        Div(className="container", style={"padding": "20px"})

        # Or as a container
        with Div(className="wrapper"):
            Span(text="Hello")
        ```
    """

    def decorator(
        func: Callable[P, tp.Any],
    ) -> Callable[P, ElementNode]:
        # Use provided name or function name
        element_name = name or func.__name__

        # Create a generated class with the element name
        class _Generated(HtmlElement):
            _tag = tag
            _is_container = is_container

        # Create singleton instance with explicit name
        _singleton = _Generated(element_name)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> ElementNode:
            return _singleton._place(**kwargs)

        # Expose the underlying component for introspection
        wrapper._component = _singleton  # type: ignore[attr-defined]

        return wrapper

    return decorator


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
