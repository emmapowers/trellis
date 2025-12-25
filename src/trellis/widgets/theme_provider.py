"""ThemeProvider widget for CSS-based theming.

The ThemeProvider manages the data-theme attribute on the trellis-root element,
enabling CSS selectors like `[data-theme="dark"]` for styling widgets.

The React component listens for OS theme changes (via matchMedia) when mode
is "system" and calls back to Python to update the theme state.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from trellis.core.client_state import ThemeMode
from trellis.core.react_component import react_component_base
from trellis.core.rendering import ElementNode


@react_component_base("ThemeProvider", has_children=True)
def ThemeProvider(
    *,
    mode: ThemeMode | Literal["system", "light", "dark"],
    resolved_theme: ThemeMode | Literal["light", "dark"],
    root_id: str | None = None,
    on_system_theme_change: Callable[[Literal["light", "dark"]], None] | None = None,
    on_theme_mode_change: Callable[[Literal["system", "light", "dark"]], None] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Theme provider that manages the data-theme attribute on trellis-root.

    Updates the data-theme attribute on the trellis-root element based on
    resolved_theme, and listens for OS theme changes when mode is "system".

    Args:
        mode: The user's theme mode preference ("system", "light", or "dark").
            When "system", the component listens for OS theme changes.
        resolved_theme: The actual theme to apply ("light" or "dark").
            This is what gets set as the data-theme attribute.
        root_id: ID of the trellis-root element. If not provided, finds
            the element by .trellis-root class.
        on_system_theme_change: Callback invoked when OS theme changes.
            Only called when mode is "system". Receives the new theme
            as a string ("light" or "dark").
        on_theme_mode_change: Callback invoked when host application changes
            the theme mode (for browser extension use). Receives the new mode
            as a string ("system", "light", or "dark").
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the ThemeProvider component.

    Example:
        with ThemeProvider(
            mode=theme.mode,
            resolved_theme=theme.resolved_theme,
            on_system_theme_change=theme.handle_system_theme_change,
        ):
            Label(text="This content is themed")
            Button(text="Click me")
    """
    ...
