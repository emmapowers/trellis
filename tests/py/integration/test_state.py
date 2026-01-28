"""Tests for trellis.core.state module."""

import asyncio
import gc
from dataclasses import dataclass
from typing import TYPE_CHECKING

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful

if TYPE_CHECKING:
    from tests.conftest import PatchCapture, RenderResult


class TestStateful:
    def test_stateful_set_and_get(self) -> None:
        """State values can be set and retrieved."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        state.value = "hello"
        assert state.value == "hello"

    def test_stateful_tracks_dependencies(self, rendered: "type[RenderResult]") -> None:
        """Accessing state during render registers the element as dependent."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            text: str = ""

        state = MyState()
        state.text = "hello"

        @component
        def MyComponent() -> None:
            _ = state.text  # Access the state

        result = rendered(MyComponent)

        # INTERNAL TEST: Verify dependency tracking internals - no public API to inspect watchers
        state_info = state._state_props["text"]
        assert len(state_info.watchers) == 1
        # Keep result alive to prevent GC of Element
        assert result.root_element is not None

    def test_stateful_marks_dirty_on_change(self, capture_patches: "type[PatchCapture]") -> None:
        """Changing state marks dependent elements as dirty."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            text: str = ""

        state = MyState()
        state.text = "hello"

        @component
        def MyComponent() -> None:
            _ = state.text

        capture = capture_patches(MyComponent)
        capture.render()

        # Clear dirty state
        ctx = capture.session
        ctx.dirty.pop_all()

        # Change state
        state.text = "world"

        # Element should be marked dirty
        assert ctx.root_element.id in ctx.dirty

    def test_stateful_render_dirty_updates(self, capture_patches: "type[PatchCapture]") -> None:
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

        capture = capture_patches(MyComponent)
        capture.render()
        assert render_count[0] == 1

        state.text = "changed"
        capture.render()
        assert render_count[0] == 2

    def test_fine_grained_tracking(self, capture_patches: "type[PatchCapture]") -> None:
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

        capture = capture_patches(Parent)
        capture.render()

        assert name_renders[0] == 1
        assert count_renders[0] == 1

        # Change only name - only NameComponent should re-render
        state.name = "updated"
        capture.render()

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

    def test_local_state_persists_across_rerenders(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
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

        capture = capture_patches(Counter)
        capture.render()

        # Re-render by marking dirty - should reuse same instance
        ctx = capture.session
        ctx.dirty.mark(ctx.root_element.id)
        capture.render()

        # Third render
        ctx.dirty.mark(ctx.root_element.id)
        capture.render()

        # All renders should return the same state instance
        assert len(captured_state_ids) == 3
        assert captured_state_ids[0] == captured_state_ids[1] == captured_state_ids[2]

    def test_local_state_values_preserved(self, capture_patches: "type[PatchCapture]") -> None:
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

        capture = capture_patches(Counter)
        capture.render()
        # Increment outside render
        ctx = capture.session
        state_ref[0].count = 1
        ctx.dirty.mark(ctx.root_element.id)
        capture.render()
        # Increment again outside render
        state_ref[0].count = 2
        ctx.dirty.mark(ctx.root_element.id)
        capture.render()

        # Should see 0, 1, 2 as count persists across re-renders
        assert observed_counts == [0, 1, 2]

    def test_multiple_state_instances_same_type(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
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

        capture = capture_patches(MultiToggle)
        capture.render()

        # Verify we got two distinct instances
        assert len(captured) == 2
        assert captured[0] is not captured[1]

        # Re-render - each should get its own cached instance
        ctx = capture.session
        ctx.dirty.mark(ctx.root_element.id)
        capture.render()

        # Should return same instances on re-render
        assert len(captured) == 4
        assert captured[0] is captured[2]  # first instance reused
        assert captured[1] is captured[3]  # second instance reused

        # Check that we have 2 distinct state entries in the root element's cache
        root_state = ctx.states.get(ctx.root_element.id)
        state_keys = [k for k in root_state.local_state.keys() if k[0].__name__ == "ToggleState"]
        assert len(state_keys) == 2

        # Check they have different call indices
        indices = [k[1] for k in state_keys]
        assert 0 in indices
        assert 1 in indices

    def test_subclass_state_works(self, capture_patches: "type[PatchCapture]") -> None:
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

        capture = capture_patches(MyComponent)
        capture.render()

        # Both should be cached separately by their actual types on the element
        ctx = capture.session
        root_state = ctx.states.get(ctx.root_element.id)
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
        ctx.dirty.mark(ctx.root_element.id)
        capture.render()

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
    """Tests for state dependency tracking internals.

    INTERNAL TEST: These tests verify the internal dependency tracking mechanism
    (_state_props, watchers WeakSet, _session_ref) which has no public API.
    """

    def test_watchers_weakset_populated(self, rendered: "type[RenderResult]") -> None:
        """Accessing state property populates watchers WeakSet."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        state.value = "test"

        @component
        def Consumer() -> None:
            _ = state.value  # Access the property

        result = rendered(Consumer)

        # Check that node was recorded in state deps
        assert "value" in state._state_props
        deps = state._state_props["value"]
        # WeakSet contains the Element
        watchers_list = list(deps.watchers)
        assert len(watchers_list) == 1
        assert watchers_list[0].id == result.root_element.id

    def test_session_ref_set_on_element_node(self, rendered: "type[RenderResult]") -> None:
        """Element has _session_ref pointing to RenderSession.

        INTERNAL TEST: _session_ref is internal - verifies Element-Session linkage.
        """

        @dataclass(kw_only=True)
        class MyState(Stateful):
            counter: int = 0

        state = MyState()

        @component
        def Counter() -> None:
            _ = state.counter

        result = rendered(Counter)

        node = result.root_element
        assert node._session_ref() is result.session

    def test_child_and_parent_track_same_state(self, rendered: "type[RenderResult]") -> None:
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

        result = rendered(Parent)

        parent_id = result.root_element.id
        child_id = result.root_element.child_ids[0]

        # Both nodes should be tracked
        deps = state._state_props["value"]
        watcher_ids = {node.id for node in deps.watchers}
        assert parent_id in watcher_ids
        assert child_id in watcher_ids
        assert len(watcher_ids) == 2

    def test_state_change_marks_all_dependents_dirty(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
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

        capture = capture_patches(Parent)
        capture.render()

        ctx = capture.session
        parent_id = ctx.root_element.id
        child_id = ctx.root_element.child_ids[0]

        # Clear dirty state
        ctx.dirty.pop_all()

        # Change state - both should be marked dirty
        state.value = 42

        assert parent_id in ctx.dirty
        assert child_id in ctx.dirty

    def test_dependency_persists_across_rerenders(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Dependencies persist when component re-renders."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()

        @component
        def Consumer() -> None:
            _ = state.value

        capture = capture_patches(Consumer)
        capture.render()

        ctx = capture.session
        node_id = ctx.root_element.id

        # Verify dependency exists
        watcher_ids = {node.id for node in state._state_props["value"].watchers}
        assert node_id in watcher_ids

        # Re-render
        ctx.dirty.mark(node_id)
        capture.render()

        # Dependency should still exist (may be a different node object but same id)
        watcher_ids = {node.id for node in state._state_props["value"].watchers}
        assert node_id in watcher_ids

    def test_multiple_properties_tracked_independently(
        self, rendered: "type[RenderResult]"
    ) -> None:
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

        result = rendered(App)

        name_id = result.root_element.child_ids[0]
        count_id = result.root_element.child_ids[1]

        # Check name deps
        name_deps = state._state_props["name"]
        name_watcher_ids = {node.id for node in name_deps.watchers}
        assert name_id in name_watcher_ids
        assert count_id not in name_watcher_ids

        # Check count deps
        count_deps = state._state_props["count"]
        count_watcher_ids = {node.id for node in count_deps.watchers}
        assert count_id in count_watcher_ids
        assert name_id not in count_watcher_ids

    def test_dependency_cleanup_on_unmount(self, capture_patches: "type[PatchCapture]") -> None:
        """Dependencies are cleaned up when component is unmounted (via WeakSet GC)."""

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

        capture = capture_patches(App)
        capture.render()

        # Get the Consumer's node id
        ctx = capture.session
        consumer_id = ctx.root_element.child_ids[0]

        # Verify consumer is tracking state
        watcher_ids = {node.id for node in state._state_props["value"].watchers}
        assert consumer_id in watcher_ids

        # Unmount Consumer by removing it
        show_consumer[0] = False
        ctx.dirty.mark(ctx.root_element.id)
        capture.render()

        # Force garbage collection to clean up WeakSet
        gc.collect()

        # Consumer's dependency should be cleaned up (WeakSet auto-removes dead refs)
        watcher_ids = {node.id for node in state._state_props["value"].watchers}
        assert consumer_id not in watcher_ids

    def test_dependency_cleanup_on_rerender_without_read(self) -> None:
        """Dependencies are cleaned up when component stops reading state (via WeakSet GC).

        NOTE: This test uses RenderSession directly because it's testing internal
        WeakSet GC behavior that's sensitive to reference retention patterns.
        """

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        read_state = [True]

        @component
        def Consumer() -> None:
            if read_state[0]:
                _ = state.value

        ctx = RenderSession(Consumer)
        render(ctx)

        node_id = ctx.root_element.id

        # Initially tracking
        watcher_ids = {node.id for node in state._state_props["value"].watchers}
        assert node_id in watcher_ids

        # Stop reading state and re-render
        read_state[0] = False
        ctx.dirty.mark(node_id)
        render(ctx)

        # Force garbage collection
        gc.collect()

        # The old node is replaced by a new one that doesn't read state
        # WeakSet should no longer contain the old node (GC'd), and new node
        # doesn't register because it doesn't read state.value
        watcher_ids = {node.id for node in state._state_props["value"].watchers}
        assert node_id not in watcher_ids


class TestLifecycleHooksWithContext:
    """Tests for from_context() working in on_mount and on_unmount hooks."""

    def test_from_context_works_in_on_mount(self, capture_patches: "type[PatchCapture]") -> None:
        """from_context() retrieves state in on_mount hook."""

        @dataclass(kw_only=True)
        class AppState(Stateful):
            value: str = ""

        retrieved_values: list[str] = []

        @dataclass(kw_only=True)
        class ChildState(Stateful):
            def on_mount(self) -> None:
                # This should work - from_context() in on_mount
                state = AppState.from_context()
                retrieved_values.append(state.value)

        @component
        def App() -> None:
            with AppState(value="mounted"):
                Child()

        @component
        def Child() -> None:
            ChildState()

        capture = capture_patches(App)
        capture.render()

        # on_mount should have been called and from_context should have worked
        assert retrieved_values == ["mounted"]

    def test_from_context_works_in_on_unmount(self, capture_patches: "type[PatchCapture]") -> None:
        """from_context() retrieves state in on_unmount hook."""

        @dataclass(kw_only=True)
        class AppState(Stateful):
            value: str = ""

        retrieved_values: list[str] = []
        show_child = [True]

        @dataclass(kw_only=True)
        class ChildState(Stateful):
            def on_unmount(self) -> None:
                # This should work - from_context() in on_unmount
                state = AppState.from_context()
                retrieved_values.append(state.value)

        @component
        def App() -> None:
            with AppState(value="unmounting"):
                if show_child[0]:
                    Child()

        @component
        def Child() -> None:
            ChildState()

        capture = capture_patches(App)
        capture.render()

        # Initially, nothing should be in retrieved_values
        assert retrieved_values == []

        # Unmount the child
        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        # on_unmount should have been called and from_context should have worked
        assert retrieved_values == ["unmounting"]

    def test_from_context_returns_default_in_mount_when_not_in_context(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """from_context(default=None) returns None in on_mount when state not found."""

        @dataclass(kw_only=True)
        class MissingState(Stateful):
            pass

        results: list = []

        @dataclass(kw_only=True)
        class ChildState(Stateful):
            def on_mount(self) -> None:
                state = MissingState.from_context(default=None)
                results.append(state)

        @component
        def App() -> None:
            ChildState()

        capture = capture_patches(App)
        capture.render()

        assert results == [None]


class TestAsyncLifecycleHooks:
    """Tests for async on_mount and on_unmount hooks."""

    def test_async_on_mount_is_called(self, capture_patches: "type[PatchCapture]") -> None:
        """Async on_mount hooks are called and complete."""
        completed: list[str] = []
        done_event = asyncio.Event()

        @dataclass(kw_only=True)
        class AsyncMountState(Stateful):
            async def on_mount(self) -> None:
                completed.append("mount")
                done_event.set()

        @component
        def App() -> None:
            AsyncMountState()

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await asyncio.wait_for(done_event.wait(), timeout=1.0)
            assert completed == ["mount"]

        asyncio.run(test())

    def test_async_on_unmount_is_called(self, capture_patches: "type[PatchCapture]") -> None:
        """Async on_unmount hooks are called and complete."""
        completed: list[str] = []
        done_event = asyncio.Event()
        show_child = [True]

        @dataclass(kw_only=True)
        class AsyncUnmountState(Stateful):
            async def on_unmount(self) -> None:
                completed.append("unmount")
                done_event.set()

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        @component
        def Child() -> None:
            AsyncUnmountState()

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            assert completed == []

            # Unmount the child
            show_child[0] = False
            capture.session.dirty.mark(capture.session.root_element.id)
            capture.render()

            await asyncio.wait_for(done_event.wait(), timeout=1.0)
            assert completed == ["unmount"]

        asyncio.run(test())

    def test_async_on_mount_with_from_context(self, capture_patches: "type[PatchCapture]") -> None:
        """Async on_mount can use from_context()."""
        retrieved_values: list[str] = []
        done_event = asyncio.Event()

        @dataclass(kw_only=True)
        class AppState(Stateful):
            value: str = ""

        @dataclass(kw_only=True)
        class AsyncChildState(Stateful):
            async def on_mount(self) -> None:
                state = AppState.from_context()
                retrieved_values.append(state.value)
                done_event.set()

        @component
        def App() -> None:
            with AppState(value="async-mounted"):
                Child()

        @component
        def Child() -> None:
            AsyncChildState()

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()
            await asyncio.wait_for(done_event.wait(), timeout=1.0)

        asyncio.run(test())

        assert retrieved_values == ["async-mounted"]

    def test_background_tasks_tracked_on_session(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Background tasks from async hooks are tracked on session.

        INTERNAL TEST: _background_tasks is internal - verifies GC prevention.
        """
        completed: list[str] = []
        proceed_event = asyncio.Event()
        done_event = asyncio.Event()

        @dataclass(kw_only=True)
        class AsyncState(Stateful):
            async def on_mount(self) -> None:
                await proceed_event.wait()
                completed.append("done")
                done_event.set()

        @component
        def App() -> None:
            AsyncState()

        capture = capture_patches(App)

        async def test() -> None:
            capture.render()

            # Give task a chance to start
            await asyncio.sleep(0)

            # Task should be tracked
            assert len(capture.session._background_tasks) == 1

            # Let task complete
            proceed_event.set()
            await asyncio.wait_for(done_event.wait(), timeout=1.0)

            # Give done callback a chance to run
            await asyncio.sleep(0)

            # Task should be removed after completion
            assert len(capture.session._background_tasks) == 0
            assert completed == ["done"]

        asyncio.run(test())


class TestAttributeTracking:
    """Tests for type-annotation-based attribute tracking."""

    def test_only_annotated_attributes_tracked(self, rendered: "type[RenderResult]") -> None:
        """Only attributes with type annotations in subclasses are tracked."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            annotated: str = ""

        state = MyState()
        state.annotated = "value"
        # Add non-annotated attribute dynamically
        state.unannotated = "dynamic"  # type: ignore[attr-defined]

        @component
        def MyComponent() -> None:
            _ = state.annotated
            _ = state.unannotated  # type: ignore[attr-defined]

        result = rendered(MyComponent)

        # INTERNAL TEST: annotated attribute should be tracked
        assert "annotated" in state._state_props
        # Non-annotated attribute should NOT be tracked
        assert "unannotated" not in state._state_props
        assert result.root_element is not None

    def test_private_annotated_attributes_tracked(self, rendered: "type[RenderResult]") -> None:
        """Private attributes with type annotations ARE tracked."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            _private: str = ""  # Private but annotated

        state = MyState()
        state._private = "secret"

        @component
        def MyComponent() -> None:
            _ = state._private

        result = rendered(MyComponent)

        # INTERNAL TEST: private annotated attribute should be tracked
        assert "_private" in state._state_props
        assert len(state._state_props["_private"].watchers) == 1
        assert result.root_element is not None

    def test_stateful_internal_attrs_not_tracked(self, rendered: "type[RenderResult]") -> None:
        """Internal Stateful attributes (_state_props, _initialized) are NOT tracked."""

        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: str = ""

        state = MyState()
        state.value = "test"

        @component
        def MyComponent() -> None:
            _ = state.value
            # These are internal Stateful attrs, not tracked
            _ = state._initialized
            _ = state._state_props

        result = rendered(MyComponent)

        # INTERNAL TEST: only user-defined annotated attrs should be tracked
        assert "value" in state._state_props
        assert "_initialized" not in state._state_props
        assert "_state_props" not in state._state_props
        assert result.root_element is not None
