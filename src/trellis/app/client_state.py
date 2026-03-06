"""Client state for Trellis apps.

Provides runtime theme-mode state for system/light/dark handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, auto

from trellis.core.state import Stateful

# =============================================================================
# Enums for client state
# =============================================================================


class ThemeMode(StrEnum):
    """Theme mode preference.

    SYSTEM follows the OS preference and updates when it changes.
    LIGHT and DARK are explicit overrides that ignore OS preference.
    """

    SYSTEM = auto()
    LIGHT = auto()
    DARK = auto()


# =============================================================================
# ClientState - reactive state for the client
# =============================================================================


@dataclass(kw_only=True)
class ClientState(Stateful):
    """Reactive runtime theme-mode state for the current client."""

    # Theme state
    theme_setting: ThemeMode = ThemeMode.SYSTEM
    system_theme: ThemeMode = ThemeMode.LIGHT

    # needed to set the theme attribute
    root_element_id: str = ""

    # -------------------------------------------------------------------------
    # Theme properties
    # -------------------------------------------------------------------------

    @property
    def theme(self) -> ThemeMode:
        """The actual theme to apply (LIGHT or DARK).

        When mode is SYSTEM, returns the detected OS theme.
        Otherwise returns the explicit mode setting.
        """
        if self.theme_setting == ThemeMode.SYSTEM:
            return self.system_theme
        return self.theme_setting

    @property
    def is_dark(self) -> bool:
        """Check if dark theme should be applied."""
        return self.theme == ThemeMode.DARK

    @property
    def is_light(self) -> bool:
        """Check if light theme should be applied."""
        return self.theme == ThemeMode.LIGHT

    # -------------------------------------------------------------------------
    # Theme methods
    # -------------------------------------------------------------------------

    def set_mode(self, mode: ThemeMode) -> None:
        """Set the theme mode.

        Args:
            mode: The mode to set (SYSTEM, LIGHT, or DARK)
        """
        self.theme_setting = mode

    def toggle(self) -> None:
        """Cycle through theme modes: SYSTEM → LIGHT → DARK → SYSTEM."""
        if self.theme_setting == ThemeMode.SYSTEM:
            self.theme_setting = ThemeMode.LIGHT
        elif self.theme_setting == ThemeMode.LIGHT:
            self.theme_setting = ThemeMode.DARK
        else:
            self.theme_setting = ThemeMode.SYSTEM

    def handle_system_theme_change(self, new_theme: ThemeMode) -> None:
        """Handle OS theme change notification from client.

        Updates system_theme regardless of current theme_setting, so that
        switching back to SYSTEM mode will immediately reflect the OS theme.
        Called by TrellisApp when the client detects an OS theme change.

        Args:
            new_theme: The new OS theme (LIGHT or DARK, not SYSTEM)

        Raises:
            ValueError: If new_theme is SYSTEM
        """
        if new_theme == ThemeMode.SYSTEM:
            raise ValueError("System theme change must be LIGHT or DARK, not SYSTEM")
        self.system_theme = new_theme
