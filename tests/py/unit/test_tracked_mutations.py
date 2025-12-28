"""Integration tests for tracked collection mutations during render and guards."""

from dataclasses import dataclass, field

import pytest

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful


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
            """
            Component used by tests to mutate a tracked list during render and trigger the mutation guard.
            
            When executed in a render context, this component appends to `state.items`, which raises a RuntimeError with the message "Cannot modify tracked collection".
            """
            state.items.append(4)  # Mutation during render!

        ctx = RenderSession(BadComponent)
        with pytest.raises(RuntimeError, match="Cannot modify tracked collection"):
            render(ctx)

    def test_dict_mutation_during_render_raises(self) -> None:
        """Mutating TrackedDict during render raises RuntimeError."""

        @dataclass
        class MyState(Stateful):
            data: dict[str, int] = field(default_factory=dict)

        state = MyState()
        state.data = {"a": 1}

        @component
        def BadComponent() -> None:
            """
            Component that mutates the tracked dict `state.data` during render to exercise the runtime check preventing collection modifications during rendering.
            
            This component assigns a new key to `state.data` when invoked, which is intended to trigger the "Cannot modify tracked collection" error in tests.
            """
            state.data["b"] = 2  # Mutation during render!

        ctx = RenderSession(BadComponent)
        with pytest.raises(RuntimeError, match="Cannot modify tracked collection"):
            render(ctx)

    def test_set_mutation_during_render_raises(self) -> None:
        """Mutating TrackedSet during render raises RuntimeError."""

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a"}

        @component
        def BadComponent() -> None:
            """
            Component used in tests that mutates the tracked `tags` set during render to trigger the render-time mutation guard.
            
            This function performs `state.tags.add("b")` when invoked; it is intended to cause the rendering system to raise a `RuntimeError` for modifying a tracked collection during render.
            """
            state.tags.add("b")  # Mutation during render!

        ctx = RenderSession(BadComponent)
        with pytest.raises(RuntimeError, match="Cannot modify tracked collection"):
            render(ctx)


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
            """
            Increments the render counter and accesses the index of "b" in state.items to establish a dependency on that item's position.
            
            This updates renders[0] and performs state.items.index("b"), causing the render system to track the item's position so changes that affect that position will invalidate the render.
            """
            renders[0] += 1
            _ = state.items.index("b")

        ctx = RenderSession(IndexChecker)
        render(ctx)
        assert renders[0] == 1

        # Append should trigger re-render (ITER_KEY)
        state.items.append("d")
        render(ctx)
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
            """
            Increments the render counter and reads the count of "a" in state.items to record a dependency on the list's contents.
            
            Used by tests to trigger and observe re-renders when the number of `"a"` elements changes.
            """
            renders[0] += 1
            _ = state.items.count("a")

        ctx = RenderSession(CountChecker)
        render(ctx)
        assert renders[0] == 1

        # Append should trigger re-render (ITER_KEY)
        state.items.append("a")
        render(ctx)
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
            """
            Increment the render counter and read whether the key "y" exists in the state's data mapping.
            
            This function accesses membership of "y" in `state.data` to establish a dependency and increments `renders[0]` to record a render.
            """
            renders[0] += 1
            _ = "y" in state.data  # Check for missing key

        ctx = RenderSession(KeyChecker)
        render(ctx)
        assert renders[0] == 1

        # Adding "y" should trigger re-render (key dependency)
        state.data["y"] = 2
        render(ctx)
        assert renders[0] == 2

        # Adding "z" should NOT trigger re-render
        state.data["z"] = 3
        render(ctx)
        assert renders[0] == 2  # No change

    def test_set_issubset_tracks_iter_key(self) -> None:
        """
        Verify that evaluating set.issubset registers an iteration-key dependency so the component re-renders when a relevant element is added.
        
        The test renders a component that calls state.tags.issubset({"a", "b", "c"}), asserts a single initial render, then adds "c" to the tracked set and asserts the component re-renders.
        """

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b"}

        renders = [0]

        @component
        def SubsetChecker() -> None:
            """
            Render callback that records a render and checks whether the state's tags are a subset of {"a", "b", "c"}.
            
            This increments the render counter and evaluates `state.tags.issubset({"a", "b", "c"})` to register a dependency on the tag membership.
            """
            renders[0] += 1
            _ = state.tags.issubset({"a", "b", "c"})

        ctx = RenderSession(SubsetChecker)
        render(ctx)
        assert renders[0] == 1

        # Adding item should trigger re-render (ITER_KEY)
        state.tags.add("c")
        render(ctx)
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
            """
            Increment the render counter and evaluate whether state.tags is a superset of {'a', 'b'}.
            """
            renders[0] += 1
            _ = state.tags.issuperset({"a", "b"})

        ctx = RenderSession(SupersetChecker)
        render(ctx)
        assert renders[0] == 1

        # Removing item should trigger re-render (ITER_KEY)
        state.tags.remove("c")
        render(ctx)
        assert renders[0] == 2

    def test_set_isdisjoint_tracks_iter_key(self) -> None:
        """
        Verify that calling `set.isdisjoint` registers an iteration-key dependency so changes in set membership cause a re-render.
        
        This test asserts that an initial render occurs when a component calls `state.tags.isdisjoint(...)`, and that adding an element to `state.tags` that affects the `isdisjoint` result triggers a subsequent render.
        """

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b"}

        renders = [0]

        @component
        def DisjointChecker() -> None:
            """
            Render callback that records a render and evaluates whether state's tags are disjoint from {"x", "y"}.
            """
            renders[0] += 1
            _ = state.tags.isdisjoint({"x", "y"})

        ctx = RenderSession(DisjointChecker)
        render(ctx)
        assert renders[0] == 1

        # Adding item should trigger re-render (ITER_KEY)
        state.tags.add("x")
        render(ctx)
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
            """
            Increment the iteration render counter and read all items to establish an iteration dependency on `state.items`.
            
            This viewer is used by tests to mark that iteration over `state.items` occurred (by incrementing `iter_renders[0]`) so that changes affecting iteration will trigger re-renders.
            """
            iter_renders[0] += 1
            for _ in state.items:
                pass

        @component
        def ItemAViewer() -> None:
            """
            Increment the item-A render counter and read the first element of state.items to establish a dependency on index 0.
            
            Increments item_a_renders[0] and accesses state.items[0], causing renders that depend on that specific list index to be tracked.
            """
            item_a_renders[0] += 1
            _ = state.items[0]  # Read "a"

        @component
        def App() -> None:
            """
            Render the IterViewer and ItemAViewer components.
            
            This function invokes the two viewer components so their render effects and tracking
            behaviors are exercised within the test render session.
            """
            IterViewer()
            ItemAViewer()

        ctx = RenderSession(App)
        render(ctx)
        assert iter_renders[0] == 1
        assert item_a_renders[0] == 1

        # Slice assignment in middle - should trigger iter, not item_a
        state.items[1:3] = ["x", "y", "z"]
        render(ctx)
        assert iter_renders[0] == 2
        assert item_a_renders[0] == 1  # Not affected

    def test_list_slice_deletion(self) -> None:
        """
        Deleting a slice from a tracked list invalidates iteration dependencies and marks the removed items dirty.
        
        This causes components that depended on iterating the list to be re-rendered when the slice is deleted.
        """

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c", "d"]

        iter_renders = [0]

        @component
        def IterViewer() -> None:
            """
            Increment the iteration render counter and read all items to establish an iteration dependency on `state.items`.
            
            This viewer is used by tests to mark that iteration over `state.items` occurred (by incrementing `iter_renders[0]`) so that changes affecting iteration will trigger re-renders.
            """
            iter_renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert iter_renders[0] == 1

        del state.items[1:3]
        render(ctx)
        assert iter_renders[0] == 2
        assert list(state.items) == ["a", "d"]


