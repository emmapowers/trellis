"""Helpers for building lightweight generated HTML runtime wrappers."""

from __future__ import annotations

import typing as tp

from trellis.core.rendering.element import Element
from trellis.html.base import HtmlContainerElement, HtmlElement


def create_html_element(
    tag: str,
    *,
    component_name: str,
    export_name: str,
    is_container: bool = False,
    doc: str | None = None,
) -> tp.Callable[..., Element]:
    """Create a permissive runtime wrapper for a generated HTML element."""

    class _Generated(HtmlElement):
        _tag = tag
        _is_container = is_container

    element_class = HtmlContainerElement if is_container else Element
    singleton = _Generated(component_name, element_class=element_class)

    def wrapper(*args: tp.Any, **kwargs: tp.Any) -> Element:
        if len(args) > 1:
            raise TypeError(
                f"{component_name}() accepts at most one positional argument for text content."
            )
        if args and "inner_text" in kwargs:
            raise TypeError(
                f"{component_name}() received both positional text and 'inner_text' keyword argument."
            )
        if args and "_text" in kwargs:
            raise TypeError(
                f"{component_name}() received both positional text and '_text' keyword argument."
            )

        props = dict(kwargs)
        if args:
            props["_text"] = args[0]

        if "inner_text" in props:
            text_value = props.pop("inner_text")
            if text_value is not None:
                props["_text"] = text_value

        if "_text" in props and props["_text"] is None:
            del props["_text"]

        normalized_props: dict[str, tp.Any] = {}
        for key, value in props.items():
            if value is None:
                continue
            normalized_key = key.removesuffix("_")
            if normalized_key in normalized_props:
                raise TypeError(
                    f"{component_name}() received duplicate keyword arguments after "
                    f"normalization ({normalized_key})."
                )
            normalized_props[normalized_key] = value

        return singleton._place(**normalized_props)

    wrapper.__name__ = export_name
    wrapper.__qualname__ = export_name
    wrapper.__doc__ = doc
    wrapper._component = singleton  # type: ignore[attr-defined]
    return wrapper
