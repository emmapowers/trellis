"""Integration tests for rendering module - RenderSession, concurrency, lifecycle."""

import concurrent.futures
import logging
import threading
import time
from dataclasses import dataclass

import pytest

from trellis import html as h
from trellis.core.components.composition import CompositionComponent, component
from trellis.core.rendering.child_ref import ChildRef
from trellis.core.rendering.frames import _escape_key
from trellis.core.rendering.render import render
from trellis.core.rendering.session import (
    RenderSession,
    get_active_session,
    is_render_active,
    set_active_session,
)
from trellis.core.state.stateful import Stateful
from trellis.widgets import Button, Column, Label, Row


def make_component(name: str) -> CompositionComponent:
    """Helper to create a simple test component."""
    return CompositionComponent(name=name, render_func=lambda: None)


class TestActiveSession:
    def test_default_is_none(self) -> None:
        assert get_active_session() is None

    def test_set_and_get(self) -> None:
        comp = make_component("Root")
        ctx = RenderSession(comp)

        set_active_session(ctx)
        assert get_active_session() is ctx

        set_active_session(None)
        assert get_active_session() is None


class TestRenderSession:
    def test_creation(self) -> None:
        comp = make_component("Root")
        ctx = RenderSession(comp)

        assert ctx.root_component == comp
        assert ctx.root_element is None
        assert not ctx.dirty.has_dirty()

    def test_mark_dirty_id(self) -> None:
        @component
        def Root() -> None:
            pass

        ctx = RenderSession(Root)
        render(ctx)

        # The root node should have an ID now
        assert ctx.root_element is not None
        node_id = ctx.root_element.id

        # Clear dirty state
        ctx.dirty.pop_all()

        # Mark dirty by ID
        ctx.dirty.mark(node_id)

        assert node_id in ctx.dirty


class TestConcurrentRenderSessionIsolation:
    """Tests for thread/task isolation of render sessions using contextvars."""

    def test_concurrent_threads_have_isolated_sessions(self) -> None:
        """Each thread has its own active render session."""
        results: dict[str, RenderSession | None] = {}
        barrier = threading.Barrier(2)

        @component
        def AppA() -> None:
            pass

        @component
        def AppB() -> None:
            pass

        def thread_a() -> None:
            ctx = RenderSession(AppA)
            set_active_session(ctx)
            barrier.wait()  # Sync with thread B
            results["a"] = get_active_session()
            set_active_session(None)

        def thread_b() -> None:
            ctx = RenderSession(AppB)
            set_active_session(ctx)
            barrier.wait()  # Sync with thread A
            results["b"] = get_active_session()
            set_active_session(None)

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
            ctx = RenderSession(AppA)
            render(ctx)

        def render_app_b() -> None:
            ctx = RenderSession(AppB)
            render(ctx)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(render_app_a), executor.submit(render_app_b)]
            concurrent.futures.wait(futures)

        # Each render should have created its own children (order may vary due to set iteration)
        assert sorted(render_results["a"]) == [f"a_{i}" for i in range(5)]
        assert sorted(render_results["b"]) == [f"b_{i}" for i in range(5)]


class TestComponentOutsideRenderSession:
    """Tests for RuntimeError when creating components outside render session."""

    def test_component_outside_render_raises(self) -> None:
        """Creating a component outside render context raises RuntimeError."""

        @component
        def MyComponent() -> None:
            pass

        # Ensure no active context
        set_active_session(None)

        with pytest.raises(RuntimeError, match="outside of render context"):
            MyComponent()

    def test_container_with_block_outside_render_raises(self) -> None:
        """Using 'with' on container outside render context raises RuntimeError."""

        @component
        def Container(children: list) -> None:
            for c in children:
                c()

        set_active_session(None)

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

        ctx = RenderSession(Parent)

        with pytest.raises(ValueError, match="intentional failure"):
            render(ctx)

        # Stack should be clean after exception (active is set to None in finally)
        assert ctx.active is None

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

        ctx = RenderSession(App)

        with pytest.raises(RuntimeError, match="nested failure"):
            render(ctx)

        assert ctx.active is None


