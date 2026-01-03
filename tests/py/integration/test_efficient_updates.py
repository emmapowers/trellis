"""Tests for efficient update behavior - verifying minimal re-renders.

These tests ensure that the fine-grained reactivity system actually works:
- Only components that read a specific state property re-render when it changes
- Components with unchanged props skip execution entirely
- Deeply nested components only re-render when their dependencies change
"""

from dataclasses import dataclass

from tests.conftest import PatchCapture
from trellis.core.components.composition import component
from trellis.core.rendering.child_ref import ChildRef
from trellis.core.state.stateful import Stateful


class TestMinimalRerenders:
    """Tests verifying that only necessary components re-render."""

    def test_state_change_only_rerenders_dependent_component(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """State change should only re-render the component that reads it."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            value: int = 0

        counter = CounterState()

        @component
        def Counter() -> None:
            render_counts["counter"] = render_counts.get("counter", 0) + 1
            _ = counter.value

        @component
        def Sibling() -> None:
            render_counts["sibling"] = render_counts.get("sibling", 0) + 1

        @component
        def Parent() -> None:
            render_counts["parent"] = render_counts.get("parent", 0) + 1
            Counter()
            Sibling()

        capture = capture_patches(Parent)
        capture.render()

        assert render_counts == {"parent": 1, "counter": 1, "sibling": 1}

        # Change state - only Counter should re-render
        counter.value = 1
        capture.render()

        assert render_counts == {"parent": 1, "counter": 2, "sibling": 1}

    def test_fine_grained_property_tracking(self, capture_patches: "type[PatchCapture]") -> None:
        """Only components reading the changed property should re-render."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class AppState(Stateful):
            name: str = ""
            count: int = 0
            flag: bool = False

        state = AppState()

        @component
        def NameReader() -> None:
            render_counts["name"] = render_counts.get("name", 0) + 1
            _ = state.name

        @component
        def CountReader() -> None:
            render_counts["count"] = render_counts.get("count", 0) + 1
            _ = state.count

        @component
        def FlagReader() -> None:
            render_counts["flag"] = render_counts.get("flag", 0) + 1
            _ = state.flag

        @component
        def App() -> None:
            render_counts["app"] = render_counts.get("app", 0) + 1
            NameReader()
            CountReader()
            FlagReader()

        capture = capture_patches(App)
        capture.render()

        assert render_counts == {"app": 1, "name": 1, "count": 1, "flag": 1}

        # Change only name - only NameReader should re-render
        state.name = "Alice"
        capture.render()

        assert render_counts == {"app": 1, "name": 2, "count": 1, "flag": 1}

        # Change only count - only CountReader should re-render
        state.count = 42
        capture.render()

        assert render_counts == {"app": 1, "name": 2, "count": 2, "flag": 1}

        # Change only flag - only FlagReader should re-render
        state.flag = True
        capture.render()

        assert render_counts == {"app": 1, "name": 2, "count": 2, "flag": 2}

    def test_multiple_state_changes_batched(self, capture_patches: "type[PatchCapture]") -> None:
        """Multiple state changes before render_dirty are batched."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class State(Stateful):
            a: int = 0
            b: int = 0

        state = State()

        @component
        def ReaderA() -> None:
            render_counts["a"] = render_counts.get("a", 0) + 1
            _ = state.a

        @component
        def ReaderB() -> None:
            render_counts["b"] = render_counts.get("b", 0) + 1
            _ = state.b

        @component
        def ReaderBoth() -> None:
            render_counts["both"] = render_counts.get("both", 0) + 1
            _ = state.a
            _ = state.b

        @component
        def App() -> None:
            ReaderA()
            ReaderB()
            ReaderBoth()

        capture = capture_patches(App)
        capture.render()

        assert render_counts == {"a": 1, "b": 1, "both": 1}

        # Multiple changes, single render_dirty call
        state.a = 1
        state.b = 2
        capture.render()

        # ReaderA, ReaderB, and ReaderBoth should all re-render exactly once
        assert render_counts == {"a": 2, "b": 2, "both": 2}


class TestPropsUnchangedOptimization:
    """Tests verifying that unchanged props skip component execution."""

    def test_unchanged_props_skip_execution(self, capture_patches: "type[PatchCapture]") -> None:
        """Component with unchanged props should not re-execute."""
        render_counts: dict[str, int] = {}

        @component
        def Child(value: int = 0) -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def Parent() -> None:
            render_counts["parent"] = render_counts.get("parent", 0) + 1
            Child(value=42)  # Always same props

        capture = capture_patches(Parent)
        capture.render()

        assert render_counts == {"parent": 1, "child": 1}

        # Re-render parent - child should NOT re-execute since props unchanged
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert render_counts == {"parent": 2, "child": 1}  # Child still 1!

    def test_changed_props_trigger_execution(self, capture_patches: "type[PatchCapture]") -> None:
        """Component with changed props should re-execute."""
        render_counts: dict[str, int] = {}
        value_ref = [0]

        @component
        def Child(value: int = 0) -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def Parent() -> None:
            render_counts["parent"] = render_counts.get("parent", 0) + 1
            Child(value=value_ref[0])

        capture = capture_patches(Parent)
        capture.render()

        assert render_counts == {"parent": 1, "child": 1}

        # Change props
        value_ref[0] = 1
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert render_counts == {"parent": 2, "child": 2}  # Child re-executed

    def test_deeply_nested_unchanged_props(self, capture_patches: "type[PatchCapture]") -> None:
        """Deeply nested components with unchanged props should skip execution."""
        render_counts: dict[str, int] = {}

        @component
        def Leaf(value: int = 0) -> None:
            render_counts["leaf"] = render_counts.get("leaf", 0) + 1

        @component
        def Level3() -> None:
            render_counts["level3"] = render_counts.get("level3", 0) + 1
            Leaf(value=42)

        @component
        def Level2() -> None:
            render_counts["level2"] = render_counts.get("level2", 0) + 1
            Level3()

        @component
        def Level1() -> None:
            render_counts["level1"] = render_counts.get("level1", 0) + 1
            Level2()

        @component
        def Root() -> None:
            render_counts["root"] = render_counts.get("root", 0) + 1
            Level1()

        capture = capture_patches(Root)
        capture.render()

        assert render_counts == {"root": 1, "level1": 1, "level2": 1, "level3": 1, "leaf": 1}

        # Re-render only root - nothing else should change
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        # Only root re-executes since all children have unchanged props
        assert render_counts == {"root": 2, "level1": 1, "level2": 1, "level3": 1, "leaf": 1}


class TestDirtyMarkingBehavior:
    """Tests for dirty marking and render order."""

    def test_mark_dirty_only_affects_target(self, capture_patches: "type[PatchCapture]") -> None:
        """Marking an element dirty should not affect its parent or siblings."""
        render_counts: dict[str, int] = {}

        @component
        def Child1() -> None:
            render_counts["child1"] = render_counts.get("child1", 0) + 1

        @component
        def Child2() -> None:
            render_counts["child2"] = render_counts.get("child2", 0) + 1

        @component
        def Parent() -> None:
            render_counts["parent"] = render_counts.get("parent", 0) + 1
            Child1()
            Child2()

        capture = capture_patches(Parent)
        capture.render()

        assert render_counts == {"parent": 1, "child1": 1, "child2": 1}

        # Mark only child1 dirty
        ctx = capture.session
        child1_node = ctx.elements.get(ctx.root_element.child_ids[0])
        ctx.dirty.mark(child1_node.id)
        capture.render()

        # Only child1 should re-render
        assert render_counts == {"parent": 1, "child1": 2, "child2": 1}

    def test_dirty_parent_and_child_renders_child_once(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """When both parent and child are dirty, child renders only once."""
        render_counts: dict[str, int] = {"parent": 0, "child": 0}

        @component
        def Child() -> None:
            render_counts["child"] += 1

        @component
        def Parent() -> None:
            render_counts["parent"] += 1
            Child()

        capture = capture_patches(Parent)
        capture.render()
        render_counts["parent"] = 0
        render_counts["child"] = 0

        # Mark both dirty (child first to test that order doesn't matter)
        ctx = capture.session
        child_node = ctx.elements.get(ctx.root_element.child_ids[0])
        ctx.dirty.mark(child_node.id)
        ctx.dirty.mark(ctx.root_element.id)

        capture.render()

        # Child should render exactly once (via parent re-render)
        # Parent clears child's dirty flag when it re-renders child
        assert render_counts["parent"] == 1
        assert render_counts["child"] == 1

    def test_child_dirty_cleared_by_parent_rerender(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """If parent re-renders child, child's dirty flag should be handled."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class State(Stateful):
            value: int = 0

        state = State()

        @component
        def Child() -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1
            _ = state.value

        @component
        def Parent() -> None:
            render_counts["parent"] = render_counts.get("parent", 0) + 1
            Child()

        capture = capture_patches(Parent)
        capture.render()

        assert render_counts == {"parent": 1, "child": 1}

        # Mark parent dirty - child will be re-rendered as part of parent
        # But child's props unchanged so it should be skipped
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert render_counts == {"parent": 2, "child": 1}

    def test_dirty_container_preserves_children(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Container marked dirty should keep its children."""
        render_counts: dict[str, int] = {"container": 0, "child": 0}
        children_received: list[int] = []

        @component
        def Child() -> None:
            render_counts["child"] += 1

        @component
        def Container(children: list[ChildRef] | None = None) -> None:
            render_counts["container"] += 1
            children_received.append(len(children) if children else 0)
            for child in children or []:
                child()

        @component
        def App() -> None:
            with Container():
                Child()

        capture = capture_patches(App)
        capture.render()

        assert render_counts == {"container": 1, "child": 1}
        assert children_received == [1]

        # Mark container dirty directly (not parent)
        container_id = capture.session.root_element.child_ids[0]
        capture.session.dirty.mark(container_id)
        capture.render()

        # Container should still receive its child
        assert render_counts == {"container": 2, "child": 1}
        assert children_received == [1, 1]


class TestDeeplyNestedStateUpdates:
    """Tests for state updates in deeply nested trees."""

    def test_deep_state_change_only_rerenders_path(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """State change in deep component only re-renders the dependent path."""
        render_counts: dict[str, int] = {}
        DEPTH = 10

        @dataclass(kw_only=True)
        class LeafState(Stateful):
            value: int = 0

        leaf_state = LeafState()

        @component
        def Leaf() -> None:
            render_counts["leaf"] = render_counts.get("leaf", 0) + 1
            _ = leaf_state.value

        def make_level(n: int):
            @component
            def Level() -> None:
                render_counts[f"level{n}"] = render_counts.get(f"level{n}", 0) + 1
                if n == DEPTH:
                    Leaf()
                else:
                    make_level(n + 1)()

            return Level

        @component
        def Root() -> None:
            render_counts["root"] = render_counts.get("root", 0) + 1
            make_level(1)()

        capture = capture_patches(Root)
        capture.render()

        # All components should have rendered once
        expected = {"root": 1, "leaf": 1}
        for i in range(1, DEPTH + 1):
            expected[f"level{i}"] = 1
        assert render_counts == expected

        # Change leaf state - only leaf should re-render
        leaf_state.value = 1
        capture.render()

        expected["leaf"] = 2
        assert render_counts == expected

    def test_multiple_readers_at_different_depths(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Multiple components at different depths reading same state."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class SharedState(Stateful):
            value: int = 0

        state = SharedState()

        @component
        def Level3Reader() -> None:
            render_counts["level3"] = render_counts.get("level3", 0) + 1
            _ = state.value

        @component
        def Level2() -> None:
            render_counts["level2"] = render_counts.get("level2", 0) + 1
            Level3Reader()

        @component
        def Level1Reader() -> None:
            render_counts["level1"] = render_counts.get("level1", 0) + 1
            _ = state.value
            Level2()

        @component
        def RootReader() -> None:
            render_counts["root"] = render_counts.get("root", 0) + 1
            _ = state.value
            Level1Reader()

        capture = capture_patches(RootReader)
        capture.render()

        assert render_counts == {"root": 1, "level1": 1, "level2": 1, "level3": 1}

        # Change state - root, level1, and level3 should re-render (they all read it)
        # level2 doesn't read state so shouldn't re-render
        state.value = 1
        capture.render()

        assert render_counts == {"root": 2, "level1": 2, "level2": 1, "level3": 2}


class TestStateWithMultipleComponents:
    """Tests for state shared across multiple components."""

    def test_same_state_multiple_readers(self, capture_patches: "type[PatchCapture]") -> None:
        """Multiple components reading the same state property all re-render."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class SharedState(Stateful):
            value: int = 0

        state = SharedState()

        @component
        def Reader1() -> None:
            render_counts["reader1"] = render_counts.get("reader1", 0) + 1
            _ = state.value

        @component
        def Reader2() -> None:
            render_counts["reader2"] = render_counts.get("reader2", 0) + 1
            _ = state.value

        @component
        def NonReader() -> None:
            render_counts["non_reader"] = render_counts.get("non_reader", 0) + 1

        @component
        def App() -> None:
            Reader1()
            Reader2()
            NonReader()

        capture = capture_patches(App)
        capture.render()

        assert render_counts == {"reader1": 1, "reader2": 1, "non_reader": 1}

        state.value = 1
        capture.render()

        # Both readers re-render, non-reader doesn't
        assert render_counts == {"reader1": 2, "reader2": 2, "non_reader": 1}

    def test_independent_states_independent_updates(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Independent state instances trigger independent updates."""
        render_counts: dict[str, int] = {}

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            value: int = 0

        state_a = CounterState()
        state_b = CounterState()

        @component
        def ReaderA() -> None:
            render_counts["a"] = render_counts.get("a", 0) + 1
            _ = state_a.value

        @component
        def ReaderB() -> None:
            render_counts["b"] = render_counts.get("b", 0) + 1
            _ = state_b.value

        @component
        def App() -> None:
            ReaderA()
            ReaderB()

        capture = capture_patches(App)
        capture.render()

        assert render_counts == {"a": 1, "b": 1}

        # Change only state_a
        state_a.value = 1
        capture.render()

        assert render_counts == {"a": 2, "b": 1}

        # Change only state_b
        state_b.value = 1
        capture.render()

        assert render_counts == {"a": 2, "b": 2}
