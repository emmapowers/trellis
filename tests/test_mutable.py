"""Tests for trellis.core.mutable module."""

from dataclasses import dataclass

import pytest

from trellis.core.composition_component import component
from trellis.core.mutable import Mutable, mutable
from trellis.core.rendering import RenderTree
from trellis.core.state import Stateful


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

    def test_hash_same_reference(self) -> None:
        """Same owner and attr produce same hash."""

        @dataclass
        class State(Stateful):
            value: str = ""

        state = State()
        m1 = Mutable(state, "value")
        m2 = Mutable(state, "value")
        assert hash(m1) == hash(m2)

    def test_hash_different_attr(self) -> None:
        """Different attrs produce different hashes."""

        @dataclass
        class State(Stateful):
            a: int = 0
            b: int = 0

        state = State()
        m1 = Mutable(state, "a")
        m2 = Mutable(state, "b")
        assert hash(m1) != hash(m2)

    def test_hash_different_owner(self) -> None:
        """Different owners produce different hashes."""

        @dataclass
        class State(Stateful):
            value: int = 0

        state1 = State()
        state2 = State()
        m1 = Mutable(state1, "value")
        m2 = Mutable(state2, "value")
        assert hash(m1) != hash(m2)

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
        """Comparing Mutable to non-Mutable returns NotImplemented."""

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

    def test_mutable_is_hashable(self) -> None:
        """Mutable can be used in sets and as dict keys."""

        @dataclass
        class State(Stateful):
            value: int = 0

        state = State()
        m1 = Mutable(state, "value")
        m2 = Mutable(state, "value")

        # Can use in set
        s = {m1, m2}
        assert len(s) == 1

        # Can use as dict key
        d = {m1: "hello"}
        assert d[m2] == "hello"


class TestMutableFunction:
    """Tests for the mutable() function."""

    def test_mutable_captures_property_access(self) -> None:
        """mutable() captures the reference from a Stateful property access."""

        @dataclass
        class State(Stateful):
            name: str = "hello"

        captured: list[Mutable[str]] = []

        @component
        def TestComponent() -> None:
            state = State()
            m = mutable(state.name)
            captured.append(m)

        ctx = RenderTree(TestComponent)
        ctx.render()

        assert len(captured) == 1
        assert captured[0].value == "hello"

    def test_mutable_outside_render_raises(self) -> None:
        """mutable() raises TypeError outside render context."""

        @dataclass
        class State(Stateful):
            value: int = 0

        state = State()
        with pytest.raises(TypeError, match="must be called immediately after"):
            mutable(state.value)

    def test_mutable_with_non_property_value_raises(self) -> None:
        """mutable() raises TypeError if value doesn't match last access."""

        @dataclass
        class State(Stateful):
            value: int = 10

        @component
        def TestComponent() -> None:
            state = State()
            _ = state.value  # Access property
            mutable(42)  # But pass different value

        ctx = RenderTree(TestComponent)
        with pytest.raises(TypeError, match="must be called immediately after"):
            ctx.render()

    def test_mutable_with_plain_variable_raises(self) -> None:
        """mutable() raises TypeError with plain variable (no property access)."""

        @component
        def TestComponent() -> None:
            x = 42
            mutable(x)

        ctx = RenderTree(TestComponent)
        with pytest.raises(TypeError, match="must be called immediately after"):
            ctx.render()

    def test_mutable_clears_after_capture(self) -> None:
        """mutable() clears the recorded access so it can't be reused."""
        from trellis.core.mutable import _last_property_access

        @dataclass
        class State(Stateful):
            value: int = 10

        captured_value: list[int] = []

        @component
        def TestComponent() -> None:
            state = State()
            val = state.value  # Record access
            captured_value.append(val)
            mutable(val)  # First capture consumes the recorded access
            # Now _last_property_access should be None
            mutable(val)  # Should fail - no recorded access

        ctx = RenderTree(TestComponent)
        with pytest.raises(TypeError, match="must be called immediately after"):
            ctx.render()

    def test_mutable_works_with_new_access(self) -> None:
        """mutable() works if you access the property again."""

        @dataclass
        class State(Stateful):
            value: int = 10

        captured: list[Mutable[int]] = []

        @component
        def TestComponent() -> None:
            state = State()
            captured.append(mutable(state.value))  # First capture
            captured.append(mutable(state.value))  # New access, new capture

        ctx = RenderTree(TestComponent)
        ctx.render()

        assert len(captured) == 2
        assert captured[0] == captured[1]  # Same reference


class TestMutableSerialization:
    """Tests for Mutable serialization."""

    def test_mutable_serializes_with_callback(self) -> None:
        """Mutable props serialize to __mutable__ format with callback."""
        from trellis.core.serialization import serialize_node

        @dataclass
        class State(Stateful):
            text: str = "hello"

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            w.TextInput(value=mutable(state.text))

        ctx = RenderTree(TestComponent)
        result = ctx.render()

        # Find the TextInput node
        text_input = result["children"][0]
        assert text_input["type"] == "TextInput"

        # Check value prop has __mutable__ format
        value_prop = text_input["props"]["value"]
        assert "__mutable__" in value_prop
        assert "value" in value_prop
        assert value_prop["value"] == "hello"

    def test_mutable_callback_updates_state(self) -> None:
        """The mutable callback updates the underlying state."""
        from trellis.core.serialization import serialize_node

        @dataclass
        class State(Stateful):
            text: str = "hello"

        state_ref: list[State] = []

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            state_ref.append(state)
            w.TextInput(value=mutable(state.text))

        ctx = RenderTree(TestComponent)
        result = ctx.render()

        # Get the callback ID
        text_input = result["children"][0]
        cb_id = text_input["props"]["value"]["__mutable__"]

        # Invoke the callback
        callback = ctx.get_callback(cb_id)
        assert callback is not None
        callback("world")

        # State should be updated
        assert state_ref[0].text == "world"
