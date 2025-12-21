"""Tests for trellis.core.tracked module - reactive tracked collections."""

from dataclasses import dataclass, field

import pytest

from trellis.core.composition_component import component
from trellis.core.rendering import RenderTree
from trellis.core.state import Stateful
from trellis.core.tracked import ITER_KEY, TrackedDict, TrackedList, TrackedSet


class TestTrackedListBasics:
    """Basic functionality tests for TrackedList."""

    def test_isinstance_list(self) -> None:
        """TrackedList passes isinstance check for list."""
        lst = TrackedList([1, 2, 3])
        assert isinstance(lst, list)

    def test_list_operations(self) -> None:
        """TrackedList supports all standard list operations."""
        lst: TrackedList[int] = TrackedList([1, 2, 3])

        # Indexing
        assert lst[0] == 1
        assert lst[-1] == 3

        # Slicing
        assert lst[1:] == [2, 3]

        # Length
        assert len(lst) == 3

        # Contains
        assert 2 in lst
        assert 4 not in lst

        # Iteration
        assert list(lst) == [1, 2, 3]

    def test_list_mutations(self) -> None:
        """TrackedList supports mutation operations."""
        lst: TrackedList[int] = TrackedList([1, 2, 3])

        lst.append(4)
        assert list(lst) == [1, 2, 3, 4]

        lst.insert(0, 0)
        assert list(lst) == [0, 1, 2, 3, 4]

        lst.remove(2)
        assert list(lst) == [0, 1, 3, 4]

        item = lst.pop()
        assert item == 4
        assert list(lst) == [0, 1, 3]

        lst.extend([5, 6])
        assert list(lst) == [0, 1, 3, 5, 6]

        lst.clear()
        assert list(lst) == []

    def test_copy_returns_plain_list(self) -> None:
        """copy() returns a plain list, not TrackedList."""
        lst = TrackedList([1, 2, 3])
        copy = lst.copy()
        assert copy == [1, 2, 3]
        assert not isinstance(copy, TrackedList)

    def test_add_returns_plain_list(self) -> None:
        """+ operator returns plain list."""
        lst = TrackedList([1, 2])
        result = lst + [3, 4]
        assert result == [1, 2, 3, 4]
        assert not isinstance(result, TrackedList)

    def test_slice_returns_plain_list(self) -> None:
        """Slicing a TrackedList returns a plain list."""
        lst = TrackedList([1, 2, 3, 4, 5])
        sliced = lst[1:4]
        assert sliced == [2, 3, 4]
        assert not isinstance(sliced, TrackedList)

    def test_repr(self) -> None:
        """TrackedList has a useful repr."""
        lst = TrackedList([1, 2, 3])
        assert repr(lst) == "TrackedList([1, 2, 3])"


class TestTrackedDictBasics:
    """Basic functionality tests for TrackedDict."""

    def test_isinstance_dict(self) -> None:
        """TrackedDict passes isinstance check for dict."""
        d = TrackedDict({"a": 1})
        assert isinstance(d, dict)

    def test_dict_operations(self) -> None:
        """TrackedDict supports all standard dict operations."""
        d: TrackedDict[str, int] = TrackedDict({"a": 1, "b": 2})

        # Indexing
        assert d["a"] == 1

        # Get
        assert d.get("a") == 1
        assert d.get("c") is None
        assert d.get("c", 0) == 0

        # Keys/values/items
        assert list(d.keys()) == ["a", "b"]
        assert list(d.values()) == [1, 2]
        assert list(d.items()) == [("a", 1), ("b", 2)]

        # Contains
        assert "a" in d
        assert "c" not in d

        # Length
        assert len(d) == 2

    def test_dict_mutations(self) -> None:
        """TrackedDict supports mutation operations."""
        d: TrackedDict[str, int] = TrackedDict({"a": 1})

        d["b"] = 2
        assert d["b"] == 2

        del d["a"]
        assert "a" not in d

        d.update({"c": 3, "d": 4})
        assert d["c"] == 3

        val = d.pop("c")
        assert val == 3

        d.clear()
        assert len(d) == 0

    def test_copy_returns_plain_dict(self) -> None:
        """copy() returns a plain dict, not TrackedDict."""
        d = TrackedDict({"a": 1})
        copy = d.copy()
        assert copy == {"a": 1}
        assert not isinstance(copy, TrackedDict)

    def test_repr(self) -> None:
        """TrackedDict has a useful repr."""
        d = TrackedDict({"a": 1})
        assert repr(d) == "TrackedDict({'a': 1})"


