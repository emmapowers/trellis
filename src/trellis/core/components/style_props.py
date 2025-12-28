"""Ergonomic styling props for widgets.

These dataclasses provide a clean API for common CSS properties,
avoiding the need to construct style dicts for simple layouts.

Usage:
    # Simple values (shorthand for all sides)
    w.Card(margin=8)           # margin: 8px
    w.Card(padding=16)         # padding: 16px

    # Specific sides
    w.Card(margin=Margin(top=8, bottom=16))
    w.Card(margin=Margin(x=8))  # left and right
    w.Card(margin=Margin(y=16)) # top and bottom

    # Width/height with constraints
    w.Card(width=200)
    w.Card(width=Width(value=200, min=100, max=400))
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Margin:
    """Margin specification for widgets.

    Args:
        top: Top margin in pixels
        bottom: Bottom margin in pixels
        left: Left margin in pixels
        right: Right margin in pixels
        x: Horizontal margins (left and right) in pixels
        y: Vertical margins (top and bottom) in pixels

    The x/y shorthands are overridden by specific sides if both are provided.
    """

    top: int | None = None
    bottom: int | None = None
    left: int | None = None
    right: int | None = None
    x: int | None = None
    y: int | None = None

    def to_style(self) -> dict[str, str]:
        """Convert to CSS style dict with marginTop, marginBottom, etc."""
        style: dict[str, str] = {}

        # y expands to top/bottom, x expands to left/right
        # Specific values override the shorthands
        top = self.top if self.top is not None else self.y
        bottom = self.bottom if self.bottom is not None else self.y
        left = self.left if self.left is not None else self.x
        right = self.right if self.right is not None else self.x

        if top is not None:
            style["marginTop"] = f"{top}px"
        if bottom is not None:
            style["marginBottom"] = f"{bottom}px"
        if left is not None:
            style["marginLeft"] = f"{left}px"
        if right is not None:
            style["marginRight"] = f"{right}px"

        return style


@dataclass(frozen=True, slots=True)
class Padding:
    """Padding specification for widgets.

    Args:
        top: Top padding in pixels
        bottom: Bottom padding in pixels
        left: Left padding in pixels
        right: Right padding in pixels
        x: Horizontal padding (left and right) in pixels
        y: Vertical padding (top and bottom) in pixels

    The x/y shorthands are overridden by specific sides if both are provided.
    """

    top: int | None = None
    bottom: int | None = None
    left: int | None = None
    right: int | None = None
    x: int | None = None
    y: int | None = None

    def to_style(self) -> dict[str, str]:
        """Convert to CSS style dict with paddingTop, paddingBottom, etc."""
        style: dict[str, str] = {}

        top = self.top if self.top is not None else self.y
        bottom = self.bottom if self.bottom is not None else self.y
        left = self.left if self.left is not None else self.x
        right = self.right if self.right is not None else self.x

        if top is not None:
            style["paddingTop"] = f"{top}px"
        if bottom is not None:
            style["paddingBottom"] = f"{bottom}px"
        if left is not None:
            style["paddingLeft"] = f"{left}px"
        if right is not None:
            style["paddingRight"] = f"{right}px"

        return style


@dataclass(frozen=True, slots=True)
class Width:
    """Width specification with optional constraints.

    Args:
        value: The width value (int for pixels, str for CSS values like "100%")
        min: Minimum width constraint
        max: Maximum width constraint
    """

    value: int | str | None = None
    min: int | str | None = None
    max: int | str | None = None

    def to_style(self) -> dict[str, str]:
        """Convert to CSS style dict with width, minWidth, maxWidth."""
        style: dict[str, str] = {}

        if self.value is not None:
            style["width"] = f"{self.value}px" if isinstance(self.value, int) else self.value
        if self.min is not None:
            style["minWidth"] = f"{self.min}px" if isinstance(self.min, int) else self.min
        if self.max is not None:
            style["maxWidth"] = f"{self.max}px" if isinstance(self.max, int) else self.max

        return style


@dataclass(frozen=True, slots=True)
class Height:
    """Height specification with optional constraints.

    Args:
        value: The height value (int for pixels, str for CSS values like "100%")
        min: Minimum height constraint
        max: Maximum height constraint
    """

    value: int | str | None = None
    min: int | str | None = None
    max: int | str | None = None

    def to_style(self) -> dict[str, str]:
        """Convert to CSS style dict with height, minHeight, maxHeight."""
        style: dict[str, str] = {}

        if self.value is not None:
            style["height"] = f"{self.value}px" if isinstance(self.value, int) else self.value
        if self.min is not None:
            style["minHeight"] = f"{self.min}px" if isinstance(self.min, int) else self.min
        if self.max is not None:
            style["maxHeight"] = f"{self.max}px" if isinstance(self.max, int) else self.max

        return style
