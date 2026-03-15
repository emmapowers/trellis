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
    CssRawString,
    CssTime,
)
from trellis.html._css_primitives import (
    format_number as _format_number,
)

if tp.TYPE_CHECKING:
    from trellis.html._generated_style_types import HeightValue, SpacingShorthand, WidthValue

type StyleScalar = (
    int | float | CssRawString | CssLength | CssPercent | CssTime | CssAngle | CssColor
)
type RawStyleMapping = Mapping[str, tp.Any]

if tp.TYPE_CHECKING:
    type WidthInput = WidthValue | int | float
    type HeightInput = HeightValue | int | float
    type SpacingInput = SpacingShorthand | int | float
else:
    type WidthInput = int | float | CssRawString | CssLength | CssPercent
    type HeightInput = int | float | CssRawString | CssLength | CssPercent
    type SpacingInput = int | float | CssRawString | CssLength | CssPercent

__all__ = [
    "Css",
    "CssAngle",
    "CssClass",
    "CssColor",
    "CssInput",
    "CssLength",
    "CssPercent",
    "CssRawString",
    "CssTime",
    "HeightInput",
    "MediaRule",
    "RawStyleMapping",
    "SpacingInput",
    "Style",
    "StyleInput",
    "StyleScalar",
    "WidthInput",
    "border",
    "calc",
    "ch",
    "clamp",
    "color",
    "color_space",
    "cqh",
    "cqw",
    "deg",
    "dvh",
    "dvw",
    "em",
    "fr",
    "hsl",
    "hwb",
    "inset",
    "lab",
    "lch",
    "lvh",
    "lvw",
    "margin",
    "max_",
    "media",
    "min_",
    "ms",
    "oklab",
    "oklch",
    "padding",
    "pct",
    "px",
    "rad",
    "raw",
    "rem",
    "rgb",
    "rgba",
    "rotate",
    "scale",
    "sec",
    "shadow",
    "svh",
    "svw",
    "translate",
    "turn",
    "var",
    "vh",
    "vmax",
    "vmin",
    "vw",
]

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


class Css:
    """Inline CSS properties for ``style=`` on HTML elements and widgets.

    Use ``Css(...)`` for structured CSS properties and custom properties.
    For unsupported or highly dynamic cases, ``style`` also accepts raw
    dicts using DOM-style CSS keys.

    For hover, media queries, and selectors, use ``CssClass`` instead.
    """

    __slots__ = ("props", "vars")

    props: dict[str, tp.Any]
    vars: dict[str, StyleScalar]

    def __init__(self, _mapping: CssInput | None = None, /, **kwargs: tp.Any) -> None:
        self.props = {}
        self.vars = {}

        if _mapping is not None:
            self._consume_input(_mapping)
        self._consume_kwargs(kwargs)

    def _consume_input(self, style_input: CssInput) -> None:
        if isinstance(style_input, Css):
            self.props.update(style_input.props)
            self.vars.update(style_input.vars)
            return

        for key, value in style_input.items():
            if value is None:
                continue
            if key == "vars":
                self._consume_vars(tp.cast("Mapping[str, StyleScalar]", value))
                continue
            self.props[key] = value

    def _consume_kwargs(self, kwargs: dict[str, tp.Any]) -> None:
        vars_value = kwargs.pop("vars", None)
        if vars_value is not None:
            self._consume_vars(tp.cast("Mapping[str, StyleScalar]", vars_value))

        for key, value in kwargs.items():
            if value is None:
                continue
            self.props[key] = value

    def _consume_vars(self, vars_mapping: Mapping[str, StyleScalar]) -> None:
        for key, value in vars_mapping.items():
            self.vars[key] = value


