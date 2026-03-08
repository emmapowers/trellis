"""Widget-layer style sugar helpers."""

from __future__ import annotations

import functools
import typing as tp
from collections.abc import Callable
from typing import ParamSpec

from trellis.html import Style
from trellis.html._style_compiler import merge_style_inputs

P = ParamSpec("P")
R = tp.TypeVar("R")

WidgetStyleField = tp.Literal[
    "margin", "padding", "width", "height", "flex", "text_align", "font_weight"
]

_FONT_WEIGHT_KEYWORDS = {"normal": 400, "medium": 500, "semibold": 600, "bold": 700}


def merge_widget_style_props(
    props: dict[str, tp.Any],
    style_fields: frozenset[WidgetStyleField],
) -> dict[str, tp.Any]:
    result = dict(props)
    style_updates: dict[str, tp.Any] = {}

    for field_name in ("margin", "padding", "width", "height", "flex"):
        if field_name in style_fields and field_name in result:
            value = result.pop(field_name)
            if value is not None:
                style_updates[field_name] = value

    if "text_align" in style_fields and "text_align" in result:
        value = result.pop("text_align")
        if value is not None:
            style_updates["text_align"] = value

    if "font_weight" in style_fields and "font_weight" in result:
        value = result.pop("font_weight")
        if value is not None:
            if isinstance(value, str):
                value = _FONT_WEIGHT_KEYWORDS.get(value, value)
            style_updates["font_weight"] = value

    merged_style = result.pop("style", None)
    if style_updates:
        merged_style = merge_style_inputs(merged_style, Style(**style_updates))
    if merged_style is not None:
        result["style"] = merged_style
    return result


def widget_style_props(
    *style_fields: WidgetStyleField,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    declared_fields = frozenset(style_fields)

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            rewritten_kwargs = merge_widget_style_props(dict(kwargs), declared_fields)
            return func(*args, **rewritten_kwargs)

        return wrapper

    return decorator
