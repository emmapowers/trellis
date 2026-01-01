"""Integration tests for ThemeSwitcher widget."""

import pytest

from trellis.app import ClientState, ThemeMode, TrellisApp
from trellis.core.components.composition import component
from trellis.core.rendering import RenderSession, render
from trellis.widgets.theme_switcher import ThemeSwitcher


class TestThemeSwitcherComponent:
    """Tests for ThemeSwitcher component rendering."""

    def test_requires_client_state_context(self) -> None:
        """ThemeSwitcher should raise when no ClientState in context."""

        @component
        def App() -> None:
            ThemeSwitcher()

        tree = RenderSession(App)
        with pytest.raises(LookupError):
            render(tree)

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

        tree = RenderSession(Root)
        render(tree)

        assert rendered is True

    def test_uses_client_state_mode(self) -> None:
        """ThemeSwitcher should read mode from ClientState context."""
        client_state = ClientState(theme_setting=ThemeMode.DARK)
        rendered_mode: ThemeMode | None = None

        @component
        def App() -> None:
            nonlocal rendered_mode
            state = ClientState.from_context()
            rendered_mode = state.theme_setting
            ThemeSwitcher()

        @component
        def Root() -> None:
            TrellisApp(app=App, client_state=client_state)

        tree = RenderSession(Root)
        render(tree)

        assert rendered_mode == ThemeMode.DARK
