"""Tests for Stateful context API."""

from dataclasses import dataclass

import pytest

from trellis.core.composition_component import component
from trellis.core.rendering import RenderSession, render
from trellis.core.state import Stateful


class TestContextAPI:
    """Tests for the context API (with state: / from_context())."""

    def test_context_requires_render_context(self) -> None:
        """Context API raises RuntimeError outside render context."""

        class AppState(Stateful):
            name: str = "test"

        state = AppState()

        with pytest.raises(RuntimeError, match="outside of render context"):
            with state:
                pass

    def test_from_context_requires_render_context(self) -> None:
        """from_context() raises RuntimeError outside render context."""

        class MissingState(Stateful):
            pass

        with pytest.raises(RuntimeError, match="outside of render context"):
            MissingState.from_context()

    def test_context_basic_push_pop(self) -> None:
        """Basic context push/pop with 'with' statement inside render."""
        captured: list[str] = []

        class AppState(Stateful):
            name: str = "alice"  # Use class default

        @component
        def Child() -> None:
            retrieved = AppState.from_context()
            captured.append(retrieved.name)

        @component
        def Parent() -> None:
            state = AppState()
            with state:
                Child()

        ctx = RenderSession(Parent)
        render(ctx)

        assert captured == ["alice"]

    def test_context_nested_same_type(self) -> None:
        """Nested contexts of same type - inner shadows outer in child components."""
        captured: list[tuple[str, int]] = []

        # Use separate classes to represent different context levels
        class OuterState(Stateful):
            level: int = 1

        class InnerState(Stateful):
            level: int = 2

        @component
        def DeepChild() -> None:
            # DeepChild finds InnerState from MiddleWithInner
            captured.append(("DeepChild", InnerState.from_context().level))

        @component
        def MiddleWithInner() -> None:
            inner = InnerState()
            with inner:
                DeepChild()
            captured.append(("MiddleWithInner", InnerState.from_context().level))

        @component
        def OuterOnlyChild() -> None:
            # This component finds OuterState from Parent
            captured.append(("OuterOnlyChild", OuterState.from_context().level))

        @component
        def Parent() -> None:
            outer = OuterState()
            with outer:
                captured.append(("Parent", OuterState.from_context().level))
                MiddleWithInner()
                OuterOnlyChild()

        ctx = RenderSession(Parent)
        render(ctx)

        # Verify all components found the correct context values
        # (execution order between siblings is non-deterministic due to set iteration)
        assert ("Parent", 1) in captured
        assert ("MiddleWithInner", 2) in captured
        assert ("OuterOnlyChild", 1) in captured
        assert ("DeepChild", 2) in captured
        assert len(captured) == 4

    def test_context_different_types(self) -> None:
        """Different state types have separate context stacks."""
        captured: list[tuple[str, bool]] = []

        class UserState(Stateful):
            name: str = "bob"  # Use class default

        class ThemeState(Stateful):
            dark: bool = True  # Use class default

        @component
        def Child() -> None:
            captured.append((UserState.from_context().name, ThemeState.from_context().dark))

        @component
        def Parent() -> None:
            user = UserState()
            theme = ThemeState()
            with user:
                with theme:
                    Child()

        ctx = RenderSession(Parent)
        render(ctx)

        assert captured == [("bob", True)]

    def test_context_not_found_raises(self) -> None:
        """from_context() raises LookupError when no context provided."""

        class MissingState(Stateful):
            pass

        @component
        def Child() -> None:
            MissingState.from_context()

        @component
        def Parent() -> None:
            Child()

        ctx = RenderSession(Parent)
        with pytest.raises(LookupError, match="No MissingState found in context"):
            render(ctx)

    def test_context_with_default_returns_none(self) -> None:
        """from_context(default=None) returns None when no context provided."""
        captured: list[Stateful | None] = []

        class OptionalState(Stateful):
            pass

        @component
        def Child() -> None:
            result = OptionalState.from_context(default=None)
            captured.append(result)

        @component
        def Parent() -> None:
            Child()

        ctx = RenderSession(Parent)
        render(ctx)

        assert captured == [None]

    def test_context_with_default_returns_found(self) -> None:
        """from_context(default=None) returns found context when available."""
        captured: list[Stateful | None] = []

        class FoundState(Stateful):
            value: str = "found"

        @component
        def Child() -> None:
            result = FoundState.from_context(default=None)
            captured.append(result)

        @component
        def Parent() -> None:
            state = FoundState()
            with state:
                Child()

        ctx = RenderSession(Parent)
        render(ctx)

        assert len(captured) == 1
        assert captured[0] is not None
        assert captured[0].value == "found"

    def test_context_with_render(self) -> None:
        """Context works during component rendering."""

        class SharedState(Stateful):
            message: str = "hello from parent"  # Use class default

        captured: list[str] = []

        @component
        def Child() -> None:
            state = SharedState.from_context()
            captured.append(state.message)

        @component
        def Parent() -> None:
            shared = SharedState()
            with shared:
                Child()

        ctx = RenderSession(Parent)
        render(ctx)

        assert captured == ["hello from parent"]

    def test_context_deeply_nested_components(self) -> None:
        """Context accessible through deep component nesting."""

        class AppState(Stateful):
            value: str = "deep"  # Use class default

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
            with app_state:
                Wrapper()

        ctx = RenderSession(App)
        render(ctx)

        assert captured == ["deep"]

    def test_context_as_variable(self) -> None:
        """'with state as var' pattern works."""
        captured: list[bool] = []

        class ConfigState(Stateful):
            debug: bool = True  # Use class default

        @component
        def Child() -> None:
            captured.append(ConfigState.from_context().debug)

        @component
        def Parent() -> None:
            config_state = ConfigState()
            with config_state as config:
                assert config.debug is True
                Child()

        ctx = RenderSession(Parent)
        render(ctx)

        assert captured == [True]

    def test_context_exception_safety(self) -> None:
        """Context is still accessible in except block during render."""
        captured: list[bool] = []

        class TestState(Stateful):
            pass

        @component
        def Parent() -> None:
            state = TestState()
            with state:
                captured.append(TestState.from_context() is state)
                # Context persists on node, not a stack, so no cleanup needed

        ctx = RenderSession(Parent)
        render(ctx)

        assert captured == [True]

    def test_context_multiple_instances_different_subclasses(self) -> None:
        """Subclasses have their own context stacks."""
        captured: list[tuple[int, int, str]] = []

        class BaseState(Stateful):
            base_val: int = 1  # Use class default

        class DerivedState(Stateful):
            base_val: int = 2  # Use class default
            derived_val: str = "hello"  # Use class default

        @component
        def Child() -> None:
            base = BaseState.from_context()
            derived = DerivedState.from_context()
            captured.append((base.base_val, derived.base_val, derived.derived_val))

        @component
        def Parent() -> None:
            base = BaseState()
            derived = DerivedState()
            with base:
                with derived:
                    Child()

        ctx = RenderSession(Parent)
        render(ctx)

        assert captured == [(1, 2, "hello")]

    def test_context_reuse_same_instance(self) -> None:
        """Same instance can be used in context multiple times."""
        captured: list[int] = []

        class CountState(Stateful):
            count: int = 10  # Use constructor default

        @component
        def Child() -> None:
            captured.append(CountState.from_context().count)

        @component
        def Parent() -> None:
            # Same instance used in context multiple times
            state = CountState()
            with state:
                Child()  # First child
            with state:
                Child()  # Second child - same instance

        ctx = RenderSession(Parent)
        render(ctx)

        # Both children see the same state instance
        assert captured == [10, 10]

    def test_context_state_modification_during_render_raises(self) -> None:
        """Modifying state during render raises RuntimeError."""

        @dataclass
        class ModState(Stateful):
            value: int = 1

        @component
        def Parent() -> None:
            state = ModState()  # value=1 is now in instance __dict__
            state.value = 2  # Try to modify existing value - should raise

        ctx = RenderSession(Parent)
        with pytest.raises(RuntimeError, match="Cannot modify state"):
            render(ctx)