class CssClass:
    """Named CSS class with selectors and media queries.

    Declare a class with hover/focus/media rules, then use ``str(...)``
    to get the CSS rules for a ``<style>`` element, and ``.class_name``
    to apply the class to elements.

    Example::

        card_style = h.CssClass("card",
            background_color="white",
            hover=h.Css(background_color="blue"),
            media=[h.media(min_width=640, style=h.Css(padding=24))],
        )
        with h.StyleTag(str(card_style)):
            pass
        h.Div(class_name=card_style.class_name)
    """

    __slots__ = ("class_name", "media", "props", "selectors", "vars")

    class_name: str
    props: dict[str, tp.Any]
    vars: dict[str, StyleScalar]
    selectors: dict[str, CssInput]
    media: list[MediaRule]

    def __init__(self, class_name: str, /, **kwargs: tp.Any) -> None:
        self.class_name = class_name
        self.props = {}
        self.vars = {}
        self.selectors = {}
        self.media = []
        self._consume_kwargs(kwargs)

    def _consume_kwargs(self, kwargs: dict[str, tp.Any]) -> None:
        vars_value = kwargs.pop("vars", None)
        if vars_value is not None:
            for key, value in vars_value.items():
                self.vars[key] = value

        selectors_value = kwargs.pop("selectors", None)
        if selectors_value is not None:
            for selector, nested_style in selectors_value.items():
                self.selectors[selector] = nested_style

        media_value = kwargs.pop("media", None)
        if media_value is not None:
            self._consume_media(media_value)

        for pseudo_name, selector in _PSEUDO_SELECTORS.items():
            pseudo_value = kwargs.pop(pseudo_name, None)
            if pseudo_value is not None:
                self.selectors[selector] = tp.cast("CssInput", pseudo_value)

        for key, value in kwargs.items():
            if value is None:
                continue
            self.props[key] = value

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
                raise TypeError("CssClass.media entries must be MediaRule instances")
            return

        raise TypeError("CssClass.media must be a mapping or iterable of MediaRule values")

    def __str__(self) -> str:
        # Local import to avoid circular dependency: _style_compiler imports from this module.
        from trellis.html._style_compiler import compile_css_class  # noqa: PLC0415

        return compile_css_class(self)


# Keep Style as an alias during migration
Style = Css

type CssInput = Css | RawStyleMapping
# Legacy alias
type StyleInput = CssInput


_CV = tp.TypeVar("_CV", CssRawString, CssLength, CssPercent, CssTime, CssAngle, CssColor)


def _wrap_value(
    cls: type[_CV],
    value: int | float | str,
    unit: str = "",
) -> _CV:
    if isinstance(value, (int, float)):
        return cls(f"{_format_number(value)}{unit}")
    return cls(value)


def raw(value: str) -> CssRawString:
    """Return a raw CSS value string without additional normalization."""
    return CssRawString(value)


def color(value: str) -> CssColor:
    """Return an arbitrary CSS color value."""
    return CssColor(value)


def px(value: int | float) -> CssLength:
    """Return a CSS length in pixels."""
    return _wrap_value(CssLength, value, "px")


def rem(value: int | float) -> CssLength:
    """Return a CSS length in rem units."""
    return _wrap_value(CssLength, value, "rem")


def em(value: int | float) -> CssLength:
    """Return a CSS length in em units."""
    return _wrap_value(CssLength, value, "em")


def vw(value: int | float) -> CssLength:
    """Return a CSS length in viewport-width units."""
    return _wrap_value(CssLength, value, "vw")


def vh(value: int | float) -> CssLength:
    """Return a CSS length in viewport-height units."""
    return _wrap_value(CssLength, value, "vh")


def pct(value: int | float) -> CssPercent:
    """Return a CSS percentage value."""
    return _wrap_value(CssPercent, value, "%")


def sec(value: int | float) -> CssTime:
    """Return a CSS time value in seconds."""
    return _wrap_value(CssTime, value, "s")


def ms(value: int | float) -> CssTime:
    """Return a CSS time value in milliseconds."""
    return _wrap_value(CssTime, value, "ms")


def deg(value: int | float) -> CssAngle:
    """Return a CSS angle value in degrees."""
    return _wrap_value(CssAngle, value, "deg")


def rad(value: int | float) -> CssAngle:
    """Return a CSS angle value in radians."""
    return _wrap_value(CssAngle, value, "rad")


def turn(value: int | float) -> CssAngle:
    """Return a CSS angle value in turns."""
    return _wrap_value(CssAngle, value, "turn")


def ch(value: int | float) -> CssLength:
    """Return a CSS length in ch units (character width)."""
    return _wrap_value(CssLength, value, "ch")


def vmin(value: int | float) -> CssLength:
    """Return a CSS length in vmin units."""
    return _wrap_value(CssLength, value, "vmin")


def vmax(value: int | float) -> CssLength:
    """Return a CSS length in vmax units."""
    return _wrap_value(CssLength, value, "vmax")


def dvh(value: int | float) -> CssLength:
    """Return a CSS length in dynamic viewport height units."""
    return _wrap_value(CssLength, value, "dvh")


def dvw(value: int | float) -> CssLength:
    """Return a CSS length in dynamic viewport width units."""
    return _wrap_value(CssLength, value, "dvw")


def svh(value: int | float) -> CssLength:
    """Return a CSS length in small viewport height units."""
    return _wrap_value(CssLength, value, "svh")


