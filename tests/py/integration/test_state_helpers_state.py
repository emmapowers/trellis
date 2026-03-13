"""Integration tests for trellis.state.state_var()."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.conftest import render_to_tree
from trellis import component, mutable, state_var
from trellis import widgets as w
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.serialization import parse_callback_id
from trellis.state import StateVar
from trellis.state import state_var as package_state_var

if TYPE_CHECKING:
    from tests.conftest import PatchCapture


def _get_callback(session: RenderSession, callback_id: str):
    element_id, prop_name = parse_callback_id(callback_id)
    callback = session.get_callback(element_id, prop_name)
    assert callback is not None
    return callback


class TestStateHelper:
    def test_state_value_persists_across_rerenders(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """state_var(initial) returns a stable object whose value survives rerenders."""
        observed_values: list[int] = []
        state_var_ids: list[int] = []
        count_state_var: list[StateVar[int]] = []

        @component
        def Counter() -> None:
            count = state_var(0)
            count_state_var[:] = [count]
            state_var_ids.append(id(count))
            observed_values.append(count.value)

        capture = capture_patches(Counter)
        capture.render()

        count_state_var[0].set(3)
        capture.render()

        assert observed_values == [0, 3]
        assert state_var_ids[0] == state_var_ids[1]

    def test_state_factory_called_once_per_mount_and_recreates_on_remount(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """state_var(factory=...) runs once per mount and again after remount."""
        show_child = [True]
        factory_calls: list[int] = []
        observed_values: list[int] = []
        state_var_ids: list[int] = []
        child_state_var: list[StateVar[int]] = []

        def make_value() -> int:
            factory_calls.append(len(factory_calls) + 1)
            return factory_calls[-1]

        @component
        def Child() -> None:
            value = state_var(factory=make_value)
            child_state_var[:] = [value]
            state_var_ids.append(id(value))
            observed_values.append(value.value)

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(App)
        capture.render()

        child_state_var[0].set(10)
        capture.render()

        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        show_child[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert factory_calls == [1, 2]
        assert observed_values == [1, 10, 2]
        assert state_var_ids[0] == state_var_ids[1]
        assert state_var_ids[2] != state_var_ids[0]

    def test_multiple_state_calls_are_slot_stable_and_independent(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Multiple state_var() calls in one component keep stable, independent slots."""
        first_ids: list[int] = []
        second_ids: list[int] = []
        observed_pairs: list[tuple[str, str]] = []
        state_vars: list[StateVar[str]] = []

        @component
        def App() -> None:
            first = state_var("alpha")
            second = state_var("beta")
            state_vars[:] = [first, second]
            first_ids.append(id(first))
            second_ids.append(id(second))
            observed_pairs.append((first.value, second.value))

        capture = capture_patches(App)
        capture.render()

        state_vars[0].set("updated")
        capture.render()

        assert observed_pairs == [("alpha", "beta"), ("updated", "beta")]
        assert first_ids[0] == first_ids[1]
        assert second_ids[0] == second_ids[1]
        assert first_ids[0] != second_ids[0]

    def test_mutable_bindings_work_with_state_var_values(self) -> None:
        """mutable(state_var.value) works with common widget bindings."""
        text_state_var: list[StateVar[str]] = []
        enabled_state_var: list[StateVar[bool]] = []
        slider_state_var: list[StateVar[float]] = []

        @component
        def App() -> None:
            text = state_var("hello")
            enabled = state_var(False)
            slider = state_var(12.5)

            text_state_var[:] = [text]
            enabled_state_var[:] = [enabled]
            slider_state_var[:] = [slider]

            w.TextInput(value=mutable(text.value))
            w.Checkbox(checked=mutable(enabled.value), label="Enabled")
            w.Slider(value=mutable(slider.value), min=0, max=100)

        session = RenderSession(App)
        tree = render_to_tree(session)

        text_input = tree["children"][0]
        checkbox = tree["children"][1]
        slider = tree["children"][2]

        _get_callback(session, text_input["props"]["value"]["__mutable__"])("world")
        _get_callback(session, checkbox["props"]["checked"]["__mutable__"])(True)
        _get_callback(session, slider["props"]["value"]["__mutable__"])(88.0)

        assert text_state_var[0].value == "world"
        assert enabled_state_var[0].value is True
        assert slider_state_var[0].value == 88.0

    def test_state_var_is_reexported_from_root_and_package(self, rendered) -> None:
        """trellis and trellis.state expose the helper API."""
        captured: list[StateVar[str]] = []

        @component
        def App() -> None:
            captured.append(state_var("hello"))

        rendered(App)

        assert state_var is package_state_var
        assert isinstance(captured[0], StateVar)
