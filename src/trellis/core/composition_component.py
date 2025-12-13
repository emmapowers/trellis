"""Composition component implementation for the Trellis UI framework.

This module provides the `@component` decorator for creating components
from plain Python functions. This is the primary way to define components
in Trellis applications.

Example:
    ```python
    @component
    def Greeting(name: str = "World") -> None:
        Text(f"Hello, {name}!")

    @component
    def Counter() -> None:
        state = CounterState()
        Text(f"Count: {state.count}")
        Button(text="Increment", on_click=lambda: state.count += 1)

    # Container component (receives children)
    @component
    def Card(title: str, children: list[ElementNode]) -> None:
        with Column():
            Text(title)
            for child in children:
                child()  # Mount each child
    ```

The decorated function becomes a CompositionComponent that can be called
to create ElementNodes and used in the component tree.
"""

from __future__ import annotations

import inspect
import typing as tp
from dataclasses import dataclass, field

from trellis.core.base import ElementKind
from trellis.core.base_component import Component

__all__ = ["CompositionComponent", "RenderFunc", "component"]


class RenderFunc(tp.Protocol):
    """Protocol for render functions used with @component decorator.

    Render functions take keyword-only props and return None.
    They create child components by calling them during execution.
    """

    __name__: str

    def __call__(self, /, **props: tp.Any) -> None: ...


@dataclass(kw_only=True)
class CompositionComponent(Component):
    """A component implemented by a render function.

    CompositionComponent wraps a plain Python function to make it usable
    as a Trellis component. The function is called during the render
    phase when the component needs to render.

    All CompositionComponents share the same element_name ("CompositionComponent")
    which simply renders their children. The Python component name is preserved
    for debugging purposes.

    Attributes:
        render_func: The function that renders this component
        _has_children_param: True if render_func accepts a `children` parameter

    Example:
        ```python
        def my_button(text: str = "", on_click: Callable = None) -> None:
            # Create native button element
            NativeButton(text=text, on_click=on_click)

        MyButton = CompositionComponent(name="MyButton", render_func=my_button)
        ```

    Note:
        Prefer using the `@component` decorator instead of creating
        CompositionComponent instances directly.
    """

    render_func: RenderFunc
    _has_children_param: bool = field(init=False, default=False)

    @property
    def element_kind(self) -> ElementKind:
        """CompositionComponents are React components on the client."""
        return ElementKind.REACT_COMPONENT

    @property
    def element_name(self) -> str:
        """All CompositionComponents use the same wrapper component."""
        return "CompositionComponent"

    def __post_init__(self) -> None:
        """Inspect the render function to determine if it accepts children."""
        sig = inspect.signature(self.render_func)
        self._has_children_param = "children" in sig.parameters

    def render(self, /, **props: tp.Any) -> None:
        """Render this component by calling the render function.

        For container components, `props['children']` contains a list of
        ElementNodes. The render function should call `child()` on
        each descriptor to mount it at the appropriate location.

        Args:
            **props: Properties passed to the component, including `children`
                for container components
        """
        self.render_func(**props)

    def __hash__(self) -> int:
        """Hash by identity since components are mutable objects."""
        # TODO: Find a less naive way to do this
        return id(self)


def component(render_func: RenderFunc) -> CompositionComponent:
    """Decorator to create a component from a render function.

    This is the primary way to define components in Trellis. The decorated
    function becomes callable and returns ElementNodes when invoked.

    Args:
        render_func: A function that renders the component. Should accept
            keyword arguments for props and return None. Can optionally
            accept a `children` parameter to become a container component.

    Returns:
        A CompositionComponent wrapping the render function.

    Example:
        ```python
        @component
        def Greeting(name: str = "World") -> None:
            Text(f"Hello, {name}!")

        # Use it
        Greeting(name="Alice")  # Creates ElementNode

        # Container component
        @component
        def Box(children: list[ElementNode]) -> None:
            with Div(class_name="box"):
                for child in children:
                    child()

        # Use with `with` block
        with Box():
            Text("Inside the box")
        ```
    """
    return CompositionComponent(
        name=render_func.__name__,
        render_func=render_func,
    )
