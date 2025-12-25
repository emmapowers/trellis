"""Tests for ThemeSwitcher widget."""

import pytest

from trellis.core.client_state import ClientState, ThemeMode
from trellis.core.composition_component import component
from trellis.core.rendering import RenderTree
from trellis.core.trellis_app import TrellisApp
from trellis.widgets.theme_switcher import ThemeSwitcher, _get_next_mode, _get_icon_for_mode
from trellis.widgets.icons import IconName


class TestThemeSwitcherHelpers:
    """Tests for ThemeSwitcher helper functions."""

    def test_get_next_mode_from_system(self) -> None:
        """_get_next_mode(SYSTEM) should return LIGHT."""
        assert _get_next_mode(ThemeMode.SYSTEM) == ThemeMode.LIGHT

    def test_get_next_mode_from_light(self) -> None:
        """_get_next_mode(LIGHT) should return DARK."""
        assert _get_next_mode(ThemeMode.LIGHT) == ThemeMode.DARK

    def test_get_next_mode_from_dark(self) -> None:
        """_get_next_mode(DARK) should return SYSTEM."""
        assert _get_next_mode(ThemeMode.DARK) == ThemeMode.SYSTEM

    def test_get_icon_for_system_mode(self) -> None:
        """System mode should show monitor icon."""
        icon, tooltip = _get_icon_for_mode(ThemeMode.SYSTEM)
        assert icon == IconName.MONITOR
        assert "System" in tooltip

    def test_get_icon_for_light_mode(self) -> None:
        """Light mode should show sun icon."""
        icon, tooltip = _get_icon_for_mode(ThemeMode.LIGHT)
        assert icon == IconName.SUN
        assert "Light" in tooltip

    def test_get_icon_for_dark_mode(self) -> None:
        """Dark mode should show moon icon."""
        icon, tooltip = _get_icon_for_mode(ThemeMode.DARK)
        assert icon == IconName.MOON
        assert "Dark" in tooltip


class TestThemeSwitcherComponent:
    """Tests for ThemeSwitcher component."""

    def test_requires_client_state_context(self) -> None:
        """ThemeSwitcher should raise when no ClientState in context."""

        @component
        def App() -> None:
            ThemeSwitcher()

        tree = RenderTree(App)
        with pytest.raises(LookupError):
            tree.render()

    def test_renders_with_client_state_context(self) -> None:
        """ThemeSwitcher should render when ClientState is in context."""
        rendered = False

        @component
        def App() -> None:
            nonlocal rendered
            ThemeSwitcher()
            rendered = True

        @component
        def Root() -> None:
            TrellisApp(app=App)

        tree = RenderTree(Root)
        tree.render()

        assert rendered is True

    def test_uses_client_state_mode(self) -> None:
        """ThemeSwitcher should read mode from ClientState context."""
        client_state = ClientState(mode=ThemeMode.DARK)
        rendered_mode: ThemeMode | None = None

        @component
        def App() -> None:
            nonlocal rendered_mode
            state = ClientState.from_context()
            rendered_mode = state.mode
            ThemeSwitcher()

        @component
        def Root() -> None:
            TrellisApp(app=App, client_state=client_state)

        tree = RenderTree(Root)
        tree.render()

        assert rendered_mode == ThemeMode.DARK