class TestReverseAndSort:
    """Tests for reverse() and sort() methods."""

    def test_list_reverse_marks_iter_dirty(self) -> None:
        """
        Marks that calling `reverse()` on a tracked list invalidates iteration dependencies so components that iterate over it are re-rendered.
        """

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [1, 2, 3]

        renders = [0]

        @component
        def IterViewer() -> None:
            """
            Increment the render counter and iterate over state.items to exercise iteration-based tracking.
            
            This function increments renders[0] and iterates through state.items so tests can observe renders triggered by changes to the collection.
            """
            renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.items.reverse()
        render(ctx)
        assert renders[0] == 2
        assert list(state.items) == [3, 2, 1]

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
            """
            Increment the render counter and iterate over state.items to exercise iteration-based tracking.
            
            This function increments renders[0] and iterates through state.items so tests can observe renders triggered by changes to the collection.
            """
            renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        # Sort by length
        state.items.sort(key=len)
        render(ctx)
        assert renders[0] == 2
        assert list(state.items) == ["pie", "zoo", "apple"]


class TestPopWithIndex:
    """Tests for pop() with specific index."""

    def test_list_pop_with_index(self) -> None:
        """
        Verifies that popping an element by index marks the specific indexed item and collection length as dirty so dependent components re-render.
        
        This test renders two components: one that reads the item at index 1 and one that reads the collection length. After popping the element at index 1, it asserts both the item-dependent and length-dependent components re-render once more.
        """

        @dataclass
        class MyState(Stateful):
            items: list[str] = field(default_factory=list)

        state = MyState()
        state.items = ["a", "b", "c"]

        item_b_renders = [0]
        iter_renders = [0]

        @component
        def ItemBViewer() -> None:
            """
            Increment the render counter and, if present, read the second item from state.items.
            
            This function increments the outer `item_b_renders[0]` counter and accesses `state.items[1]` when the list has at least two elements to record a dependency on that index.
            """
            item_b_renders[0] += 1
            if len(state.items) > 1:
                _ = state.items[1]

        @component
        def IterViewer() -> None:
            """
            Increment the iteration render counter and read the length of the tracked items collection to establish a dependency on its iteration/size.
            
            This function updates the outer `iter_renders` counter and accesses `state.items` length so that renders depend on the list's contents or size.
            """
            iter_renders[0] += 1
            _ = len(state.items)

        @component
        def App() -> None:
            """
            Render both ItemBViewer and IterViewer components.
            
            Composes the test view by instantiating ItemBViewer and IterViewer within the render tree.
            """
            ItemBViewer()
            IterViewer()

        ctx = RenderSession(App)
        render(ctx)
        assert item_b_renders[0] == 1
        assert iter_renders[0] == 1

        # Pop item at index 1 ("b")
        popped = state.items.pop(1)
        assert popped == "b"
        render(ctx)
        assert item_b_renders[0] == 2  # Was watching "b"
        assert iter_renders[0] == 2  # Length changed


