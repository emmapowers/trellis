"""Typed CSS runtime helpers exposed from trellis.html.

Use these helpers with ``style=...`` on HTML elements and widgets:

- ``Style(...)`` for structured, typed CSS declarations
- raw dicts with DOM-style CSS keys for escape-hatch usage
- helper functions like ``px(...)``, ``rgb(...)``, ``border(...)``, and ``media(...)``
  for common CSS values and shorthands
"""

from __future__ import annotations

import typing as tp
from collections.abc import Mapping
from dataclasses import dataclass

from trellis.html._css_primitives import (
    CssAngle,
    CssColor,
    CssLength,
    CssPercent,
    CssTime,
    CssValue,
)
from trellis.html._generated_style_types import (
    HeightValue,
    MediaRule,
    SpacingShorthand,
    WidthValue,
    _GeneratedStyleFields,
)

type StyleScalar = str | int | float | CssValue
type RawStyleMapping = Mapping[str, tp.Any]
type WidthInput = WidthValue | int | float
type HeightInput = HeightValue | int | float
type SpacingInput = SpacingShorthand | int | float


@dataclass(kw_only=True)
class Style(_GeneratedStyleFields):
    """Structured CSS style input for ``trellis.html``.

    Use ``Style(...)`` for typed CSS properties, pseudo states, media queries,
    selectors, and custom properties. For unsupported or highly dynamic cases,
    ``style`` also accepts raw dicts using DOM-style CSS keys.
    """

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
    media: list[MediaRule] | dict[str, StyleInput] | None = None
    selectors: dict[str, StyleInput] | None = None


type StyleInput = Style | RawStyleMapping


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
    """Return a raw CSS value string without additional normalization."""
    return CssValue(value)


def color(value: str) -> CssColor:
    """Return an arbitrary CSS color value."""
    return CssColor(value)


def px(value: int | float) -> CssLength:
    """Return a CSS length in pixels."""
    return tp.cast("CssLength", _wrap_value(CssLength, value, "px"))


def rem(value: int | float) -> CssLength:
    """Return a CSS length in rem units."""
    return tp.cast("CssLength", _wrap_value(CssLength, value, "rem"))


def em(value: int | float) -> CssLength:
    """Return a CSS length in em units."""
    return tp.cast("CssLength", _wrap_value(CssLength, value, "em"))


def vw(value: int | float) -> CssLength:
    """Return a CSS length in viewport-width units."""
    return tp.cast("CssLength", _wrap_value(CssLength, value, "vw"))


def vh(value: int | float) -> CssLength:
    """Return a CSS length in viewport-height units."""
    return tp.cast("CssLength", _wrap_value(CssLength, value, "vh"))


def pct(value: int | float) -> CssPercent:
    """Return a CSS percentage value."""
    return tp.cast("CssPercent", _wrap_value(CssPercent, value, "%"))


def sec(value: int | float) -> CssTime:
    """Return a CSS time value in seconds."""
    return tp.cast("CssTime", _wrap_value(CssTime, value, "s"))


def ms(value: int | float) -> CssTime:
    """Return a CSS time value in milliseconds."""
    return tp.cast("CssTime", _wrap_value(CssTime, value, "ms"))


def deg(value: int | float) -> CssAngle:
    """Return a CSS angle value in degrees."""
    return tp.cast("CssAngle", _wrap_value(CssAngle, value, "deg"))


def rgb(red: int, green: int, blue: int) -> CssColor:
    """Return a CSS ``rgb(...)`` color value."""
    return CssColor(f"rgb({red} {green} {blue})")


def rgba(red: int, green: int, blue: int, alpha: float) -> CssColor:
    """Return a CSS ``rgb(... / alpha)`` color value."""
    return CssColor(f"rgb({red} {green} {blue} / {_format_number(alpha)})")


def hsl(hue: int | float, saturation: int | float, lightness: int | float) -> CssColor:
    """Return a CSS ``hsl(...)`` color value."""
    return CssColor(
        f"hsl({_format_number(hue)} {_format_number(saturation)}% {_format_number(lightness)}%)"
    )


def hwb(
    hue: int | float,
    whiteness: int | float,
    blackness: int | float,
    *,
    alpha: float | None = None,
) -> CssColor:
    """Return a CSS ``hwb(...)`` color value."""
    return CssColor(
        _serialize_color_function(
            "hwb",
            _format_number(hue),
            _format_percent(whiteness),
            _format_percent(blackness),
            alpha=alpha,
        )
    )


def lab(
    lightness: int | float,
    a_value: int | float,
    b_value: int | float,
    *,
    alpha: float | None = None,
) -> CssColor:
    """Return a CSS ``lab(...)`` color value."""
    return CssColor(
        _serialize_color_function(
            "lab",
            _format_percent(lightness),
            _format_number(a_value),
            _format_number(b_value),
            alpha=alpha,
        )
    )


def lch(
    lightness: int | float,
    chroma: int | float,
    hue: int | float,
    *,
    alpha: float | None = None,
) -> CssColor:
    """Return a CSS ``lch(...)`` color value."""
    return CssColor(
        _serialize_color_function(
            "lch",
            _format_percent(lightness),
            _format_number(chroma),
            _format_number(hue),
            alpha=alpha,
        )
    )


def oklab(
    lightness: int | float,
    a_value: int | float,
    b_value: int | float,
    *,
    alpha: float | None = None,
) -> CssColor:
    """Return a CSS ``oklab(...)`` color value."""
    return CssColor(
        _serialize_color_function(
            "oklab",
            _format_percent_unit_interval(lightness),
            _format_number(a_value),
            _format_number(b_value),
            alpha=alpha,
        )
    )