class TestThreadSafeStateUpdates:
    """Tests for thread safety of state updates during render."""

    def test_state_updates_during_concurrent_renders(self) -> None:
        """State updates in one render don't affect another concurrent render."""
        results: dict[str, int] = {}

        def render_with_value(initial: int, name: str) -> None:
            # Create a fresh Counter class per thread to avoid class-level state sharing
            @dataclass
            class Counter(Stateful):
                value: int = 0

            @component
            def LocalApp() -> None:
                # Initialize state via constructor kwargs
                state = Counter(value=initial)
                results[name] = state.value

            ctx = RenderSession(LocalApp)
            render(ctx)

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

    def test_callback_lookup_from_node_props(self) -> None:
        """Callbacks can be looked up from node props via get_callback."""

        @component
        def App() -> None:
            pass

        ctx = RenderSession(App)
        render(ctx)

        # Store a callback in a node's props
        node = ctx.root_element

        def test_cb() -> str:
            return "test_callback"

        node.props["on_click"] = test_cb

        # get_callback should find it
        result = ctx.get_callback(node.id, "on_click")
        assert result is not None
        assert result() == "test_callback"

        # Non-existent prop returns None
        assert ctx.get_callback(node.id, "on_missing") is None

        # Non-existent node returns None
        assert ctx.get_callback("nonexistent", "on_click") is None

    def test_state_update_blocks_during_render(self) -> None:
        """State updates on another thread block while render holds the lock.

        This tests that dirty.mark() blocks when called from another thread
        while a render is in progress on the same RenderSession.
        """
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

        ctx = RenderSession(SlowApp)

        def background_update() -> None:
            # Wait for render to start and state to be created
            while not state_holder:
                time.sleep(0.01)
            # Give render a moment to be in the slow section
            time.sleep(0.05)
            state = state_holder[0]
            events.append("update_start")
            # This triggers dirty.mark() which acquires the lock
            state.value = 42
            events.append("update_done")

        updater = threading.Thread(target=background_update)
        updater.start()

        # Start render (holds lock via with session.lock in render())
        render(ctx)

        updater.join()

        # Verify ordering: update_start happens during render (before first_render_done)
        # but update_done happens after first_render_done because dirty.mark() blocks
        assert "update_start" in events
        assert "first_render_done" in events
        assert "update_done" in events
        # The key assertion: dirty.mark() blocks, so update_done must come after render releases lock
        assert events.index("first_render_done") < events.index("update_done")


class TestElementStateParentId:
    """Tests for ElementState.parent_id tracking."""

    def test_element_state_parent_id_tracking(self) -> None:
        """ElementState.parent_id correctly tracks parent node."""

        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            Child()

        ctx = RenderSession(Parent)
        render(ctx)

        # Root has no parent
        root_state = ctx.states.get(ctx.root_element.id)
        assert root_state.parent_id is None

        # Child's parent should be root
        child_id = ctx.elements.get(ctx.root_element.child_ids[0]).id
        child_state = ctx.states.get(child_id)
        assert child_state.parent_id == ctx.root_element.id

    def test_parent_id_preserved_on_rerender(self) -> None:
        """parent_id is preserved when component re-renders."""

        @dataclass
        class Counter(Stateful):
            value: int = 0

        state_holder: list[Counter] = []

        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            state = Counter()
            state_holder.append(state)
            Child()

        ctx = RenderSession(Parent)
        render(ctx)

        child_id = ctx.elements.get(ctx.root_element.child_ids[0]).id
        original_parent_id = ctx.states.get(child_id).parent_id

        # Trigger re-render
        state_holder[0].value += 1
        render(ctx)

        # parent_id should be preserved
        assert ctx.states.get(child_id).parent_id == original_parent_id


