"""Integration tests for ClientState context provision.

These tests use the actual rendering infrastructure since context
requires an active render context.
"""

from trellis.app import ClientState, ThemeMode
from trellis.core.components.composition import component
from trellis.core.rendering import RenderSession, render


class TestClientStateContext:
    """Tests for ClientState context provision during rendering."""

    def test_context_provision_in_component(self) -> None:
        """ClientState should be accessible via context when provided in component."""
        retrieved_state: ClientState | None = None

        @component
        def ChildComponent() -> None:
            nonlocal retrieved_state
            retrieved_state = ClientState.from_context()

        @component
        def ParentComponent() -> None:
            state = ClientState(theme_setting=ThemeMode.DARK)
            with state:
                ChildComponent()

        tree = RenderSession(ParentComponent)
        render(tree)

        assert retrieved_state is not None
        assert retrieved_state.theme_setting == ThemeMode.DARK

    def test_context_not_found_raises_lookup_error(self) -> None:
        """from_context() without provider raises LookupError."""
        error_raised = False

        @component
        def ComponentWithoutContext() -> None:
            nonlocal error_raised
            try:
                ClientState.from_context()
            except LookupError:
                error_raised = True

        tree = RenderSession(ComponentWithoutContext)
        render(tree)

        assert error_raised is True

    def test_context_default_returns_none(self) -> None:
        """from_context(default=None) returns None when not found."""
        result: ClientState | None = "not_set"  # type: ignore

        @component
        def ComponentWithDefault() -> None:
            nonlocal result
            result = ClientState.from_context(default=None)

        tree = RenderSession(ComponentWithDefault)
        render(tree)

        assert result is None