class TestInPlaceOperators:
    """Tests for in-place operators."""

    def test_list_iadd(self) -> None:
        """
        Verify that in-place list concatenation (+=) marks iteration dependencies so components that iterate the list are re-rendered when the list changes.
        
        Initial render increments the render counter once; after performing `state.items += [3, 4]`, a subsequent render increments the counter again and the list becomes `[1, 2, 3, 4]`.
        """

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [1, 2]

        renders = [0]

        @component
        def IterViewer() -> None:
            """
            Increment the render counter and iterate over state.items to exercise iteration-based tracking.
            
            This function increments renders[0] and iterates through state.items so tests can observe renders triggered by changes to the collection.
            """
            renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.items += [3, 4]
        render(ctx)
        assert renders[0] == 2
        assert list(state.items) == [1, 2, 3, 4]

    def test_list_imul(self) -> None:
        """
        Verify that in-place list multiplication (list *= n) marks iteration dependencies and causes a re-render.
        
        Renders a component that iterates over `state.items`, performs `state.items *= 2`, and asserts the component re-renders once and the list becomes duplicated accordingly.
        """

        @dataclass
        class MyState(Stateful):
            items: list[int] = field(default_factory=list)

        state = MyState()
        state.items = [1, 2]

        renders = [0]

        @component
        def IterViewer() -> None:
            """
            Increment the render counter and iterate over state.items to exercise iteration-based tracking.
            
            This function increments renders[0] and iterates through state.items so tests can observe renders triggered by changes to the collection.
            """
            renders[0] += 1
            for _ in state.items:
                pass

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.items *= 2
        render(ctx)
        assert renders[0] == 2
        assert list(state.items) == [1, 2, 1, 2]

    def test_set_ior(self) -> None:
        """
        Verify that in-place union (|=) on a tracked set marks iteration dependencies and causes dependent components to re-render.
        
        The test renders a component that iterates over a tracked `set`. After an initial render, performing `state.tags |= {"c", "d"}` adds elements to the set and should cause the component to re-render (renders count increments).
        """

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b"}

        renders = [0]

        @component
        def IterViewer() -> None:
            """
            Record a render and iterate over the tracked `state.tags` collection to register an iteration dependency.
            
            This increments the shared `renders[0]` counter and performs a no-op iteration over `state.tags`, allowing tests to observe re-renders triggered by changes to the collection.
            """
            renders[0] += 1
            for _ in state.tags:
                pass

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.tags |= {"c", "d"}
        render(ctx)
        assert renders[0] == 2

    def test_set_iand(self) -> None:
        """
        Verify that an in-place set intersection (the `&=` operator) marks iteration dependencies so components that iterate the set are re-rendered when membership changes.
        
        This test initializes a tracked set, renders a component that iterates over it, performs `state.tags &= {...}`, and asserts the component re-renders and the set's contents update accordingly.
        """

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b", "c"}

        renders = [0]

        @component
        def IterViewer() -> None:
            """
            Record a render and iterate over the tracked `state.tags` collection to register an iteration dependency.
            
            This increments the shared `renders[0]` counter and performs a no-op iteration over `state.tags`, allowing tests to observe re-renders triggered by changes to the collection.
            """
            renders[0] += 1
            for _ in state.tags:
                pass

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.tags &= {"a", "b"}
        render(ctx)
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
            """
            Increment the render counter and access the last element of the state's items.
            
            This function is used by tests to record a render and to create a dependency on the last element of `state.items` by reading `state.items[-1]`.
            """
            renders[0] += 1
            _ = state.items[-1]  # Read last item

        ctx = RenderSession(LastItemViewer)
        render(ctx)
        assert renders[0] == 1

        # Modify last item
        state.items[-1] = "z"
        render(ctx)
        assert renders[0] == 2