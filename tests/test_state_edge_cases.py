"""Tests for state management edge cases.

These tests verify correct behavior in complex state scenarios:
- Dependency tracking across component depths
- State lifecycle hooks
- Hook ordering with multiple state instances
- State in deeply nested components
"""

from dataclasses import dataclass

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful


class TestDeepDependencyTracking:
    """Tests for dependency tracking in deep component trees."""

    def test_state_read_in_deep_component(self) -> None:
        """State read 50 levels deep should trigger re-render of only that component."""
        DEPTH = 50
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class DeepState(Stateful):
            value: int = 0

        state = DeepState()

        @component
        def Level(n: int = 0) -> None:
            render_counts[f"level_{n}"] = render_counts.get(f"level_{n}", 0) + 1
            if n < DEPTH:
                Level(n=n + 1)
            else:
                # Deepest level reads the state
                _ = state.value

        @component
        def Root() -> None:
            render_counts["root"] = render_counts.get("root", 0) + 1
            Level(n=1)

        ctx = RenderSession(Root)
        render(ctx)

        # All should have rendered once
        assert render_counts["root"] == 1
        assert render_counts[f"level_{DEPTH}"] == 1

        # Change state - only deepest level should re-render
        state.value = 1
        render(ctx)

        assert render_counts["root"] == 1
        assert render_counts[f"level_{DEPTH}"] == 2
        # Intermediate levels should not re-render
        for i in range(1, DEPTH):
            assert render_counts[f"level_{i}"] == 1

    def test_multiple_components_same_property(self) -> None:
        """Multiple components reading same state property all get updates."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class SharedState(Stateful):
            value: int = 0

        state = SharedState()

        @component
        def Reader(name: str = "") -> None:
            render_counts[name] = render_counts.get(name, 0) + 1
            _ = state.value

        @component
        def App() -> None:
            for name in ["a", "b", "c", "d", "e"]:
                Reader(name=name)

        ctx = RenderSession(App)
        render(ctx)

        assert all(render_counts[n] == 1 for n in ["a", "b", "c", "d", "e"])

        # All readers should re-render on state change
        state.value = 1
        render(ctx)

        assert all(render_counts[n] == 2 for n in ["a", "b", "c", "d", "e"])

    def test_component_reads_but_doesnt_use_value(self) -> None:
        """Reading state creates dependency even if value isn't used."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class State(Stateful):
            value: int = 0

        state = State()

        @component
        def Reader() -> None:
            render_counts["reader"] = render_counts.get("reader", 0) + 1
            _ = state.value  # Read but ignore

        @component
        def App() -> None:
            Reader()

        ctx = RenderSession(App)
        render(ctx)

        assert render_counts["reader"] == 1

        state.value = 1
        render(ctx)

        # Should still re-render because dependency was created
        assert render_counts["reader"] == 2


class TestStateLifecycle:
    """Tests for state lifecycle hooks."""

    def test_on_mount_called_once(self) -> None:
        """Stateful.on_mount is called exactly once per element."""
        mount_count = [0]

        @dataclass
        class TrackedState(Stateful):
            def on_mount(self) -> None:
                mount_count[0] += 1

        @component
        def MyComponent() -> None:
            TrackedState()

        ctx = RenderSession(MyComponent)
        render(ctx)

        assert mount_count[0] == 1

        # Re-render multiple times
        for _ in range(5):
            ctx.dirty.mark(ctx.root_element.id)
            render(ctx)

        # Still only 1 mount
        assert mount_count[0] == 1

    def test_on_unmount_called_when_removed(self) -> None:
        """Stateful.on_unmount is called when element is removed."""
        unmount_log: list[str] = []
        show_ref = [True]

        @dataclass
        class TrackedState(Stateful):
            name: str = ""

            def on_unmount(self) -> None:
                unmount_log.append(self.name)

        @component
        def Child() -> None:
            TrackedState(name="child_state")

        @component
        def App() -> None:
            if show_ref[0]:
                Child()

        ctx = RenderSession(App)
        render(ctx)

        assert len(unmount_log) == 0

        # Remove child
        show_ref[0] = False
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert "child_state" in unmount_log

    def test_state_persists_across_rerenders(self) -> None:
        """State instance identity persists across re-renders."""
        state_instances: list[int] = []  # Store id() of state instances

        @dataclass
        class MyState(Stateful):
            counter: int = 0

        @component
        def MyComponent() -> None:
            state = MyState()
            state_instances.append(id(state))

        ctx = RenderSession(MyComponent)
        render(ctx)

        # Re-render
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        # All should be the same instance
        assert len(state_instances) == 3
        assert state_instances[0] == state_instances[1] == state_instances[2]