class TestPropsComparison:
    """Tests for props comparison in _place() reuse optimization.

    These tests verify that components are not re-rendered when props
    are unchanged, and are re-rendered when props change.
    """

    def test_props_with_none_values(self) -> None:
        """Props with None values should be handled correctly."""
        render_counts: dict[str, int] = {}
        value_ref: list[str | None] = [None]

        @component
        def Child(value: str | None = None) -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def Parent() -> None:
            Child(value=value_ref[0])

        ctx = RenderSession(Parent)
        render(ctx)

        assert render_counts["child"] == 1

        # Same None value - should not re-render
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert render_counts["child"] == 1

        # Change to non-None
        value_ref[0] = "hello"
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert render_counts["child"] == 2

        # Change back to None
        value_ref[0] = None
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert render_counts["child"] == 3

    def test_props_with_callable(self) -> None:
        """Props with callable values use identity comparison."""
        render_counts: dict[str, int] = {}

        def handler1() -> None:
            pass

        def handler2() -> None:
            pass

        handler_ref = [handler1]

        @component
        def Child(on_click=None) -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def Parent() -> None:
            Child(on_click=handler_ref[0])

        ctx = RenderSession(Parent)
        render(ctx)

        assert render_counts["child"] == 1

        # Same function - should not re-render
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert render_counts["child"] == 1

        # Different function - should re-render
        handler_ref[0] = handler2
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert render_counts["child"] == 2

    def test_empty_props(self) -> None:
        """Components with no props should work correctly."""
        render_counts: dict[str, int] = {}

        @component
        def NoProps() -> None:
            render_counts["no_props"] = render_counts.get("no_props", 0) + 1

        @component
        def Parent() -> None:
            NoProps()

        ctx = RenderSession(Parent)
        render(ctx)

        assert render_counts["no_props"] == 1

        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        # Should not re-render (empty props unchanged)
        assert render_counts["no_props"] == 1

    def test_props_with_tuple(self) -> None:
        """Props with tuple values should compare correctly."""
        render_counts: dict[str, int] = {}
        tuple_ref = [(1, 2, 3)]

        @component
        def Child(items: tuple = ()) -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def Parent() -> None:
            Child(items=tuple_ref[0])

        ctx = RenderSession(Parent)
        render(ctx)

        assert render_counts["child"] == 1

        # Same tuple value - should not re-render
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert render_counts["child"] == 1

        # Different tuple - should re-render
        tuple_ref[0] = (1, 2, 4)
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert render_counts["child"] == 2