def oklch(
    lightness: int | float,
    chroma: int | float,
    hue: int | float,
    *,
    alpha: float | None = None,
) -> CssColor:
    """Return a CSS ``oklch(...)`` color value."""
    return CssColor(
        _serialize_color_function(
            "oklch",
            _format_percent_unit_interval(lightness),
            _format_number(chroma),
            _format_number(hue),
            alpha=alpha,
        )
    )


def color_space(
    space: str,
    *components: int | float | str,
    alpha: float | None = None,
) -> CssColor:
    """Return a CSS ``color(...)`` value for an explicit color space."""
    return CssColor(
        _serialize_color_function(
            "color",
            space,
            *(
                _format_number(component) if isinstance(component, (int, float)) else component
                for component in components
            ),
            alpha=alpha,
        )
    )


def var(name: str, fallback: StyleScalar | None = None) -> CssValue:
    """Return a CSS custom-property reference."""
    if fallback is None:
        return CssValue(f"var({name})")
    return CssValue(f"var({name}, {_serialize_helper_value(fallback, auto_px=False)})")


def calc(expression: str) -> CssValue:
    """Return a CSS ``calc(...)`` value."""
    return CssValue(f"calc({expression})")


def min_(*values: StyleScalar) -> CssValue:
    """Return a CSS ``min(...)`` value."""
    return CssValue(
        f"min({', '.join(_serialize_helper_value(value, auto_px=False) for value in values)})"
    )


def max_(*values: StyleScalar) -> CssValue:
    """Return a CSS ``max(...)`` value."""
    return CssValue(
        f"max({', '.join(_serialize_helper_value(value, auto_px=False) for value in values)})"
    )


def clamp(minimum: StyleScalar, preferred: StyleScalar, maximum: StyleScalar) -> CssValue:
    """Return a CSS ``clamp(...)`` value."""
    return CssValue(
        "clamp("
        f"{_serialize_helper_value(minimum, auto_px=False)}, "
        f"{_serialize_helper_value(preferred, auto_px=False)}, "
        f"{_serialize_helper_value(maximum, auto_px=False)})"
    )


def margin(*values: StyleScalar) -> CssValue:
    """Return a CSS ``margin`` shorthand value."""
    return CssValue(" ".join(_serialize_helper_value(value, auto_px=True) for value in values))


def padding(*values: StyleScalar) -> CssValue:
    """Return a CSS ``padding`` shorthand value."""
    return CssValue(" ".join(_serialize_helper_value(value, auto_px=True) for value in values))


def inset(*values: StyleScalar) -> CssValue:
    """Return a CSS ``inset`` shorthand value."""
    return CssValue(" ".join(_serialize_helper_value(value, auto_px=True) for value in values))


def border(width: StyleScalar, style: str, color_value: StyleScalar) -> CssValue:
    """Return a CSS ``border`` shorthand value."""
    return CssValue(
        f"{_serialize_helper_value(width, auto_px=True)} {style} {_serialize_helper_value(color_value, auto_px=False)}"
    )


def shadow(*parts: StyleScalar) -> CssValue:
    """Return a CSS shadow shorthand value."""
    return CssValue(" ".join(_serialize_helper_value(part, auto_px=False) for part in parts))


def scale(value: int | float) -> CssValue:
    """Return a CSS ``scale(...)`` transform value."""
    return CssValue(f"scale({_format_number(value)})")


def rotate(value: CssAngle | int | float) -> CssValue:
    """Return a CSS ``rotate(...)`` transform value."""
    serialized = _serialize_helper_value(
        value if isinstance(value, CssAngle) else deg(value), auto_px=False
    )
    return CssValue(f"rotate({serialized})")


def translate(x_value: StyleScalar, y_value: StyleScalar | None = None) -> CssValue:
    """Return a CSS ``translate(...)`` transform value."""
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
    """Create a typed CSS media rule for ``Style.media``.

    Use this for common responsive and user-preference queries. For
    unsupported queries, use the raw dict ``"@media ..."`` escape hatch
    instead.
    """

    return MediaRule(
        style=style,
        min_width=tp.cast(
            "tp.Any", min_width if not isinstance(min_width, (int, float)) else px(min_width)
        ),
        max_width=tp.cast(
            "tp.Any", max_width if not isinstance(max_width, (int, float)) else px(max_width)
        ),
        min_height=tp.cast(
            "tp.Any", min_height if not isinstance(min_height, (int, float)) else px(min_height)
        ),
        max_height=tp.cast(
            "tp.Any", max_height if not isinstance(max_height, (int, float)) else px(max_height)
        ),
        orientation=orientation,
        hover=hover,
        pointer=pointer,
        prefers_color_scheme=prefers_color_scheme,
        prefers_reduced_motion=prefers_reduced_motion,
        query=query,
    )


def _format_percent(value: int | float) -> str:
    return f"{_format_number(value)}%"


def _format_percent_unit_interval(value: int | float) -> str:
    if 0 <= value <= 1:
        return _format_percent(value * 100)
    return _format_percent(value)


def _serialize_color_function(
    name: str,
    *parts: str,
    alpha: float | None = None,
) -> str:
    if alpha is None:
        return f"{name}({' '.join(parts)})"
    return f"{name}({' '.join(parts)} / {_format_number(alpha)})"


def _serialize_helper_value(value: StyleScalar, *, auto_px: bool) -> str:
    if isinstance(value, CssValue):
        return value.css_text
    if isinstance(value, (int, float)):
        return f"{_format_number(value)}px" if auto_px else _format_number(value)
    return value