class TestTrackedSetBasics:
    """Basic functionality tests for TrackedSet."""

    def test_isinstance_set(self) -> None:
        """TrackedSet passes isinstance check for set."""
        s = TrackedSet({1, 2, 3})
        assert isinstance(s, set)

    def test_set_operations(self) -> None:
        """TrackedSet supports all standard set operations."""
        s: TrackedSet[int] = TrackedSet({1, 2, 3})

        # Contains
        assert 1 in s
        assert 4 not in s

        # Length
        assert len(s) == 3

        # Iteration
        assert set(s) == {1, 2, 3}

    def test_set_mutations(self) -> None:
        """TrackedSet supports mutation operations."""
        s: TrackedSet[int] = TrackedSet({1, 2, 3})

        s.add(4)
        assert 4 in s

        s.remove(1)
        assert 1 not in s

        s.discard(2)
        assert 2 not in s

        s.discard(100)  # Should not raise

        item = s.pop()
        assert item in {3, 4}

        s.clear()
        assert len(s) == 0

    def test_copy_returns_plain_set(self) -> None:
        """copy() returns a plain set, not TrackedSet."""
        s = TrackedSet({1, 2, 3})
        copy = s.copy()
        assert copy == {1, 2, 3}
        assert not isinstance(copy, TrackedSet)

    def test_set_operators_return_plain_set(self) -> None:
        """Set operators return plain sets."""
        s1 = TrackedSet({1, 2, 3})
        s2 = {2, 3, 4}

        assert (s1 & s2) == {2, 3}
        assert not isinstance(s1 & s2, TrackedSet)

        assert (s1 | s2) == {1, 2, 3, 4}
        assert (s1 - s2) == {1}
        assert (s1 ^ s2) == {1, 4}

    def test_repr(self) -> None:
        """TrackedSet has a useful repr."""
        s = TrackedSet({1})
        assert "TrackedSet" in repr(s)


class TestAutoConversion:
    """Tests for automatic conversion of plain collections to tracked versions."""

    def test_list_auto_converts_on_stateful(self) -> None:
        """Plain list is auto-converted to TrackedList on Stateful."""

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        assert isinstance(state.items, TrackedList)

    def test_dict_auto_converts_on_stateful(self) -> None:
        """Plain dict is auto-converted to TrackedDict on Stateful."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        assert isinstance(state.data, TrackedDict)

    def test_set_auto_converts_on_stateful(self) -> None:
        """Plain set is auto-converted to TrackedSet on Stateful."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        assert isinstance(state.tags, TrackedSet)

    def test_assignment_auto_converts(self) -> None:
        """Assigning plain collection to Stateful property auto-converts."""

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [1, 2, 3]  # Assign plain list
        assert isinstance(state.items, TrackedList)
        assert list(state.items) == [1, 2, 3]

    def test_nested_list_auto_converts_on_access(self) -> None:
        """Nested plain lists are auto-converted when accessed."""

        @dataclass
        class MyState(Stateful):
            matrix: list[list[int]] = field(default_factory=list)

        state = MyState()
        state.matrix = [[1, 2], [3, 4]]

        # Outer is converted
        assert isinstance(state.matrix, TrackedList)

        # Inner is converted on access
        row = state.matrix[0]
        assert isinstance(row, TrackedList)
        assert list(row) == [1, 2]

    def test_nested_dict_auto_converts_on_access(self) -> None:
        """Nested plain dicts are auto-converted when accessed."""

        @dataclass
        class MyState(Stateful):
            config: dict[str, dict[str, int]] = field(default_factory=dict)

        state = MyState()
        state.config = {"db": {"port": 5432}}

        # Outer is converted
        assert isinstance(state.config, TrackedDict)

        # Inner is converted on access
        db_config = state.config["db"]
        assert isinstance(db_config, TrackedDict)
        assert db_config["port"] == 5432


