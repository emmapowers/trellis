"""Unit tests for _RefHolder proxy and Ref base class."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from trellis.core.state.ref import Ref, _RefHolder
from trellis.core.state.stateful import Stateful


class MyRef(Ref):
    def close(self) -> str:
        return "closed"

    def value(self) -> int:
        return 42


class TestRefHolder:
    def test_ref_holder_falsy_when_empty(self) -> None:
        """Freshly created holder is falsy."""
        holder = _RefHolder(MyRef)
        assert not holder

    def test_ref_holder_truthy_when_attached(self) -> None:
        """Holder is truthy after _attach()."""
        holder = _RefHolder(MyRef)
        ref = MyRef()
        holder._attach(ref)
        assert holder

    def test_ref_holder_proxies_methods(self) -> None:
        """holder.close() delegates to ref.close()."""
        holder = _RefHolder(MyRef)
        ref = MyRef()
        holder._attach(ref)
        assert holder.close() == "closed"

    def test_ref_holder_raises_when_not_attached(self) -> None:
        """Attribute access on empty holder raises RuntimeError."""
        holder = _RefHolder(MyRef)
        with pytest.raises(RuntimeError, match="not attached"):
            holder.close()

    def test_ref_holder_type_checks_on_attach(self) -> None:
        """_attach(wrong_type) raises TypeError."""
        holder = _RefHolder(MyRef)
        with pytest.raises(TypeError):
            holder._attach("not a ref")  # type: ignore[arg-type]

    def test_ref_holder_detach(self) -> None:
        """After detach, holder is falsy and raises on access."""
        holder = _RefHolder(MyRef)
        ref = MyRef()
        holder._attach(ref)
        assert holder
        holder._detach()
        assert not holder
        with pytest.raises(RuntimeError, match="not attached"):
            holder.close()

    def test_ref_holder_bypasses_stateful_tracking(self) -> None:
        """Attach a Stateful, read tracked property through holder, verify no watchers."""

        @dataclass(kw_only=True)
        class TrackedState(Stateful):
            count: int = 0

        state = TrackedState()
        state.count = 5

        # Manually init _state_props so we can check watchers
        try:
            _ = state._state_props
        except AttributeError:
            pass

        holder: _RefHolder[TrackedState] = _RefHolder(TrackedState)
        holder._attach(state)

        # Access through holder — should bypass Stateful.__getattribute__
        val = holder.count
        assert val == 5

        # No watchers should have been registered
        if hasattr(state, "_state_props") and "count" in state._state_props:
            assert len(state._state_props["count"].watchers) == 0


class TestRefBaseClass:
    def test_ref_base_class_lifecycle_noop(self) -> None:
        """Ref has on_mount/on_unmount that are callable no-ops."""
        ref = Ref()
        # Should not raise
        ref.on_mount()
        ref.on_unmount()
