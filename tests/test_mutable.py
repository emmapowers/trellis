"""Tests for trellis.core.mutable module."""

from dataclasses import dataclass

import pytest

from tests.helpers import render_to_tree
from trellis.core.components.composition import component
from trellis.core.state.mutable import Mutable, callback, mutable
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.core.state.stateful import Stateful
from trellis.platforms.common.serialization import parse_callback_id


def get_callback_from_id(ctx: RenderSession, cb_id: str):
    """Helper to get callback using the new two-arg API."""
    node_id, prop_name = parse_callback_id(cb_id)
    return ctx.get_callback(node_id, prop_name)


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

        ctx = RenderSession(TestComponent)
        render(ctx)

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

        ctx = RenderSession(TestComponent)
        with pytest.raises(TypeError, match="must be called immediately after"):
            render(ctx)

    def test_mutable_with_plain_variable_raises(self) -> None:
        """mutable() raises TypeError with plain variable (no property access)."""

        @component
        def TestComponent() -> None:
            x = 42
            mutable(x)

        ctx = RenderSession(TestComponent)
        with pytest.raises(TypeError, match="must be called immediately after"):
            render(ctx)

    def test_mutable_clears_after_capture(self) -> None:
        """mutable() clears the recorded access so it can't be reused."""

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

        ctx = RenderSession(TestComponent)
        with pytest.raises(TypeError, match="must be called immediately after"):
            render(ctx)

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

        ctx = RenderSession(TestComponent)
        render(ctx)

        assert len(captured) == 2
        assert captured[0] == captured[1]  # Same reference


class TestMutableSerialization:
    """Tests for Mutable serialization."""

    def test_mutable_serializes_with_callback(self) -> None:
        """Mutable props serialize to __mutable__ format with callback."""
        from trellis.platforms.common.serialization import serialize_node

        @dataclass
        class State(Stateful):
            text: str = "hello"

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            w.TextInput(value=mutable(state.text))

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

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
        from trellis.platforms.common.serialization import serialize_node

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

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

        # Get the callback ID
        text_input = result["children"][0]
        cb_id = text_input["props"]["value"]["__mutable__"]

        # Invoke the callback
        callback = get_callback_from_id(ctx,cb_id)
        assert callback is not None
        callback("world")

        # State should be updated
        assert state_ref[0].text == "world"


class TestMutableWidgets:
    """Tests for widgets that support mutable bindings."""

    def test_number_input_with_mutable(self) -> None:
        """NumberInput accepts mutable value and updates state."""

        @dataclass
        class State(Stateful):
            count: float = 42.0

        state_ref: list[State] = []

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            state_ref.append(state)
            w.NumberInput(value=mutable(state.count))

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

        number_input = result["children"][0]
        assert number_input["type"] == "NumberInput"

        value_prop = number_input["props"]["value"]
        assert "__mutable__" in value_prop
        assert value_prop["value"] == 42.0

        # Update via callback
        callback = get_callback_from_id(ctx,value_prop["__mutable__"])
        callback(100.0)
        assert state_ref[0].count == 100.0

    def test_checkbox_with_mutable(self) -> None:
        """Checkbox accepts mutable checked and updates state."""

        @dataclass
        class State(Stateful):
            enabled: bool = False

        state_ref: list[State] = []

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            state_ref.append(state)
            w.Checkbox(checked=mutable(state.enabled), label="Test")

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

        checkbox = result["children"][0]
        assert checkbox["type"] == "Checkbox"

        checked_prop = checkbox["props"]["checked"]
        assert "__mutable__" in checked_prop
        assert checked_prop["value"] is False

        # Update via callback
        callback = get_callback_from_id(ctx,checked_prop["__mutable__"])
        callback(True)
        assert state_ref[0].enabled is True

    def test_select_with_mutable(self) -> None:
        """Select accepts mutable value and updates state."""

        @dataclass
        class State(Stateful):
            choice: str = "a"

        state_ref: list[State] = []

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            state_ref.append(state)
            w.Select(
                value=mutable(state.choice),
                options=[{"value": "a", "label": "A"}, {"value": "b", "label": "B"}],
            )

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

        select = result["children"][0]
        assert select["type"] == "Select"

        value_prop = select["props"]["value"]
        assert "__mutable__" in value_prop
        assert value_prop["value"] == "a"

        # Update via callback
        callback = get_callback_from_id(ctx,value_prop["__mutable__"])
        callback("b")
        assert state_ref[0].choice == "b"

    def test_slider_with_mutable(self) -> None:
        """Slider accepts mutable value and updates state."""

        @dataclass
        class State(Stateful):
            volume: float = 50.0

        state_ref: list[State] = []

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            state_ref.append(state)
            w.Slider(value=mutable(state.volume), min=0, max=100)

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

        slider = result["children"][0]
        assert slider["type"] == "Slider"

        value_prop = slider["props"]["value"]
        assert "__mutable__" in value_prop
        assert value_prop["value"] == 50.0

        # Update via callback
        callback = get_callback_from_id(ctx,value_prop["__mutable__"])
        callback(75.0)
        assert state_ref[0].volume == 75.0

    def test_tabs_with_mutable(self) -> None:
        """Tabs accepts mutable selected and updates state."""
        from trellis import widgets as w

        @dataclass
        class State(Stateful):
            tab: str = "first"

        state_ref: list[State] = []

        @component
        def TestComponent() -> None:
            state = State()
            state_ref.append(state)
            with w.Tabs(selected=mutable(state.tab)):
                with w.Tab(id="first", label="First"):
                    w.Label(text="First tab")
                with w.Tab(id="second", label="Second"):
                    w.Label(text="Second tab")

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

        tabs = result["children"][0]
        assert tabs["type"] == "Tabs"

        selected_prop = tabs["props"]["selected"]
        assert "__mutable__" in selected_prop
        assert selected_prop["value"] == "first"

        # Update via callback
        callback = get_callback_from_id(ctx,selected_prop["__mutable__"])
        callback("second")
        assert state_ref[0].tab == "second"

    def test_collapsible_with_mutable(self) -> None:
        """Collapsible accepts mutable expanded and updates state."""
        from trellis import widgets as w

        @dataclass
        class State(Stateful):
            is_open: bool = True

        state_ref: list[State] = []

        @component
        def TestComponent() -> None:
            state = State()
            state_ref.append(state)
            with w.Collapsible(title="Section", expanded=mutable(state.is_open)):
                w.Label(text="Content")

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

        collapsible = result["children"][0]
        assert collapsible["type"] == "Collapsible"

        expanded_prop = collapsible["props"]["expanded"]
        assert "__mutable__" in expanded_prop
        assert expanded_prop["value"] is True

        # Update via callback
        cb = get_callback_from_id(ctx,expanded_prop["__mutable__"])
        cb(False)
        assert state_ref[0].is_open is False


