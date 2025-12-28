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

    def test_mutable_is_not_hashable(self) -> None:
        """Mutable cannot be hashed (snapshot makes equality value-dependent)."""

        @dataclass
        class State(Stateful):
            value: int = 0

        state = State()
        m = Mutable(state, "value")

        import pytest

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


class TestMutableRerender:
    """Tests for mutable bindings across re-renders.

    These tests verify that when state changes via a mutable callback,
    the next render produces an update patch with the new value.
    This is critical for two-way data binding to work correctly.
    """

    def test_checkbox_rerender_sends_updated_value(self) -> None:
        """After mutable callback changes state, re-render should send update patch.

        This test reproduces a bug where:
        1. Initial render: Checkbox with checked=False
        2. Callback invoked: state.checked = True
        3. Re-render: Should produce UpdatePatch with checked=True
        4. Bug: No patch produced because Mutable equality ignores value
        """
        from trellis.core.rendering.patches import RenderUpdatePatch
        from trellis.platforms.common.serialization import serialize_node

        @dataclass
        class State(Stateful):
            checked: bool = False

        state_ref: list[State] = []
        checkbox_id: list[str] = []

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            state_ref.append(state)
            node = w.Checkbox(checked=mutable(state.checked), label="Test")
            checkbox_id.append(node.id)

        ctx = RenderSession(TestComponent)

        # Initial render
        initial_patches = render(ctx)
        assert len(initial_patches) > 0

        # Get the checkbox's initial serialized value
        checkbox_node = ctx.elements.get(checkbox_id[0])
        assert checkbox_node is not None
        initial_serialized = serialize_node(checkbox_node, ctx)
        assert initial_serialized["props"]["checked"]["value"] is False

        # Simulate user clicking checkbox - invoke the mutable callback
        checked_prop = initial_serialized["props"]["checked"]
        cb = get_callback_from_id(ctx, checked_prop["__mutable__"])
        cb(True)

        # Verify state changed
        assert state_ref[0].checked is True

        # Re-render should produce an update patch for the checkbox
        update_patches = render(ctx)

        # Find the update patch for the checkbox
        checkbox_update = None
        for patch in update_patches:
            if isinstance(patch, RenderUpdatePatch) and patch.node_id == checkbox_id[0]:
                checkbox_update = patch
                break

        assert checkbox_update is not None, (
            "Expected RenderUpdatePatch for Checkbox after mutable callback, "
            f"but got patches: {update_patches}"
        )
        assert checkbox_update.props is not None, "Expected props in update patch"
        # Patch props contain raw Mutable objects, not serialized dicts
        checked_mutable = checkbox_update.props["checked"]
        assert isinstance(checked_mutable, Mutable)
        assert checked_mutable.value is True

    def test_text_input_rerender_sends_updated_value(self) -> None:
        """After mutable callback changes state, TextInput re-render should send update."""
        from trellis.core.rendering.patches import RenderUpdatePatch
        from trellis.platforms.common.serialization import serialize_node

        @dataclass
        class State(Stateful):
            text: str = "initial"

        state_ref: list[State] = []
        input_id: list[str] = []

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            state_ref.append(state)
            node = w.TextInput(value=mutable(state.text))
            input_id.append(node.id)

        ctx = RenderSession(TestComponent)

        # Initial render
        render(ctx)

        # Get initial serialized value
        input_node = ctx.elements.get(input_id[0])
        initial_serialized = serialize_node(input_node, ctx)
        assert initial_serialized["props"]["value"]["value"] == "initial"

        # Invoke mutable callback
        value_prop = initial_serialized["props"]["value"]
        cb = get_callback_from_id(ctx, value_prop["__mutable__"])
        cb("updated")

        assert state_ref[0].text == "updated"

        # Re-render should produce update patch
        update_patches = render(ctx)

        input_update = None
        for patch in update_patches:
            if isinstance(patch, RenderUpdatePatch) and patch.node_id == input_id[0]:
                input_update = patch
                break

        assert input_update is not None, (
            "Expected RenderUpdatePatch for TextInput after mutable callback"
        )
        assert input_update.props is not None
        # Patch props contain raw Mutable objects, not serialized dicts
        value_mutable = input_update.props["value"]
        assert isinstance(value_mutable, Mutable)
        assert value_mutable.value == "updated"

    def test_slider_rerender_sends_updated_value(self) -> None:
        """After mutable callback changes state, Slider re-render should send update."""
        from trellis.core.rendering.patches import RenderUpdatePatch
        from trellis.platforms.common.serialization import serialize_node

        @dataclass
        class State(Stateful):
            value: float = 50.0

        state_ref: list[State] = []
        slider_id: list[str] = []

        @component
        def TestComponent() -> None:
            from trellis import widgets as w

            state = State()
            state_ref.append(state)
            node = w.Slider(value=mutable(state.value), min=0, max=100)
            slider_id.append(node.id)

        ctx = RenderSession(TestComponent)

        # Initial render
        render(ctx)

        # Get initial serialized value
        slider_node = ctx.elements.get(slider_id[0])
        initial_serialized = serialize_node(slider_node, ctx)
        assert initial_serialized["props"]["value"]["value"] == 50.0

        # Invoke mutable callback
        value_prop = initial_serialized["props"]["value"]
        cb = get_callback_from_id(ctx, value_prop["__mutable__"])
        cb(75.0)

        assert state_ref[0].value == 75.0

        # Re-render should produce update patch
        update_patches = render(ctx)

        slider_update = None
        for patch in update_patches:
            if isinstance(patch, RenderUpdatePatch) and patch.node_id == slider_id[0]:
                slider_update = patch
                break

        assert slider_update is not None, (
            "Expected RenderUpdatePatch for Slider after mutable callback"
        )
        assert slider_update.props is not None
        # Patch props contain raw Mutable objects, not serialized dicts
        value_mutable = slider_update.props["value"]
        assert isinstance(value_mutable, Mutable)
        assert value_mutable.value == 75.0