class TestBuiltinWidgetsReconciliation:
    """Tests for reconciliation with built-in widgets (ReactComponentBase/HtmlElement).

    These tests ensure that components created via @react_component_base and
    @html_element decorators work correctly in the reconciler. Unlike @component
    decorated functions, these use different class hierarchies that need to be
    hashable for type-based matching.

    Regression tests for: TypeError: unhashable type: '_Generated'
    """

    def test_remove_widget_from_middle_of_list(self) -> None:
        """Removing a widget from the middle exercises type-based matching."""
        items_ref = [["a", "b", "c", "d"]]

        @component
        def TodoList() -> None:
            h.H1("Tasks")  # Fixed head
            for item in items_ref[0]:
                with Row():
                    h.Span(item)
                    Button(text="×")
            Button(text="Add")  # Fixed tail

        ctx = RenderSession(TodoList)
        render(ctx)

        # Should have: H1, Row, Row, Row, Row, Button = 6 children
        assert len(ctx.root_element.child_ids) == 6

        # Remove "b" from the middle - this triggers type-based matching
        items_ref[0] = ["a", "c", "d"]
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        # Should have: H1, Row, Row, Row, Button = 5 children
        assert len(ctx.root_element.child_ids) == 5

    def test_html_elements_in_dynamic_list(self) -> None:
        """HTML elements (via @html_element) should be hashable for reconciliation."""
        items_ref = [["item1", "item2", "item3"]]

        @component
        def List() -> None:
            for item in items_ref[0]:
                with h.Div():
                    h.Span(item)

        ctx = RenderSession(List)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 3

        # Remove from middle
        items_ref[0] = ["item1", "item3"]
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 2

    def test_widgets_in_dynamic_list(self) -> None:
        """Widgets (via @react_component_base) should be hashable for reconciliation."""
        items_ref = [[1, 2, 3, 4, 5]]

        @component
        def List() -> None:
            with Column():
                for n in items_ref[0]:
                    with Row():
                        Label(text=f"Item {n}")
                        Button(text="Delete")

        ctx = RenderSession(List)
        render(ctx)

        column = ctx.elements.get(ctx.root_element.child_ids[0])
        assert len(column.child_ids) == 5

        # Remove items 2 and 4 (from middle)
        items_ref[0] = [1, 3, 5]
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        column = ctx.elements.get(ctx.root_element.child_ids[0])
        assert len(column.child_ids) == 3

    def test_mixed_widgets_and_components_in_list(self) -> None:
        """Mix of @component and @react_component_base in dynamic list."""
        items_ref = [["a", "b", "c"]]

        @component
        def CustomItem(name: str = "") -> None:
            Button(text=name)

        @component
        def List() -> None:
            for item in items_ref[0]:
                CustomItem(name=item)

        ctx = RenderSession(List)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 3

        # Reorder and remove
        items_ref[0] = ["c", "a"]
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert len(ctx.root_element.child_ids) == 2


class TestEscapeKey:
    """Tests for URL-encoding special characters in keys."""

    def test_no_special_chars(self) -> None:
        """Keys without special chars pass through unchanged."""
        assert _escape_key("simple") == "simple"
        assert _escape_key("with-dash") == "with-dash"
        assert _escape_key("with_underscore") == "with_underscore"
        assert _escape_key("CamelCase") == "CamelCase"
        assert _escape_key("123") == "123"

    def test_escape_colon(self) -> None:
        """Colon is escaped."""
        assert _escape_key("my:key") == "my%3Akey"
        assert _escape_key("a:b:c") == "a%3Ab%3Ac"

    def test_escape_at(self) -> None:
        """At sign is escaped."""
        assert _escape_key("item@home") == "item%40home"
        assert _escape_key("user@domain") == "user%40domain"

    def test_escape_slash(self) -> None:
        """Slash is escaped."""
        assert _escape_key("row/5") == "row%2F5"
        assert _escape_key("path/to/item") == "path%2Fto%2Fitem"

    def test_escape_percent(self) -> None:
        """Percent must be escaped first to avoid double-encoding."""
        assert _escape_key("100%") == "100%25"
        assert _escape_key("%done") == "%25done"

    def test_multiple_special_chars(self) -> None:
        """All special characters are escaped in a single key."""
        assert _escape_key("a:b@c/d%e") == "a%3Ab%40c%2Fd%25e"
        # Percent first, then others
        assert _escape_key("%:@/") == "%25%3A%40%2F"