class TestCallbackFunction:
    """Tests for the callback() function."""

    def test_callback_captures_property_access(self) -> None:
        """callback() captures the reference from a Stateful property access."""

        @dataclass
        class State(Stateful):
            name: str = "hello"

        captured: list[Mutable[str]] = []
        handler_calls: list[str] = []

        def custom_handler(value: str) -> None:
            handler_calls.append(value)

        @component
        def TestComponent() -> None:
            state = State()
            m = callback(state.name, custom_handler)
            captured.append(m)

        ctx = RenderSession(TestComponent)
        render(ctx)

        assert len(captured) == 1
        assert captured[0].value == "hello"
        assert captured[0].on_change is custom_handler

    def test_callback_outside_render_raises(self) -> None:
        """callback() raises TypeError outside render context."""

        @dataclass
        class State(Stateful):
            value: int = 0

        state = State()
        with pytest.raises(TypeError, match="must be called immediately after"):
            callback(state.value, lambda v: None)

    def test_callback_with_non_property_value_raises(self) -> None:
        """callback() raises TypeError if value doesn't match last access."""

        @dataclass
        class State(Stateful):
            value: int = 10

        @component
        def TestComponent() -> None:
            state = State()
            _ = state.value  # Access property
            callback(42, lambda v: None)  # But pass different value

        ctx = RenderSession(TestComponent)
        with pytest.raises(TypeError, match="must be called immediately after"):
            render(ctx)

    def test_callback_serializes_with_custom_handler(self) -> None:
        """callback() serializes to __mutable__ format with custom handler."""

        @dataclass
        class State(Stateful):
            text: str = "hello"

        handler_calls: list[str] = []

        def custom_handler(value: str) -> None:
            handler_calls.append(value)

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            w.TextInput(value=callback(state.text, custom_handler))

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

        # Find the TextInput node
        text_input = result["children"][0]
        assert text_input["type"] == "TextInput"

        # Check value prop has __mutable__ format
        value_prop = text_input["props"]["value"]
        assert "__mutable__" in value_prop
        assert "value" in value_prop
        assert value_prop["value"] == "hello"

        # Invoke the callback - should call custom handler
        cb = get_callback_from_id(ctx,value_prop["__mutable__"])
        cb("world")
        assert handler_calls == ["world"]

    def test_callback_with_state_method(self) -> None:
        """callback() works with state methods for custom processing."""

        @dataclass
        class State(Stateful):
            name: str = ""

            def set_name(self, value: str) -> None:
                # Custom processing: strip and title case
                self.name = value.strip().title()

        state_ref: list[State] = []

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            state_ref.append(state)
            w.TextInput(value=callback(state.name, state.set_name))

        ctx = RenderSession(TestComponent)
        result = render_to_tree(ctx)

        text_input = result["children"][0]
        value_prop = text_input["props"]["value"]

        # Invoke callback with unprocessed input
        cb = get_callback_from_id(ctx,value_prop["__mutable__"])
        cb("  john doe  ")

        # Should be processed by custom handler
        assert state_ref[0].name == "John Doe"
