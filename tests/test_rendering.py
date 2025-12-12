"""Tests for trellis.core.rendering module."""

import concurrent.futures
import threading

import pytest

from trellis.core.rendering import (
    ElementNode,
    RenderTree,
    freeze_props,
    get_active_render_tree,
    set_active_render_tree,
)
from trellis.core.functional_component import FunctionalComponent, component
from trellis.core.state import Stateful
from dataclasses import dataclass


def make_component(name: str) -> FunctionalComponent:
    """Helper to create a simple test component."""
    return FunctionalComponent(name=name, render_func=lambda: None)


def make_descriptor(
    comp: FunctionalComponent,
    key: str = "",
    props: dict | None = None,
) -> ElementNode:
    """Helper to create an ElementNode."""
    return ElementNode(
        component=comp,
        key=key,
        props=freeze_props(props or {}),
    )


class TestElementNode:
    def test_element_node_creation(self) -> None:
        comp = make_component("Test")
        node = make_descriptor(comp)

        assert node.component == comp
        assert node.key == ""
        assert node.props == freeze_props({})
        assert node.children == ()
        assert node.id == ""

    def test_element_node_with_key(self) -> None:
        comp = make_component("Test")
        node = make_descriptor(comp, key="my-key")

        assert node.key == "my-key"

    def test_element_node_with_properties(self) -> None:
        comp = make_component("Test")
        node = make_descriptor(comp, props={"foo": "bar", "count": 42})

        assert node.properties == {"foo": "bar", "count": 42}

    def test_element_node_is_immutable(self) -> None:
        comp = make_component("Test")
        node = make_descriptor(comp, props={"a": 1})

        # ElementNode is a frozen dataclass, should be hashable
        hash(node)  # Should not raise

        # Can't modify attributes
        with pytest.raises(AttributeError):
            node.key = "new-key"  # type: ignore[misc]


class TestActiveRenderTree:
    def test_default_is_none(self) -> None:
        assert get_active_render_tree() is None

    def test_set_and_get(self) -> None:
        comp = make_component("Root")
        ctx = RenderTree(comp)

        set_active_render_tree(ctx)
        assert get_active_render_tree() is ctx

        set_active_render_tree(None)
        assert get_active_render_tree() is None


class TestRenderTree:
    def test_creation(self) -> None:
        comp = make_component("Root")
        ctx = RenderTree(comp)

        assert ctx.root_component == comp
        assert ctx.root_node is None
        assert ctx._dirty_ids == set()
        assert ctx.rendering is False

    def test_mark_dirty_id(self) -> None:
        @component
        def Root() -> None:
            pass

        ctx = RenderTree(Root)
        ctx.render()

        # The root node should have an ID now
        assert ctx.root_node is not None
        node_id = ctx.root_node.id

        # Clear dirty state
        ctx._dirty_ids.clear()
        ctx._element_state[node_id].dirty = False

        # Mark dirty by ID
        ctx.mark_dirty_id(node_id)

        assert node_id in ctx._dirty_ids
        assert ctx._element_state[node_id].dirty is True


class TestConcurrentRenderTreeIsolation:
    """Tests for thread/task isolation of render trees using contextvars."""

    def test_concurrent_threads_have_isolated_trees(self) -> None:
        """Each thread has its own active render tree."""
        results: dict[str, RenderTree | None] = {}
        barrier = threading.Barrier(2)

        @component
        def AppA() -> None:
            pass

        @component
        def AppB() -> None:
            pass

        def thread_a() -> None:
            ctx = RenderTree(AppA)
            set_active_render_tree(ctx)
            barrier.wait()  # Sync with thread B
            results["a"] = get_active_render_tree()
            set_active_render_tree(None)

        def thread_b() -> None:
            ctx = RenderTree(AppB)
            set_active_render_tree(ctx)
            barrier.wait()  # Sync with thread A
            results["b"] = get_active_render_tree()
            set_active_render_tree(None)

        t1 = threading.Thread(target=thread_a)
        t2 = threading.Thread(target=thread_b)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Each thread should see its own context
        assert results["a"] is not None
        assert results["b"] is not None
        assert results["a"] != results["b"]
        assert results["a"].root_component.name == "AppA"
        assert results["b"].root_component.name == "AppB"

    def test_concurrent_renders_dont_interfere(self) -> None:
        """Concurrent renders in different threads don't corrupt each other."""
        render_results: dict[str, list[str]] = {"a": [], "b": []}

        @component
        def ChildA(name: str = "") -> None:
            render_results["a"].append(name)

        @component
        def ChildB(name: str = "") -> None:
            render_results["b"].append(name)

        @component
        def AppA() -> None:
            for i in range(5):
                ChildA(name=f"a_{i}")

        @component
        def AppB() -> None:
            for i in range(5):
                ChildB(name=f"b_{i}")

        def render_app_a() -> None:
            ctx = RenderTree(AppA)
            ctx.render()

        def render_app_b() -> None:
            ctx = RenderTree(AppB)
            ctx.render()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(render_app_a), executor.submit(render_app_b)]
            concurrent.futures.wait(futures)

        # Each render should have created its own children
        assert render_results["a"] == [f"a_{i}" for i in range(5)]
        assert render_results["b"] == [f"b_{i}" for i in range(5)]


