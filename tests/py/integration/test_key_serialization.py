"""Integration tests for key binding serialization."""

from __future__ import annotations

from trellis.core import component
from trellis.platforms.common.serialization import serialize_element
from trellis.widgets.basic import Label
from trellis.widgets.hot_key import HotKey


def _noop():
    pass


class TestOnKeySerialization:
    def test_key_filters_serialized_with_callback(self, rendered):
        """on_key produces __key_filters__ with callback refs."""

        @component
        def Comp():
            Label(text="test").on_key("Enter", _noop)

        result = rendered(Comp)
        tree = serialize_element(result.root_element, result.session)
        # Navigate to the Label's serialized props
        label_node = tree["children"][0]
        props = label_node["props"]
        assert "__key_filters__" in props
        filters = props["__key_filters__"]
        assert len(filters) == 1
        # Handler should be serialized as a callback ref
        assert "__callback__" in filters[0]["handler"]


class TestHotKeySerialization:
    def test_global_key_filters_serialized_with_callback(self, rendered):
        """HotKey produces __global_key_filters__ with callback refs."""

        @component
        def Comp():
            HotKey(filter="Mod+S", handler=_noop)

        result = rendered(Comp)
        tree = serialize_element(result.root_element, result.session)
        # HotKey is a CompositionComponent — its __global_key_filters__ should still serialize
        hotkey_node = tree["children"][0]
        props = hotkey_node["props"]
        assert "__global_key_filters__" in props
        filters = props["__global_key_filters__"]
        assert len(filters) == 1
        assert "__callback__" in filters[0]["handler"]

    def test_nested_hotkeys_have_increasing_depth(self, rendered):
        """Deeper HotKey components should have higher depth values."""

        @component
        def Inner():
            HotKey(filter="Escape", handler=_noop)

        @component
        def Comp():
            HotKey(filter="Escape", handler=_noop)
            Inner()

        result = rendered(Comp)
        # Find the two HotKey elements
        hotkey_ids = []
        for eid in result.session.elements:
            el = result.session.elements.get(eid)
            if el and "__global_key_filters__" in el.props:
                depth = el.props["__global_key_filters__"][0]["depth"]
                hotkey_ids.append((eid, depth))

        assert len(hotkey_ids) == 2
        depths = sorted(d for _, d in hotkey_ids)
        assert depths[0] < depths[1]


class TestBothApisOnSameTree:
    def test_on_key_and_hotkey_coexist(self, rendered):
        """Both .on_key() and HotKey() work on elements in the same tree."""

        @component
        def Comp():
            Label(text="test").on_key("Enter", _noop)
            HotKey(filter="Mod+S", handler=_noop)

        result = rendered(Comp)
        tree = serialize_element(result.root_element, result.session)

        # Label should have __key_filters__
        label_node = tree["children"][0]
        assert "__key_filters__" in label_node["props"]

        # HotKey should have __global_key_filters__
        hotkey_node = tree["children"][1]
        assert "__global_key_filters__" in hotkey_node["props"]