class TestDependencyTracking:
    """Tests for dependency tracking during render."""

    def test_list_getitem_tracks_by_item_identity(self) -> None:
        """Accessing list[i] registers dependency on id(item)."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        @component
        def ItemViewer() -> None:
            _ = state.items[1]  # Access item at index 1

        ctx = RenderTree(ItemViewer)
        ctx.render()

        # Check that dependency was registered for id("b")
        tracked_list = state.items
        item_b = list.__getitem__(tracked_list, 1)
        assert id(item_b) in tracked_list._deps
        assert ctx.root_node.id in tracked_list._deps[id(item_b)]

    def test_list_iteration_tracks_iter_key(self) -> None:
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

        ctx = RenderTree(ListViewer)
        ctx.render()

        # Check ITER_KEY dependency
        tracked_list = state.items
        assert ITER_KEY in tracked_list._deps
        assert ctx.root_node.id in tracked_list._deps[ITER_KEY]

    def test_dict_getitem_tracks_by_key(self) -> None:
        """Accessing dict[key] registers dependency on that key."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"x": 1, "y": 2}

        @component
        def DataViewer() -> None:
            _ = state.data["x"]

        ctx = RenderTree(DataViewer)
        ctx.render()

        # Check dependency on key "x"
        tracked_dict = state.data
        assert "x" in tracked_dict._deps
        assert ctx.root_node.id in tracked_dict._deps["x"]

    def test_set_contains_tracks_by_value(self) -> None:
        """item in set registers dependency on the value itself."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"python", "rust"}

        @component
        def TagChecker() -> None:
            _ = "python" in state.tags

        ctx = RenderTree(TagChecker)
        ctx.render()

        # Check dependency on the value "python" (not id)
        tracked_set = state.tags
        assert "python" in tracked_set._deps
        assert ctx.root_node.id in tracked_set._deps["python"]

    def test_list_sort_marks_iter_dirty(self) -> None:
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

        ctx = RenderTree(ListViewer)
        ctx.render()
        assert iter_renders[0] == 1

        # Sort - should mark ITER_KEY dirty
        state.items.sort()
        ctx.render()
        assert iter_renders[0] == 2

    def test_dict_new_key_marks_iter_dirty(self) -> None:
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

        ctx = RenderTree(App)
        ctx.render()

        assert iter_renders[0] == 1
        assert a_renders[0] == 1

        # Add new key - Iterator should re-render
        state.data["b"] = 2
        ctx.render()

        assert iter_renders[0] == 2  # Iteration affected by new key
        assert a_renders[0] == 1  # AViewer not affected


class TestFineGrainedReactivity:
    """Tests for fine-grained re-rendering based on tracked collections."""

    def test_list_item_change_only_rerenders_affected(self) -> None:
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

        ctx = RenderTree(App)
        ctx.render()

        assert item0_renders[0] == 1
        assert item1_renders[0] == 1

        # Modify item at index 0 - only Item0 should re-render
        state.items[0] = "updated"
        ctx.render()

        assert item0_renders[0] == 2
        assert item1_renders[0] == 1  # Should NOT have re-rendered

    def test_dict_key_change_only_rerenders_affected(self) -> None:
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

        ctx = RenderTree(App)
        ctx.render()

        assert x_renders[0] == 1
        assert y_renders[0] == 1

        # Modify key "x" - only XViewer should re-render
        state.data["x"] = 100
        ctx.render()

        assert x_renders[0] == 2
        assert y_renders[0] == 1  # Should NOT have re-rendered

    def test_list_append_rerenders_iterators(self) -> None:
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

        ctx = RenderTree(App)
        ctx.render()

        assert list_renders[0] == 1
        assert item0_renders[0] == 1

        # Append - ListViewer should re-render (iterates), Item0Viewer should not
        state.items.append("c")
        ctx.render()

        assert list_renders[0] == 2  # Iterating = ITER_KEY dependency
        assert item0_renders[0] == 1  # Should NOT re-render


class TestRenderTimeMutationGuard:
    """Tests for preventing mutations during render."""

    def test_list_mutation_during_render_raises(self) -> None:
        """Mutating TrackedList during render raises RuntimeError."""

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [1, 2, 3]

        @component
        def BadComponent() -> None:
            state.items.append(4)  # Mutation during render!

        ctx = RenderTree(BadComponent)
        with pytest.raises(RuntimeError, match="Cannot modify tracked collection"):
            ctx.render()

    def test_dict_mutation_during_render_raises(self) -> None:
        """Mutating TrackedDict during render raises RuntimeError."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1}

        @component
        def BadComponent() -> None:
            state.data["b"] = 2  # Mutation during render!

        ctx = RenderTree(BadComponent)
        with pytest.raises(RuntimeError, match="Cannot modify tracked collection"):
            ctx.render()

    def test_set_mutation_during_render_raises(self) -> None:
        """Mutating TrackedSet during render raises RuntimeError."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a"}

        @component
        def BadComponent() -> None:
            state.tags.add("b")  # Mutation during render!

        ctx = RenderTree(BadComponent)
        with pytest.raises(RuntimeError, match="Cannot modify tracked collection"):
            ctx.render()


class TestDependencyCleanup:
    """Tests for dependency cleanup on unmount and re-render."""

    def test_list_dependency_cleaned_on_unmount(self) -> None:
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

        ctx = RenderTree(App)
        ctx.render()

        consumer_id = ctx.root_node.children[0].id
        tracked_list = state.items
        item_a = list.__getitem__(tracked_list, 0)

        # Verify consumer is tracking
        assert consumer_id in tracked_list._deps[id(item_a)]

        # Unmount Consumer
        show_consumer[0] = False
        ctx.mark_dirty_id(ctx.root_node.id)
        ctx.render()

        # Dependency should be cleaned up
        if id(item_a) in tracked_list._deps:
            assert consumer_id not in tracked_list._deps[id(item_a)]

    def test_dict_dependency_cleaned_on_rerender_without_read(self) -> None:
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

        ctx = RenderTree(Consumer)
        ctx.render()

        node_id = ctx.root_node.id
        tracked_dict = state.data

        # Initially tracking
        assert node_id in tracked_dict._deps["x"]

        # Stop reading and re-render
        read_data[0] = False
        ctx.mark_dirty_id(node_id)
        ctx.render()

        # No longer tracking
        if "x" in tracked_dict._deps:
            assert node_id not in tracked_dict._deps["x"]


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_list_operations(self) -> None:
        """Operations on empty TrackedList work correctly."""
        lst: TrackedList[int] = TrackedList()
        assert len(lst) == 0
        assert list(lst) == []

        lst.append(1)
        assert list(lst) == [1]

        lst.clear()
        assert list(lst) == []


class TestTrackedWithStatefulItems:
    """Tests for tracked collections containing Stateful items."""

    def test_stateful_item_tracks_own_properties(self) -> None:
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

        ctx = RenderTree(App)
        ctx.render()

        assert todo1_renders[0] == 1
        assert todo2_renders[0] == 1

        # Modify todo1.completed - only Todo1Viewer should re-render
        todo1.completed = True
        ctx.render()

        assert todo1_renders[0] == 2
        assert todo2_renders[0] == 1  # Should NOT have re-rendered

    def test_replacing_stateful_item_in_list(self) -> None:
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

        ctx = RenderTree(ItemViewer)
        ctx.render()
        assert item_renders[0] == 1

        # Replace the item - should trigger re-render
        new_todo = Todo(text="New")
        state.todos[0] = new_todo
        ctx.render()

        assert item_renders[0] == 2


class TestNewTrackingMethods:
    """Tests for newly added tracking methods."""

    def test_list_index_tracks_iter_key(self) -> None:
        """list.index() registers ITER_KEY dependency."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        renders = [0]

        @component
        def IndexChecker() -> None:
            renders[0] += 1
            _ = state.items.index("b")

        ctx = RenderTree(IndexChecker)
        ctx.render()
        assert renders[0] == 1

        # Append should trigger re-render (ITER_KEY)
        state.items.append("d")
        ctx.render()
        assert renders[0] == 2

    def test_list_count_tracks_iter_key(self) -> None:
        """list.count() registers ITER_KEY dependency."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "a"]

        renders = [0]

        @component
        def CountChecker() -> None:
            renders[0] += 1
            _ = state.items.count("a")

        ctx = RenderTree(CountChecker)
        ctx.render()
        assert renders[0] == 1

        # Append should trigger re-render (ITER_KEY)
        state.items.append("a")
        ctx.render()
        assert renders[0] == 2

    def test_dict_contains_tracks_by_key(self) -> None:
        """key in dict registers dependency on that key."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"x": 1}

        renders = [0]

        @component
        def KeyChecker() -> None:
            renders[0] += 1
            _ = "y" in state.data  # Check for missing key

        ctx = RenderTree(KeyChecker)
        ctx.render()
        assert renders[0] == 1

        # Adding "y" should trigger re-render (key dependency)
        state.data["y"] = 2
        ctx.render()
        assert renders[0] == 2

        # Adding "z" should NOT trigger re-render
        state.data["z"] = 3
        ctx.render()
        assert renders[0] == 2  # No change

    def test_set_issubset_tracks_iter_key(self) -> None:
        """set.issubset() registers ITER_KEY dependency."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b"}

        renders = [0]

        @component
        def SubsetChecker() -> None:
            renders[0] += 1
            _ = state.tags.issubset({"a", "b", "c"})

        ctx = RenderTree(SubsetChecker)
        ctx.render()
        assert renders[0] == 1

        # Adding item should trigger re-render (ITER_KEY)
        state.tags.add("c")
        ctx.render()
        assert renders[0] == 2

    def test_set_issuperset_tracks_iter_key(self) -> None:
        """set.issuperset() registers ITER_KEY dependency."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b", "c"}

        renders = [0]

        @component
        def SupersetChecker() -> None:
            renders[0] += 1
            _ = state.tags.issuperset({"a", "b"})

        ctx = RenderTree(SupersetChecker)
        ctx.render()
        assert renders[0] == 1

        # Removing item should trigger re-render (ITER_KEY)
        state.tags.remove("c")
        ctx.render()
        assert renders[0] == 2

    def test_set_isdisjoint_tracks_iter_key(self) -> None:
        """set.isdisjoint() registers ITER_KEY dependency."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b"}

        renders = [0]

        @component
        def DisjointChecker() -> None:
            renders[0] += 1
            _ = state.tags.isdisjoint({"x", "y"})

        ctx = RenderTree(DisjointChecker)
        ctx.render()
        assert renders[0] == 1

        # Adding item should trigger re-render (ITER_KEY)
        state.tags.add("x")
        ctx.render()
        assert renders[0] == 2


class TestSliceOperations:
    """Tests for slice assignment and deletion."""

    def test_list_slice_assignment(self) -> None:
        """Slice assignment marks old items and ITER_KEY dirty."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c", "d"]

        iter_renders = [0]
        item_a_renders = [0]

        @component
        def IterViewer() -> None:
            iter_renders[0] += 1
            for _ in state.items:
                pass

        @component
        def ItemAViewer() -> None:
            item_a_renders[0] += 1
            _ = state.items[0]  # Read "a"

        @component
        def App() -> None:
            IterViewer()
            ItemAViewer()

        ctx = RenderTree(App)
        ctx.render()
        assert iter_renders[0] == 1
        assert item_a_renders[0] == 1

        # Slice assignment in middle - should trigger iter, not item_a
        state.items[1:3] = ["x", "y", "z"]
        ctx.render()
        assert iter_renders[0] == 2
        assert item_a_renders[0] == 1  # Not affected

    def test_list_slice_deletion(self) -> None:
        """Slice deletion marks old items and ITER_KEY dirty."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c", "d"]

        iter_renders = [0]

        @component
        def IterViewer() -> None:
            iter_renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert iter_renders[0] == 1

        del state.items[1:3]
        ctx.render()
        assert iter_renders[0] == 2
        assert list(state.items) == ["a", "d"]


class TestReverseAndSort:
    """Tests for reverse() and sort() methods."""

    def test_list_reverse_marks_iter_dirty(self) -> None:
        """reverse() marks ITER_KEY dirty."""

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [1, 2, 3]

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        state.items.reverse()
        ctx.render()
        assert renders[0] == 2
        assert list(state.items) == [3, 2, 1]


class TestPopWithIndex:
    """Tests for pop() with specific index."""

    def test_list_pop_with_index(self) -> None:
        """pop(i) marks the correct item dirty."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        item_b_renders = [0]
        iter_renders = [0]

        @component
        def ItemBViewer() -> None:
            item_b_renders[0] += 1
            if len(state.items) > 1:
                _ = state.items[1]

        @component
        def IterViewer() -> None:
            iter_renders[0] += 1
            _ = len(state.items)

        @component
        def App() -> None:
            ItemBViewer()
            IterViewer()

        ctx = RenderTree(App)
        ctx.render()
        assert item_b_renders[0] == 1
        assert iter_renders[0] == 1

        # Pop item at index 1 ("b")
        popped = state.items.pop(1)
        assert popped == "b"
        ctx.render()
        assert item_b_renders[0] == 2  # Was watching "b"
        assert iter_renders[0] == 2  # Length changed