def svw(value: int | float) -> CssLength:
    """Return a CSS length in small viewport width units."""
    return _wrap_value(CssLength, value, "svw")


def lvh(value: int | float) -> CssLength:
    """Return a CSS length in large viewport height units."""
    return _wrap_value(CssLength, value, "lvh")


def lvw(value: int | float) -> CssLength:
    """Return a CSS length in large viewport width units."""
    return _wrap_value(CssLength, value, "lvw")


def cqw(value: int | float) -> CssLength:
    """Return a CSS length in container query width units."""
    return _wrap_value(CssLength, value, "cqw")


def cqh(value: int | float) -> CssLength:
    """Return a CSS length in container query height units."""
    return _wrap_value(CssLength, value, "cqh")


def fr(value: int | float) -> CssLength:
    """Return a CSS flex fraction unit for grid layouts."""
    return _wrap_value(CssLength, value, "fr")


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


def var(name: str, fallback: StyleScalar | None = None) -> CssRawString:
    """Return a CSS custom-property reference."""
    if fallback is None:
        return CssRawString(f"var({name})")
    return CssRawString(f"var({name}, {_serialize_helper_value(fallback, auto_px=False)})")


def calc(expression: str) -> CssRawString:
    """Return a CSS ``calc(...)`` value."""
    return CssRawString(f"calc({expression})")


def min_(*values: StyleScalar) -> CssRawString:
    """Return a CSS ``min(...)`` value."""
    return CssRawString(
        f"min({', '.join(_serialize_helper_value(value, auto_px=False) for value in values)})"
    )


def max_(*values: StyleScalar) -> CssRawString:
    """Return a CSS ``max(...)`` value."""
    return CssRawString(
        f"max({', '.join(_serialize_helper_value(value, auto_px=False) for value in values)})"
    )


def clamp(minimum: StyleScalar, preferred: StyleScalar, maximum: StyleScalar) -> CssRawString:
    """Return a CSS ``clamp(...)`` value."""
    return CssRawString(
        "clamp("
        f"{_serialize_helper_value(minimum, auto_px=False)}, "
        f"{_serialize_helper_value(preferred, auto_px=False)}, "
        f"{_serialize_helper_value(maximum, auto_px=False)})"
    )


def margin(*values: StyleScalar) -> CssRawString:
    """Return a CSS ``margin`` shorthand value."""
    return CssRawString(" ".join(_serialize_helper_value(value, auto_px=True) for value in values))


def padding(*values: StyleScalar) -> CssRawString:
    """Return a CSS ``padding`` shorthand value."""
    return CssRawString(" ".join(_serialize_helper_value(value, auto_px=True) for value in values))


def inset(*values: StyleScalar) -> CssRawString:
    """Return a CSS ``inset`` shorthand value."""
    return CssRawString(" ".join(_serialize_helper_value(value, auto_px=True) for value in values))


def border(width: StyleScalar, style: str, color_value: StyleScalar) -> CssRawString:
    """Return a CSS ``border`` shorthand value."""
    return CssRawString(
        f"{_serialize_helper_value(width, auto_px=True)} {style} {_serialize_helper_value(color_value, auto_px=False)}"
    )


def shadow(*parts: StyleScalar) -> CssRawString:
    """Return a CSS shadow shorthand value."""
    return CssRawString(" ".join(_serialize_helper_value(part, auto_px=True) for part in parts))


def scale(value: int | float) -> CssRawString:
    """Return a CSS ``scale(...)`` transform value."""
    return CssRawString(f"scale({_format_number(value)})")


def rotate(value: CssAngle | int | float) -> CssRawString:
    """Return a CSS ``rotate(...)`` transform value."""
    serialized = _serialize_helper_value(
        value if isinstance(value, CssAngle) else deg(value), auto_px=False
    )
    return CssRawString(f"rotate({serialized})")


def translate(x_value: StyleScalar, y_value: StyleScalar | None = None) -> CssRawString:
    """Return a CSS ``translate(...)`` transform value."""
    x = _serialize_helper_value(x_value, auto_px=True)
    if y_value is None:
        return CssRawString(f"translate({x})")
    return CssRawString(f"translate({x}, {_serialize_helper_value(y_value, auto_px=True)})")


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


_CSS_TYPES = (CssRawString, CssLength, CssPercent, CssTime, CssAngle, CssColor)


def _serialize_helper_value(value: StyleScalar, *, auto_px: bool) -> str:
    if isinstance(value, _CSS_TYPES):
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
