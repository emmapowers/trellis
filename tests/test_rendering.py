"""Tests for trellis.core.rendering module."""

import concurrent.futures
import threading
import weakref

import pytest

from trellis.core.components.composition import CompositionComponent, component
from trellis.core.rendering.element import ElementNode
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession, get_active_session, set_active_session
from trellis.core.state.stateful import Stateful
from dataclasses import dataclass


def make_component(name: str) -> CompositionComponent:
    """Helper to create a simple test component."""
    return CompositionComponent(name=name, render_func=lambda: None)


# Dummy session for testing ElementNode creation
_dummy_session: RenderSession | None = None


def _get_dummy_session_ref() -> weakref.ref[RenderSession]:
    """Get a weakref to a dummy session for testing."""
    global _dummy_session
    if _dummy_session is None:
        _dummy_session = RenderSession(make_component("DummyRoot"))
    return weakref.ref(_dummy_session)


def make_descriptor(
    comp: CompositionComponent,
    key: str | None = None,
    props: dict | None = None,
) -> ElementNode:
    """Helper to create an ElementNode."""
    return ElementNode(
        component=comp,
        _session_ref=_get_dummy_session_ref(),
        key=key,
        props=props or {},
    )


class TestElementNode:
    def test_element_node_creation(self) -> None:
        comp = make_component("Test")
        node = make_descriptor(comp)

        assert node.component == comp
        assert node.key is None
        assert node.props == {}
        assert node.child_ids == ()
        assert node.id == ""

    def test_element_node_with_key(self) -> None:
        comp = make_component("Test")
        node = make_descriptor(comp, key="my-key")

        assert node.key == "my-key"

    def test_element_node_with_properties(self) -> None:
        comp = make_component("Test")
        node = make_descriptor(comp, props={"foo": "bar", "count": 42})

        assert node.properties == {"foo": "bar", "count": 42}

    def test_element_node_is_mutable(self) -> None:
        comp = make_component("Test")
        node = make_descriptor(comp, props={"a": 1})

        # ElementNode is mutable and uses render_count-based hashing
        hash(node)  # Should not raise

        # Can modify attributes
        node.id = "new-id"
        assert node.id == "new-id"


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

        assert ctx._root_component == comp
        assert ctx.root_node is None
        assert not ctx._dirty.has_dirty()

    def test_mark_dirty_id(self) -> None:
        @component
        def Root() -> None:
            pass

        ctx = RenderSession(Root)
        render(ctx)

        # The root node should have an ID now
        assert ctx.root_node is not None
        node_id = ctx.root_node.id

        # Clear dirty state
        ctx._dirty.pop_all()
        ctx._element_state.get(node_id).dirty = False

        # Mark dirty by ID
        ctx.mark_dirty_id(node_id)

        assert node_id in ctx._dirty
        assert ctx._element_state.get(node_id).dirty is True


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
        assert results["a"]._root_component.name == "AppA"
        assert results["b"]._root_component.name == "AppB"

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

        # Stack should be clean after exception
        assert not ctx._frames.has_active()

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

        assert not ctx._frames.has_active()


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

    def test_callback_registry_isolated_per_session(self) -> None:
        """Callback registries are isolated per RenderSession."""

        @component
        def App() -> None:
            pass

        ctx1 = RenderSession(App)
        ctx2 = RenderSession(App)

        cb1 = lambda: "callback1"
        cb2 = lambda: "callback2"

        # Register with deterministic IDs (node_id:prop_name)
        id1 = ctx1.register_callback(cb1, "e1", "on_click")
        id2 = ctx2.register_callback(cb2, "e1", "on_click")

        # Same ID format (deterministic) but different registries
        assert id1 == id2 == "e1:on_click"

        # But they resolve to different callbacks
        assert ctx1.get_callback(id1)() == "callback1"
        assert ctx2.get_callback(id2)() == "callback2"

        # Cross-lookup returns None
        assert ctx1.get_callback("e999:on_click") is None

    def test_state_update_blocks_during_render(self) -> None:
        """State updates on another thread block while render holds the lock.

        This tests that mark_dirty_id() blocks when called from another thread
        while a render is in progress on the same RenderSession.
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

        ctx = RenderSession(SlowApp)

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
        render(ctx)

        updater.join()

        # Verify ordering: update_start happens during render (before first_render_done)
        # but update_done happens after first_render_done because mark_dirty_id blocks
        assert "update_start" in events
        assert "first_render_done" in events
        assert "update_done" in events
        # The key assertion: mark_dirty_id blocks, so update_done must come after render releases lock
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
        root_state = ctx._element_state.get(ctx.root_node.id)
        assert root_state.parent_id is None

        # Child's parent should be root
        child_id = ctx.get_node(ctx.root_node.child_ids[0]).id
        child_state = ctx._element_state.get(child_id)
        assert child_state.parent_id == ctx.root_node.id

    def test_parent_id_preserved_on_rerender(self) -> None:
        """parent_id is preserved when component re-renders."""
        from dataclasses import dataclass
        from trellis.core.state.stateful import Stateful

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

        child_id = ctx.get_node(ctx.root_node.child_ids[0]).id
        original_parent_id = ctx._element_state.get(child_id).parent_id

        # Trigger re-render
        state_holder[0].value += 1
        render(ctx)

        # parent_id should be preserved
        assert ctx._element_state.get(child_id).parent_id == original_parent_id


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
        ctx.mark_dirty_id(ctx.root_node.id)
        render(ctx)

        assert render_counts["child"] == 1

        # Change to non-None
        value_ref[0] = "hello"
        ctx.mark_dirty_id(ctx.root_node.id)
        render(ctx)

        assert render_counts["child"] == 2

        # Change back to None
        value_ref[0] = None
        ctx.mark_dirty_id(ctx.root_node.id)
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
        ctx.mark_dirty_id(ctx.root_node.id)
        render(ctx)

        assert render_counts["child"] == 1

        # Different function - should re-render
        handler_ref[0] = handler2
        ctx.mark_dirty_id(ctx.root_node.id)
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

        ctx.mark_dirty_id(ctx.root_node.id)
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
        ctx.mark_dirty_id(ctx.root_node.id)
        render(ctx)

        assert render_counts["child"] == 1

        # Different tuple - should re-render
        tuple_ref[0] = (1, 2, 4)
        ctx.mark_dirty_id(ctx.root_node.id)
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
        from trellis.widgets import Row, Button
        from trellis import html as h

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
        assert len(ctx.root_node.child_ids) == 6

        # Remove "b" from the middle - this triggers type-based matching
        items_ref[0] = ["a", "c", "d"]
        ctx.mark_dirty_id(ctx.root_node.id)
        render(ctx)

        # Should have: H1, Row, Row, Row, Button = 5 children
        assert len(ctx.root_node.child_ids) == 5

    def test_html_elements_in_dynamic_list(self) -> None:
        """HTML elements (via @html_element) should be hashable for reconciliation."""
        from trellis import html as h

        items_ref = [["item1", "item2", "item3"]]

        @component
        def List() -> None:
            for item in items_ref[0]:
                with h.Div():
                    h.Span(item)

        ctx = RenderSession(List)
        render(ctx)

        assert len(ctx.root_node.child_ids) == 3

        # Remove from middle
        items_ref[0] = ["item1", "item3"]
        ctx.mark_dirty_id(ctx.root_node.id)
        render(ctx)

        assert len(ctx.root_node.child_ids) == 2

    def test_widgets_in_dynamic_list(self) -> None:
        """Widgets (via @react_component_base) should be hashable for reconciliation."""
        from trellis.widgets import Column, Row, Label, Button

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

        column = ctx.get_node(ctx.root_node.child_ids[0])
        assert len(column.child_ids) == 5

        # Remove items 2 and 4 (from middle)
        items_ref[0] = [1, 3, 5]
        ctx.mark_dirty_id(ctx.root_node.id)
        render(ctx)

        column = ctx.get_node(ctx.root_node.child_ids[0])
        assert len(column.child_ids) == 3

    def test_mixed_widgets_and_components_in_list(self) -> None:
        """Mix of @component and @react_component_base in dynamic list."""
        from trellis.widgets import Button

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

        assert len(ctx.root_node.child_ids) == 3

        # Reorder and remove
        items_ref[0] = ["c", "a"]
        ctx.mark_dirty_id(ctx.root_node.id)
        render(ctx)

        assert len(ctx.root_node.child_ids) == 2


class TestEscapeKey:
    """Tests for URL-encoding special characters in keys."""

    def test_no_special_chars(self) -> None:
        """Keys without special chars pass through unchanged."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("simple") == "simple"
        assert _escape_key("with-dash") == "with-dash"
        assert _escape_key("with_underscore") == "with_underscore"
        assert _escape_key("CamelCase") == "CamelCase"
        assert _escape_key("123") == "123"

    def test_escape_colon(self) -> None:
        """Colon is escaped."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("my:key") == "my%3Akey"
        assert _escape_key("a:b:c") == "a%3Ab%3Ac"

    def test_escape_at(self) -> None:
        """At sign is escaped."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("item@home") == "item%40home"
        assert _escape_key("user@domain") == "user%40domain"

    def test_escape_slash(self) -> None:
        """Slash is escaped."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("row/5") == "row%2F5"
        assert _escape_key("path/to/item") == "path%2Fto%2Fitem"

    def test_escape_percent(self) -> None:
        """Percent must be escaped first to avoid double-encoding."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("100%") == "100%25"
        assert _escape_key("%done") == "%25done"

    def test_multiple_special_chars(self) -> None:
        """All special characters are escaped in a single key."""
        from trellis.core.rendering.frames import _escape_key

        assert _escape_key("a:b@c/d%e") == "a%3Ab%40c%2Fd%25e"
        # Percent first, then others
        assert _escape_key("%:@/") == "%25%3A%40%2F"


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
        assert ctx.root_node.id.startswith("/@")
        assert str(id(App)) in ctx.root_node.id

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
        child_ids = ctx.root_node.child_ids
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

        child_id = ctx.root_node.child_ids[0]
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
        id_a = ctx.root_node.child_ids[0]

        show_a[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        render(ctx)
        id_b = ctx.root_node.child_ids[0]

        # Different components at same position get different IDs
        # (because the component identity is part of the ID)
        assert id_a != id_b
        assert str(id(TypeA)) in id_a
        assert str(id(TypeB)) in id_b
