"""Internal typed CSS primitive values.

Each type is an independent frozen dataclass wrapping a ``css_text`` string.
They are deliberately *not* related by inheritance so that the type checker
can distinguish between them — e.g. ``CssLength`` is not assignable to a
slot expecting ``CssAngle``.  ``CssRawString`` is the explicit escape hatch
returned by ``h.raw()``; it is accepted wherever any CSS value is needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite as _isfinite


@dataclass(frozen=True, slots=True)
class CssRawString:
    """Untyped CSS value — the explicit escape hatch via ``h.raw()``."""

    css_text: str

    def __str__(self) -> str:
        return self.css_text


@dataclass(frozen=True, slots=True)
class CssLength:
    """A CSS length value (px, rem, em, ch, vw, vh, …)."""

    css_text: str

    def __str__(self) -> str:
        return self.css_text


@dataclass(frozen=True, slots=True)
class CssPercent:
    """A CSS percentage value."""

    css_text: str

    def __str__(self) -> str:
        return self.css_text


@dataclass(frozen=True, slots=True)
class CssTime:
    """A CSS time value (s, ms)."""

    css_text: str

    def __str__(self) -> str:
        return self.css_text


@dataclass(frozen=True, slots=True)
class CssAngle:
    """A CSS angle value (deg, rad, turn, grad)."""

    css_text: str

    def __str__(self) -> str:
        return self.css_text


@dataclass(frozen=True, slots=True)
class CssColor:
    """A CSS color value."""

    css_text: str

    def __str__(self) -> str:
        return self.css_text


def format_number(value: int | float) -> str:
    """Format a number for CSS output, dropping unnecessary decimals."""
    if isinstance(value, bool):
        raise TypeError("Boolean values are not valid CSS numbers.")
    if isinstance(value, float) and not _isfinite(value):
        raise ValueError("CSS numbers must be finite.")
    if isinstance(value, int) or value.is_integer():
        return str(int(value))
    return format(value, "g")
