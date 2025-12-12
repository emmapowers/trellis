"""React component base class for the Trellis UI framework.

This module provides the ReactComponent base class for components that have
their own React implementations on the client side. These are typically
"leaf" components like buttons, inputs, and layout containers.

Unlike FunctionalComponents which share a generic React wrapper, each
ReactComponent subclass maps to a specific React component.

Example:
    ```python
    class Column(ReactComponent):
        '''Vertical flex container.'''

        # Each ReactComponent specifies its React type
        _react_type = "Column"

        def __init__(self, gap: int = 8, padding: int = 0):
            self.gap = gap
            self.padding = padding
    ```

See Also:
    - `FunctionalComponent`: For Python-only organizational components
    - `@component`: Decorator for creating FunctionalComponents
"""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis.core.base_component import Component

__all__ = ["ReactComponent"]


@dataclass(kw_only=True)
class ReactComponent(Component):
    """Base class for components with React implementations.

    ReactComponent is used for "leaf" components that have corresponding
    React components on the client side (e.g., Column, Row, Button, Label).

    Subclasses must set the `_react_type` class attribute to specify which
    React component renders them. Container components should also set
    `_has_children` = True.

    Attributes:
        _react_type: Class attribute specifying the React component name.
            Must be set by subclasses.
        _has_children: Class attribute indicating if this is a container.

    Example:
        ```python
        class Button(ReactComponent):
            _react_type = "Button"

            text: str = ""
            on_click: Callable[[], None] | None = None
            disabled: bool = False

        class Column(ReactComponent):
            _react_type = "Column"
            _has_children = True  # Container component
        ```
    """

    # Subclasses must override this
    _react_type: tp.ClassVar[str] = ""

    # Whether this component accepts children via `with` block (class var)
    _has_children: tp.ClassVar[bool] = False

    @property
    def _has_children_param(self) -> bool:
        """Whether this component accepts children."""
        return self.__class__._has_children

    @property
    def react_type(self) -> str:
        """The React component type for this component."""
        if not self._react_type:
            raise NotImplementedError(
                f"{self.__class__.__name__} must set _react_type class attribute"
            )
        return self._react_type

    def execute(self, /, **props: tp.Any) -> None:
        """Execute this component.

        For leaf ReactComponents (no children), this is a no-op.
        For container ReactComponents, this mounts the children.

        Args:
            **props: Properties including `children` for containers
        """
        # If this is a container, mount the children
        children = props.get("children")
        if children:
            for child in children:
                child()


def react_component(
    react_type: str,
    *,
    has_children: bool = False,
) -> tp.Callable[[type[ReactComponent]], type[ReactComponent]]:
    """Decorator to configure a ReactComponent class.

    Args:
        react_type: The React component name on the client
        has_children: Whether this component accepts children via `with` block

    Returns:
        A decorator that configures the class

    Example:
        ```python
        @react_component("Button")
        class Button(ReactComponent):
            text: str = ""
            on_click: Callable[[], None] | None = None
        ```
    """

    def decorator(cls: type[ReactComponent]) -> type[ReactComponent]:
        cls._react_type = react_type
        if has_children:
            cls._has_children = True
        return cls

    return decorator