class TestHookOrdering:
    """Tests for correct ordering of state hooks."""

    def test_multiple_state_instances_order(self) -> None:
        """Multiple state instances in same component use call order."""

        @dataclass
        class StateA(Stateful):
            value: int = 0

        @dataclass
        class StateB(Stateful):
            value: str = ""

        @dataclass
        class StateC(Stateful):
            value: bool = False

        @component
        def MyComponent() -> None:
            StateA(value=1)
            StateB(value="hello")
            StateC(value=True)

        ctx = RenderSession(MyComponent)
        render(ctx)

        # Check local_state keys
        root_state = ctx.states.get(ctx.root_element.id)
        keys = list(root_state.local_state.keys())
        # Keys are (class, call_index)
        indices = [k[1] for k in keys]
        assert sorted(indices) == [0, 1, 2]

    def test_state_order_preserved_on_rerender(self) -> None:
        """State instances maintain order across re-renders."""

        @dataclass
        class Counter(Stateful):
            value: int = 0

        state_ids: list[list[int]] = []  # Track identity via id()

        @component
        def MyComponent() -> None:
            a = Counter(value=1)
            b = Counter(value=10)
            c = Counter(value=100)

            # Track identity across renders
            state_ids.append([id(a), id(b), id(c)])

        ctx = RenderSession(MyComponent)
        render(ctx)

        # Re-render - instances should be same
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        # Third render
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        # All renders should use the same instances in the same order
        assert len(state_ids) == 3
        assert state_ids[0] == state_ids[1] == state_ids[2]

    def test_state_in_loop(self) -> None:
        """State created in a loop gets different instances per iteration."""
        count_ref = [3]

        @dataclass
        class LoopState(Stateful):
            index: int = -1

        # Track which indices were used on first render
        first_render_indices: list[int] = []

        @component
        def MyComponent() -> None:
            for i in range(count_ref[0]):
                # Each iteration gets its own cached state instance, keyed by (LoopState, call_index)
                state = LoopState(index=i)
                if len(first_render_indices) < count_ref[0]:
                    first_render_indices.append(state.index)

        ctx = RenderSession(MyComponent)
        render(ctx)

        # Should have 3 state instances
        root_state = ctx.states.get(ctx.root_element.id)
        assert len(root_state.local_state) == 3

        # Each should have a different index
        indices = [s.index for s in root_state.local_state.values()]
        assert sorted(indices) == [0, 1, 2]

        # Re-render with same count - states preserved
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert len(root_state.local_state) == 3
        indices = [s.index for s in root_state.local_state.values()]
        assert sorted(indices) == [0, 1, 2]


