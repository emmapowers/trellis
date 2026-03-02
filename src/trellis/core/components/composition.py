"""The @component decorator for creating components from functions."""

from __future__ import annotations

import inspect
import typing as tp

from trellis.core.components.base import Component, ElementKind
from trellis.core.rendering.element import ContainerElement, Element
from trellis.core.rendering.traits import ContainerTrait

__all__ = ["CompositionComponent", "RenderFunc", "component"]


class RenderFunc(tp.Protocol):
    """Protocol for render functions used with @component decorator."""

    __name__: str
    __call__: tp.Callable[..., None]


class CompositionComponent(Component):
    """A component implemented by a render function."""

    render_func: RenderFunc
    _is_container: bool

    def __init__(
        self,
        name: str,
        render_func: RenderFunc,
        element_class: type[Element] | None = None,
        is_container: bool = False,
    ) -> None:
        if is_container:
            # Validate that the render function accepts a children parameter
            sig = inspect.signature(render_func)
            if "children" not in sig.parameters:
                raise TypeError(
                    f"@component(is_container=True) requires a 'children' parameter, "
                    f"but {name}() has no 'children' parameter."
                )

        self._is_container = is_container

        # Resolve element class, composing ContainerTrait dynamically if needed
        if element_class is not None:
            resolved_class = element_class
            if is_container and ContainerTrait not in element_class.__mro__:
                resolved_class = type(
                    f"{element_class.__name__}Container",
                    (ContainerTrait, element_class),
                    {},
                )
        else:
            resolved_class = ContainerElement if is_container else Element

        super().__init__(name, element_class=resolved_class)
        self.render_func = render_func

    @property
    def is_container(self) -> bool:
        return self._is_container

    @property
    def element_kind(self) -> ElementKind:
        return ElementKind.REACT_COMPONENT

    @property
    def element_name(self) -> str:
        return "CompositionComponent"

    def __call__(self, /, **props: tp.Any) -> ContainerElement:
        """Create an Element for this component invocation.

        Typed as ContainerElement so that container components can be used
        with ``with`` blocks without mypy errors. Non-container components
        return Element at runtime (which lacks __enter__), giving a clear
        runtime error if used incorrectly.
        """
        return self._place(**props)  # type: ignore[return-value]

    def execute(self, /, **props: tp.Any) -> None:
        """Execute this component by calling the render function."""
        self.render_func(**props)


@tp.overload
def component(render_func: RenderFunc) -> CompositionComponent: ...


@tp.overload
def component(
    render_func: None = None,
    *,
    element_class: type[Element] | None = None,
    is_container: bool = False,
) -> tp.Callable[[RenderFunc], CompositionComponent]: ...


def component(
    render_func: RenderFunc | None = None,
    *,
    element_class: type[Element] | None = None,
    is_container: bool = False,
) -> CompositionComponent | tp.Callable[[RenderFunc], CompositionComponent]:
    """Decorator to create a component from a render function.

    Can be used with or without parentheses:
        @component
        def MyWidget(): ...

        @component(is_container=True)
        def MyLayout(children: list[ChildRef]): ...

        @component(element_class=CustomElement)
        def MyWidget(): ...

    Args:
        render_func: The render function (when used without parentheses).
        element_class: Optional Element subclass to use for this component's nodes.
        is_container: Whether this component accepts children via ``with`` blocks.
            When True, the render function must have a ``children`` parameter.
    """
    if render_func is not None:
        # Called without parentheses: @component
        return CompositionComponent(render_func.__name__, render_func, element_class)

    # Called with parentheses: @component(is_container=True, element_class=X)
    def decorator(func: RenderFunc) -> CompositionComponent:
        return CompositionComponent(func.__name__, func, element_class, is_container=is_container)

    return decorator
