"""Functional component implementation for the Trellis UI framework.

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
    def Card(title: str, children: list[ElementDescriptor]) -> None:
        with Column():
            Text(title)
            for child in children:
                child()  # Mount each child
    ```

The decorated function becomes a FunctionalComponent that can be called
to create ElementDescriptors and used in the component tree.
"""

from __future__ import annotations

import inspect
import typing as tp
from dataclasses import dataclass, field

from trellis.core.base_component import Component
from trellis.core.rendering import Element

__all__ = ["FunctionalComponent", "RenderFunc", "component"]

T = tp.TypeVar("T", bound=Element, default=Element)


class RenderFunc(tp.Protocol):
    """Protocol for render functions used with @component decorator.

    Render functions take keyword-only props and return None.
    They create child components by calling them during execution.
    """

    __name__: str

    def __call__(self, /, **props: tp.Any) -> None: ...


@dataclass(kw_only=True)
class FunctionalComponent(Component[T], tp.Generic[T]):
    """A component implemented by a render function.

    FunctionalComponent wraps a plain Python function to make it usable
    as a Trellis component. The function is called during the execution
    phase when the component needs to render.

    Attributes:
        render_func: The function that renders this component
        _has_children_param: True if render_func accepts a `children` parameter

    Example:
        ```python
        def my_button(text: str = "", on_click: Callable = None) -> None:
            # Create native button element
            NativeButton(text=text, on_click=on_click)

        MyButton = FunctionalComponent(name="MyButton", render_func=my_button)
        ```

    Note:
        Prefer using the `@component` decorator instead of creating
        FunctionalComponent instances directly.
    """

    render_func: RenderFunc
    _has_children_param: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        """Inspect the render function to determine if it accepts children."""
        sig = inspect.signature(self.render_func)
        self._has_children_param = "children" in sig.parameters

    def execute(self, /, node: T, **props: tp.Any) -> None:
        """Execute the render function with the given props.

        For container components, `props['children']` contains a list of
        ElementDescriptors. The render function should call `child()` on
        each descriptor to mount it at the appropriate location.

        Args:
            node: The Element instance (available but typically unused)
            **props: Properties passed to the component, including `children`
                for container components
        """
        self.render_func(**props)

    def __hash__(self) -> int:
        """Hash by identity since components are mutable objects."""
        # TODO: Find a less naive way to do this
        return id(self)


def component(render_func: RenderFunc) -> FunctionalComponent[Element]:
    """Decorator to create a component from a render function.

    This is the primary way to define components in Trellis. The decorated
    function becomes callable and returns ElementDescriptors when invoked.

    Args:
        render_func: A function that renders the component. Should accept
            keyword arguments for props and return None. Can optionally
            accept a `children` parameter to become a container component.

    Returns:
        A FunctionalComponent wrapping the render function.

    Example:
        ```python
        @component
        def Greeting(name: str = "World") -> None:
            Text(f"Hello, {name}!")

        # Use it
        Greeting(name="Alice")  # Creates ElementDescriptor

        # Container component
        @component
        def Box(children: list[ElementDescriptor]) -> None:
            with Div(class_name="box"):
                for child in children:
                    child()

        # Use with `with` block
        with Box():
            Text("Inside the box")
        ```
    """
    return FunctionalComponent(
        name=render_func.__name__,
        render_func=render_func,
    )
