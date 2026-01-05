"""ThemeSwitcher widget for toggling between system/light/dark themes.

A single button that cycles through theme modes on click.
"""

from __future__ import annotations

from trellis import component
from trellis import widgets as w
from trellis.app import ClientState, ThemeMode
from trellis.widgets.icons import IconName

# Mode cycle order and display info
_MODES = [
    (ThemeMode.SYSTEM, IconName.MONITOR),
    (ThemeMode.LIGHT, IconName.SUN),
    (ThemeMode.DARK, IconName.MOON),
]


def _get_next_mode(current: ThemeMode) -> ThemeMode:
    """Get the next mode in the cycle."""
    for i, (mode, _) in enumerate(_MODES):
        if mode == current:
            return _MODES[(i + 1) % len(_MODES)][0]
    return ThemeMode.SYSTEM


def _get_icon_for_mode(mode: ThemeMode) -> IconName:
    """Get the icon for a mode."""
    for m, icon in _MODES:
        if m == mode:
            return icon
    return IconName.MONITOR


@component
def ThemeSwitcher() -> None:
    """Theme mode switcher - single button that cycles through modes.

    Click to cycle through: System → Light → Dark → System...

    The icon shown reflects the current mode:
    - Monitor icon = System (follows OS preference)
    - Sun icon = Light mode
    - Moon icon = Dark mode
    """
    client_state = ClientState.from_context()
    icon = _get_icon_for_mode(client_state.theme_setting)

    def handle_click() -> None:
        next_mode = _get_next_mode(client_state.theme_setting)
        client_state.set_mode(next_mode)

    w.Button(icon=icon, variant="ghost", size="sm", on_click=handle_click)
