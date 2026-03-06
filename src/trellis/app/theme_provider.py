"""ThemeProvider widget for runtime theme-mode application.

The ThemeProvider manages shadcn-compatible root theme classes on the
``.trellis-root`` element and keeps Python in sync with OS theme changes.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from trellis.core.components.react import react


@react("client/ThemeProvider.tsx", is_container=True)
def ThemeProvider(
    *,
    theme_setting: Literal["system", "light", "dark"],
    theme: Literal["light", "dark"],
    root_id: str | None = None,
    on_system_theme_change: Callable[[Literal["light", "dark"]], None] | None = None,
    on_theme_mode_change: Callable[[Literal["system", "light", "dark"]], None] | None = None,
    key: str | None = None,
) -> None:
    """Theme provider that manages shadcn-compatible theme classes on trellis-root.

    Updates the ``.dark`` class on the trellis-root element based on ``theme``
    and listens for OS theme changes when ``theme_setting`` is ``"system"``.

    Args:
        theme_setting: The user's theme mode preference ("system", "light", or "dark").
            When "system", the component listens for OS theme changes.
        theme: The actual theme to apply ("light" or "dark").
            This controls whether the trellis root carries the ``dark`` class.
        root_id: ID of the trellis-root element. If not provided, finds
            the element by .trellis-root class.
        on_system_theme_change: Callback invoked when OS theme changes.
            Always called regardless of current theme_setting, so switching back
            to "system" mode reflects the current OS theme. Receives the
            new theme as a string ("light" or "dark").
        on_theme_mode_change: Callback invoked when host application changes
            the theme mode (for browser extension use). Receives the new mode
            as a string ("system", "light", or "dark").
        key: Optional key for reconciliation.
    """
    pass
