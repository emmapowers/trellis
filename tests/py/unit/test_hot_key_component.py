"""Tests for HotKey — mount-scoped global keyboard shortcut."""

from __future__ import annotations

from trellis.core import component
from trellis.core.keys import sequence
from trellis.widgets.hot_key import HotKey


def _noop():
    pass


class TestHotKeyRendering:
    def test_basic_hotkey(self, rendered):
        @component
        def Comp():
            HotKey(filter="Mod+S", handler=_noop)

        result = rendered(Comp)
        hotkey_el = result.session.elements.get(result.root_element.child_ids[0])
        assert hotkey_el is not None
        filters = hotkey_el.props.get("__global_key_filters__")
        assert filters is not None
        assert len(filters) == 1
        assert filters[0]["filter"]["key"] == "S"
        assert filters[0]["filter"]["mod"] is True

    def test_sequence_hotkey(self, rendered):
        @component
        def Comp():
            HotKey(filter=sequence("G", "G"), handler=_noop)

        result = rendered(Comp)
        hotkey_el = result.session.elements.get(result.root_element.child_ids[0])
        filters = hotkey_el.props["__global_key_filters__"]
        assert "sequence" in filters[0]
        assert len(filters[0]["sequence"]["steps"]) == 2

    def test_disabled_produces_no_filters(self, rendered):
        @component
        def Comp():
            HotKey(filter="Mod+S", handler=_noop, enabled=False)

        result = rendered(Comp)
        hotkey_el = result.session.elements.get(result.root_element.child_ids[0])
        assert "__global_key_filters__" not in hotkey_el.props

    def test_depth_included(self, rendered):
        @component
        def Comp():
            HotKey(filter="Escape", handler=_noop)

        result = rendered(Comp)
        hotkey_el = result.session.elements.get(result.root_element.child_ids[0])
        filters = hotkey_el.props["__global_key_filters__"]
        assert "depth" in filters[0]
        assert isinstance(filters[0]["depth"], int)
