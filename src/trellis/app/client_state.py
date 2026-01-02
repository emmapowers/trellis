"""Client state for Trellis apps.

Provides ClientState for reactive client state management including theme,
device type, OS, and browser info. Also exports theme tokens (CSS variable
references) for use in widget styles.

Example:
    ```python
    from trellis.app import ClientState
    from trellis.app import theme

    @component
    def MyComponent():
        state = ClientState.from_context()
        if state.is_dark:
            w.Label(text="Dark mode is active")
        w.Button(text="Toggle", on_click=state.toggle)

        # Use theme tokens in styles
        h.Div(style={"background": theme.bg_surface, "color": theme.text_primary})
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Literal

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


class DeviceType(StrEnum):
    """Device type detected from user agent."""

    UNKNOWN = auto()
    WEB = auto()
    DESKTOP = auto()
    MOBILE = auto()


class OperatingSystem(StrEnum):
    """Operating system detected from user agent."""

    UNKNOWN = auto()
    MACOS = auto()
    WINDOWS = auto()
    LINUX = auto()
    IOS = auto()
    ANDROID = auto()


class Browser(StrEnum):
    """Browser detected from user agent."""

    UNKNOWN = auto()
    CHROME = auto()
    FIREFOX = auto()
    SAFARI = auto()
    EDGE = auto()


# =============================================================================
# Theme tokens - CSS variable references for use in styles
# =============================================================================


@dataclass(frozen=True)
class ThemeTokens:
    """CSS variable references matching theme.css exactly.

    Use these tokens in inline styles to reference theme colors that
    adapt to light/dark mode. All values are CSS var() references.

    Example:
        h.Div(style={"background": theme.bg_surface, "color": theme.text_primary})
    """

    # Backgrounds
    bg_page: str = "var(--trellis-bg-page)"
    bg_surface: str = "var(--trellis-bg-surface)"
    bg_surface_raised: str = "var(--trellis-bg-surface-raised)"
    bg_surface_hover: str = "var(--trellis-bg-surface-hover)"
    bg_input: str = "var(--trellis-bg-input)"
    bg_interactive: str = "var(--trellis-bg-interactive)"
    bg_interactive_hover: str = "var(--trellis-bg-interactive-hover)"
    # Borders
    border_default: str = "var(--trellis-border-default)"
    border_subtle: str = "var(--trellis-border-subtle)"
    border_strong: str = "var(--trellis-border-strong)"
    border_focus: str = "var(--trellis-border-focus)"
    # Text
    text_primary: str = "var(--trellis-text-primary)"
    text_secondary: str = "var(--trellis-text-secondary)"
    text_muted: str = "var(--trellis-text-muted)"
    text_inverse: str = "var(--trellis-text-inverse)"
    # Semantic
    success: str = "var(--trellis-success)"
    error: str = "var(--trellis-error)"
    error_hover: str = "var(--trellis-error-hover)"
    warning: str = "var(--trellis-warning)"
    info: str = "var(--trellis-info)"
    # Accent
    accent_primary: str = "var(--trellis-accent-primary)"
    accent_primary_hover: str = "var(--trellis-accent-primary-hover)"
    accent_subtle: str = "var(--trellis-accent-subtle)"
    # Shadows
    shadow_sm: str = "var(--trellis-shadow-sm)"
    shadow_md: str = "var(--trellis-shadow-md)"
    shadow_lg: str = "var(--trellis-shadow-lg)"
    # Focus
    focus_ring_color: str = "var(--trellis-focus-ring-color)"


# Singleton instance for use in styles
theme = ThemeTokens()


# =============================================================================
# ClientState - reactive state for the client
# =============================================================================


@dataclass(kw_only=True)
class ClientState(Stateful):
    """Reactive client state including theme, device info, and more.

    Tracks both the user's theme mode preference (system/light/dark) and the
    resolved theme that should actually be applied. When mode is SYSTEM,
    the resolved theme follows the OS preference and updates automatically.

    Also provides access to device information detected at connection time.

    Attributes:
        mode: The user's theme mode preference (SYSTEM, LIGHT, or DARK)
        system_theme: The OS theme preference detected from the client
        device_type: Device type (web, desktop, mobile)
        os: Operating system
        browser: Browser name
        root_element_id: ID of the trellis-root element in the DOM
    """

    # Theme state
    theme_setting: ThemeMode = ThemeMode.SYSTEM
    system_theme: ThemeMode = ThemeMode.LIGHT

    # Device info (set at connection time, typically not changed after)
    device_type: DeviceType = DeviceType.UNKNOWN
    os: OperatingSystem = OperatingSystem.UNKNOWN
    browser: Browser = Browser.UNKNOWN
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

    def set_mode(self, mode: ThemeMode | Literal["system", "light", "dark"]) -> None:
        """Set the theme mode.

        Args:
            mode: The mode to set (SYSTEM, LIGHT, DARK, or string equivalent)

        Raises:
            ValueError: If mode string is not one of "system", "light", "dark"
        """
        if isinstance(mode, str):
            if mode not in ("system", "light", "dark"):
                raise ValueError(
                    f"Invalid theme mode: {mode!r}. Must be 'system', 'light', or 'dark'."
                )
            mode = ThemeMode(mode)
        self.theme_setting = mode

    def toggle(self) -> None:
        """Cycle through theme modes: SYSTEM → LIGHT → DARK → SYSTEM."""
        if self.theme_setting == ThemeMode.SYSTEM:
            self.theme_setting = ThemeMode.LIGHT
        elif self.theme_setting == ThemeMode.LIGHT:
            self.theme_setting = ThemeMode.DARK
        else:
            self.theme_setting = ThemeMode.SYSTEM

    def handle_system_theme_change(self, new_theme: Literal["light", "dark"]) -> None:
        """Handle OS theme change notification from client.

        Updates system_theme regardless of current theme_setting, so that
        switching back to SYSTEM mode will immediately reflect the OS theme.
        Called by ThemeProvider when the client detects an OS theme change.

        Args:
            new_theme: The new OS theme ("light" or "dark")
        """
        self.system_theme = ThemeMode.DARK if new_theme == "dark" else ThemeMode.LIGHT