class TestIsRenderActiveSemantics:
    """Tests for is_render_active() semantics.

    is_render_active() returns True when session.active is not None,
    i.e., when we're inside a render pass.

    - True during component execution
    - False during hooks (hooks run after session.active is cleared)
    - False outside render
    """

    def test_is_render_active_true_during_component_execution(self) -> None:
        """is_render_active() returns True during component execution."""
        values_during_execution: list[bool] = []

        @component
        def App() -> None:
            values_during_execution.append(is_render_active())

        ctx = RenderSession(App)
        render(ctx)

        assert len(values_during_execution) == 1
        assert values_during_execution[0] is True

    def test_is_render_active_false_during_hooks(self) -> None:
        """is_render_active() returns False during lifecycle hooks."""
        values_during_mount: list[bool] = []

        @dataclass
        class CheckDuringMount(Stateful):
            def on_mount(self) -> None:
                values_during_mount.append(is_render_active())

        @component
        def App() -> None:
            CheckDuringMount()

        ctx = RenderSession(App)
        render(ctx)

        assert len(values_during_mount) == 1
        assert values_during_mount[0] is False

    def test_session_active_none_during_hooks(self) -> None:
        """session.active should be None during lifecycle hooks.

        This is the implementation requirement: hooks must run after
        session.active is cleared, not just after current_element_id is None.
        """
        active_values: list[bool] = []

        @dataclass
        class CheckSessionActive(Stateful):
            def on_mount(self) -> None:
                session = get_active_session()
                # session.active should be None during hooks
                active_values.append(session.active is None if session else True)

        @component
        def App() -> None:
            CheckSessionActive()

        ctx = RenderSession(App)
        render(ctx)

        assert len(active_values) == 1
        assert active_values[0] is True, "session.active should be None during hooks"


class TestLifecycleHooksCanModifyState:
    """Tests that lifecycle hooks can safely modify state.

    Hooks run AFTER session.active is cleared, so is_render_active()=False.
    This allows state modification during hooks.
    """

    def test_on_mount_can_modify_shared_state(self) -> None:
        """on_mount hook should be able to modify shared state without error.

        This tests the case where an on_mount hook modifies a Stateful instance
        that other components depend on - the real scenario that could deadlock
        or raise RuntimeError if hooks run during render.
        """

        # Shared state that will be modified by on_mount
        @dataclass
        class SharedState(Stateful):
            value: int = 0

        shared: SharedState | None = None

        @dataclass
        class StateWithMount(Stateful):
            def on_mount(self) -> None:
                # Modify shared state - this triggers dirty marking
                if shared is not None:
                    shared.value = 42

        @component
        def Consumer() -> None:
            # Read shared state to register dependency
            if shared is not None:
                _ = shared.value

        @component
        def Producer() -> None:
            StateWithMount()

        @component
        def App() -> None:
            Consumer()
            Producer()

        # Create shared state outside render
        shared = SharedState()

        ctx = RenderSession(App)
        render(ctx)

        # Hook should have modified shared state
        assert shared.value == 42

    def test_on_unmount_can_modify_shared_state(self) -> None:
        """on_unmount hook should be able to modify shared state without error."""

        @dataclass
        class SharedState(Stateful):
            value: int = 0

        shared: SharedState | None = None

        @dataclass
        class StateWithUnmount(Stateful):
            def on_unmount(self) -> None:
                if shared is not None:
                    shared.value = 99

        show_child = [True]

        @component
        def Child() -> None:
            StateWithUnmount()

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        shared = SharedState()
        ctx = RenderSession(App)
        render(ctx)

        # Remove child to trigger unmount
        show_child[0] = False
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        assert shared.value == 99


