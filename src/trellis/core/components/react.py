"""React component base class and @react decorator."""

from __future__ import annotations

import functools
import inspect
import typing as tp
from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec

from trellis.bundler.registry import ExportKind, registry
from trellis.core.components.base import Component, ElementKind
from trellis.core.components.style_props import Height, Margin, Padding, Width
from trellis.core.rendering.element import Element

__all__ = ["ReactComponentBase", "react"]

# ParamSpec for preserving function signatures through decorators
P = ParamSpec("P")


def _merge_style_props(props: dict[str, tp.Any]) -> dict[str, tp.Any]:
    """Convert ergonomic style props to style dict entries."""
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


def react(
    source: str,
    *,
    export_name: str | None = None,
    is_container: bool = False,
    packages: dict[str, str] | None = None,
    element_class: type[Element] = Element,
) -> Callable[[Callable[P, tp.Any]], Callable[P, Element]]:
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
    # Capture caller's directory at decoration time (before entering decorator)
    frame = inspect.currentframe()
    if frame is not None and frame.f_back is not None:
        caller_file = frame.f_back.f_code.co_filename
        caller_dir = Path(caller_file).parent.resolve()
    else:
        caller_dir = None

    def decorator(
        func: Callable[P, tp.Any],
    ) -> Callable[P, Element]:
        resolved_export_name = export_name or func.__name__

        # Create a generated ReactComponentBase subclass
        class _Generated(ReactComponentBase):
            _element_name = resolved_export_name
            _is_container = is_container

        # Create singleton instance
        _singleton = _Generated(func.__name__, element_class=element_class)

        # Register module with the bundler
        module_name = f"{func.__module__}.{func.__qualname__}".replace(".", "-")
        registry.register(
            module_name,
            base_path=caller_dir,
            packages=packages,
            exports=[(resolved_export_name, ExportKind.COMPONENT, source)],
        )

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Element:
            return _singleton._place(**_merge_style_props(dict(kwargs)))

        wrapper._component = _singleton  # type: ignore[attr-defined]

        return wrapper

    return decorator
