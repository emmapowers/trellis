"""Integration tests for tracked collection dependency tracking and fine-grained reactivity."""

import gc
from dataclasses import dataclass, field

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful
from trellis.core.state.tracked import ITER_KEY, TrackedDict, TrackedList


class TestDependencyTracking:
    """Tests for dependency tracking during render.

    INTERNAL TEST: These tests verify the internal dependency graph (_deps)
    which has no public API for inspection.
    """

    def test_list_getitem_tracks_by_item_identity(self) -> None:
        """
        Verify that reading a list element by index records a dependency keyed by the element's identity.
        
        After rendering a component that accesses state.items[i], the tracked list's internal dependencies contain an entry keyed by id(the item) and the render session's root element is registered in that dependency set.
        """

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        @component
        def ItemViewer() -> None:
            """
            Component that reads the item at index 1 from state.items to establish a dependency.
            
            This component performs a single read of state.items[1], causing the render system to track a dependency on that specific list entry.
            """
            _ = state.items[1]  # Access item at index 1

        ctx = RenderSession(ItemViewer)
        render(ctx)

        # Check that dependency was registered for id("b")
        tracked_list = state.items
        item_b = list.__getitem__(tracked_list, 1)
        assert id(item_b) in tracked_list._deps
        assert ctx.root_element in tracked_list._deps[id(item_b)]

    def test_list_iteration_tracks_iter_key(self) -> None:
        """Iterating over list registers dependency on ITER_KEY."""

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        @component
        def ListViewer() -> None:
            """
            Reads every element of `state.items` to register an iteration dependency used by tests.
            
            Used in integration tests to ensure iteration tracking (the `ITER_KEY`) is recorded when a component iterates over a tracked list.
            """
            for item in state.items:
                _ = item

        ctx = RenderSession(ListViewer)
        render(ctx)

        # Check ITER_KEY dependency
        tracked_list = state.items
        assert ITER_KEY in tracked_list._deps
        assert ctx.root_element in tracked_list._deps[ITER_KEY]

    def test_dict_getitem_tracks_by_key(self) -> None:
        """Accessing dict[key] registers dependency on that key."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"x": 1, "y": 2}

        @component
        def DataViewer() -> None:
            """
            Reads the "x" entry from the shared state data to establish a render dependency.
            """
            _ = state.data["x"]

        ctx = RenderSession(DataViewer)
        render(ctx)

        # Check dependency on key "x"
        tracked_dict = state.data
        assert "x" in tracked_dict._deps
        assert ctx.root_element in tracked_dict._deps["x"]

    def test_set_contains_tracks_by_value(self) -> None:
        """
        Asserts that checking membership of a value in a TrackedSet registers a dependency on that value (by value, not identity).
        
        Verifies that rendering a component which evaluates `"python" in state.tags` results in the tracked set's dependency map containing the key `"python"` and the render session's root element being recorded for that key.
        """

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"python", "rust"}

        @component
        def TagChecker() -> None:
            _ = "python" in state.tags

        ctx = RenderSession(TagChecker)
        render(ctx)

        # Check dependency on the value "python" (not id)
        tracked_set = state.tags
        assert "python" in tracked_set._deps
        assert ctx.root_element in tracked_set._deps["python"]

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
            """
            Component that iterates over state.items and increments the iterator render counter.
            
            Increments iter_renders[0] on each render and reads each element of state.items to establish an iteration dependency for testing.
            """
            iter_renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderSession(ListViewer)
        render(ctx)
        assert iter_renders[0] == 1

        # Sort - should mark ITER_KEY dirty
        state.items.sort()
        render(ctx)
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
            """
            Increment the iteration render counter and iterate over state.data to register iteration dependencies.
            
            This component increments iter_renders[0] each time it renders, then iterates over state.data (no other side effects), so tests can observe iteration-based dependency tracking.
            """
            iter_renders[0] += 1
            for _ in state.data:
                pass

        @component
        def AViewer() -> None:
            """
            Component that reads the "a" key from state.data and records a render by incrementing a_renders[0].
            
            Reading the key registers a dependency on the dictionary entry "a".
            """
            a_renders[0] += 1
            _ = state.data["a"]

        @component
        def App() -> None:
            """
            Component that mounts the Iterator and AViewer components.
            
            Used in tests to render both components together so iteration-related updates and individual key views can be exercised within a single app.
            """
            Iterator()
            AViewer()

        ctx = RenderSession(App)
        render(ctx)

        assert iter_renders[0] == 1
        assert a_renders[0] == 1

        # Add new key - Iterator should re-render
        state.data["b"] = 2
        render(ctx)

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
            """
            Increment the Item0 render counter and access the first item of state.items to register a read dependency.
            
            This increments item0_renders[0] and reads state.items[0], causing the render to be associated with that item.
            """
            item0_renders[0] += 1
            _ = state.items[0]

        @component
        def Item1() -> None:
            """
            Test component that increments the Item1 render counter and reads the second item from state to establish a dependency.
            """
            item1_renders[0] += 1
            _ = state.items[1]

        @component
        def App() -> None:
            """
            Compose and render Item0 and Item1 components in sequence.
            """
            Item0()
            Item1()

        ctx = RenderSession(App)
        render(ctx)

        assert item0_renders[0] == 1
        assert item1_renders[0] == 1

        # Modify item at index 0 - only Item0 should re-render
        state.items[0] = "updated"
        render(ctx)

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
            """
            Test component that increments the x_renders counter and reads state.data["x"] to establish a dependency on the "x" key.
            """
            x_renders[0] += 1
            _ = state.data["x"]

        @component
        def YViewer() -> None:
            """
            Increment the shared render counter and read state.data["y"] to establish a dependency on the "y" key.
            
            This component is used in tests to count renders and ensure dependency tracking for the `"y"` dictionary key.
            """
            y_renders[0] += 1
            _ = state.data["y"]

        @component
        def App() -> None:
            """
            Compose and mount XViewer and YViewer into the current render tree.
            
            Instantiates both viewer components so they are rendered together as part of the application.
            """
            XViewer()
            YViewer()

        ctx = RenderSession(App)
        render(ctx)

        assert x_renders[0] == 1
        assert y_renders[0] == 1

        # Modify key "x" - only XViewer should re-render
        state.data["x"] = 100
        render(ctx)

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
            """
            Component used in tests that iterates over state.items and increments the list render counter each render.
            
            Increments list_renders[0] and iterates over state.items to exercise iteration-based dependency tracking during a render.
            """
            list_renders[0] += 1
            for _ in state.items:
                pass

        @component
        def Item0Viewer() -> None:
            """
            Component used in tests to record a render and read the first item from `state.items` to establish a dependency.
            """
            item0_renders[0] += 1
            _ = state.items[0]

        @component
        def App() -> None:
            """
            Compose the application component tree containing the list iterator and a single-item viewer.
            
            This component instantiates ListViewer and Item0Viewer so both child components are part of the rendered tree.
            """
            ListViewer()
            Item0Viewer()

        ctx = RenderSession(App)
        render(ctx)

        assert list_renders[0] == 1
        assert item0_renders[0] == 1

        # Append - ListViewer should re-render (iterates), Item0Viewer should not
        state.items.append("c")
        render(ctx)

        assert list_renders[0] == 2  # Iterating = ITER_KEY dependency
        assert item0_renders[0] == 1  # Should NOT re-render


class TestDependencyCleanup:
    """Tests for dependency cleanup on unmount and re-render.

    INTERNAL TEST: These tests verify the internal dependency graph (_deps)
    cleanup behavior which has no public API for inspection.
    """

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
            """
            Conditionally renders the Consumer component when the show_consumer flag is set.
            
            If show_consumer[0] is True, mounts Consumer; otherwise renders nothing.
            """
            if show_consumer[0]:
                Consumer()

        ctx = RenderSession(App)
        render(ctx)

        # Get consumer ID without keeping strong reference to node
        consumer_id = ctx.elements.get(ctx.root_element.child_ids[0]).id
        tracked_list = state.items
        item_a = list.__getitem__(tracked_list, 0)

        # Verify consumer is tracking (check by node ID since object identity may differ)
        dep_node_ids = {n.id for n in tracked_list._deps[id(item_a)]}
        assert consumer_id in dep_node_ids

        # Unmount Consumer
        show_consumer[0] = False
        ctx.dirty.mark(ctx.root_element.id)
        render(ctx)

        # Force GC so WeakSet can remove dead references
        gc.collect()

        # Dependency should be cleaned up (WeakSet auto-removes dead refs after GC)
        if id(item_a) in tracked_list._deps:
            dep_node_ids = {n.id for n in tracked_list._deps[id(item_a)]}
            assert consumer_id not in dep_node_ids

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
            """
            Conditionally accesses the "x" key of the shared state dictionary when the external flag is true.
            
            When `read_data[0]` is truthy, reads `state.data["x"]` so the current render will depend on that key; does nothing when the flag is false.
            """
            if read_data[0]:
                _ = state.data["x"]

        ctx = RenderSession(Consumer)
        render(ctx)

        # Get root ID without keeping strong reference to old node
        root_id = ctx.root_element.id
        tracked_dict = state.data

        # Initially tracking (check by node ID since object identity may differ)
        dep_node_ids = {n.id for n in tracked_dict._deps["x"]}
        assert root_id in dep_node_ids

        # Stop reading and re-render
        read_data[0] = False
        ctx.dirty.mark(root_id)
        render(ctx)

        # Force GC so WeakSet can remove dead references (old node from previous render)
        gc.collect()

        # No longer tracking (WeakSet auto-removes dead refs after GC)
        if "x" in tracked_dict._deps:
            dep_node_ids = {n.id for n in tracked_dict._deps["x"]}
            assert root_id not in dep_node_ids


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
            """
            Increment the Todo1 render counter and read the first todo's completed property to establish a dependency.
            
            This component increments todo1_renders[0] when invoked and accesses state.todos[0].completed so the viewer depends on that property's value.
            """
            todo1_renders[0] += 1
            _ = state.todos[0].completed  # Read todo1.completed

        @component
        def Todo2Viewer() -> None:
            """
            Increment the second todo's render counter and read its `completed` property to establish a dependency.
            
            This component-side function updates `todo2_renders[0]` and accesses `state.todos[1].completed`.
            """
            todo2_renders[0] += 1
            _ = state.todos[1].completed  # Read todo2.completed

        @component
        def App() -> None:
            """
            Mounts the two todo viewer components.
            
            This App component composes Todo1Viewer and Todo2Viewer for tests that assert fine-grained re-rendering behavior.
            """
            Todo1Viewer()
            Todo2Viewer()

        ctx = RenderSession(App)
        render(ctx)

        assert todo1_renders[0] == 1
        assert todo2_renders[0] == 1

        # Modify todo1.completed - only Todo1Viewer should re-render
        todo1.completed = True
        render(ctx)

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
            """
            Component used in tests that increments a render counter and reads the first todo item to record a dependency on that item.
            
            Increments `item_renders[0]` each time it is invoked and reads `state.todos[0]`.
            """
            item_renders[0] += 1
            _ = state.todos[0]  # Just read the item

        ctx = RenderSession(ItemViewer)
        render(ctx)
        assert item_renders[0] == 1

        # Replace the item - should trigger re-render
        new_todo = Todo(text="New")
        state.todos[0] = new_todo
        render(ctx)

        assert item_renders[0] == 2


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
            """
            Component that reads the first item of `state.items` to register a dependency and increments a render counter.
            """
            comp1_renders[0] += 1
            _ = state.items[0]

        @component
        def Component2() -> None:
            """
            Increment the component render counter and read the first item from state to establish a dependency.
            
            This component increments comp2_renders[0] each time it runs and accesses state.items[0] so the render system registers a dependency on that list slot.
            """
            comp2_renders[0] += 1
            _ = state.items[0]

        @component
        def App() -> None:
            """
            Compose and render Component1 followed by Component2.
            
            This function invokes Component1 and Component2 in sequence to assemble the application UI.
            """
            Component1()
            Component2()

        ctx = RenderSession(App)
        render(ctx)
        assert comp1_renders[0] == 1
        assert comp2_renders[0] == 1

        # Both should re-render when the shared item changes
        state.items[0] = "updated"
        render(ctx)
        assert comp1_renders[0] == 2
        assert comp2_renders[0] == 2


class TestDeeplyNested:
    """Tests for deeply nested access."""

    def test_deeply_nested_list_dict_list(self) -> None:
        """
        Verify that reading a value nested inside a list of dicts of lists is tracked at every container level and that updating that deeply nested element triggers a re-render.
        
        This test builds a Stateful with type list[dict[str, list[int]]], confirms the nested runtime containers are TrackedList/TrackedDict/TrackedList, accesses state.data[0]["x"][1] during rendering, then mutates that element and asserts the component renders again.
        """

        @dataclass
        class MyState(Stateful):
            data: list[dict[str, list[int]]] = field(default_factory=list)

        state = MyState()
        state.data = [{"x": [10, 20, 30]}]

        renders = [0]

        @component
        def DeepViewer() -> None:
            """
            Increment the render counter and read the deeply nested value at data[0]["x"][1] to register its dependency.
            
            This component records a render (increments renders[0]) and accesses the nested element so the rendering system tracks dependencies on that specific nested location.
            """
            renders[0] += 1
            _ = state.data[0]["x"][1]  # Access 20

        ctx = RenderSession(DeepViewer)
        render(ctx)
        assert renders[0] == 1

        # All levels should be tracked
        assert isinstance(state.data, TrackedList)
        assert isinstance(state.data[0], TrackedDict)
        assert isinstance(state.data[0]["x"], TrackedList)

        # Modify the deeply nested value
        state.data[0]["x"][1] = 999
        render(ctx)
        assert renders[0] == 2


class TestSetValueTracking:
    """Tests for set value-based tracking (vs id-based)."""

    def test_set_contains_with_different_string_objects(self) -> None:
        """
        Verifies set membership tracking uses value equality rather than object identity.
        
        Renders a component that checks whether a specific string value is in a tracked set, then adds a distinct string object with the same value and asserts the component re-renders due to the value-based dependency.
        """

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = set()  # Start empty

        renders = [0]
        check_value = "python"  # This string object

        @component
        def TagChecker() -> None:
            """
            Component that records a render and reads membership of `check_value` in `state.tags`.
            
            Increments `renders[0]` to count this render, and evaluates `check_value in state.tags` so a dependency on the set membership is observed.
            """
            renders[0] += 1
            _ = check_value in state.tags

        ctx = RenderSession(TagChecker)
        render(ctx)
        assert renders[0] == 1

        # Add a different string object with same value
        # (In practice, Python often interns strings, but the point is
        # we track by value, not id)
        state.tags.add("python")
        render(ctx)
        assert renders[0] == 2  # Should re-render!