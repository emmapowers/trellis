"""Keyboard shortcut display widget."""

from __future__ import annotations

import typing as tp

from trellis.core.components.react import react


@react("client/Kbd.tsx")
def Kbd(
    keys: str = "",
    *,
    style: dict[str, tp.Any] | None = None,
) -> None:
    """Display a keyboard shortcut with platform-appropriate symbols.

    Resolves modifier names to platform symbols client-side:
    - ``Mod`` becomes ``⌘`` on Mac, ``Ctrl`` elsewhere
    - ``Alt`` becomes ``⌥`` on Mac, ``Alt`` elsewhere
    - Arrow keys, Enter, Escape, etc. become Unicode symbols

    The ``keys`` format matches HotKey filter strings, so the same
    string can be passed to both::

        HotKey(filter="Mod+S", handler=save)
        w.Kbd(keys="Mod+S")  # renders ⌘+S on Mac, Ctrl+S on others

    Args:
        keys: Key filter string (e.g. "Mod+S", "Shift+?", "Alt+ArrowLeft").
        style: Additional inline styles.
    """
    pass
