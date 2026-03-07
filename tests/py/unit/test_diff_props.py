"""Unit tests for diff_props."""

from __future__ import annotations

from unittest.mock import Mock

from trellis.core.rendering.element import _REMOVED, _RemovedType, diff_props
from trellis.core.state.mutable import Mutable


class TestDiffProps:
    def test_identical_props_returns_empty(self) -> None:
        props = {"a": 1, "b": "hello"}
        assert diff_props(props, props.copy()) == {}

    def test_added_key(self) -> None:
        old = {"a": 1}
        new = {"a": 1, "b": 2}
        assert diff_props(old, new) == {"b": 2}

    def test_removed_key(self) -> None:
        old = {"a": 1, "b": 2}
        new = {"a": 1}
        assert diff_props(old, new) == {"b": _REMOVED}

    def test_changed_value(self) -> None:
        old = {"a": 1}
        new = {"a": 2}
        assert diff_props(old, new) == {"a": 2}

    def test_changed_value_to_none(self) -> None:
        old = {"a": 1}
        new = {"a": None}
        result = diff_props(old, new)
        assert result == {"a": None}
        assert result["a"] is None
        assert result["a"] is not _REMOVED

    def test_mixed_changes(self) -> None:
        old = {"a": 1, "b": 2, "c": 3}
        new = {"a": 1, "b": 99, "d": 4}
        result = diff_props(old, new)
        assert result == {"b": 99, "c": _REMOVED, "d": 4}

    def test_callable_equivalence(self) -> None:
        old = {"on_click": lambda: None}
        new = {"on_click": lambda: None}
        assert diff_props(old, new) == {}

    def test_mutable_same_snapshot_no_diff(self) -> None:
        m1 = Mock(spec=Mutable)
        m2 = Mock(spec=Mutable)
        m1.__eq__ = Mock(return_value=True)
        old = {"value": m1}
        new = {"value": m2}
        assert diff_props(old, new) == {}

    def test_mutable_different_snapshot_has_diff(self) -> None:
        m1 = Mock(spec=Mutable)
        m2 = Mock(spec=Mutable)
        m1.__eq__ = Mock(return_value=False)
        old = {"value": m1}
        new = {"value": m2}
        assert diff_props(old, new) == {"value": m2}

    def test_empty_to_populated(self) -> None:
        result = diff_props({}, {"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_populated_to_empty(self) -> None:
        result = diff_props({"a": 1, "b": 2}, {})
        assert result == {"a": _REMOVED, "b": _REMOVED}

    def test_both_empty(self) -> None:
        assert diff_props({}, {}) == {}


class TestRemovedSentinel:
    def test_singleton(self) -> None:
        assert _RemovedType() is _RemovedType()
        assert _RemovedType() is _REMOVED

    def test_repr(self) -> None:
        assert repr(_REMOVED) == "_REMOVED"
