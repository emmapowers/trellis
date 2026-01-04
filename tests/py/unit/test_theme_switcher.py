"""Unit tests for ThemeSwitcher helper functions."""

from trellis.app import ThemeMode
from trellis.widgets.icons import IconName

# INTERNAL TEST: Testing private helpers because the public component's button behavior
# depends on correct mode cycling and icon selection logic. These are core to the
# ThemeSwitcher's correctness.
from trellis.widgets.theme_switcher import _get_icon_for_mode, _get_next_mode


class TestGetNextMode:
    """Tests for _get_next_mode helper function."""

    def test_system_to_light(self) -> None:
        """_get_next_mode(SYSTEM) should return LIGHT."""
        assert _get_next_mode(ThemeMode.SYSTEM) == ThemeMode.LIGHT

    def test_light_to_dark(self) -> None:
        """_get_next_mode(LIGHT) should return DARK."""
        assert _get_next_mode(ThemeMode.LIGHT) == ThemeMode.DARK

    def test_dark_to_system(self) -> None:
        """_get_next_mode(DARK) should return SYSTEM."""
        assert _get_next_mode(ThemeMode.DARK) == ThemeMode.SYSTEM


class TestGetIconForMode:
    """Tests for _get_icon_for_mode helper function."""

    def test_system_mode_shows_monitor_icon(self) -> None:
        """System mode should show monitor icon."""
        icon = _get_icon_for_mode(ThemeMode.SYSTEM)
        assert icon == IconName.MONITOR

    def test_light_mode_shows_sun_icon(self) -> None:
        """Light mode should show sun icon."""
        icon = _get_icon_for_mode(ThemeMode.LIGHT)
        assert icon == IconName.SUN

    def test_dark_mode_shows_moon_icon(self) -> None:
        """Dark mode should show moon icon."""
        icon = _get_icon_for_mode(ThemeMode.DARK)
        assert icon == IconName.MOON
