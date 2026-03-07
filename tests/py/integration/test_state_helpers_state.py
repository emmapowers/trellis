"""Integration tests for trellis.state.state()."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.conftest import render_to_tree
from trellis import component, mutable, state
from trellis import widgets as w
from trellis.core.rendering.session import RenderSession
from trellis.platforms.common.serialization import parse_callback_id
from trellis.state import StateCell
from trellis.state import state as package_state

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
        """state(initial) returns a stable cell whose value survives rerenders."""
        observed_values: list[int] = []
        cell_ids: list[int] = []
        count_cell: list[StateCell[int]] = []

        @component
        def Counter() -> None:
            count = state(0)
            count_cell[:] = [count]
            cell_ids.append(id(count))
            observed_values.append(count.value)

        capture = capture_patches(Counter)
        capture.render()

        count_cell[0].set(3)
        capture.render()

        assert observed_values == [0, 3]
        assert cell_ids[0] == cell_ids[1]

    def test_state_factory_called_once_per_mount_and_recreates_on_remount(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """state(factory=...) runs once per mount and again after remount."""
        show_child = [True]
        factory_calls: list[int] = []
        observed_values: list[int] = []
        cell_ids: list[int] = []
        child_cell: list[StateCell[int]] = []

        def make_value() -> int:
            factory_calls.append(len(factory_calls) + 1)
            return factory_calls[-1]

        @component
        def Child() -> None:
            cell = state(factory=make_value)
            child_cell[:] = [cell]
            cell_ids.append(id(cell))
            observed_values.append(cell.value)

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(App)
        capture.render()

        child_cell[0].set(10)
        capture.render()

        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        show_child[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert factory_calls == [1, 2]
        assert observed_values == [1, 10, 2]
        assert cell_ids[0] == cell_ids[1]
        assert cell_ids[2] != cell_ids[0]

    def test_multiple_state_calls_are_slot_stable_and_independent(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Multiple state() calls in one component keep stable, independent slots."""
        first_ids: list[int] = []
        second_ids: list[int] = []
        observed_pairs: list[tuple[str, str]] = []
        cells: list[StateCell[str]] = []

        @component
        def App() -> None:
            first = state("alpha")
            second = state("beta")
            cells[:] = [first, second]
            first_ids.append(id(first))
            second_ids.append(id(second))
            observed_pairs.append((first.value, second.value))

        capture = capture_patches(App)
        capture.render()

        cells[0].set("updated")
        capture.render()

        assert observed_pairs == [("alpha", "beta"), ("updated", "beta")]
        assert first_ids[0] == first_ids[1]
        assert second_ids[0] == second_ids[1]
        assert first_ids[0] != second_ids[0]

    def test_mutable_bindings_work_with_state_cell_values(self) -> None:
        """mutable(cell.value) works with common widget bindings."""
        text_cell: list[StateCell[str]] = []
        enabled_cell: list[StateCell[bool]] = []
        slider_cell: list[StateCell[float]] = []

        @component
        def App() -> None:
            text = state("hello")
            enabled = state(False)
            slider = state(12.5)

            text_cell[:] = [text]
            enabled_cell[:] = [enabled]
            slider_cell[:] = [slider]

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

        assert text_cell[0].value == "world"
        assert enabled_cell[0].value is True
        assert slider_cell[0].value == 88.0

    def test_state_is_reexported_from_root_and_package(self, rendered) -> None:
        """trellis and trellis.state expose the helper API."""
        captured: list[StateCell[str]] = []

        @component
        def App() -> None:
            captured.append(state("hello"))

        rendered(App)

        assert state is package_state
        assert isinstance(captured[0], StateCell)
