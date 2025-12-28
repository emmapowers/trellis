"""Integration tests for tracked collection mutations during render and guards."""

from dataclasses import dataclass, field

import pytest

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful
from trellis.core.state.tracked import TrackedDict, TrackedList, TrackedSet


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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.items += [3, 4]
        render(ctx)
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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.items *= 2
        render(ctx)
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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.tags |= {"c", "d"}
        render(ctx)
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
            renders[0] += 1
            _ = state.items[-1]  # Read last item

        ctx = RenderSession(LastItemViewer)
        render(ctx)
        assert renders[0] == 1

        # Modify last item
        state.items[-1] = "z"
        render(ctx)
        assert renders[0] == 2
