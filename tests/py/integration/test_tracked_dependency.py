"""Integration tests for tracked collection dependency tracking and fine-grained reactivity."""

import gc
from dataclasses import dataclass, field

from tests.conftest import PatchCapture
from trellis.core.components.composition import component
from trellis.core.state.stateful import Stateful
from trellis.core.state.tracked import ITER_KEY, TrackedDict, TrackedList


class TestDependencyTracking:
    """Tests for dependency tracking during render.

    INTERNAL TEST: These tests verify the internal dependency graph (_deps)
    which has no public API for inspection.
    """

    def test_list_getitem_tracks_by_item_identity(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Accessing list[i] registers dependency on id(item)."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        @component
        def ItemViewer() -> None:
            _ = state.items[1]  # Access item at index 1

        capture = capture_patches(ItemViewer)
        capture.render()

        # Check that dependency was registered for id("b")
        tracked_list = state.items
        item_b = list.__getitem__(tracked_list, 1)
        assert id(item_b) in tracked_list._deps
        assert capture.session.root_element in tracked_list._deps[id(item_b)]

    def test_list_iteration_tracks_iter_key(self, capture_patches: "type[PatchCapture]") -> None:
        """Iterating over list registers dependency on ITER_KEY."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        @component
        def ListViewer() -> None:
            for item in state.items:
                _ = item

        capture = capture_patches(ListViewer)
        capture.render()

        # Check ITER_KEY dependency
        tracked_list = state.items
        assert ITER_KEY in tracked_list._deps
        assert capture.session.root_element in tracked_list._deps[ITER_KEY]

    def test_dict_getitem_tracks_by_key(self, capture_patches: "type[PatchCapture]") -> None:
        """Accessing dict[key] registers dependency on that key."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"x": 1, "y": 2}

        @component
        def DataViewer() -> None:
            _ = state.data["x"]

        capture = capture_patches(DataViewer)
        capture.render()

        # Check dependency on key "x"
        tracked_dict = state.data
        assert "x" in tracked_dict._deps
        assert capture.session.root_element in tracked_dict._deps["x"]

    def test_set_contains_tracks_by_value(self, capture_patches: "type[PatchCapture]") -> None:
        """item in set registers dependency on the value itself."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"python", "rust"}

        @component
        def TagChecker() -> None:
            _ = "python" in state.tags

        capture = capture_patches(TagChecker)
        capture.render()

        # Check dependency on the value "python" (not id)
        tracked_set = state.tags
        assert "python" in tracked_set._deps
        assert capture.session.root_element in tracked_set._deps["python"]

    def test_list_sort_marks_iter_dirty(self, capture_patches: "type[PatchCapture]") -> None:
        """Sorting a list marks ITER_KEY dirty."""

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [3, 1, 2]

        iter_renders = [0]

        @component
        def ListViewer() -> None:
            iter_renders[0] += 1
            for _ in state.items:
                pass

        capture = capture_patches(ListViewer)
        capture.render()
        assert iter_renders[0] == 1

        # Sort - should mark ITER_KEY dirty
        state.items.sort()
        capture.render()
        assert iter_renders[0] == 2

    def test_dict_new_key_marks_iter_dirty(self, capture_patches: "type[PatchCapture]") -> None:
        """Adding a new key marks ITER_KEY dirty for iterators."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1}

        iter_renders = [0]
        a_renders = [0]

        @component
        def Iterator() -> None:
            iter_renders[0] += 1
            for _ in state.data:
                pass

        @component
        def AViewer() -> None:
            a_renders[0] += 1
            _ = state.data["a"]

        @component
        def App() -> None:
            Iterator()
            AViewer()

        capture = capture_patches(App)
        capture.render()

        assert iter_renders[0] == 1
        assert a_renders[0] == 1

        # Add new key - Iterator should re-render
        state.data["b"] = 2
        capture.render()

        assert iter_renders[0] == 2  # Iteration affected by new key
        assert a_renders[0] == 1  # AViewer not affected


class TestFineGrainedReactivity:
    """Tests for fine-grained re-rendering based on tracked collections."""

    def test_list_item_change_only_rerenders_affected(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Modifying one list item only re-renders components that read it."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        item0_renders = [0]
        item1_renders = [0]

        @component
        def Item0() -> None:
            item0_renders[0] += 1
            _ = state.items[0]

        @component
        def Item1() -> None:
            item1_renders[0] += 1
            _ = state.items[1]

        @component
        def App() -> None:
            Item0()
            Item1()

        capture = capture_patches(App)
        capture.render()

        assert item0_renders[0] == 1
        assert item1_renders[0] == 1

        # Modify item at index 0 - only Item0 should re-render
        state.items[0] = "updated"
        capture.render()

        assert item0_renders[0] == 2
        assert item1_renders[0] == 1  # Should NOT have re-rendered

    def test_dict_key_change_only_rerenders_affected(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Modifying one dict key only re-renders components that read it."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"x": 1, "y": 2}

        x_renders = [0]
        y_renders = [0]

        @component
        def XViewer() -> None:
            x_renders[0] += 1
            _ = state.data["x"]

        @component
        def YViewer() -> None:
            y_renders[0] += 1
            _ = state.data["y"]

        @component
        def App() -> None:
            XViewer()
            YViewer()

        capture = capture_patches(App)
        capture.render()

        assert x_renders[0] == 1
        assert y_renders[0] == 1

        # Modify key "x" - only XViewer should re-render
        state.data["x"] = 100
        capture.render()

        assert x_renders[0] == 2
        assert y_renders[0] == 1  # Should NOT have re-rendered

    def test_list_append_rerenders_iterators(self, capture_patches: "type[PatchCapture]") -> None:
        """Appending to list re-renders components that iterate."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b"]

        list_renders = [0]
        item0_renders = [0]

        @component
        def ListViewer() -> None:
            list_renders[0] += 1
            for _ in state.items:
                pass

        @component
        def Item0Viewer() -> None:
            item0_renders[0] += 1
            _ = state.items[0]

        @component
        def App() -> None:
            ListViewer()
            Item0Viewer()

        capture = capture_patches(App)
        capture.render()

        assert list_renders[0] == 1
        assert item0_renders[0] == 1

        # Append - ListViewer should re-render (iterates), Item0Viewer should not
        state.items.append("c")
        capture.render()

        assert list_renders[0] == 2  # Iterating = ITER_KEY dependency
        assert item0_renders[0] == 1  # Should NOT re-render


class TestDependencyCleanup:
    """Tests for dependency cleanup on unmount and re-render.

    INTERNAL TEST: These tests verify the internal dependency graph (_deps)
    cleanup behavior which has no public API for inspection.
    """

    def test_list_dependency_cleaned_on_unmount(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """List dependencies are cleaned up when component unmounts."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b"]

        show_consumer = [True]

        @component
        def Consumer() -> None:
            _ = state.items[0]

        @component
        def App() -> None:
            if show_consumer[0]:
                Consumer()

        capture = capture_patches(App)
        capture.render()

        # Get consumer ID without keeping strong reference to node
        ctx = capture.session
        consumer_id = ctx.elements.get(ctx.root_element.child_ids[0]).id
        tracked_list = state.items
        item_a = list.__getitem__(tracked_list, 0)

        # Verify consumer is tracking (check by node ID since object identity may differ)
        dep_node_ids = {n.id for n in tracked_list._deps[id(item_a)]}
        assert consumer_id in dep_node_ids

        # Unmount Consumer
        show_consumer[0] = False
        ctx.dirty.mark(ctx.root_element.id)
        capture.render()

        # Force GC so WeakSet can remove dead references
        gc.collect()

        # Dependency should be cleaned up (WeakSet auto-removes dead refs after GC)
        if id(item_a) in tracked_list._deps:
            dep_node_ids = {n.id for n in tracked_list._deps[id(item_a)]}
            assert consumer_id not in dep_node_ids

    def test_dict_dependency_cleaned_on_rerender_without_read(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Dict dependencies are cleaned when component stops reading."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"x": 1}

        read_data = [True]

        @component
        def Consumer() -> None:
            if read_data[0]:
                _ = state.data["x"]

        capture = capture_patches(Consumer)
        capture.render()

        # Get root ID without keeping strong reference to old node
        ctx = capture.session
        root_id = ctx.root_element.id
        tracked_dict = state.data

        # Initially tracking (check by node ID since object identity may differ)
        dep_node_ids = {n.id for n in tracked_dict._deps["x"]}
        assert root_id in dep_node_ids

        # Stop reading and re-render
        read_data[0] = False
        ctx.dirty.mark(root_id)
        capture.render()

        # Force GC so WeakSet can remove dead references (old node from previous render)
        gc.collect()

        # No longer tracking (WeakSet auto-removes dead refs after GC)
        if "x" in tracked_dict._deps:
            dep_node_ids = {n.id for n in tracked_dict._deps["x"]}
            assert root_id not in dep_node_ids


class TestTrackedWithStatefulItems:
    """Tests for tracked collections containing Stateful items."""

    def test_stateful_item_tracks_own_properties(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Stateful items in a list track their own properties."""

        @dataclass
        class Todo(Stateful):
            text: str = ""
            completed: bool = False

        @dataclass
        class TodosState(Stateful):
            todos: list[Todo] = field(default_factory=list)

        state = TodosState()
        todo1 = Todo(text="First")
        todo2 = Todo(text="Second")
        state.todos = [todo1, todo2]

        todo1_renders = [0]
        todo2_renders = [0]

        @component
        def Todo1Viewer() -> None:
            todo1_renders[0] += 1
            _ = state.todos[0].completed  # Read todo1.completed

        @component
        def Todo2Viewer() -> None:
            todo2_renders[0] += 1
            _ = state.todos[1].completed  # Read todo2.completed

        @component
        def App() -> None:
            Todo1Viewer()
            Todo2Viewer()

        capture = capture_patches(App)
        capture.render()

        assert todo1_renders[0] == 1
        assert todo2_renders[0] == 1

        # Modify todo1.completed - only Todo1Viewer should re-render
        todo1.completed = True
        capture.render()

        assert todo1_renders[0] == 2
        assert todo2_renders[0] == 1  # Should NOT have re-rendered

    def test_replacing_stateful_item_in_list(self, capture_patches: "type[PatchCapture]") -> None:
        """Replacing a Stateful item in list marks the slot dirty."""

        @dataclass
        class Todo(Stateful):
            text: str = ""

        @dataclass
        class TodosState(Stateful):
            todos: list[Todo] = field(default_factory=list)

        state = TodosState()
        todo1 = Todo(text="First")
        state.todos = [todo1]

        item_renders = [0]

        @component
        def ItemViewer() -> None:
            item_renders[0] += 1
            _ = state.todos[0]  # Just read the item

        capture = capture_patches(ItemViewer)
        capture.render()
        assert item_renders[0] == 1

        # Replace the item - should trigger re-render
        new_todo = Todo(text="New")
        state.todos[0] = new_todo
        capture.render()

        assert item_renders[0] == 2


class TestMultiComponentScenarios:
    """Tests for multiple components reading same data."""

    def test_two_components_read_same_item(self, capture_patches: "type[PatchCapture]") -> None:
        """Two components reading same item both re-render on change."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["shared"]

        comp1_renders = [0]
        comp2_renders = [0]

        @component
        def Component1() -> None:
            comp1_renders[0] += 1
            _ = state.items[0]

        @component
        def Component2() -> None:
            comp2_renders[0] += 1
            _ = state.items[0]

        @component
        def App() -> None:
            Component1()
            Component2()

        capture = capture_patches(App)
        capture.render()
        assert comp1_renders[0] == 1
        assert comp2_renders[0] == 1

        # Both should re-render when the shared item changes
        state.items[0] = "updated"
        capture.render()
        assert comp1_renders[0] == 2
        assert comp2_renders[0] == 2


class TestDeeplyNested:
    """Tests for deeply nested access."""

    def test_deeply_nested_list_dict_list(self, capture_patches: "type[PatchCapture]") -> None:
        """Deeply nested state.a[0]["x"][1] works correctly."""

        @dataclass
        class MyState(Stateful):
            data: list[dict[str, list[int]]] = field(default_factory=list)

        state = MyState()
        state.data = [{"x": [10, 20, 30]}]

        renders = [0]

        @component
        def DeepViewer() -> None:
            renders[0] += 1
            _ = state.data[0]["x"][1]  # Access 20

        capture = capture_patches(DeepViewer)
        capture.render()
        assert renders[0] == 1

        # All levels should be tracked
        assert isinstance(state.data, TrackedList)
        assert isinstance(state.data[0], TrackedDict)
        assert isinstance(state.data[0]["x"], TrackedList)

        # Modify the deeply nested value
        state.data[0]["x"][1] = 999
        capture.render()
        assert renders[0] == 2


class TestSetValueTracking:
    """Tests for set value-based tracking (vs id-based)."""

    def test_set_contains_with_different_string_objects(
        self, capture_patches: "type[PatchCapture]"
    ) -> None:
        """Set tracking works with different string objects of same value."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = set()  # Start empty

        renders = [0]
        check_value = "python"  # This string object

        @component
        def TagChecker() -> None:
            renders[0] += 1
            _ = check_value in state.tags

        capture = capture_patches(TagChecker)
        capture.render()
        assert renders[0] == 1

        # Add a different string object with same value
        # (In practice, Python often interns strings, but the point is
        # we track by value, not id)
        state.tags.add("python")
        capture.render()
        assert renders[0] == 2  # Should re-render!
