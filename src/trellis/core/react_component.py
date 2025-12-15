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

from trellis.core.base import ElementKind
from trellis.core.base_component import Component

if tp.TYPE_CHECKING:
    from trellis.core.rendering import ElementNode

__all__ = ["ReactComponentBase", "react_component_base"]


class _DecoratedComponent(tp.Protocol):
    """Protocol for functions decorated with @react_component_base."""

    _component: ReactComponentBase

    def __call__(self, **props: tp.Any) -> ElementNode: ...


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

    def render(self, /, **props: tp.Any) -> None:
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
) -> tp.Callable[[tp.Callable[..., tp.Any]], _DecoratedComponent]:
    """Decorator to create a ReactComponentBase from a function signature.

    This is the simplest way to define React components. The function body is
    ignored; only the signature is used for documentation and type hints.
    Internally, a singleton ReactComponentBase instance is created.

    Args:
        element_name: The React component name on the client
        has_children: Whether this component accepts children via `with` block

    Returns:
        A decorator that creates a callable returning ElementNodes

    Example:
        ```python
        @react_component_base("Button")
        def Button(
            text: str = "",
            on_click: Callable[[], None] | None = None,
            disabled: bool = False,
        ) -> ElementNode:
            '''Clickable button widget.'''
            ...  # Body ignored

        # Use like a regular function
        Button(text="Click me", on_click=handle_click)
        ```
    """

    def decorator(
        func: tp.Callable[..., tp.Any],
    ) -> _DecoratedComponent:
        # Create a generated class with the function's name
        class _Generated(ReactComponentBase):
            _element_name = element_name
            _has_children = has_children

        # Create singleton instance
        _singleton = _Generated(func.__name__)

        @functools.wraps(func)
        def wrapper(**props: tp.Any) -> ElementNode:
            return _singleton._place(**props)

        # Expose the underlying component for introspection
        wrapper._component = _singleton  # type: ignore[attr-defined]

        return tp.cast("_DecoratedComponent", wrapper)

    return decorator
