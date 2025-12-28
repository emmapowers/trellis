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
            """
            Component used in tests to iterate over state.data while recording renders.
            
            Increments the external render counter at each invocation and iterates over `state.data` to establish an iteration-based dependency for reactive tests.
            """
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
            """
            Component that iterates over the tracked set `state.tags` to record render occurrences.
            
            Increments the external render counter and iterates `state.tags` so the component's render depends on the collection's iteration.
            """
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
            """
            Component that increments a render counter and iterates over state.data to observe iteration-based reactivity.
            
            Increments iter_renders[0] as a side effect.
            """
            iter_renders[0] += 1
            for _ in state.data:
                pass

        @component
        def KeyBViewer() -> None:
            """
            Record a render and access the 'b' key of state.data to establish a reactive dependency.
            
            Increments the external counter key_b_renders[0] and reads state.data.get("b") so components observing this function react when key 'b' is added, removed, or changed.
            """
            key_b_renders[0] += 1
            _ = state.data.get("b")

        @component
        def App() -> None:
            """
            Compose a component tree that renders IterViewer followed by KeyBViewer.
            
            Used in tests to observe reactivity for dictionary iteration and for accessing the key "b".
            """
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
            """
            Component used in tests to iterate over state.data while recording renders.
            
            Increments the external render counter at each invocation and iterates over `state.data` to establish an iteration-based dependency for reactive tests.
            """
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
            """
            Component used in tests to iterate over state.data while recording renders.
            
            Increments the external render counter at each invocation and iterates over `state.data` to establish an iteration-based dependency for reactive tests.
            """
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
            """
            Component used in tests to iterate over state.data while recording renders.
            
            Increments the external render counter at each invocation and iterates over `state.data` to establish an iteration-based dependency for reactive tests.
            """
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
            """
            Component that increments a render counter and iterates over state.data to observe iteration-based reactivity.
            
            Increments iter_renders[0] as a side effect.
            """
            iter_renders[0] += 1
            for _ in state.data:
                pass

        @component
        def AViewer() -> None:
            """
            Increments the render counter and accesses state.data["a"] to register a dependency on the 'a' key for reactivity.
            """
            a_renders[0] += 1
            _ = state.data["a"]

        @component
        def App() -> None:
            """
            Compose the UI by instantiating IterViewer and AViewer components.
            
            This function creates the component tree used by tests to observe rendering and reactivity for iteration and key-specific viewers.
            """
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
            """
            Record a render and observe iteration over the state's tags set.
            
            Increments the external render counter and iterates over `state.tags` to establish an iteration dependency used by the test.
            """
            iter_renders[0] += 1
            for _ in state.tags:
                pass

        @component
        def CChecker() -> None:
            """
            Component that records a render and observes whether the tag "c" is present in state.tags.
            
            Increments the shared render counter and reads membership of "c" in state.tags to create a reactive dependency on that membership.
            """
            c_renders[0] += 1
            _ = "c" in state.tags

        @component
        def App() -> None:
            """
            Compose IterViewer and CChecker into a single component.
            
            This component mounts IterViewer (which observes iteration over a collection) and CChecker (which checks membership of "c") so they can be rendered together in tests verifying collection reactivity.
            """
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
        """
        Verify that removing items with `set.difference_update` causes dependent components to re-render.
        
        This test creates a tracked set containing {"a", "b", "c"}, renders a component that observes membership of "b", performs `difference_update({"b", "x"})`, and asserts the component re-renders and the set becomes {"a", "c"}.
        """

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b", "c"}

        renders = [0]

        @component
        def BChecker() -> None:
            """
            Component that observes whether the tag "b" is present in state.tags and increments the render counter.
            
            This function reads membership of "b" from the tracked set to establish a reactive dependency used by tests.
            """
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
        """
        Verify that symmetric_difference_update marks removed and added set items as dirty, causing dependent components to re-render.
        
        After performing symmetric_difference_update with {"b", "c"}, the component observing membership of "b" re-renders (due to removal), the component observing "c" re-renders (due to addition), and the set becomes {"a", "c"}.
        """

        @dataclass
        class MyState(Stateful):
            tags: set[str] = field(default_factory=set)

        state = MyState()
        state.tags = {"a", "b"}

        b_renders = [0]
        c_renders = [0]

        @component
        def BChecker() -> None:
            """
            Increment the B-render counter and read whether 'b' is present in state.tags.
            
            This increments b_renders[0] and performs a membership check for "b" in the tracked set to establish a dependency on that membership.
            """
            b_renders[0] += 1
            _ = "b" in state.tags

        @component
        def CChecker() -> None:
            """
            Component that records a render and observes whether the tag "c" is present in state.tags.
            
            Increments the shared render counter and reads membership of "c" in state.tags to create a reactive dependency on that membership.
            """
            c_renders[0] += 1
            _ = "c" in state.tags

        @component
        def App() -> None:
            """
            Compose and render the BChecker and CChecker components within a single test component tree.
            """
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
        """
        Verifies that in-place list multiplication by zero empties the list and triggers a re-render.
        
        Asserts that `state.items *= 0` clears the list and marks the iteration dependency dirty so an observing component re-renders.
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
            Component that iterates over state.items to establish an iteration-based reactive dependency.
            
            Increments renders[0] each time it is executed.
            """
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
            """
            Component used in tests to iterate over state.data while recording renders.
            
            Increments the external render counter at each invocation and iterates over `state.data` to establish an iteration-based dependency for reactive tests.
            """
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
            """
            Component that iterates over the tracked set `state.tags` to record render occurrences.
            
            Increments the external render counter and iterates `state.tags` so the component's render depends on the collection's iteration.
            """
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