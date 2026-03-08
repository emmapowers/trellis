"""Unit tests for Stateful tracked attribute detection."""

from __future__ import annotations

from dataclasses import dataclass

from trellis import Tracked as RootTracked
from trellis.core.state import Tracked as PackageTracked
from trellis.core.state.stateful import Stateful, Tracked, _is_tracked_attribute


class TestTrackedAttributeDetection:
    def test_tracked_is_reexported_from_root_and_package(self) -> None:
        assert RootTracked is PackageTracked is Tracked

    def test_public_annotated_attribute_is_tracked(self) -> None:
        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: int = 0

        assert _is_tracked_attribute(MyState, "value") is True

    def test_public_tracked_attribute_is_tracked(self) -> None:
        @dataclass(kw_only=True)
        class MyState(Stateful):
            value: Tracked[int] = 0

        assert _is_tracked_attribute(MyState, "value") is True

    def test_private_tracked_attribute_is_tracked(self) -> None:
        @dataclass(kw_only=True)
        class MyState(Stateful):
            _value: Tracked[int] = 0

        assert _is_tracked_attribute(MyState, "_value") is True

    def test_private_annotated_attribute_is_not_tracked(self) -> None:
        @dataclass(kw_only=True)
        class MyState(Stateful):
            _value: int = 0

        assert _is_tracked_attribute(MyState, "_value") is False

    def test_inherited_tracked_attribute_is_recognized(self) -> None:
        @dataclass(kw_only=True)
        class BaseState(Stateful):
            _value: Tracked[int] = 0

        @dataclass(kw_only=True)
        class ChildState(BaseState):
            other: int = 0

        assert _is_tracked_attribute(ChildState, "_value") is True
