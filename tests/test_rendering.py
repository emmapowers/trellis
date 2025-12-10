"""Tests for trellis.core.rendering module."""

import concurrent.futures
import threading

import pytest

from trellis.core.rendering import (
    Element,
    ElementDescriptor,
    RenderContext,
    freeze_props,
    get_active_render_context,
    set_active_render_context,
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
) -> ElementDescriptor:
    """Helper to create an ElementDescriptor."""
    return ElementDescriptor(
        component=comp,
        key=key,
        props=freeze_props(props or {}),
    )


def make_element(
    comp: FunctionalComponent,
    key: str = "",
    props: dict | None = None,
    depth: int = 0,
) -> Element:
    """Helper to create an Element with a descriptor."""
    desc = make_descriptor(comp, key, props)
    return Element(descriptor=desc, depth=depth)


class TestElement:
    def test_element_creation(self) -> None:
        comp = make_component("Test")
        elem = make_element(comp)

        assert elem.component == comp
        assert elem.key == ""
        assert elem.properties == {}
        assert elem.children == []
        assert elem.dirty is False
        assert elem.parent is None
        assert elem.depth == 0

    def test_element_with_key(self) -> None:
        comp = make_component("Test")
        elem = make_element(comp, key="my-key")

        assert elem.key == "my-key"

    def test_element_with_properties(self) -> None:
        comp = make_component("Test")
        elem = make_element(comp, props={"foo": "bar", "count": 42})

        assert elem.properties == {"foo": "bar", "count": 42}

    def test_element_hash_uses_identity(self) -> None:
        comp = make_component("Test")
        elem1 = make_element(comp)
        elem2 = make_element(comp)

        assert hash(elem1) != hash(elem2)
        assert hash(elem1) == hash(elem1)

    def test_element_replace(self) -> None:
        comp = make_component("Test")
        elem1 = make_element(comp, props={"a": 1}, depth=0)
        elem2 = make_element(comp, props={"b": 2}, depth=5)

        elem1.replace(elem2)

        assert elem1.properties == {"b": 2}
        assert elem1.depth == 5


class TestActiveRenderContext:
    def test_default_is_none(self) -> None:
        assert get_active_render_context() is None

    def test_set_and_get(self) -> None:
        comp = make_component("Root")
        ctx = RenderContext(comp)

        set_active_render_context(ctx)
        assert get_active_render_context() is ctx

        set_active_render_context(None)
        assert get_active_render_context() is None


class TestRenderContext:
    def test_creation(self) -> None:
        comp = make_component("Root")
        ctx = RenderContext(comp)

        assert ctx.root_component == comp
        assert ctx.root_element is None
        assert ctx.dirty_elements == set()
        assert ctx.rendering is False

    def test_mark_dirty(self) -> None:
        comp = make_component("Root")
        ctx = RenderContext(comp)
        elem = make_element(comp)

        ctx.mark_dirty(elem)

        assert elem in ctx.dirty_elements
        assert elem.dirty is True

    def test_current_element_empty_stack(self) -> None:
        comp = make_component("Root")
        ctx = RenderContext(comp)

        assert ctx.current_element is None


class TestConcurrentRenderContextIsolation:
    """Tests for thread/task isolation of render contexts using contextvars."""

    def test_concurrent_threads_have_isolated_contexts(self) -> None:
        """Each thread has its own active render context."""
        results: dict[str, RenderContext | None] = {}
        barrier = threading.Barrier(2)

        @component
        def AppA() -> None:
            pass

        @component
        def AppB() -> None:
            pass

        def thread_a() -> None:
            ctx = RenderContext(AppA)
            set_active_render_context(ctx)
            barrier.wait()  # Sync with thread B
            results["a"] = get_active_render_context()
            set_active_render_context(None)

        def thread_b() -> None:
            ctx = RenderContext(AppB)
            set_active_render_context(ctx)
            barrier.wait()  # Sync with thread A
            results["b"] = get_active_render_context()
            set_active_render_context(None)

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
            ctx = RenderContext(AppA)
            ctx.render_tree(from_element=None)

        def render_app_b() -> None:
            ctx = RenderContext(AppB)
            ctx.render_tree(from_element=None)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(render_app_a), executor.submit(render_app_b)]
            concurrent.futures.wait(futures)

        # Each render should have created its own children
        assert render_results["a"] == [f"a_{i}" for i in range(5)]
        assert render_results["b"] == [f"b_{i}" for i in range(5)]


class TestComponentOutsideRenderContext:
    """Tests for RuntimeError when creating components outside render context."""

    def test_component_outside_render_raises(self) -> None:
        """Creating a component outside render context raises RuntimeError."""

        @component
        def MyComponent() -> None:
            pass

        # Ensure no active context
        set_active_render_context(None)

        with pytest.raises(RuntimeError, match="outside of render context"):
            MyComponent()

    def test_container_with_block_outside_render_raises(self) -> None:
        """Using 'with' on container outside render context raises RuntimeError."""

        @component
        def Container(children: list) -> None:
            for c in children:
                c()

        set_active_render_context(None)

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

        ctx = RenderContext(Parent)

        with pytest.raises(ValueError, match="intentional failure"):
            ctx.render_tree(from_element=None)

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

        ctx = RenderContext(App)

        with pytest.raises(RuntimeError, match="nested failure"):
            ctx.render_tree(from_element=None)

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

            ctx = RenderContext(LocalApp)
            ctx.render_tree(from_element=None)

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

    def test_callback_registry_isolated_per_context(self) -> None:
        """Callback registries are isolated per RenderContext."""

        @component
        def App() -> None:
            pass

        ctx1 = RenderContext(App)
        ctx2 = RenderContext(App)

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

        This tests that mark_dirty() blocks when called from another thread
        while a render is in progress on the same RenderContext.
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

        ctx = RenderContext(SlowApp)

        def background_update() -> None:
            # Wait for render to start and state to be created
            while not state_holder:
                time.sleep(0.01)
            # Give render a moment to be in the slow section
            time.sleep(0.05)
            state = state_holder[0]
            events.append("update_start")
            # This triggers mark_dirty which needs the lock
            state.value = 42
            events.append("update_done")

        updater = threading.Thread(target=background_update)
        updater.start()

        # Start render (holds lock via @with_lock on render_tree)
        ctx.render_tree(from_element=None)

        updater.join()

        # Verify ordering: update_start happens during render (before first_render_done)
        # but update_done happens after first_render_done because mark_dirty blocks
        assert "update_start" in events
        assert "first_render_done" in events
        assert "update_done" in events
        # The key assertion: mark_dirty blocks, so update_done must come after render releases lock
        assert events.index("first_render_done") < events.index("update_done")