class TestDependencyAcrossComponents:
    """Tests for state dependencies across component boundaries."""

    def test_parent_and_child_read_same_state(self) -> None:
        """Parent and child reading same state both get updates."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class SharedState(Stateful):
            value: int = 0

        state = SharedState()

        @component
        def Child() -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1
            _ = state.value

        @component
        def Parent() -> None:
            render_counts["parent"] = render_counts.get("parent", 0) + 1
            _ = state.value
            Child()

        ctx = RenderSession(Parent)
        render(ctx)

        assert render_counts == {"parent": 1, "child": 1}

        state.value = 1
        render(ctx)

        # Both should re-render
        assert render_counts == {"parent": 2, "child": 2}

    def test_sibling_components_independent_state(self) -> None:
        """Siblings with different state dependencies update independently."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class StateA(Stateful):
            value: int = 0

        @dataclass(kw_only=True)
        class StateB(Stateful):
            value: int = 0

        state_a = StateA()
        state_b = StateB()

        @component
        def SiblingA() -> None:
            render_counts["a"] = render_counts.get("a", 0) + 1
            _ = state_a.value

        @component
        def SiblingB() -> None:
            render_counts["b"] = render_counts.get("b", 0) + 1
            _ = state_b.value

        @component
        def Parent() -> None:
            SiblingA()
            SiblingB()

        ctx = RenderSession(Parent)
        render(ctx)

        assert render_counts == {"a": 1, "b": 1}

        # Change only state_a
        state_a.value = 1
        render(ctx)

        assert render_counts == {"a": 2, "b": 1}

        # Change only state_b
        state_b.value = 1
        render(ctx)

        assert render_counts == {"a": 2, "b": 2}


class TestStateCleanup:
    """Tests for proper state cleanup."""

    def test_state_cleared_on_unmount(self) -> None:
        """State is cleared from element when unmounted."""
        show_ref = [True]

        @dataclass
        class MyState(Stateful):
            value: int = 42

        @component
        def Child() -> None:
            MyState()

        @component
        def App() -> None:
            if show_ref[0]:
                Child()

        ctx = RenderSession(App)
        render(ctx)

        # Capture child node and state
        child_id = ctx.root_element.child_ids[0]
        child_state = ctx.states.get(child_id)
        assert len(child_state.local_state) == 1

        # Unmount
        show_ref[0] = False
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        # State should be cleaned up - element state removed entirely
        assert child_id not in ctx.states

    def test_dirty_elements_cleaned_on_unmount(self) -> None:
        """Element removed from dirty set when unmounted."""
        show_ref = [True]

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: int = 0

        state = MyState()

        @component
        def Child() -> None:
            _ = state.value

        @component
        def App() -> None:
            if show_ref[0]:
                Child()

        ctx = RenderSession(App)
        render(ctx)

        child_id = ctx.root_element.child_ids[0]

        # Mark child dirty by changing state
        state.value = 1
        assert child_id in ctx.dirty

        # Unmount child (without render_dirty first)
        show_ref[0] = False
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        # Child should be removed from dirty set
        assert child_id not in ctx.dirty


class TestMultipleStateTypes:
    """Tests for components using multiple state types."""

    def test_different_state_types_independent(self) -> None:
        """Different state types in same component are independent."""
        render_count = [0]

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        @dataclass(kw_only=True)
        class NameState(Stateful):
            name: str = ""

        counter = CounterState()
        name = NameState()

        @component
        def MyComponent() -> None:
            render_count[0] += 1
            _ = counter.count
            _ = name.name

        ctx = RenderSession(MyComponent)
        render(ctx)

        assert render_count[0] == 1

        # Change counter - should re-render
        counter.count = 1
        render(ctx)
        assert render_count[0] == 2

        # Change name - should re-render
        name.name = "Alice"
        render(ctx)
        assert render_count[0] == 3

    def test_state_inheritance(self) -> None:
        """State subclasses work correctly."""

        @dataclass
        class BaseState(Stateful):
            base_value: int = 0

        @dataclass
        class ExtendedState(BaseState):
            extended_value: str = ""

        @component
        def MyComponent() -> None:
            BaseState(base_value=1)
            ExtendedState(base_value=2, extended_value="hello")

        ctx = RenderSession(MyComponent)
        render(ctx)

        # Both should be cached
        root_state = ctx.states.get(ctx.root_element.id)
        assert len(root_state.local_state) == 2

        # Verify values
        states = list(root_state.local_state.values())
        base_states = [s for s in states if type(s).__name__ == "BaseState"]
        ext_states = [s for s in states if type(s).__name__ == "ExtendedState"]

        assert len(base_states) == 1
        assert len(ext_states) == 1
        assert base_states[0].base_value == 1
        assert ext_states[0].base_value == 2
        assert ext_states[0].extended_value == "hello"
