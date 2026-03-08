"""React component base class and @react decorator."""

from __future__ import annotations

import functools
import inspect
import typing as tp
from collections.abc import Callable
from pathlib import Path
from typing import Literal, ParamSpec

from trellis.core.components.base import Component, ElementKind
from trellis.core.rendering.element import ContainerElement, Element
from trellis.core.rendering.traits import ContainerTrait
from trellis.registry import ExportKind, registry

__all__ = ["ReactComponentBase", "react"]

# ParamSpec for preserving function signatures through decorators
P = ParamSpec("P")
E = tp.TypeVar("E", bound=Element)


class ReactComponentBase(Component):
    """Base class for components with React implementations."""

    _element_name: tp.ClassVar[str] = ""
    _is_container: tp.ClassVar[bool] = False

    @property
    def is_container(self) -> bool:
        return self.__class__._is_container

    @property
    def element_kind(self) -> ElementKind:
        return ElementKind.REACT_COMPONENT

    @property
    def element_name(self) -> str:
        if not self.__class__._element_name:
            raise NotImplementedError(
                f"{self.__class__.__name__} must set _element_name class attribute"
            )
        return self.__class__._element_name

    def execute(self, /, **props: tp.Any) -> None:
        """Execute this component, mounting any children."""
        children = props.get("children")
        if children:
            for child in children:
                child()


@tp.overload
def react(
    source: str,
    *,
    export_name: str | None = None,
    is_container: Literal[True],
    packages: dict[str, str] | None = None,
    element_class: Literal[None] = None,
) -> Callable[[Callable[P, tp.Any]], Callable[P, ContainerElement]]: ...


@tp.overload
def react(
    source: str,
    *,
    export_name: str | None = None,
    is_container: Literal[False] = ...,
    packages: dict[str, str] | None = None,
    element_class: Literal[None] = None,
) -> Callable[[Callable[P, tp.Any]], Callable[P, Element]]: ...


@tp.overload
def react(
    source: str,
    *,
    export_name: str | None = None,
    is_container: bool = ...,
    packages: dict[str, str] | None = None,
    element_class: type[E],
) -> Callable[[Callable[P, tp.Any]], Callable[P, E]]: ...


def react(
    source: str,
    *,
    export_name: str | None = None,
    is_container: bool = False,
    packages: dict[str, str] | None = None,
    element_class: type[E] | None = None,
) -> Callable[[Callable[P, tp.Any]], Callable[P, Element | E]]:
    """Decorator that creates a React component wrapper and registers it with the bundler.

    Combines component creation with module
    registration, so that widget Python definitions and TSX implementations are
    colocated and the module registry is the single source of truth.

    Args:
        source: TSX source file path relative to the caller's directory.
        export_name: React component export name. Defaults to the function name.
        is_container: Whether this component accepts children via ``with`` blocks.
        packages: NPM packages required by this component (name -> version).
        element_class: Element subclass to use for this component's nodes.
    """
    if element_class is not None:
        resolved_element_class: type[Element] = element_class
        if is_container and ContainerTrait not in element_class.__mro__:
            raise TypeError(
                "@react(..., is_container=True, element_class=...) requires "
                f"element_class to include ContainerTrait in its MRO. "
                f"Got {element_class.__name__}. "
                "Define a class like "
                f"'class {element_class.__name__}Container(ContainerTrait, "
                f"{element_class.__name__}): ...'."
            )
    else:
        resolved_element_class = ContainerElement if is_container else Element

    # Capture caller's directory at decoration time (before entering decorator)
    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None:
        caller_file = frame.f_back.f_code.co_filename
        caller_dir = Path(caller_file).parent.resolve()
    else:
        caller_dir = None

    def decorator(
        func: Callable[P, tp.Any],
    ) -> Callable[P, Element | E]:
        resolved_export_name = export_name or func.__name__

        # Create a generated ReactComponentBase subclass
        class _Generated(ReactComponentBase):
            _element_name = resolved_export_name
            _is_container = is_container

        # Create singleton instance
        _singleton = _Generated(func.__name__, element_class=resolved_element_class)

        # Register module with the bundler
        module_name = f"{func.__module__}.{func.__qualname__}".replace(".", "-")
        registry.register(
            module_name,
            base_path=caller_dir,
            packages=packages,
            exports=[(resolved_export_name, ExportKind.COMPONENT, source)],
        )

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Element | E:
            return _singleton._place(**dict(kwargs))

        wrapper._component = _singleton  # type: ignore[attr-defined]

        return wrapper

    return decorator