class TestHookErrorHandling:
    """Tests for error handling in lifecycle hooks.

    Ensures that exceptions in hooks don't prevent state cleanup.
    """

    def test_unmount_hook_exception_logs_and_removes_state(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When on_unmount raises, the exception is logged and state is still removed."""

        @dataclass
        class ThrowingStateful(Stateful):
            def on_unmount(self) -> None:
                raise ValueError("unmount hook error")

        show_child = [True]

        @component
        def Child() -> None:
            ThrowingStateful()

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        ctx = RenderSession(App)
        render(ctx)

        child_id = ctx.root_element.child_ids[0]
        assert ctx.states.get(child_id) is not None

        show_child[0] = False
        ctx.dirty.mark(ctx.root_element.id)

        with caplog.at_level(logging.ERROR):
            render(ctx)  # Should not raise

        # State should still be removed
        assert ctx.states.get(child_id) is None
        # Exception should be logged
        assert "unmount hook error" in caplog.text

    def test_mount_hook_exception_logs_and_continues(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When on_mount raises, the exception is logged and render continues."""
        mount_order: list[str] = []

        @dataclass
        class ThrowingMountStateful(Stateful):
            name: str = ""

            def on_mount(self) -> None:
                mount_order.append(f"before_{self.name}")
                if self.name == "child1":
                    raise ValueError("mount hook error")
                mount_order.append(f"after_{self.name}")

        @component
        def Child(name: str = "") -> None:
            ThrowingMountStateful(name=name)

        @component
        def App() -> None:
            Child(name="child1")
            Child(name="child2")

        ctx = RenderSession(App)

        with caplog.at_level(logging.ERROR):
            render(ctx)  # Should not raise

        # Exception should be logged
        assert "mount hook error" in caplog.text
        # child2's mount should still have been called
        assert "before_child2" in mount_order
        assert "after_child2" in mount_order


class TestPositionIdGeneration:
    """Tests for position-based ID generation."""

    def test_root_id_format(self) -> None:
        """Root node ID includes component identity."""

        @component
        def App() -> None:
            pass

        ctx = RenderSession(App)
        render(ctx)

        # Format: /@{id(component)}
        assert ctx.root_element.id.startswith("/@")
        assert str(id(App)) in ctx.root_element.id

    def test_child_id_includes_position(self) -> None:
        """Child IDs include position index."""

        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            Child()
            Child()
            Child()

        ctx = RenderSession(Parent)
        render(ctx)

        # Children should have /0@, /1@, /2@ in their IDs
        child_ids = ctx.root_element.child_ids
        assert len(child_ids) == 3
        assert "/0@" in child_ids[0]
        assert "/1@" in child_ids[1]
        assert "/2@" in child_ids[2]

    def test_keyed_child_id_format(self) -> None:
        """Keyed children use :key@ format."""

        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            Child(key="submit")

        ctx = RenderSession(Parent)
        render(ctx)

        child_id = ctx.root_element.child_ids[0]
        assert ":submit@" in child_id

    def test_different_component_types_different_ids(self) -> None:
        """Same position, different component = different ID."""

        @component
        def TypeA() -> None:
            pass

        @component
        def TypeB() -> None:
            pass

        show_a = [True]

        @component
        def Parent() -> None:
            if show_a[0]:
                TypeA()
            else:
                TypeB()

        ctx = RenderSession(Parent)
        render(ctx)
        id_a = ctx.root_element.child_ids[0]

        show_a[0] = False
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)
        id_b = ctx.root_element.child_ids[0]

        # Different components at same position get different IDs
        # (because the component identity is part of the ID)
        assert id_a != id_b
        assert str(id(TypeA)) in id_a
        assert str(id(TypeB)) in id_b