class TestInPlaceOperators:
    """Tests for in-place operators."""

    def test_list_iadd(self) -> None:
        """list += triggers ITER_KEY."""

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [1, 2]

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        state.items += [3, 4]
        ctx.render()
        assert renders[0] == 2
        assert list(state.items) == [1, 2, 3, 4]

    def test_list_imul(self) -> None:
        """list *= triggers ITER_KEY."""

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [1, 2]

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        state.items *= 2
        ctx.render()
        assert renders[0] == 2
        assert list(state.items) == [1, 2, 1, 2]

    def test_set_ior(self) -> None:
        """set |= triggers ITER_KEY."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b"}

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.tags:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        state.tags |= {"c", "d"}
        ctx.render()
        assert renders[0] == 2

    def test_set_iand(self) -> None:
        """set &= triggers ITER_KEY."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b", "c"}

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.tags:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        state.tags &= {"a", "b"}
        ctx.render()
        assert renders[0] == 2
        assert state.tags == {"a", "b"}


class TestNegativeIndices:
    """Tests for negative indices."""

    def test_list_negative_index_getitem(self) -> None:
        """Negative index access works correctly."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        renders = [0]

        @component
        def LastItemViewer() -> None:
            renders[0] += 1
            _ = state.items[-1]  # Read last item

        ctx = RenderTree(LastItemViewer)
        ctx.render()
        assert renders[0] == 1

        # Modify last item
        state.items[-1] = "z"
        ctx.render()
        assert renders[0] == 2

    def test_list_negative_index_setitem(self) -> None:
        """Negative index assignment works correctly."""
        lst: TrackedList[str] = TrackedList(["a", "b", "c"])
        lst[-1] = "z"
        assert list(lst) == ["a", "b", "z"]


class TestErrorCases:
    """Tests for error handling."""

    def test_list_remove_missing_raises(self) -> None:
        """Removing non-existent item raises ValueError."""
        lst: TrackedList[int] = TrackedList([1, 2, 3])
        with pytest.raises(ValueError):
            lst.remove(999)

    def test_list_pop_empty_raises(self) -> None:
        """Popping from empty list raises IndexError."""
        lst: TrackedList[int] = TrackedList()
        with pytest.raises(IndexError):
            lst.pop()

    def test_list_index_missing_raises(self) -> None:
        """index() on missing item raises ValueError."""
        lst: TrackedList[int] = TrackedList([1, 2, 3])
        with pytest.raises(ValueError):
            lst.index(999)

    def test_dict_getitem_missing_raises(self) -> None:
        """Getting missing key raises KeyError."""
        d: TrackedDict[str, int] = TrackedDict({"a": 1})
        with pytest.raises(KeyError):
            _ = d["missing"]

    def test_set_remove_missing_raises(self) -> None:
        """Removing non-existent item raises KeyError."""
        s: TrackedSet[int] = TrackedSet({1, 2, 3})
        with pytest.raises(KeyError):
            s.remove(999)


class TestPopitem:
    """Tests for dict popitem()."""

    def test_dict_popitem_marks_iter_dirty(self) -> None:
        """popitem() marks key and ITER_KEY dirty."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1, "b": 2}

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.data:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        state.data.popitem()
        ctx.render()
        assert renders[0] == 2


