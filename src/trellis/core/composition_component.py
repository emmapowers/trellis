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

from trellis.core.base import ElementKind
from trellis.core.base_component import Component

__all__ = ["CompositionComponent", "RenderFunc", "component"]


class RenderFunc(tp.Protocol):
    """Protocol for render functions used with @component decorator.

    Render functions take keyword-only props and return None.
    They create child components by calling them during execution.

    Note: The signature uses `*args, **props` to be permissive and allow
    functions with specific typed parameters. All components should use
    keyword-only arguments when called.
    """

    __name__: str

    # Use permissive signature to allow functions with specific typed parameters.
    # Actual component functions use keyword-only args (e.g., def Foo(*, text: str)).
    def __call__(self, *args: tp.Any, **props: tp.Any) -> None: ...


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
    _children_param: bool

    def __init__(self, name: str, render_func: RenderFunc) -> None:
        super().__init__(name)
        self.render_func = render_func
        # Inspect the render function to determine if it accepts children
        sig = inspect.signature(render_func)
        self._children_param = "children" in sig.parameters

    @property
    def _has_children_param(self) -> bool:
        """Whether this component accepts children via `with` block."""
        return self._children_param

    @property
    def element_kind(self) -> ElementKind:
        """CompositionComponents are React components on the client."""
        return ElementKind.REACT_COMPONENT

    @property
    def element_name(self) -> str:
        """All CompositionComponents use the same wrapper component."""
        return "CompositionComponent"

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
    return CompositionComponent(render_func.__name__, render_func)
