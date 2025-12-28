"""Tests for Stateful context API."""

from dataclasses import dataclass

import pytest

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful


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


class TestContextEdgeCases:
    """Tests for context edge cases and error messages."""

    def test_context_same_type_shadowing(self) -> None:
        """Inner context of same type shadows outer at nested level."""
        captured: list[str] = []

        @dataclass
        class CounterState(Stateful):
            name: str = "default"

        @component
        def Leaf() -> None:
            """
            Capture the current CounterState name and append it to the module-level `captured` list.
            
            This function reads CounterState.from_context() and records its `name` value into the existing `captured` list for later assertions.
            """
            captured.append(CounterState.from_context().name)

        @component
        def Inner() -> None:
            """
            Establish a CounterState context named "inner" for the duration of rendering the Leaf component.
            
            Creates a CounterState with name "inner" and invokes Leaf() while that state is active so Leaf can read the inner CounterState.
            """
            inner_state = CounterState(name="inner")
            with inner_state:
                Leaf()

        @component
        def Parent() -> None:
            """
            Establishes an outer CounterState context and renders Leaf and Inner so that Leaf sees the outer state and the Leaf inside Inner sees a nested inner state.
            """
            outer_state = CounterState(name="outer")
            with outer_state:
                Leaf()  # Should see "outer"
                Inner()  # Leaf inside should see "inner"

        ctx = RenderSession(Parent)
        render(ctx)

        assert "outer" in captured
        assert "inner" in captured

    def test_context_with_custom_default(self) -> None:
        """from_context() with custom default value returns default when not found."""
        captured: list[int] = []

        @dataclass
        class MissingState(Stateful):
            value: int = 0

        default_instance = MissingState(value=42)

        @component
        def Child() -> None:
            """
            Append the `value` from the current `MissingState` context (or the provided default) to the `captured` list.
            
            If no `MissingState` is present in the render context, `default_instance` is used and its `value` is appended.
            """
            result = MissingState.from_context(default=default_instance)
            captured.append(result.value)

        @component
        def Parent() -> None:
            """
            Render a parent component that invokes Child without supplying MissingState.
            
            This causes Child to run with no MissingState present in the context.
            """
            Child()  # No MissingState provided

        ctx = RenderSession(Parent)
        render(ctx)

        assert captured == [42]

    def test_context_error_message_includes_class_name(self) -> None:
        """
        Verifies that a missing context LookupError message includes the Stateful subclass name and suggests using `with`.
        
        Creates a small component tree that attempts to read a custom Stateful subclass from context, renders it, and asserts the raised LookupError message contains the subclass's class name and the word "with".
        """

        class MyCustomStatefulClass(Stateful):
            pass

        @component
        def Child() -> None:
            """
            Component that reads MyCustomStatefulClass from the current render context.
            """
            MyCustomStatefulClass.from_context()

        @component
        def Parent() -> None:
            """
            Renders the Child component.
            """
            Child()

        ctx = RenderSession(Parent)
        with pytest.raises(LookupError) as exc_info:
            render(ctx)

        # Verify error message is helpful
        assert "MyCustomStatefulClass" in str(exc_info.value)
        assert "with" in str(exc_info.value)  # Suggests the fix

    def test_context_runtime_error_message_includes_class_name(self) -> None:
        """RuntimeError message for outside-render includes class name."""

        class OutsideRenderState(Stateful):
            pass

        state = OutsideRenderState()

        with pytest.raises(RuntimeError) as exc_info:
            with state:
                pass

        # Verify error message is helpful
        assert "OutsideRenderState" in str(exc_info.value)
        assert "render context" in str(exc_info.value)

    def test_from_context_outside_render_error_message(self) -> None:
        """
        Verifies that calling `from_context` on a `Stateful` subclass outside a render context raises a `RuntimeError` whose message includes the subclass name and the text "from_context".
        """

        class CalledOutsideState(Stateful):
            pass

        with pytest.raises(RuntimeError) as exc_info:
            CalledOutsideState.from_context()

        # Verify error message is helpful
        assert "CalledOutsideState" in str(exc_info.value)
        assert "from_context" in str(exc_info.value)

    def test_context_available_after_conditional_branch(self) -> None:
        """Context is available in subsequent children after conditional."""
        captured: list[str] = []

        class SafeState(Stateful):
            value: str = "safe"

        @component
        def SafeChild() -> None:
            """
            Append the current SafeState context's value to the outer `captured` list.
            
            This function reads the active SafeState from the render context and appends its `value` attribute to the surrounding `captured` list as a side effect.
            """
            captured.append(SafeState.from_context().value)

        @component
        def ConditionalChild() -> None:
            """
            A no-op component used in tests to represent a conditional child that performs no rendering.
            
            This function intentionally does nothing and exists solely as a placeholder for conditional-branch tests.
            """
            pass  # Does nothing

        @component
        def Parent() -> None:
            """
            Renders child components within a SafeState context to verify the state's availability before and after an intermediate conditional child.
            
            Used by tests to ensure a provided context remains accessible to later children following a conditional branch.
            """
            state = SafeState()
            with state:
                SafeChild()  # First access
                ConditionalChild()  # Intermediate child
                SafeChild()  # Second access after conditional

        ctx = RenderSession(Parent)
        render(ctx)

        # Both SafeChild calls should have accessed context
        assert captured == ["safe", "safe"]

    def test_context_sibling_components_isolated(self) -> None:
        """Context provided in one sibling doesn't leak to another."""
        captured: list[str | None] = []

        class SiblingState(Stateful):
            name: str = "sibling"

        @component
        def ProviderChild() -> None:
            """
            Establishes a SiblingState instance in the current render context for this component and its descendants.
            
            This function creates a SiblingState and enters it as a context provider so that nested children can read the state via the context API. The provided context is scoped to this with-block and is not visible to sibling components outside the block.
            """
            state = SiblingState()
            with state:
                pass  # Provides context to self, not siblings

        @component
        def ConsumerChild() -> None:
            # Should NOT find SiblingState - not an ancestor
            result = SiblingState.from_context(default=None)
            captured.append(result.name if result else None)

        @component
        def Parent() -> None:
            """
            Render a parent component that mounts a provider child followed by a consumer child.
            
            This component composes ProviderChild and ConsumerChild in sequence to establish and then consume context during a render.
            """
            ProviderChild()
            ConsumerChild()

        ctx = RenderSession(Parent)
        render(ctx)

        # Consumer should not find sibling's context
        assert captured == [None]