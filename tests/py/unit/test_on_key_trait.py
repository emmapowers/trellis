"""Tests for OnKeyTrait — focus-scoped key handling."""

from __future__ import annotations

from trellis.core import component
from trellis.core.keys import KeyFilter, KeySequence, sequence
from trellis.core.rendering.on_key_trait import _resolve_ignore_in_inputs
from trellis.widgets.basic import Label


def _noop():
    pass


class TestOnKeyChaining:
    def test_returns_self(self, rendered):
        @component
        def Comp():
            el = Label(text="test").on_key("Enter", _noop)
            # Should return the element for chaining
            assert el is not None

        rendered(Comp)

    def test_multiple_on_key_calls(self, rendered):
        @component
        def Comp():
            Label(text="test").on_key("Enter", _noop).on_key("Escape", _noop)

        result = rendered(Comp)
        label_el = result.session.elements.get(result.root_element.child_ids[0])
        assert label_el is not None
        filters = label_el.props.get("__key_filters__")
        assert filters is not None
        assert len(filters) == 2


class TestOnKeySerialization:
    def test_enter_key_serializes(self, rendered):
        @component
        def Comp():
            Label(text="test").on_key("Enter", _noop)

        result = rendered(Comp)
        label_el = result.session.elements.get(result.root_element.child_ids[0])
        filters = label_el.props["__key_filters__"]
        assert len(filters) == 1
        assert filters[0]["filter"]["key"] == "Enter"

    def test_sequence_serializes(self, rendered):
        @component
        def Comp():
            Label(text="test").on_key(sequence("G", "G"), _noop)

        result = rendered(Comp)
        label_el = result.session.elements.get(result.root_element.child_ids[0])
        filters = label_el.props["__key_filters__"]
        assert "sequence" in filters[0]
        assert len(filters[0]["sequence"]["steps"]) == 2

    def test_options_serialize(self, rendered):
        @component
        def Comp():
            Label(text="test").on_key(
                "Enter",
                _noop,
                event_type="keyup",
                require_reset=False,
                ignore_in_inputs=True,
            )

        result = rendered(Comp)
        label_el = result.session.elements.get(result.root_element.child_ids[0])
        f = label_el.props["__key_filters__"][0]
        assert f["event_type"] == "keyup"
        assert f["require_reset"] is False
        assert f["ignore_in_inputs"] is True

    def test_disabled_excluded(self, rendered):
        @component
        def Comp():
            Label(text="test").on_key("Enter", _noop, enabled=False)

        result = rendered(Comp)
        label_el = result.session.elements.get(result.root_element.child_ids[0])
        assert "__key_filters__" not in label_el.props


class TestSmartIgnoreDefaults:
    def test_bare_key_ignored_in_inputs(self):
        assert _resolve_ignore_in_inputs(None, KeyFilter(key="K")) is True

    def test_mod_combo_fires_in_inputs(self):
        assert _resolve_ignore_in_inputs(None, KeyFilter(key="S", mod=True)) is False

    def test_ctrl_combo_fires_in_inputs(self):
        assert _resolve_ignore_in_inputs(None, KeyFilter(key="S", ctrl=True)) is False

    def test_meta_combo_fires_in_inputs(self):
        assert _resolve_ignore_in_inputs(None, KeyFilter(key="S", meta=True)) is False

    def test_escape_fires_in_inputs(self):
        assert _resolve_ignore_in_inputs(None, KeyFilter(key="Escape")) is False

    def test_sequence_ignored_in_inputs(self):
        ks = KeySequence(steps=(KeyFilter(key="G"), KeyFilter(key="G")))
        assert _resolve_ignore_in_inputs(None, ks) is True

    def test_explicit_override(self):
        assert _resolve_ignore_in_inputs(False, KeyFilter(key="K")) is False
        assert _resolve_ignore_in_inputs(True, KeyFilter(key="S", mod=True)) is True
