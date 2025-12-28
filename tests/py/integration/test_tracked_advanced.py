"""Integration tests for advanced tracked collection patterns and edge cases."""

from dataclasses import dataclass, field

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful


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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.data.popitem()
        render(ctx)
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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.tags.update({"b", "c", "d"})
        render(ctx)
        assert renders[0] == 2
        assert state.tags == {"a", "b", "c", "d"}


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

        ctx = RenderSession(App)
        render(ctx)
        assert iter_renders[0] == 1
        assert key_b_renders[0] == 1

        # setdefault with new key - both should re-render
        state.data.setdefault("b", 2)
        render(ctx)
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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        # setdefault with existing key - should NOT re-render
        result = state.data.setdefault("a", 999)
        assert result == 1  # Returns existing value
        render(ctx)
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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        # Update with kwargs
        state.data.update(b=2, c=3)
        render(ctx)
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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        # Update with iterable of tuples
        state.data.update([("b", 2), ("c", 3)])
        render(ctx)
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

        ctx = RenderSession(App)
        render(ctx)
        assert iter_renders[0] == 1
        assert a_renders[0] == 1

        # Update existing key only
        state.data.update({"a": 100})
        render(ctx)
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

        ctx = RenderSession(App)
        render(ctx)
        assert iter_renders[0] == 1
        assert c_renders[0] == 1

        # Keep only "a" and "b" - removes "c" and "d"
        state.tags.intersection_update({"a", "b"})
        render(ctx)
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

        ctx = RenderSession(BChecker)
        render(ctx)
        assert renders[0] == 1

        # Remove "b" via difference_update
        state.tags.difference_update({"b", "x"})  # "x" not in set
        render(ctx)
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

        ctx = RenderSession(App)
        render(ctx)
        assert b_renders[0] == 1
        assert c_renders[0] == 1

        # Symmetric difference: remove "b", add "c"
        state.tags.symmetric_difference_update({"b", "c"})
        render(ctx)
        assert b_renders[0] == 2  # "b" was removed
        assert c_renders[0] == 2  # "c" was added
        assert state.tags == {"a", "c"}


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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        state.items *= 0
        render(ctx)
        assert renders[0] == 2  # ITER_KEY dirty
        assert list(state.items) == []

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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        # Pop missing key with default - should NOT trigger re-render
        result = state.data.pop("missing", 99)
        assert result == 99
        render(ctx)
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

        ctx = RenderSession(IterViewer)
        render(ctx)
        assert renders[0] == 1

        # Discard non-existent item - should NOT trigger re-render
        state.tags.discard("nonexistent")
        render(ctx)
        assert renders[0] == 1  # No change
        assert state.tags == {"a", "b"}
