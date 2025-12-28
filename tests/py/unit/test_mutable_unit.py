"""Unit tests for Mutable class - tests in isolation without render context."""

from dataclasses import dataclass

import pytest

from trellis.core.state.mutable import Mutable
from trellis.core.state.stateful import Stateful


class TestMutableClass:
    """Tests for the Mutable class."""

    def test_value_getter(self) -> None:
        """Mutable.value returns the current property value."""

        @dataclass
        class State(Stateful):
            count: int = 10

        state = State()
        m = Mutable(state, "count")
        assert m.value == 10

    def test_value_setter(self) -> None:
        """Mutable.value setter updates the property."""

        @dataclass
        class State(Stateful):
            count: int = 10

        state = State()
        m = Mutable(state, "count")
        m.value = 42
        assert state.count == 42
        assert m.value == 42

    def test_equality_same_reference(self) -> None:
        """Mutables with same owner and attr are equal."""

        @dataclass
        class State(Stateful):
            value: str = ""

        state = State()
        m1 = Mutable(state, "value")
        m2 = Mutable(state, "value")
        assert m1 == m2

    def test_equality_different_attr(self) -> None:
        """Mutables with different attrs are not equal."""

        @dataclass
        class State(Stateful):
            a: int = 0
            b: int = 0

        state = State()
        m1 = Mutable(state, "a")
        m2 = Mutable(state, "b")
        assert m1 != m2

    def test_equality_different_owner(self) -> None:
        """Mutables with different owners are not equal."""

        @dataclass
        class State(Stateful):
            value: int = 0

        state1 = State()
        state2 = State()
        m1 = Mutable(state1, "value")
        m2 = Mutable(state2, "value")
        assert m1 != m2

    def test_equality_with_non_mutable(self) -> None:
        """
        Verify that comparing a Mutable instance with a non-Mutable value is treated as unequal.
        
        This ensures the Mutable's equality machinery defers to Python's comparison protocol so that comparisons with unrelated types do not raise and result in inequality.
        """

        @dataclass
        class State(Stateful):
            value: int = 10

        state = State()
        m = Mutable(state, "value")
        # Should not raise, returns NotImplemented which Python handles
        assert m != 10
        assert m != "value"

    def test_repr(self) -> None:
        """Mutable has useful repr."""

        @dataclass
        class State(Stateful):
            name: str = "test"

        state = State()
        m = Mutable(state, "name")
        assert repr(m) == "Mutable(name='test')"

    def test_mutable_is_not_hashable(self) -> None:
        """Mutable cannot be hashed (snapshot makes equality value-dependent)."""

        @dataclass
        class State(Stateful):
            value: int = 0

        state = State()
        m = Mutable(state, "value")

        with pytest.raises(TypeError, match="unhashable type"):
            hash(m)


class TestMutableSnapshot:
    """Tests for Mutable snapshot behavior.

    Mutable captures a snapshot of the value at creation time. This snapshot
    is used for equality comparison to detect changes across renders, while
    reads/writes still use the live state value.
    """

    def test_snapshot_captured_at_creation(self) -> None:
        """Mutable captures value snapshot at creation time."""

        @dataclass
        class State(Stateful):
            count: int = 10

        state = State()
        m = Mutable(state, "count")

        # Snapshot should be accessible and match initial value
        assert m.snapshot == 10

    def test_snapshot_unchanged_after_state_modification(self) -> None:
        """Snapshot doesn't change when state is modified directly."""

        @dataclass
        class State(Stateful):
            count: int = 10

        state = State()
        m = Mutable(state, "count")

        # Modify state directly
        state.count = 99

        # Snapshot should still be the original value
        assert m.snapshot == 10
        # But live read returns new value
        assert m.value == 99

    def test_snapshot_unchanged_after_mutable_set(self) -> None:
        """Snapshot doesn't change when value is set via Mutable."""

        @dataclass
        class State(Stateful):
            count: int = 10

        state = State()
        m = Mutable(state, "count")

        # Set via mutable
        m.value = 42

        # State should be updated
        assert state.count == 42
        # Live read should return new value
        assert m.value == 42
        # But snapshot should still be original
        assert m.snapshot == 10

    def test_equality_compares_snapshots(self) -> None:
        """Two Mutables are equal only if their snapshots match."""

        @dataclass
        class State(Stateful):
            count: int = 10

        state = State()

        # Create first mutable when count=10
        m1 = Mutable(state, "count")
        assert m1.snapshot == 10

        # Change state
        state.count = 20

        # Create second mutable when count=20
        m2 = Mutable(state, "count")
        assert m2.snapshot == 20

        # Same owner and attr, but different snapshots -> not equal
        assert m1 != m2

    def test_equality_same_snapshot_same_binding(self) -> None:
        """Mutables with same binding and same snapshot are equal."""

        @dataclass
        class State(Stateful):
            count: int = 10

        state = State()

        # Create two mutables at the same time (same snapshot)
        m1 = Mutable(state, "count")
        m2 = Mutable(state, "count")

        assert m1 == m2

    def test_value_read_is_live_not_snapshot(self) -> None:
        """Reading value returns live state, not snapshot."""

        @dataclass
        class State(Stateful):
            count: int = 10

        state = State()
        m = Mutable(state, "count")

        # Initial read matches snapshot
        assert m.value == 10
        assert m.snapshot == 10

        # Modify state externally
        state.count = 999

        # Live read returns new value
        assert m.value == 999
        # Snapshot unchanged
        assert m.snapshot == 10