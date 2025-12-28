"""Unit tests for TrackedList, TrackedDict, TrackedSet - basic operations without render context."""

from dataclasses import dataclass, field

import pytest

from trellis.core.state.stateful import Stateful
from trellis.core.state.tracked import TrackedDict, TrackedList, TrackedSet


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

    def test_list_negative_index_setitem(self) -> None:
        """Negative index assignment works correctly."""
        lst: TrackedList[str] = TrackedList(["a", "b", "c"])
        lst[-1] = "z"
        assert list(lst) == ["a", "b", "z"]

    def test_list_index_with_bounds(self) -> None:
        """index() with start/stop bounds works correctly."""
        lst: TrackedList[int] = TrackedList([1, 2, 1, 2, 1])
        assert lst.index(2) == 1  # First occurrence
        assert lst.index(2, 2) == 3  # Start at index 2
        assert lst.index(1, 2, 5) == 2  # Between indices 2 and 5

    def test_list_sort_with_reverse(self) -> None:
        """sort() with reverse=True works correctly."""
        lst: TrackedList[int] = TrackedList([3, 1, 2])
        lst.sort(reverse=True)
        assert list(lst) == [3, 2, 1]

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

    def test_update_multiple_iterables(self) -> None:
        """update() with multiple iterables works correctly."""
        s: TrackedSet[int] = TrackedSet({1, 2})
        s.update({3, 4}, {5, 6})
        assert s == {1, 2, 3, 4, 5, 6}


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