class TestSetUpdate:
    """Tests for set update()."""

    def test_set_update_marks_multiple_items_dirty(self) -> None:
        """update() marks all new items and ITER_KEY dirty."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a"}

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.tags:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        state.tags.update({"b", "c", "d"})
        ctx.render()
        assert renders[0] == 2
        assert state.tags == {"a", "b", "c", "d"}


class TestMultiComponentScenarios:
    """Tests for multiple components reading same data."""

    def test_two_components_read_same_item(self) -> None:
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

        ctx = RenderTree(App)
        ctx.render()
        assert comp1_renders[0] == 1
        assert comp2_renders[0] == 1

        # Both should re-render when the shared item changes
        state.items[0] = "updated"
        ctx.render()
        assert comp1_renders[0] == 2
        assert comp2_renders[0] == 2


class TestRebinding:
    """Tests for re-binding collections."""

    def test_tracked_list_cannot_rebind_to_different_owner(self) -> None:
        """TrackedList cannot be assigned to a different Stateful."""

        @dataclass
        class State1(Stateful):
            items: list[int] = field(default_factory=list)

        @dataclass
        class State2(Stateful):
            items: list[int] = field(default_factory=list)

        s1 = State1()
        s1.items = [1, 2, 3]

        s2 = State2()
        # Trying to assign s1's list to s2 should raise ValueError
        with pytest.raises(ValueError, match="Cannot assign tracked collection"):
            s2.items = s1.items

    def test_tracked_list_can_copy_to_new_owner(self) -> None:
        """TrackedList can be copied to a new owner."""

        @dataclass
        class State1(Stateful):
            items: list[int] = field(default_factory=list)

        @dataclass
        class State2(Stateful):
            items: list[int] = field(default_factory=list)

        s1 = State1()
        s1.items = [1, 2, 3]

        s2 = State2()
        # Copy the list to s2 - this creates a new TrackedList
        s2.items = list(s1.items)

        # They should be different TrackedList instances
        assert s1.items is not s2.items
        # But have the same content
        assert list(s1.items) == list(s2.items)


class TestDeeplyNested:
    """Tests for deeply nested access."""

    def test_deeply_nested_list_dict_list(self) -> None:
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

        ctx = RenderTree(DeepViewer)
        ctx.render()
        assert renders[0] == 1

        # All levels should be tracked
        assert isinstance(state.data, TrackedList)
        assert isinstance(state.data[0], TrackedDict)
        assert isinstance(state.data[0]["x"], TrackedList)

        # Modify the deeply nested value
        state.data[0]["x"][1] = 999
        ctx.render()
        assert renders[0] == 2


class TestMutationsOutsideRender:
    """Tests for mutations outside render context."""

    def test_mutations_outside_render_work(self) -> None:
        """Mutations outside of render context should work fine."""
        lst: TrackedList[int] = TrackedList([1, 2, 3])

        # All these should work without error
        lst.append(4)
        lst.insert(0, 0)
        lst.remove(2)
        lst.pop()
        lst.extend([5, 6])
        lst.reverse()
        lst.sort()
        lst.clear()
        lst += [1, 2]
        lst *= 2

        d: TrackedDict[str, int] = TrackedDict({"a": 1})
        d["b"] = 2
        del d["a"]
        d.update({"c": 3})
        d.pop("b")
        d.setdefault("d", 4)
        d.clear()

        s: TrackedSet[int] = TrackedSet({1, 2, 3})
        s.add(4)
        s.remove(1)
        s.discard(2)
        s.update({5, 6})
        s.intersection_update({3, 4, 5})
        s.difference_update({5})
        s.symmetric_difference_update({1, 3})
        s.clear()

    def test_standalone_tracked_then_assign(self) -> None:
        """TrackedList created standalone, then assigned to Stateful."""

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        # Create standalone
        lst: TrackedList[int] = TrackedList([1, 2, 3])

        # Assign to Stateful
        state = MyState()
        state.items = lst  # type: ignore[assignment]

        # Should be bound now
        assert state.items._owner is not None
        assert state.items._attr == "items"


class TestSetValueTracking:
    """Tests for set value-based tracking (vs id-based)."""

    def test_set_contains_with_different_string_objects(self) -> None:
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

        ctx = RenderTree(TagChecker)
        ctx.render()
        assert renders[0] == 1

        # Add a different string object with same value
        # (In practice, Python often interns strings, but the point is
        # we track by value, not id)
        state.tags.add("python")
        ctx.render()
        assert renders[0] == 2  # Should re-render!


class TestDictSetdefault:
    """Tests for TrackedDict.setdefault()."""

    def test_setdefault_new_key_marks_dirty(self) -> None:
        """setdefault() with new key marks key and ITER_KEY dirty."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1}

        iter_renders = [0]
        key_b_renders = [0]

        @component
        def IterViewer() -> None:
            iter_renders[0] += 1
            for _ in state.data:
                pass

        @component
        def KeyBViewer() -> None:
            key_b_renders[0] += 1
            _ = state.data.get("b")

        @component
        def App() -> None:
            IterViewer()
            KeyBViewer()

        ctx = RenderTree(App)
        ctx.render()
        assert iter_renders[0] == 1
        assert key_b_renders[0] == 1

        # setdefault with new key - both should re-render
        state.data.setdefault("b", 2)
        ctx.render()
        assert iter_renders[0] == 2  # New key = ITER_KEY dirty
        assert key_b_renders[0] == 2  # Key "b" now exists

    def test_setdefault_existing_key_no_change(self) -> None:
        """setdefault() with existing key doesn't mark anything dirty."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1}

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.data:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        # setdefault with existing key - should NOT re-render
        result = state.data.setdefault("a", 999)
        assert result == 1  # Returns existing value
        ctx.render()
        assert renders[0] == 1  # No change


class TestDictUpdateVariants:
    """Tests for TrackedDict.update() with different argument types."""

    def test_update_with_kwargs(self) -> None:
        """update() with keyword arguments works correctly."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1}

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.data:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        # Update with kwargs
        state.data.update(b=2, c=3)
        ctx.render()
        assert renders[0] == 2
        assert state.data == {"a": 1, "b": 2, "c": 3}

    def test_update_with_iterable(self) -> None:
        """update() with iterable of tuples works correctly."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1}

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.data:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        # Update with iterable of tuples
        state.data.update([("b", 2), ("c", 3)])
        ctx.render()
        assert renders[0] == 2
        assert state.data == {"a": 1, "b": 2, "c": 3}

    def test_update_existing_key_no_iter_dirty(self) -> None:
        """update() of existing key doesn't mark ITER_KEY dirty."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1, "b": 2}

        iter_renders = [0]
        a_renders = [0]

        @component
        def IterViewer() -> None:
            iter_renders[0] += 1
            for _ in state.data:
                pass

        @component
        def AViewer() -> None:
            a_renders[0] += 1
            _ = state.data["a"]

        @component
        def App() -> None:
            IterViewer()
            AViewer()

        ctx = RenderTree(App)
        ctx.render()
        assert iter_renders[0] == 1
        assert a_renders[0] == 1

        # Update existing key only
        state.data.update({"a": 100})
        ctx.render()
        assert iter_renders[0] == 1  # No new keys = no ITER_KEY dirty
        assert a_renders[0] == 2  # Key "a" was updated


