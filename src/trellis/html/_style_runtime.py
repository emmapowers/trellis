"""Typed CSS runtime helpers exposed from trellis.html."""

from __future__ import annotations

import typing as tp
from dataclasses import dataclass

from trellis.html._css_primitives import (
    CssAngle,
    CssColor,
    CssLength,
    CssPercent,
    CssTime,
    CssValue,
)
from trellis.html._generated_style_types import MediaRule, _GeneratedStyleFields

StyleScalar = str | int | float | CssValue


@dataclass(kw_only=True)
class Style(_GeneratedStyleFields):
    vars: dict[str, StyleScalar] | None = None
    hover: Style | None = None
    focus: Style | None = None
    focus_visible: Style | None = None
    focus_within: Style | None = None
    active: Style | None = None
    visited: Style | None = None
    disabled: Style | None = None
    checked: Style | None = None
    placeholder: Style | None = None
    before: Style | None = None
    after: Style | None = None
    selection: Style | None = None
    media: list[MediaRule] | dict[str, Style] | None = None
    selectors: dict[str, Style] | None = None


def _format_number(value: int | float) -> str:
    if isinstance(value, int) or value.is_integer():
        return str(int(value))
    return format(value, "g")


def _wrap_value(
    cls: type[CssValue],
    value: int | float | str,
    unit: str = "",
) -> CssValue:
    if isinstance(value, (int, float)):
        return cls(f"{_format_number(value)}{unit}")
    return cls(value)


def raw(value: str) -> CssValue:
    return CssValue(value)


def color(value: str) -> CssColor:
    return CssColor(value)


def px(value: int | float) -> CssLength:
    return tp.cast(CssLength, _wrap_value(CssLength, value, "px"))


def rem(value: int | float) -> CssLength:
    return tp.cast(CssLength, _wrap_value(CssLength, value, "rem"))


def em(value: int | float) -> CssLength:
    return tp.cast(CssLength, _wrap_value(CssLength, value, "em"))


def vw(value: int | float) -> CssLength:
    return tp.cast(CssLength, _wrap_value(CssLength, value, "vw"))


def vh(value: int | float) -> CssLength:
    return tp.cast(CssLength, _wrap_value(CssLength, value, "vh"))


def pct(value: int | float) -> CssPercent:
    return tp.cast(CssPercent, _wrap_value(CssPercent, value, "%"))


def sec(value: int | float) -> CssTime:
    return tp.cast(CssTime, _wrap_value(CssTime, value, "s"))


def ms(value: int | float) -> CssTime:
    return tp.cast(CssTime, _wrap_value(CssTime, value, "ms"))


def deg(value: int | float) -> CssAngle:
    return tp.cast(CssAngle, _wrap_value(CssAngle, value, "deg"))


def rgb(red: int, green: int, blue: int) -> CssColor:
    return CssColor(f"rgb({red} {green} {blue})")


def rgba(red: int, green: int, blue: int, alpha: float) -> CssColor:
    return CssColor(f"rgb({red} {green} {blue} / {_format_number(alpha)})")


def hsl(hue: int | float, saturation: int | float, lightness: int | float) -> CssColor:
    return CssColor(
        f"hsl({_format_number(hue)} {_format_number(saturation)}% {_format_number(lightness)}%)"
    )


def var(name: str, fallback: StyleScalar | None = None) -> CssValue:
    if fallback is None:
        return CssValue(f"var({name})")
    return CssValue(f"var({name}, {_serialize_helper_value(fallback, auto_px=False)})")


def calc(expression: str) -> CssValue:
    return CssValue(f"calc({expression})")


def min_(*values: StyleScalar) -> CssValue:
    return CssValue(f"min({', '.join(_serialize_helper_value(value, auto_px=False) for value in values)})")


def max_(*values: StyleScalar) -> CssValue:
    return CssValue(f"max({', '.join(_serialize_helper_value(value, auto_px=False) for value in values)})")


def clamp(minimum: StyleScalar, preferred: StyleScalar, maximum: StyleScalar) -> CssValue:
    return CssValue(
        "clamp("
        f"{_serialize_helper_value(minimum, auto_px=False)}, "
        f"{_serialize_helper_value(preferred, auto_px=False)}, "
        f"{_serialize_helper_value(maximum, auto_px=False)})"
    )


def margin(*values: StyleScalar) -> CssValue:
    return CssValue(" ".join(_serialize_helper_value(value, auto_px=True) for value in values))


def padding(*values: StyleScalar) -> CssValue:
    return CssValue(" ".join(_serialize_helper_value(value, auto_px=True) for value in values))


def inset(*values: StyleScalar) -> CssValue:
    return CssValue(" ".join(_serialize_helper_value(value, auto_px=True) for value in values))


def border(width: StyleScalar, style: str, color_value: StyleScalar) -> CssValue:
    return CssValue(
        f"{_serialize_helper_value(width, auto_px=True)} {style} {_serialize_helper_value(color_value, auto_px=False)}"
    )


def shadow(*parts: StyleScalar) -> CssValue:
    return CssValue(" ".join(_serialize_helper_value(part, auto_px=False) for part in parts))


def scale(value: int | float) -> CssValue:
    return CssValue(f"scale({_format_number(value)})")


def rotate(value: CssAngle | int | float) -> CssValue:
    serialized = _serialize_helper_value(value if isinstance(value, CssAngle) else deg(value), auto_px=False)
    return CssValue(f"rotate({serialized})")


def translate(x_value: StyleScalar, y_value: StyleScalar | None = None) -> CssValue:
    x = _serialize_helper_value(x_value, auto_px=True)
    if y_value is None:
        return CssValue(f"translate({x})")
    return CssValue(f"translate({x}, {_serialize_helper_value(y_value, auto_px=True)})")


def media(
    *,
    style: Style,
    min_width: CssLength | int | float | None = None,
    max_width: CssLength | int | float | None = None,
    min_height: CssLength | int | float | None = None,
    max_height: CssLength | int | float | None = None,
    orientation: tp.Literal["portrait", "landscape"] | None = None,
    hover: tp.Literal["hover", "none"] | None = None,
    pointer: tp.Literal["none", "coarse", "fine"] | None = None,
    prefers_color_scheme: tp.Literal["light", "dark"] | None = None,
    prefers_reduced_motion: tp.Literal["reduce", "no-preference"] | None = None,
    query: str | None = None,
) -> MediaRule:
    return MediaRule(
        style=style,
        min_width=tp.cast(tp.Any, min_width if not isinstance(min_width, (int, float)) else px(min_width)),
        max_width=tp.cast(tp.Any, max_width if not isinstance(max_width, (int, float)) else px(max_width)),
        min_height=tp.cast(tp.Any, min_height if not isinstance(min_height, (int, float)) else px(min_height)),
        max_height=tp.cast(tp.Any, max_height if not isinstance(max_height, (int, float)) else px(max_height)),
        orientation=orientation,
        hover=hover,
        pointer=pointer,
        prefers_color_scheme=prefers_color_scheme,
        prefers_reduced_motion=prefers_reduced_motion,
        query=query,
    )


def _serialize_helper_value(value: StyleScalar, *, auto_px: bool) -> str:
    if isinstance(value, CssValue):
        return value.css_text
    if isinstance(value, (int, float)):
        return f"{_format_number(value)}px" if auto_px else _format_number(value)
    return value