class TestConditionalRendering:
    """Tests for conditional container children rendering.

    With ChildRef:
    - `child_ids` reflects RENDERED children (what's shown to frontend)
    - `props["children"]` contains ChildRefs (stable references to collected children)

    When a container hides children:
    - child_ids becomes empty (nothing rendered)
    - props["children"] still has ChildRefs (can render them later)
    - Unmount hooks are called, ElementState is removed
    - Element stays in session.elements (so ChildRef.element works)

    When a container shows children again:
    - Container calls ChildRef() to render them
    - child_ids reflects rendered children again
    - Mount hooks are called, new ElementState is created
    """

    def test_conditional_container_preserves_children_when_only_container_rerenders(
        self,
    ) -> None:
        """Children are preserved when container re-renders without parent re-rendering."""
        render_counts: dict[str, int] = {}

        @dataclass
        class VisibilityState(Stateful):
            visible: bool = True

        container_state: list[VisibilityState] = []

        @component
        def Child() -> None:
            render_counts["child"] = render_counts.get("child", 0) + 1

        @component
        def ConditionalContainer(*, children: list[ChildRef] | None = None) -> None:
            state = VisibilityState()
            container_state.append(state)
            if state.visible and children:
                for child in children:
                    child()

        @component
        def App() -> None:
            render_counts["app"] = render_counts.get("app", 0) + 1
            with ConditionalContainer():
                Child()

        ctx = RenderSession(App)
        render(ctx)

        assert render_counts.get("child", 0) == 1
        assert render_counts.get("app", 0) == 1

        container_id = ctx.root_element.child_ids[0]
        container = ctx.elements.get(container_id)
        assert container is not None
        assert len(container.child_ids) == 1

        # Hide children (only container re-renders)
        container_state[-1].visible = False
        render(ctx)

        assert render_counts.get("app", 0) == 1  # App should not re-render
        container = ctx.elements.get(container_id)
        assert len(container.child_ids) == 0  # No children rendered when hidden

        # Show again
        container_state[-1].visible = True
        render(ctx)

        assert render_counts.get("app", 0) == 1  # App still should not re-render
        container = ctx.elements.get(container_id)
        assert len(container.child_ids) == 1  # Children rendered again
        assert render_counts.get("child", 0) == 2  # Child re-renders when shown

    def test_tab_container_preserves_unrendered_children(self) -> None:
        """Tab container preserves all children even when only rendering one."""
        render_counts: dict[str, int] = {}

        @dataclass
        class SelectionState(Stateful):
            selected: int = 0

        container_state: list[SelectionState] = []

        @component
        def ChildA() -> None:
            render_counts["a"] = render_counts.get("a", 0) + 1

        @component
        def ChildB() -> None:
            render_counts["b"] = render_counts.get("b", 0) + 1

        @component
        def ChildC() -> None:
            render_counts["c"] = render_counts.get("c", 0) + 1

        @component
        def TabContainer(*, children: list[ChildRef] | None = None) -> None:
            state = SelectionState()
            container_state.append(state)
            if children and 0 <= state.selected < len(children):
                children[state.selected]()

        @component
        def App() -> None:
            render_counts["app"] = render_counts.get("app", 0) + 1
            with TabContainer():
                ChildA()
                ChildB()
                ChildC()

        ctx = RenderSession(App)
        render(ctx)

        assert render_counts == {"app": 1, "a": 1}

        container_id = ctx.root_element.child_ids[0]
        container = ctx.elements.get(container_id)
        assert len(container.child_ids) == 1  # Only selected child rendered
        assert len(container.props.get("children", [])) == 3  # All children collected

        # Switch to ChildB
        container_state[-1].selected = 1
        render(ctx)

        assert render_counts.get("app", 0) == 1  # App should not re-render
        container = ctx.elements.get(container_id)
        assert render_counts.get("b", 0) == 1  # ChildB renders when selected
        assert len(container.child_ids) == 1

    def test_nested_conditional_containers_with_internal_state(self) -> None:
        """Nested conditional containers with internal state work correctly."""
        render_counts: dict[str, int] = {}

        @dataclass
        class VisibilityState(Stateful):
            visible: bool = True

        outer_state: list[VisibilityState] = []

        @component
        def DeepChild() -> None:
            render_counts["deep"] = render_counts.get("deep", 0) + 1

        @component
        def InnerContainer(*, children: list[ChildRef] | None = None) -> None:
            render_counts["inner"] = render_counts.get("inner", 0) + 1
            if children:
                for child in children:
                    child()

        @component
        def OuterContainer(*, children: list[ChildRef] | None = None) -> None:
            state = VisibilityState()
            outer_state.append(state)
            render_counts["outer"] = render_counts.get("outer", 0) + 1
            if state.visible and children:
                for child in children:
                    child()

        @component
        def App() -> None:
            render_counts["app"] = render_counts.get("app", 0) + 1
            with OuterContainer():
                with InnerContainer():
                    DeepChild()

        ctx = RenderSession(App)
        render(ctx)

        assert render_counts == {"app": 1, "outer": 1, "inner": 1, "deep": 1}

        # Hide outer
        outer_state[-1].visible = False
        render(ctx)

        assert render_counts.get("app", 0) == 1
        assert render_counts.get("outer", 0) == 2

        # Show outer again
        outer_state[-1].visible = True
        render(ctx)

        assert render_counts.get("app", 0) == 1
        assert render_counts.get("inner", 0) == 2
        assert render_counts.get("deep", 0) == 2


