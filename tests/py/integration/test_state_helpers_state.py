"""Integration tests for trellis.state.state_var()."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from tests.conftest import render_to_tree
from trellis import component, mutable, state_var
from trellis import widgets as w
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession, set_render_session
from trellis.core.state import state_var as core_state_var
from trellis.platforms.common.serialization import parse_callback_id

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
        """state_var(initial) returns a stable value that survives rerenders."""
        observed_values: list[int] = []
        setters: list[Callable[[int], None]] = []

        @component
        def Counter() -> None:
            count = state_var(0)
            observed_values.append(count)

            def _set(v: int) -> None:
                nonlocal count
                count = v

            setters[:] = [_set]

        capture = capture_patches(Counter)
        capture.render()

        setters[0](3)
        capture.render()

        assert observed_values == [0, 3]

    def test_state_factory_called_once_per_mount_and_recreates_on_remount(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """state_var(factory=...) runs once per mount and again after remount."""
        show_child = [True]
        factory_calls: list[int] = []
        observed_values: list[int] = []
        setters: list[Callable[[int], None]] = []

        def make_value() -> int:
            factory_calls.append(len(factory_calls) + 1)
            return factory_calls[-1]

        @component
        def Child() -> None:
            value = state_var(factory=make_value)
            observed_values.append(value)

            def _set(v: int) -> None:
                nonlocal value
                value = v

            setters[:] = [_set]

        @component
        def App() -> None:
            if show_child[0]:
                Child()

        capture = capture_patches(App)
        capture.render()

        setters[0](10)
        capture.render()

        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        show_child[0] = True
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert factory_calls == [1, 2]
        assert observed_values == [1, 10, 2]

    def test_multiple_state_calls_are_slot_stable_and_independent(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Multiple state_var() calls in one component keep stable, independent slots."""
        observed_pairs: list[tuple[str, str]] = []
        setters: list[Callable[[str], None]] = []

        @component
        def App() -> None:
            first = state_var("alpha")
            second = state_var("beta")

            def _set_first(v: str) -> None:
                nonlocal first
                first = v

            setters[:] = [_set_first]
            observed_pairs.append((first, second))

        capture = capture_patches(App)
        capture.render()

        setters[0]("updated")
        capture.render()

        assert observed_pairs == [("alpha", "beta"), ("updated", "beta")]

    def test_mutable_bindings_work_with_state_var_values(self) -> None:
        """mutable(state_var_name) works with common widget bindings."""
        observed_text: list[str] = []
        observed_enabled: list[bool] = []
        observed_slider: list[float] = []

        @component
        def App() -> None:
            text = state_var("hello")
            enabled = state_var(False)
            slider = state_var(12.5)

            observed_text.append(text)
            observed_enabled.append(enabled)
            observed_slider.append(slider)

            w.TextInput(value=mutable(text))
            w.Checkbox(checked=mutable(enabled), label="Enabled")
            w.Slider(value=mutable(slider), min=0, max=100)

        session = RenderSession(App)
        set_render_session(session)
        tree = render_to_tree(session)

        text_input = tree["children"][0]
        checkbox = tree["children"][1]
        slider_el = tree["children"][2]

        _get_callback(session, text_input["props"]["value"]["__mutable__"])("world")
        _get_callback(session, checkbox["props"]["checked"]["__mutable__"])(True)
        _get_callback(session, slider_el["props"]["value"]["__mutable__"])(88.0)

        # Re-render to observe updated values
        render(session)

        assert observed_text == ["hello", "world"]
        assert observed_enabled == [False, True]
        assert observed_slider == [12.5, 88.0]

    def test_state_var_is_reexported_from_root_and_package(self, rendered) -> None:
        """trellis and trellis.state expose the helper API."""
        captured: list[str] = []

        @component
        def App() -> None:
            val = state_var("hello")
            captured.append(val)

        rendered(App)

        assert state_var is core_state_var
        assert captured[0] == "hello"
