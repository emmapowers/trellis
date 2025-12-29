"""Tests for TrellisApp wrapper component."""

from trellis.app import ClientState, ThemeMode, TrellisApp
from trellis.core.components.composition import component
from trellis.core.rendering import RenderSession, render
from trellis import widgets as w


class TestTrellisApp:
    """Tests for TrellisApp wrapper component."""

    def test_provides_client_state_to_children(self) -> None:
        """TrellisApp should make ClientState accessible via context."""
        retrieved_state: ClientState | None = None

        @component
        def ChildComponent() -> None:
            nonlocal retrieved_state
            retrieved_state = ClientState.from_context()

        @component
        def MyApp() -> None:
            ChildComponent()

        @component
        def Root() -> None:
            TrellisApp(app=MyApp)

        tree = RenderSession(Root)
        render(tree)

        assert retrieved_state is not None
        assert isinstance(retrieved_state, ClientState)

    def test_uses_provided_client_state(self) -> None:
        """TrellisApp should use provided ClientState instead of creating one."""
        custom_state = ClientState(mode=ThemeMode.DARK)
        retrieved_state: ClientState | None = None

        @component
        def MyApp() -> None:
            nonlocal retrieved_state
            retrieved_state = ClientState.from_context()

        @component
        def Root() -> None:
            TrellisApp(app=MyApp, client_state=custom_state)

        tree = RenderSession(Root)
        render(tree)

        assert retrieved_state is custom_state
        assert retrieved_state.mode == ThemeMode.DARK

    def test_creates_default_client_state_when_none_provided(self) -> None:
        """TrellisApp should create ClientState with defaults when not provided."""
        retrieved_state: ClientState | None = None

        @component
        def MyApp() -> None:
            nonlocal retrieved_state
            retrieved_state = ClientState.from_context()

        @component
        def Root() -> None:
            TrellisApp(app=MyApp)

        tree = RenderSession(Root)
        render(tree)

        assert retrieved_state is not None
        assert retrieved_state.mode == ThemeMode.SYSTEM  # Default

    def test_renders_app_content(self) -> None:
        """TrellisApp should render the app component's content."""
        label_rendered = False

        @component
        def MyApp() -> None:
            nonlocal label_rendered
            w.Label(text="Hello")
            label_rendered = True

        @component
        def Root() -> None:
            TrellisApp(app=MyApp)

        tree = RenderSession(Root)
        render(tree)

        assert label_rendered is True

    def test_client_state_theme_accessible(self) -> None:
        """ClientState theme properties should be accessible in app."""
        is_dark: bool | None = None
        is_light: bool | None = None

        @component
        def MyApp() -> None:
            nonlocal is_dark, is_light
            state = ClientState.from_context()
            is_dark = state.is_dark
            is_light = state.is_light

        @component
        def Root() -> None:
            TrellisApp(app=MyApp, client_state=ClientState(mode=ThemeMode.DARK))

        tree = RenderSession(Root)
        render(tree)

        assert is_dark is True
        assert is_light is False