class TestElementRemovalStorage:
    """Tests for Element and ElementState storage during unmount/removal.

    Soft unmount (child hidden but still collected):
    - Element stays in session.elements
    - ElementState removed from session.states

    Full removal (child no longer collected):
    - Element removed from session.elements
    - ElementState removed from session.states
    """

    def test_soft_unmount_preserves_element_removes_state(self) -> None:
        """Hidden child: Element stays in storage, ElementState is removed."""

        @dataclass
        class VisibilityState(Stateful):
            visible: bool = True

        container_state: list[VisibilityState] = []

        @component
        def Child() -> None:
            pass

        @component
        def Container(*, children: list[ChildRef] | None = None) -> None:
            state = VisibilityState()
            container_state.append(state)
            if state.visible and children:
                for child in children:
                    child()

        @component
        def App() -> None:
            with Container():
                Child()

        ctx = RenderSession(App)
        render(ctx)

        container_id = ctx.root_element.child_ids[0]
        child_id = ctx.elements.get(container_id).child_ids[0]

        # Verify child exists in both stores
        assert ctx.elements.get(child_id) is not None
        assert ctx.states.get(child_id) is not None

        # Hide child (soft unmount)
        container_state[-1].visible = False
        render(ctx)

        # Element stays (for ChildRef), ElementState removed
        assert ctx.elements.get(child_id) is not None
        assert ctx.states.get(child_id) is None

    def test_full_removal_removes_element_and_state(self) -> None:
        """Child no longer collected: both Element and ElementState removed."""
        show_child = [True]

        @component
        def Child() -> None:
            pass

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        ctx = RenderSession(App)
        render(ctx)

        child_id = ctx.root_element.child_ids[0]

        # Verify child exists
        assert ctx.elements.get(child_id) is not None
        assert ctx.states.get(child_id) is not None

        # Remove child completely (full removal)
        show_child[0] = False
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        # Both Element and ElementState removed
        assert ctx.elements.get(child_id) is None
        assert ctx.states.get(child_id) is None

    def test_soft_unmount_then_rerender_creates_new_state(self) -> None:
        """Re-rendering a soft-unmounted child creates fresh ElementState."""

        @dataclass
        class VisibilityState(Stateful):
            visible: bool = True

        @dataclass
        class ChildState(Stateful):
            value: int = 0

        container_state: list[VisibilityState] = []
        child_state_instances: list[ChildState] = []

        @component
        def Child() -> None:
            state = ChildState()
            child_state_instances.append(state)

        @component
        def Container(*, children: list[ChildRef] | None = None) -> None:
            state = VisibilityState()
            container_state.append(state)
            if state.visible and children:
                for child in children:
                    child()

        @component
        def App() -> None:
            with Container():
                Child()

        ctx = RenderSession(App)
        render(ctx)

        container_id = ctx.root_element.child_ids[0]
        child_id = ctx.elements.get(container_id).child_ids[0]

        # Modify child state
        child_state_instances[-1].value = 42
        assert len(child_state_instances) == 1

        # Hide child
        container_state[-1].visible = False
        render(ctx)

        assert ctx.states.get(child_id) is None

        # Show child again
        container_state[-1].visible = True
        render(ctx)

        # New ElementState created (new ChildState instance)
        assert ctx.states.get(child_id) is not None
        assert len(child_state_instances) == 2
        # New state starts fresh (value=0), not preserved from before
        assert child_state_instances[-1].value == 0
