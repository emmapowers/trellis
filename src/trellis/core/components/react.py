"""React component base class for the Trellis UI framework.

This module provides the ReactComponentBase class for components that have
their own React implementations on the client side. These are typically
"leaf" components like buttons, inputs, and layout containers.

Unlike CompositionComponents which share a generic wrapper, each
ReactComponentBase subclass maps to a specific React component.

Example:
    ```python
    class Column(ReactComponentBase):
        '''Vertical flex container.'''

        # Each ReactComponentBase specifies its element name
        _element_name = "Column"

        def __init__(self, gap: int = 8, padding: int = 0):
            super().__init__("Column")
            self.gap = gap
            self.padding = padding
    ```

See Also:
    - `CompositionComponent`: For Python-only organizational components
    - `@component`: Decorator for creating CompositionComponents
"""

from __future__ import annotations

import functools
import typing as tp
from collections.abc import Callable
from typing import ParamSpec

from trellis.core.components.base import Component, ElementKind
from trellis.core.components.style_props import Height, Margin, Padding, Width

if tp.TYPE_CHECKING:
    from trellis.core.rendering.element import ElementNode

__all__ = ["ReactComponentBase", "react_component_base"]

# ParamSpec for preserving function signatures through decorators
P = ParamSpec("P")


def _merge_style_props(props: dict[str, tp.Any]) -> dict[str, tp.Any]:
    """Convert ergonomic style props to style dict entries.

    This function processes Margin, Padding, Width, Height dataclasses and flex,
    converting them to CSS style properties. Plain int/str values for margin,
    padding, width, height are passed through unchanged (widget-specific).

    Args:
        props: The widget props, potentially containing style shorthand props

    Returns:
        Modified props dict with style props merged into the style dict
    """
    result = dict(props)
    style: dict[str, tp.Any] = dict(props.get("style") or {})

    # Handle margin - only convert dataclass instances
    if "margin" in result and isinstance(result["margin"], Margin):
        style.update(result.pop("margin").to_style())

    # Handle padding - only convert dataclass instances
    if "padding" in result and isinstance(result["padding"], Padding):
        style.update(result.pop("padding").to_style())

    # Handle width - convert dataclass or plain values (most widgets don't have width prop)
    if "width" in result:
        width = result.pop("width")
        if isinstance(width, Width):
            style.update(width.to_style())
        elif isinstance(width, int):
            style["width"] = f"{width}px"
        elif isinstance(width, str):
            style["width"] = width

    # Handle height - only convert dataclass instances (ProgressBar has its own height)
    if "height" in result and isinstance(result["height"], Height):
        style.update(result.pop("height").to_style())

    # Handle flex
    if "flex" in result:
        style["flex"] = result.pop("flex")

    # Handle text_align
    if "text_align" in result:
        style["textAlign"] = result.pop("text_align")

    # Handle font_weight
    if "font_weight" in result:
        fw = result.pop("font_weight")
        weight_map = {"normal": 400, "medium": 500, "semibold": 600, "bold": 700}
        style["fontWeight"] = weight_map.get(fw, fw) if isinstance(fw, str) else fw

    if style:
        result["style"] = style

    return result


class ReactComponentBase(Component):
    """Base class for components with React implementations.

    ReactComponentBase is used for "leaf" components that have corresponding
    React components on the client side (e.g., Column, Row, Button, Label).

    Subclasses must set the `_element_name` class attribute to specify which
    React component renders them. Container components should also set
    `_has_children` = True.

    Attributes:
        _element_name: Class attribute specifying the React component name.
            Must be set by subclasses.
        _has_children: Class attribute indicating if this is a container.

    Example:
        ```python
        class Button(ReactComponentBase):
            _element_name = "Button"

            text: str = ""
            on_click: Callable[[], None] | None = None
            disabled: bool = False

        class Column(ReactComponentBase):
            _element_name = "Column"
            _has_children = True  # Container component
        ```
    """

    # Subclasses must override this
    _element_name: tp.ClassVar[str] = ""

    # Whether this component accepts children via `with` block (class var)
    _has_children: tp.ClassVar[bool] = False

    @property
    def _has_children_param(self) -> bool:
        """Whether this component accepts children."""
        return self.__class__._has_children

    @property
    def element_kind(self) -> ElementKind:
        """ReactComponentBase subclasses are React components."""
        return ElementKind.REACT_COMPONENT

    @property
    def element_name(self) -> str:
        """The React component type for this component."""
        if not self.__class__._element_name:
            raise NotImplementedError(
                f"{self.__class__.__name__} must set _element_name class attribute"
            )
        return self.__class__._element_name

    def execute(self, /, **props: tp.Any) -> None:
        """Render this component.

        For leaf ReactComponentBase (no children), this is a no-op.
        For container ReactComponentBase, this mounts the children.

        Args:
            **props: Properties including `children` for containers
        """
        # If this is a container, mount the children
        children = props.get("children")
        if children:
            for child in children:
                child()


def react_component_base(
    element_name: str,
    *,
    has_children: bool = False,
) -> Callable[[Callable[P, tp.Any]], Callable[P, ElementNode]]:
    """Decorator to create a ReactComponentBase from a function signature.

    This is the simplest way to define React components. The function body is
    ignored; only the signature is used for documentation and type hints.
    Internally, a singleton ReactComponentBase instance is created.

    The decorator preserves the function's type signature using ParamSpec,
    so mypy will catch invalid prop names passed to widgets.

    Args:
        element_name: The React component name on the client
        has_children: Whether this component accepts children via `with` block

    Returns:
        A decorator that creates a callable returning ElementNodes

    Example:
        ```python
        @react_component_base("Button")
        def Button(
            *,
            text: str = "",
            on_click: Callable[[], None] | None = None,
            disabled: bool = False,
            key: str | None = None,
        ) -> ElementNode:
            '''Clickable button widget.'''
            ...  # Body ignored

        # Use like a regular function
        Button(text="Click me", on_click=handle_click)

        # Type error: unexpected keyword argument
        Button(invalid_prop=True)  # mypy catches this!
        ```
    """

    def decorator(
        func: Callable[P, tp.Any],
    ) -> Callable[P, ElementNode]:
        # Create a generated class with the function's name
        class _Generated(ReactComponentBase):
            _element_name = element_name
            _has_children = has_children

        # Create singleton instance
        _singleton = _Generated(func.__name__)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> ElementNode:
            # Widgets only accept keyword arguments, so args should be empty
            return _singleton._place(**_merge_style_props(dict(kwargs)))

        # Expose the underlying component for introspection
        wrapper._component = _singleton  # type: ignore[attr-defined]

        return wrapper

    return decorator