class TestSetBulkOperations:
    """Tests for TrackedSet bulk update operations."""

    def test_intersection_update_marks_removed_dirty(self) -> None:
        """intersection_update() marks removed items dirty."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b", "c", "d"}

        iter_renders = [0]
        c_renders = [0]

        @component
        def IterViewer() -> None:
            iter_renders[0] += 1
            for _ in state.tags:
                pass

        @component
        def CChecker() -> None:
            c_renders[0] += 1
            _ = "c" in state.tags

        @component
        def App() -> None:
            IterViewer()
            CChecker()

        ctx = RenderTree(App)
        ctx.render()
        assert iter_renders[0] == 1
        assert c_renders[0] == 1

        # Keep only "a" and "b" - removes "c" and "d"
        state.tags.intersection_update({"a", "b"})
        ctx.render()
        assert iter_renders[0] == 2  # Items removed
        assert c_renders[0] == 2  # "c" was removed
        assert state.tags == {"a", "b"}

    def test_difference_update_marks_removed_dirty(self) -> None:
        """difference_update() marks removed items dirty."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b", "c"}

        renders = [0]

        @component
        def BChecker() -> None:
            renders[0] += 1
            _ = "b" in state.tags

        ctx = RenderTree(BChecker)
        ctx.render()
        assert renders[0] == 1

        # Remove "b" via difference_update
        state.tags.difference_update({"b", "x"})  # "x" not in set
        ctx.render()
        assert renders[0] == 2  # "b" was removed
        assert state.tags == {"a", "c"}

    def test_symmetric_difference_update(self) -> None:
        """symmetric_difference_update() marks changed items dirty."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b"}

        b_renders = [0]
        c_renders = [0]

        @component
        def BChecker() -> None:
            b_renders[0] += 1
            _ = "b" in state.tags

        @component
        def CChecker() -> None:
            c_renders[0] += 1
            _ = "c" in state.tags

        @component
        def App() -> None:
            BChecker()
            CChecker()

        ctx = RenderTree(App)
        ctx.render()
        assert b_renders[0] == 1
        assert c_renders[0] == 1

        # Symmetric difference: remove "b", add "c"
        state.tags.symmetric_difference_update({"b", "c"})
        ctx.render()
        assert b_renders[0] == 2  # "b" was removed
        assert c_renders[0] == 2  # "c" was added
        assert state.tags == {"a", "c"}

    def test_update_multiple_iterables(self) -> None:
        """update() with multiple iterables works correctly."""
        s: TrackedSet[int] = TrackedSet({1, 2})
        s.update({3, 4}, {5, 6})
        assert s == {1, 2, 3, 4, 5, 6}


class TestEdgeCasesExtended:
    """Extended edge case tests."""

    def test_list_imul_zero_clears(self) -> None:
        """list *= 0 clears the list."""

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [1, 2, 3]

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        state.items *= 0
        ctx.render()
        assert renders[0] == 2  # ITER_KEY dirty
        assert list(state.items) == []

    def test_dict_pop_with_default(self) -> None:
        """pop() with default returns default when key missing."""
        d: TrackedDict[str, int] = TrackedDict({"a": 1})

        # Pop existing key
        result = d.pop("a")
        assert result == 1
        assert "a" not in d

        # Pop missing key with default
        result = d.pop("missing", 99)
        assert result == 99

    def test_dict_pop_missing_no_dirty(self) -> None:
        """pop() on missing key with default doesn't mark dirty."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1}

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.data:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        # Pop missing key with default - should NOT trigger re-render
        result = state.data.pop("missing", 99)
        assert result == 99
        ctx.render()
        assert renders[0] == 1  # No change

    def test_set_discard_nonexistent_no_dirty(self) -> None:
        """discard() on non-existent item doesn't trigger reactivity."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b"}

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.tags:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        # Discard non-existent item - should NOT trigger re-render
        state.tags.discard("nonexistent")
        ctx.render()
        assert renders[0] == 1  # No change
        assert state.tags == {"a", "b"}

    def test_list_index_with_bounds(self) -> None:
        """index() with start/stop bounds works correctly."""
        lst: TrackedList[int] = TrackedList([1, 2, 1, 2, 1])
        assert lst.index(2) == 1  # First occurrence
        assert lst.index(2, 2) == 3  # Start at index 2
        assert lst.index(1, 2, 5) == 2  # Between indices 2 and 5

    def test_list_sort_with_key(self) -> None:
        """sort() with key parameter works correctly."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["apple", "pie", "zoo"]

        renders = [0]

        @component
        def IterViewer() -> None:
            renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderTree(IterViewer)
        ctx.render()
        assert renders[0] == 1

        # Sort by length
        state.items.sort(key=len)
        ctx.render()
        assert renders[0] == 2
        assert list(state.items) == ["pie", "zoo", "apple"]

    def test_list_sort_with_reverse(self) -> None:
        """sort() with reverse=True works correctly."""
        lst: TrackedList[int] = TrackedList([3, 1, 2])
        lst.sort(reverse=True)
        assert list(lst) == [3, 2, 1]

    def test_clear_dep_nonexistent(self) -> None:
        """_clear_dep on non-existent dependency doesn't raise."""
        lst: TrackedList[int] = TrackedList([1, 2, 3])
        # Should not raise
        lst._clear_dep("fake_node_id", "fake_key")

    def test_list_of_sets_auto_converts(self) -> None:
        """List containing sets auto-converts sets on assignment."""

        @dataclass
        class MyState(Stateful):
            data: list[set[str]] = field(default_factory=list)

        state = MyState()
        state.data = [{"a", "b"}, {"c", "d"}]

        # Outer is converted
        assert isinstance(state.data, TrackedList)

        # Inner sets are converted too (eager conversion)
        assert isinstance(state.data[0], TrackedSet)
        assert state.data[0] == {"a", "b"}
