"""Tests for trellis.core.state module."""

from dataclasses import dataclass

from trellis.core.rendering import RenderTree
from trellis.core.composition_component import component
from trellis.core.state import Stateful


class TestStateful:
    def test_stateful_set_and_get(self) -> None:
        """State values can be set and retrieved."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        state.value = "hello"
        assert state.value == "hello"

    def test_stateful_tracks_dependencies(self) -> None:
        """Accessing state during render registers the element as dependent."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            text: str = ""

        state = MyState()
        state.text = "hello"

        @component
        def MyComponent() -> None:
            _ = state.text  # Access the state

        ctx = RenderTree(MyComponent)
        ctx.render()

        # The component should be registered as dependent on state.text
        state_info = state._state_props["text"]
        assert len(state_info.node_ids) == 1

    def test_stateful_marks_dirty_on_change(self) -> None:
        """Changing state marks dependent elements as dirty."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            text: str = ""

        state = MyState()
        state.text = "hello"

        @component
        def MyComponent() -> None:
            _ = state.text

        ctx = RenderTree(MyComponent)
        ctx.render()

        # Clear dirty state
        ctx._dirty_ids.clear()
        ctx._element_state[ctx.root_node.id].dirty = False

        # Change state
        state.text = "world"

        # Element should be marked dirty
        assert ctx.root_node.id in ctx._dirty_ids
        assert ctx._element_state[ctx.root_node.id].dirty is True

    def test_stateful_render_dirty_updates(self) -> None:
        """render_dirty() re-renders components affected by state changes."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            text: str = ""

        state = MyState()
        state.text = "initial"
        render_count = [0]

        @component
        def MyComponent() -> None:
            render_count[0] += 1
            _ = state.text

        ctx = RenderTree(MyComponent)
        ctx.render()
        assert render_count[0] == 1

        state.text = "changed"
        ctx.render()
        assert render_count[0] == 2

    def test_fine_grained_tracking(self) -> None:
        """Only components that read a specific property should re-render."""

        @dataclass(kw_only=True, repr=False)
        class MyState(Stateful):
            name: str = ""
            count: int = 0

        state = MyState()
        state.name = ""
        state.count = 0

        name_renders = [0]
        count_renders = [0]

        @component
        def NameComponent() -> None:
            name_renders[0] += 1
            _ = state.name

        @component
        def CountComponent() -> None:
            count_renders[0] += 1
            _ = state.count

        @component
        def Parent() -> None:
            NameComponent()
            CountComponent()

        ctx = RenderTree(Parent)
        ctx.render()

        assert name_renders[0] == 1
        assert count_renders[0] == 1

        # Change only name - only NameComponent should re-render
        state.name = "updated"
        ctx.render()

        assert name_renders[0] == 2
        assert count_renders[0] == 1  # Should NOT have re-rendered

    def test_state_change_without_render_context(self) -> None:
        """State can be changed outside of a render context."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        state.value = "one"
        state.value = "two"
        assert state.value == "two"


class TestLocalStatePersistence:
    """Tests for component-local state that persists across re-renders."""

    def test_local_state_persists_across_rerenders(self) -> None:
        """State created in a component persists when re-rendered."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        captured_state_ids: list[int] = []

        @component
        def Counter() -> None:
            state = CounterState()
            captured_state_ids.append(id(state))
            _ = state.count  # Access to register dependency

        ctx = RenderTree(Counter)
        ctx.render()

        # Re-render by marking dirty - should reuse same instance
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Third render
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # All renders should return the same state instance
        assert len(captured_state_ids) == 3
        assert captured_state_ids[0] == captured_state_ids[1] == captured_state_ids[2]

    def test_local_state_values_preserved(self) -> None:
        """State values are preserved across re-renders."""

        @dataclass(kw_only=True)
        class CounterState(Stateful):
            count: int = 0

        observed_counts: list[int] = []
        state_ref: list[CounterState] = []

        @component
        def Counter() -> None:
            state = CounterState()
            state_ref.clear()
            state_ref.append(state)
            observed_counts.append(state.count)

        ctx = RenderTree(Counter)
        ctx.render()
        # Increment outside render
        state_ref[0].count = 1
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()
        # Increment again outside render
        state_ref[0].count = 2
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Should see 0, 1, 2 as count persists across re-renders
        assert observed_counts == [0, 1, 2]

    def test_multiple_state_instances_same_type(self) -> None:
        """Multiple instances of same state type use call order."""

        @dataclass(kw_only=True)
        class ToggleState(Stateful):
            on: bool = False

        captured: list[ToggleState] = []

        @component
        def MultiToggle() -> None:
            first = ToggleState()
            second = ToggleState()
            captured.append(first)
            captured.append(second)

        ctx = RenderTree(MultiToggle)
        ctx.render()

        # Verify we got two distinct instances
        assert len(captured) == 2
        assert captured[0] is not captured[1]

        # Re-render - each should get its own cached instance
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Should return same instances on re-render
        assert len(captured) == 4
        assert captured[0] is captured[2]  # first instance reused
        assert captured[1] is captured[3]  # second instance reused

        # Check that we have 2 distinct state entries in the root element's cache
        root_state = ctx._element_state[ctx.root_node.id]
        state_keys = [k for k in root_state.local_state.keys() if k[0].__name__ == "ToggleState"]
        assert len(state_keys) == 2

        # Check they have different call indices
        indices = [k[1] for k in state_keys]
        assert 0 in indices
        assert 1 in indices

    def test_subclass_state_works(self) -> None:
        """Subclassed state types work correctly."""

        @dataclass(kw_only=True)
        class BaseState(Stateful):
            value: int = 0

        @dataclass(kw_only=True)
        class ExtendedState(BaseState):
            extra: str = ""

        captured: list[Stateful] = []

        @component
        def MyComponent() -> None:
            base = BaseState()
            extended = ExtendedState()
            captured.append(base)
            captured.append(extended)

        ctx = RenderTree(MyComponent)
        ctx.render()

        # Both should be cached separately by their actual types on the element
        root_state = ctx._element_state[ctx.root_node.id]
        local_state = root_state.local_state
        base_keys = [k for k in local_state.keys() if k[0].__name__ == "BaseState"]
        ext_keys = [k for k in local_state.keys() if k[0].__name__ == "ExtendedState"]

        assert len(base_keys) == 1
        assert len(ext_keys) == 1

        # Set values outside of render
        base_instance = local_state[base_keys[0]]
        ext_instance = local_state[ext_keys[0]]
        base_instance.value = 10
        ext_instance.value = 20
        ext_instance.extra = "hello"

        # Values should be preserved on re-render
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        assert base_instance.value == 10
        assert ext_instance.value == 20
        assert ext_instance.extra == "hello"

    def test_state_outside_render_not_cached(self) -> None:
        """State created outside render context is not cached."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: int = 0

        # Create outside any render
        state1 = MyState()
        state2 = MyState()

        # Should be different instances
        assert state1 is not state2


class TestStateDependencyTracking:
    """Tests for state dependency tracking internals."""

    def test_node_ids_set_populated(self) -> None:
        """Accessing state property populates node_ids set."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        state.value = "test"

        @component
        def Consumer() -> None:
            _ = state.value  # Access the property

        ctx = RenderTree(Consumer)
        ctx.render()

        # Check that node_id was recorded in state deps
        assert "value" in state._state_props
        deps = state._state_props["value"]
        assert ctx.root_node.id in deps.node_ids

    def test_node_trees_dict_populated(self) -> None:
        """Accessing state property records RenderTree in node_trees dict."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            counter: int = 0

        state = MyState()

        @component
        def Counter() -> None:
            _ = state.counter

        ctx = RenderTree(Counter)
        ctx.render()

        # Check that the RenderTree weakref is recorded for this node
        deps = state._state_props["counter"]
        assert ctx.root_node.id in deps.node_trees
        # node_trees stores weakrefs to allow RenderTree garbage collection
        assert deps.node_trees[ctx.root_node.id]() is ctx

    def test_child_and_parent_track_same_state(self) -> None:
        """Parent and child accessing same state are tracked independently."""

        @dataclass(kw_only=True)
        class SharedState(Stateful):
            value: int = 0

        state = SharedState()

        @component
        def Child() -> None:
            _ = state.value

        @component
        def Parent() -> None:
            _ = state.value
            Child()

        ctx = RenderTree(Parent)
        ctx.render()

        parent_id = ctx.root_node.id
        child_id = ctx.root_node.child_ids[0]

        # Both nodes should be tracked
        deps = state._state_props["value"]
        assert parent_id in deps.node_ids
        assert child_id in deps.node_ids
        assert len(deps.node_ids) == 2

    def test_state_change_marks_all_dependents_dirty(self) -> None:
        """State change marks all dependent nodes dirty."""

        @dataclass(kw_only=True)
        class SharedState(Stateful):
            value: int = 0

        state = SharedState()

        @component
        def Child() -> None:
            _ = state.value

        @component
        def Parent() -> None:
            _ = state.value
            Child()

        ctx = RenderTree(Parent)
        ctx.render()

        parent_id = ctx.root_node.id
        child_id = ctx.root_node.child_ids[0]

        # Clear dirty state
        ctx._dirty_ids.clear()
        ctx._element_state[parent_id].dirty = False
        ctx._element_state[child_id].dirty = False

        # Change state - both should be marked dirty
        state.value = 42

        assert parent_id in ctx._dirty_ids
        assert child_id in ctx._dirty_ids

    def test_dependency_persists_across_rerenders(self) -> None:
        """Dependencies persist when component re-renders."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()

        @component
        def Consumer() -> None:
            _ = state.value

        ctx = RenderTree(Consumer)
        ctx.render()

        node_id = ctx.root_node.id

        # Verify dependency exists
        assert node_id in state._state_props["value"].node_ids

        # Re-render
        ctx.mark_dirty_id(node_id)
        ctx.render()

        # Dependency should still exist
        assert node_id in state._state_props["value"].node_ids

    def test_multiple_properties_tracked_independently(self) -> None:
        """Different properties track dependencies independently."""

        @dataclass(kw_only=True)
        class MultiState(Stateful):
            name: str = ""
            count: int = 0

        state = MultiState()

        @component
        def NameConsumer() -> None:
            _ = state.name

        @component
        def CountConsumer() -> None:
            _ = state.count

        @component
        def App() -> None:
            NameConsumer()
            CountConsumer()

        ctx = RenderTree(App)
        ctx.render()

        name_id = ctx.root_node.child_ids[0]
        count_id = ctx.root_node.child_ids[1]

        # Check name deps
        name_deps = state._state_props["name"]
        assert name_id in name_deps.node_ids
        assert count_id not in name_deps.node_ids

        # Check count deps
        count_deps = state._state_props["count"]
        assert count_id in count_deps.node_ids
        assert name_id not in count_deps.node_ids

    def test_dependency_cleanup_on_unmount(self) -> None:
        """Dependencies are cleaned up when component is unmounted."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        show_consumer = [True]

        @component
        def Consumer() -> None:
            _ = state.value

        @component
        def App() -> None:
            if show_consumer[0]:
                Consumer()

        ctx = RenderTree(App)
        ctx.render()

        # Get the Consumer's node id
        consumer_id = ctx.root_node.child_ids[0]

        # Verify consumer is tracking state
        assert consumer_id in state._state_props["value"].node_ids

        # Unmount Consumer by removing it
        show_consumer[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Consumer's dependency should be cleaned up
        assert consumer_id not in state._state_props["value"].node_ids
        assert consumer_id not in state._state_props["value"].node_trees

    def test_dependency_cleanup_on_rerender_without_read(self) -> None:
        """Dependencies are cleaned up when component stops reading state."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        read_state = [True]

        @component
        def Consumer() -> None:
            if read_state[0]:
                _ = state.value

        ctx = RenderTree(Consumer)
        ctx.render()

        node_id = ctx.root_node.id

        # Initially tracking
        assert node_id in state._state_props["value"].node_ids

        # Stop reading state and re-render
        read_state[0] = False
        ctx.mark_dirty_id(node_id)
        ctx.render()

        # No longer tracking (cleared before render, not re-registered)
        assert node_id not in state._state_props["value"].node_ids
