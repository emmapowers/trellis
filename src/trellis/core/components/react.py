"""React component base class."""

from __future__ import annotations

import functools
import typing as tp
from collections.abc import Callable
from typing import ParamSpec

from trellis.core.components.base import Component, ElementKind
from trellis.core.components.style_props import Height, Margin, Padding, Width
from trellis.core.rendering.element import Element

__all__ = ["ReactComponentBase", "react_component_base"]

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
    _has_children: tp.ClassVar[bool] = False

    @property
    def _has_children_param(self) -> bool:
        return self.__class__._has_children

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


def react_component_base(
    element_name: str,
    *,
    has_children: bool = False,
    element_class: type[Element] = Element,
) -> Callable[[Callable[P, tp.Any]], Callable[P, Element]]:
    """Decorator to create a ReactComponentBase from a function signature."""

    def decorator(
        func: Callable[P, tp.Any],
    ) -> Callable[P, Element]:
        # Create a generated class with the function's name
        class _Generated(ReactComponentBase):
            _element_name = element_name
            _has_children = has_children

        # Create singleton instance with the element_class
        _singleton = _Generated(func.__name__, element_class=element_class)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Element:
            # Widgets only accept keyword arguments, so args should be empty
            return _singleton._place(**_merge_style_props(dict(kwargs)))

        # Expose the underlying component for introspection
        wrapper._component = _singleton  # type: ignore[attr-defined]

        return wrapper

    return decorator
