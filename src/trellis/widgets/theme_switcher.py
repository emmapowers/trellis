"""ThemeSwitcher widget for toggling between system/light/dark themes.

A single button that cycles through theme modes on click.
Accesses ClientState via context - must be used inside TrellisApp.
"""

from __future__ import annotations

from trellis import component
from trellis import html as h
from trellis import widgets as w
from trellis.core.client_state import ClientState, ThemeMode, theme
from trellis.widgets.icons import IconName

# Mode cycle order and display info
_MODES = [
    (ThemeMode.SYSTEM, IconName.MONITOR, "System theme"),
    (ThemeMode.LIGHT, IconName.SUN, "Light theme"),
    (ThemeMode.DARK, IconName.MOON, "Dark theme"),
]


def _get_next_mode(current: ThemeMode) -> ThemeMode:
    """Get the next mode in the cycle."""
    for i, (mode, _, _) in enumerate(_MODES):
        if mode == current:
            return _MODES[(i + 1) % len(_MODES)][0]
    return ThemeMode.SYSTEM


def _get_icon_for_mode(mode: ThemeMode) -> tuple[IconName, str]:
    """Get the icon and tooltip for a mode."""
    for m, icon, tooltip in _MODES:
        if m == mode:
            return icon, tooltip
    return IconName.MONITOR, "System theme"


@component
def ThemeSwitcher() -> None:
    """Theme mode switcher - single button that cycles through modes.

    Click to cycle through: System → Light → Dark → System...

    The icon shown reflects the current mode:
    - Monitor icon = System (follows OS preference)
    - Sun icon = Light mode
    - Moon icon = Dark mode

    Must be used inside a TrellisApp wrapper to access ClientState via context.
    """
    client_state = ClientState.from_context()

    icon, tooltip = _get_icon_for_mode(client_state.mode)

    def handle_click(*_args: object) -> None:
        next_mode = _get_next_mode(client_state.mode)
        client_state.set_mode(next_mode)

    with h.Div(
        onClick=handle_click,
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "width": "32px",
            "height": "32px",
            "borderRadius": "6px",
            "cursor": "pointer",
            "transition": "all 0.15s ease",
            "backgroundColor": theme.bg_surface_hover,
            "color": theme.text_secondary,
        },
        title=tooltip,
    ):
        w.Icon(name=icon, size=16)
