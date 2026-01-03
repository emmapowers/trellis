"""The @component decorator for creating components from functions."""

from __future__ import annotations

import inspect
import typing as tp

from trellis.core.components.base import Component, ElementKind
from trellis.core.rendering.element import Element

__all__ = ["CompositionComponent", "RenderFunc", "component"]


class RenderFunc(tp.Protocol):
    """Protocol for render functions used with @component decorator."""

    __name__: str
    __call__: tp.Callable[..., None]


class CompositionComponent(Component):
    """A component implemented by a render function."""

    render_func: RenderFunc
    _children_param: bool

    def __init__(
        self,
        name: str,
        render_func: RenderFunc,
        element_class: type[Element] = Element,
    ) -> None:
        super().__init__(name, element_class=element_class)
        self.render_func = render_func
        # Inspect the render function to determine if it accepts children
        sig = inspect.signature(render_func)
        self._children_param = "children" in sig.parameters

    @property
    def is_container(self) -> bool:
        return self._children_param

    @property
    def element_kind(self) -> ElementKind:
        return ElementKind.REACT_COMPONENT

    @property
    def element_name(self) -> str:
        return "CompositionComponent"

    def execute(self, /, **props: tp.Any) -> None:
        """Execute this component by calling the render function."""
        self.render_func(**props)


@tp.overload
def component(render_func: RenderFunc) -> CompositionComponent: ...


@tp.overload
def component(
    render_func: None = None,
    *,
    element_class: type[Element] = Element,
) -> tp.Callable[[RenderFunc], CompositionComponent]: ...


def component(
    render_func: RenderFunc | None = None,
    *,
    element_class: type[Element] = Element,
) -> CompositionComponent | tp.Callable[[RenderFunc], CompositionComponent]:
    """Decorator to create a component from a render function.

    Can be used with or without parentheses:
        @component
        def MyWidget(): ...

        @component(element_class=CustomElement)
        def MyWidget(): ...
    """
    if render_func is not None:
        # Called without parentheses: @component
        return CompositionComponent(render_func.__name__, render_func, element_class)

    # Called with parentheses: @component(element_class=X)
    def decorator(func: RenderFunc) -> CompositionComponent:
        return CompositionComponent(func.__name__, func, element_class)

    return decorator
