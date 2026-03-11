"""Typed CSS runtime helpers exposed from trellis.html.

Use these helpers with ``style=...`` on HTML elements and widgets:

- ``Style(...)`` for structured, typed CSS declarations
- raw dicts with DOM-style CSS keys for escape-hatch usage
- helper functions like ``px(...)``, ``rgb(...)``, ``border(...)``, and ``media(...)``
  for common CSS values and shorthands
"""

from __future__ import annotations

import typing as tp
from collections.abc import Iterable, Mapping

from trellis.html._css_primitives import (
    CssAngle,
    CssColor,
    CssLength,
    CssPercent,
    CssTime,
    CssValue,
)

if tp.TYPE_CHECKING:
    from trellis.html._generated_style_types import HeightValue, SpacingShorthand, WidthValue

type StyleScalar = str | int | float | CssValue
type RawStyleMapping = Mapping[str, tp.Any]

if tp.TYPE_CHECKING:
    type WidthInput = WidthValue | int | float | str
    type HeightInput = HeightValue | int | float | str
    type SpacingInput = SpacingShorthand | int | float | str
else:
    type WidthInput = str | int | float | CssValue
    type HeightInput = str | int | float | CssValue
    type SpacingInput = str | int | float | CssValue

_PSEUDO_SELECTORS = {
    "hover": ":hover",
    "focus": ":focus",
    "focus_visible": ":focus-visible",
    "focus_within": ":focus-within",
    "active": ":active",
    "visited": ":visited",
    "disabled": ":disabled",
    "checked": ":checked",
    "placeholder": "::placeholder",
    "before": "::before",
    "after": "::after",
    "selection": "::selection",
}


class MediaRule:
    """Runtime representation of a CSS media rule."""

    __slots__ = ("features", "query", "style")

    def __init__(
        self,
        *,
        style: StyleInput,
        query: str | None = None,
        **feature_values: tp.Any,
    ) -> None:
        self.style = style
        self.query = query
        self.features = {name: value for name, value in feature_values.items() if value is not None}


class Style:
    """Structured CSS style input for ``trellis.html``.

    Use ``Style(...)`` for structured CSS properties, pseudo states, media
    queries, selectors, and custom properties. For unsupported or highly
    dynamic cases, ``style`` also accepts raw dicts using DOM-style CSS keys.
    """

    __slots__ = ("media", "props", "selectors", "vars")

    props: dict[str, tp.Any]
    vars: dict[str, StyleScalar]
    selectors: dict[str, StyleInput]
    media: list[MediaRule]

    def __init__(self, _mapping: StyleInput | None = None, /, **kwargs: tp.Any) -> None:
        self.props = {}
        self.vars = {}
        self.selectors = {}
        self.media = []

        if _mapping is not None:
            self._consume_input(_mapping)
        self._consume_kwargs(kwargs)

    def _consume_input(self, style_input: StyleInput) -> None:
        if isinstance(style_input, Style):
            self.props.update(style_input.props)
            self.vars.update(style_input.vars)
            self.selectors.update(style_input.selectors)
            self.media.extend(style_input.media)
            return

        for key, value in style_input.items():
            if value is None:
                continue
            if key == "vars":
                self._consume_vars(tp.cast("Mapping[str, StyleScalar]", value))
                continue
            if key == "selectors":
                self._consume_selectors(tp.cast("Mapping[str, StyleInput]", value))
                continue
            if key == "media":
                self._consume_media(value)
                continue
            if key in _PSEUDO_SELECTORS:
                self.selectors[_PSEUDO_SELECTORS[key]] = tp.cast("StyleInput", value)
                continue
            if key.startswith("@media "):
                self.media.append(MediaRule(query=key.removeprefix("@media ").strip(), style=value))
                continue
            if key.startswith(":") or "&" in key:
                self.selectors[key] = tp.cast("StyleInput", value)
                continue
            self.props[key] = value

    def _consume_kwargs(self, kwargs: dict[str, tp.Any]) -> None:
        vars_value = kwargs.pop("vars", None)
        if vars_value is not None:
            self._consume_vars(tp.cast("Mapping[str, StyleScalar]", vars_value))

        selectors_value = kwargs.pop("selectors", None)
        if selectors_value is not None:
            self._consume_selectors(tp.cast("Mapping[str, StyleInput]", selectors_value))

        media_value = kwargs.pop("media", None)
        if media_value is not None:
            self._consume_media(media_value)

        for pseudo_name, selector in _PSEUDO_SELECTORS.items():
            pseudo_value = kwargs.pop(pseudo_name, None)
            if pseudo_value is not None:
                self.selectors[selector] = tp.cast("StyleInput", pseudo_value)

        for key, value in kwargs.items():
            if value is None:
                continue
            self.props[key] = value

    def _consume_vars(self, vars_mapping: Mapping[str, StyleScalar]) -> None:
        for key, value in vars_mapping.items():
            self.vars[key] = value

    def _consume_selectors(self, selectors: Mapping[str, StyleInput]) -> None:
        for selector, nested_style in selectors.items():
            self.selectors[selector] = nested_style

    def _consume_media(self, media_value: tp.Any) -> None:
        if isinstance(media_value, Mapping):
            for query, nested_style in media_value.items():
                normalized_query = query.removeprefix("@media ").strip()
                self.media.append(MediaRule(query=normalized_query, style=nested_style))
            return

        if isinstance(media_value, Iterable) and not isinstance(media_value, (str, bytes)):
            for item in media_value:
                if isinstance(item, MediaRule):
                    self.media.append(item)
                    continue
                raise TypeError("Style.media entries must be MediaRule instances")
            return

        raise TypeError("Style.media must be a mapping or iterable of MediaRule values")


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
    return CssValue(" ".join(_serialize_helper_value(part, auto_px=True) for part in parts))


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


def media(*, style: StyleInput, query: str | None = None, **feature_values: tp.Any) -> MediaRule:
    """Create a typed CSS media rule for ``Style.media``.

    Use this for common responsive and user-preference queries. For
    unsupported queries, use the raw dict ``"@media ..."`` escape hatch
    instead.
    """

    return MediaRule(style=style, query=query, **_normalize_media_kwargs(feature_values))


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


def _normalize_media_kwargs(
    feature_values: Mapping[str, tp.Any],
) -> dict[str, tp.Any]:
    normalized: dict[str, tp.Any] = {}
    for name, value in feature_values.items():
        if value is None:
            continue
        if isinstance(value, (int, float)) and ("width" in name or "height" in name):
            normalized[name] = px(value)
            continue
        normalized[name] = value
    return normalized