class TestComponentOutsideRenderTree:
    """Tests for RuntimeError when creating components outside render tree."""

    def test_component_outside_render_raises(self) -> None:
        """Creating a component outside render context raises RuntimeError."""

        @component
        def MyComponent() -> None:
            pass

        # Ensure no active context
        set_active_render_tree(None)

        with pytest.raises(RuntimeError, match="outside of render context"):
            MyComponent()

    def test_container_with_block_outside_render_raises(self) -> None:
        """Using 'with' on container outside render context raises RuntimeError."""

        @component
        def Container(children: list) -> None:
            for c in children:
                c()

        set_active_render_tree(None)

        with pytest.raises(RuntimeError, match="outside of render context"):
            with Container():
                pass


class TestDescriptorStackCleanupOnException:
    """Tests for descriptor stack cleanup when component execution fails."""

    def test_exception_in_component_cleans_up_stack(self) -> None:
        """Exception during component execution doesn't corrupt descriptor stack."""

        @component
        def FailingChild() -> None:
            raise ValueError("intentional failure")

        @component
        def Parent() -> None:
            FailingChild()

        ctx = RenderTree(Parent)

        with pytest.raises(ValueError, match="intentional failure"):
            ctx.render()

        # Stack should be clean after exception
        assert ctx._descriptor_stack == []

    def test_exception_in_nested_with_block_cleans_up(self) -> None:
        """Exception in nested with block doesn't corrupt stack."""

        @component
        def Container(children: list) -> None:
            for c in children:
                c()

        @component
        def FailingComponent() -> None:
            raise RuntimeError("nested failure")

        @component
        def App() -> None:
            with Container():
                FailingComponent()

        ctx = RenderTree(App)

        with pytest.raises(RuntimeError, match="nested failure"):
            ctx.render()

        assert ctx._descriptor_stack == []


class TestThreadSafeStateUpdates:
    """Tests for thread safety of state updates during render."""

    def test_state_updates_during_concurrent_renders(self) -> None:
        """State updates in one render don't affect another concurrent render."""
        results: dict[str, int] = {}

        @dataclass
        class Counter(Stateful):
            value: int = 0

        @component
        def AppWithState(initial: int = 0, name: str = "") -> None:
            state = Counter()
            # On first render, state.value will be set
            if state.value == 0:
                state.value = initial
            results[name] = state.value

        def render_with_value(initial: int, name: str) -> None:
            # Create a fresh component for each render to avoid sharing
            @component
            def LocalApp() -> None:
                state = Counter()
                if state.value == 0:
                    state.value = initial
                results[name] = state.value

            ctx = RenderTree(LocalApp)
            ctx.render()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(render_with_value, 100, "ctx_100"),
                executor.submit(render_with_value, 200, "ctx_200"),
                executor.submit(render_with_value, 300, "ctx_300"),
                executor.submit(render_with_value, 400, "ctx_400"),
            ]
            concurrent.futures.wait(futures)

        # Each context should have its own state value
        assert results["ctx_100"] == 100
        assert results["ctx_200"] == 200
        assert results["ctx_300"] == 300
        assert results["ctx_400"] == 400

    def test_callback_registry_isolated_per_tree(self) -> None:
        """Callback registries are isolated per RenderTree."""

        @component
        def App() -> None:
            pass

        ctx1 = RenderTree(App)
        ctx2 = RenderTree(App)

        cb1 = lambda: "callback1"
        cb2 = lambda: "callback2"

        id1 = ctx1.register_callback(cb1)
        id2 = ctx2.register_callback(cb2)

        # Same ID format but different registries
        assert id1 == id2 == "cb_1"

        # But they resolve to different callbacks
        assert ctx1.get_callback(id1)() == "callback1"
        assert ctx2.get_callback(id2)() == "callback2"

        # Cross-lookup returns None
        assert ctx1.get_callback("cb_999") is None

    def test_state_update_blocks_during_render(self) -> None:
        """State updates on another thread block while render holds the lock.

        This tests that mark_dirty_id() blocks when called from another thread
        while a render is in progress on the same RenderTree.
        """
        import time

        events: list[str] = []
        state_holder: list[Stateful] = []
        render_count = [0]

        @dataclass
        class SlowState(Stateful):
            value: int = 0

        @component
        def SlowApp() -> None:
            state = SlowState()
            # Read value to register dependency
            _ = state.value
            render_count[0] += 1

            if render_count[0] == 1:
                # First render - store state and wait
                state_holder.append(state)
                # Simulate slow render - background thread will try to update during this
                time.sleep(0.15)
                events.append("first_render_done")
            else:
                # Re-render triggered by state change
                events.append("rerender_started")

        ctx = RenderTree(SlowApp)

        def background_update() -> None:
            # Wait for render to start and state to be created
            while not state_holder:
                time.sleep(0.01)
            # Give render a moment to be in the slow section
            time.sleep(0.05)
            state = state_holder[0]
            events.append("update_start")
            # This triggers mark_dirty_id which needs the lock
            state.value = 42
            events.append("update_done")

        updater = threading.Thread(target=background_update)
        updater.start()

        # Start render (holds lock via @with_lock on render_tree)
        ctx.render()

        updater.join()

        # Verify ordering: update_start happens during render (before first_render_done)
        # but update_done happens after first_render_done because mark_dirty_id blocks
        assert "update_start" in events
        assert "first_render_done" in events
        assert "update_done" in events
        # The key assertion: mark_dirty_id blocks, so update_done must come after render releases lock
        assert events.index("first_render_done") < events.index("update_done")
