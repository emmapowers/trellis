"""Tests for Stateful context API."""

import pytest

from trellis.core.composition_component import component
from trellis.core.rendering import RenderTree
from trellis.core.state import Stateful, clear_context_stacks


class TestContextAPI:
    """Tests for the context API (with state: / from_context())."""

    def setup_method(self) -> None:
        """Clear context stacks between tests."""
        clear_context_stacks()

    def teardown_method(self) -> None:
        """Clean up context stacks after tests."""
        clear_context_stacks()

    def test_context_basic_push_pop(self) -> None:
        """Basic context push/pop with 'with' statement."""

        class AppState(Stateful):
            name: str = "test"

        state = AppState()
        state.name = "alice"

        with state:
            retrieved = AppState.from_context()
            assert retrieved is state
            assert retrieved.name == "alice"

        # After exiting, should raise
        with pytest.raises(LookupError):
            AppState.from_context()

    def test_context_nested_same_type(self) -> None:
        """Nested contexts of same type - inner shadows outer."""

        class AppState(Stateful):
            level: int = 0

        outer = AppState()
        outer.level = 1
        inner = AppState()
        inner.level = 2

        with outer:
            assert AppState.from_context().level == 1

            with inner:
                assert AppState.from_context().level == 2

            # Back to outer
            assert AppState.from_context().level == 1

    def test_context_different_types(self) -> None:
        """Different state types have separate context stacks."""

        class UserState(Stateful):
            name: str = ""

        class ThemeState(Stateful):
            dark: bool = False

        user = UserState()
        user.name = "bob"
        theme = ThemeState()
        theme.dark = True

        with user:
            with theme:
                assert UserState.from_context().name == "bob"
                assert ThemeState.from_context().dark is True

            # Theme popped, user still available
            assert UserState.from_context().name == "bob"
            with pytest.raises(LookupError):
                ThemeState.from_context()

    def test_context_not_found_raises(self) -> None:
        """from_context() raises LookupError when no context."""

        class MissingState(Stateful):
            pass

        with pytest.raises(LookupError, match="No MissingState found in context"):
            MissingState.from_context()

    def test_try_from_context_returns_none(self) -> None:
        """try_from_context() returns None when no context."""

        class OptionalState(Stateful):
            value: int = 0

        assert OptionalState.try_from_context() is None

        state = OptionalState()
        state.value = 42
        with state:
            assert OptionalState.try_from_context() is state
            assert OptionalState.try_from_context().value == 42

        assert OptionalState.try_from_context() is None

    def test_context_with_render(self) -> None:
        """Context works during component rendering."""

        class SharedState(Stateful):
            message: str = ""

        captured: list[str] = []

        @component
        def Child() -> None:
            state = SharedState.from_context()
            captured.append(state.message)

        @component
        def Parent() -> None:
            shared = SharedState()
            shared.message = "hello from parent"
            with shared:
                Child()

        ctx = RenderTree(Parent)
        ctx.render()

        assert captured == ["hello from parent"]

    def test_context_deeply_nested_components(self) -> None:
        """Context accessible through deep component nesting."""

        class AppState(Stateful):
            value: str = ""

        captured: list[str] = []

        @component
        def DeepChild() -> None:
            state = AppState.from_context()
            captured.append(state.value)

        @component
        def Middle() -> None:
            DeepChild()

        @component
        def Wrapper() -> None:
            Middle()

        @component
        def App() -> None:
            app_state = AppState()
            app_state.value = "deep"
            with app_state:
                Wrapper()

        ctx = RenderTree(App)
        ctx.render()

        assert captured == ["deep"]

    def test_context_as_variable(self) -> None:
        """'with state as var' pattern works."""

        class ConfigState(Stateful):
            debug: bool = False

        config_state = ConfigState()
        config_state.debug = True
        with config_state as config:
            assert config.debug is True
            assert ConfigState.from_context() is config

    def test_context_exception_safety(self) -> None:
        """Context is popped even if exception occurs."""

        class TestState(Stateful):
            pass

        state = TestState()

        try:
            with state:
                assert TestState.from_context() is state
                raise ValueError("test error")
        except ValueError:
            pass

        # Context should be cleaned up
        with pytest.raises(LookupError):
            TestState.from_context()

    def test_context_multiple_instances_different_subclasses(self) -> None:
        """Subclasses have their own context stacks."""

        class BaseState(Stateful):
            base_val: int = 0

        class DerivedState(BaseState):
            derived_val: str = ""

        base = BaseState()
        base.base_val = 1
        derived = DerivedState()
        derived.base_val = 2
        derived.derived_val = "hello"

        with base:
            with derived:
                # Each type has its own stack
                assert BaseState.from_context().base_val == 1
                assert DerivedState.from_context().base_val == 2
                assert DerivedState.from_context().derived_val == "hello"

    def test_context_reuse_same_instance(self) -> None:
        """Same instance can be used in context multiple times."""

        class CountState(Stateful):
            count: int = 0

        state = CountState()
        state.count = 10

        # First context block
        with state:
            assert CountState.from_context().count == 10
            state.count = 20

        # Second context block with same instance
        with state:
            assert CountState.from_context().count == 20

    def test_context_state_modifications(self) -> None:
        """State can be modified while in context."""

        class ModState(Stateful):
            value: int = 0

        state = ModState()
        state.value = 1

        with state:
            retrieved = ModState.from_context()
            assert retrieved.value == 1

            # Modify via original reference
            state.value = 2
            assert retrieved.value == 2

            # Modify via retrieved reference
            retrieved.value = 3
            assert state.value == 3
