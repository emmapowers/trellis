"""Internal typed CSS primitive values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CssValue:
    """Base wrapper for structured CSS values."""

    css_text: str

    def __str__(self) -> str:
        return self.css_text


@dataclass(frozen=True, slots=True)
class CssLength(CssValue):
    """A CSS length value."""


@dataclass(frozen=True, slots=True)
class CssPercent(CssValue):
    """A CSS percentage value."""


@dataclass(frozen=True, slots=True)
class CssTime(CssValue):
    """A CSS time value."""


@dataclass(frozen=True, slots=True)
class CssAngle(CssValue):
    """A CSS angle value."""


@dataclass(frozen=True, slots=True)
class CssColor(CssValue):
    """A CSS color value."""


def format_number(value: int | float) -> str:
    """Format a number for CSS output, dropping unnecessary decimals."""
    if isinstance(value, int) or value.is_integer():
        return str(int(value))
    return format(value, "g")
