"""The @component decorator for creating components from functions."""

from __future__ import annotations

import inspect
import types
import typing as tp

from trellis.core.components.base import Component, ElementKind
from trellis.core.rendering.element import ContainerElement, Element
from trellis.core.rendering.traits import ContainerTrait
from trellis.core.transforms import StateVarTransform, apply_transforms

__all__ = ["CompositionComponent", "RenderFunc", "component"]

E_co = tp.TypeVar("E_co", bound=Element, default=Element, covariant=True)
E = tp.TypeVar("E", bound=Element, default=Element)


class RenderFunc(tp.Protocol):
    """Protocol for render functions used with @component decorator."""

    __name__: str
    __code__: types.CodeType
    __call__: tp.Callable[..., None]


class CompositionComponent(Component, tp.Generic[E_co]):
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

        # Resolve element class.
        if element_class is not None:
            resolved_class: type[Element] = element_class
            if is_container and ContainerTrait not in element_class.__mro__:
                raise TypeError(
                    "@component(is_container=True, element_class=...) requires "
                    f"element_class to include ContainerTrait in its MRO. "
                    f"Got {element_class.__name__}. "
                    "Define a class like "
                    f"'class {element_class.__name__}Container(ContainerTrait, "
                    f"{element_class.__name__}): ...'."
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

    def __call__(self, /, **props: tp.Any) -> E_co:
        """Create an Element for this component invocation."""
        return tp.cast("E_co", self._place(**props))

    def execute(self, /, **props: tp.Any) -> None:
        """Execute this component by calling the render function."""
        self.render_func(**props)


@tp.overload
def component(render_func: RenderFunc) -> CompositionComponent[Element]: ...


@tp.overload
def component(
    render_func: None = None,
    *,
    element_class: tp.Literal[None] = None,
    is_container: tp.Literal[True],
) -> tp.Callable[[RenderFunc], CompositionComponent[ContainerElement]]: ...


@tp.overload
def component(
    render_func: None = None,
    *,
    element_class: tp.Literal[None] = None,
    is_container: tp.Literal[False] = False,
) -> tp.Callable[[RenderFunc], CompositionComponent[Element]]: ...


@tp.overload
def component(
    render_func: None = None,
    *,
    element_class: type[E],
    is_container: bool = False,
) -> tp.Callable[[RenderFunc], CompositionComponent[E]]: ...


def component(
    render_func: RenderFunc | None = None,
    *,
    element_class: type[E] | None = None,
    is_container: bool = False,
) -> CompositionComponent[Element] | tp.Callable[[RenderFunc], CompositionComponent[Element]]:
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
    _transforms = [StateVarTransform()]

    if render_func is not None:
        # Called without parentheses: @component
        transformed = tp.cast("RenderFunc", apply_transforms(render_func, _transforms))
        return CompositionComponent(
            render_func.__name__, transformed, element_class, is_container=is_container
        )

    # Called with parentheses: @component(is_container=True, element_class=X)
    def decorator(func: RenderFunc) -> CompositionComponent[Element]:
        transformed = tp.cast("RenderFunc", apply_transforms(func, _transforms))
        return CompositionComponent(
            func.__name__, transformed, element_class, is_container=is_container
        )

    return decorator
