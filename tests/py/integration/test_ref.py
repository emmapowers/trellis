"""Integration tests for the ref API (get_ref, set_ref, Element.ref)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from trellis.core.components.composition import component
from trellis.core.state.ref import Ref, _RefHolder, get_ref, set_ref
from trellis.core.state.stateful import Stateful

if TYPE_CHECKING:
    from tests.conftest import PatchCapture


# ---- Ref types for tests ----


class DialogRef(Ref):
    def __init__(self) -> None:
        self._open = False

    def open(self) -> None:
        self._open = True

    def close(self) -> None:
        self._open = False

    def is_open(self) -> bool:
        return self._open


# =============================================================================
# get_ref / set_ref basics
# =============================================================================


class TestGetRef:
    def test_get_ref_returns_falsy_holder(self, capture_patches: type[PatchCapture]) -> None:
        """Inside a component, get_ref(MyRef) returns a falsy holder."""
        holders: list[_RefHolder[DialogRef]] = []

        @component
        def Parent() -> None:
            holder = get_ref(DialogRef)
            holders.append(holder)

        capture = capture_patches(Parent)
        capture.render()

        assert len(holders) == 1
        assert not holders[0]

    def test_get_ref_cached_across_rerenders(self, capture_patches: type[PatchCapture]) -> None:
        """Same holder instance is returned on re-render."""
        holder_ids: list[int] = []

        @component
        def Parent() -> None:
            holder = get_ref(DialogRef)
            holder_ids.append(id(holder))

        capture = capture_patches(Parent)
        capture.render()

        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert len(holder_ids) == 2
        assert holder_ids[0] == holder_ids[1]

    def test_get_ref_outside_render_raises(self) -> None:
        """get_ref() outside render raises RuntimeError."""
        with pytest.raises(RuntimeError, match="render context"):
            get_ref(DialogRef)


class TestSetRef:
    def test_set_ref_outside_render_raises(self) -> None:
        """set_ref() outside render raises RuntimeError."""
        with pytest.raises(RuntimeError, match="render context"):
            set_ref(DialogRef())

    def test_set_ref_called_twice_raises(self, capture_patches: type[PatchCapture]) -> None:
        """Second set_ref() in same component raises RuntimeError."""
        error: Exception | None = None

        @component
        def Child() -> None:
            nonlocal error
            ref1 = DialogRef()
            ref2 = DialogRef()
            set_ref(ref1)
            try:
                set_ref(ref2)
            except RuntimeError as e:
                error = e

        capture = capture_patches(Child)
        capture.render()

        assert error is not None
        assert "once per component" in str(error)


# =============================================================================
# Element.ref() and render wiring
# =============================================================================


class TestElementRef:
    def test_element_ref_returns_self(self, capture_patches: type[PatchCapture]) -> None:
        """Element.ref() returns the element for chaining."""

        element_refs: list[bool] = []

        @component
        def Child() -> None:
            set_ref(DialogRef())

        @component
        def Parent() -> None:
            holder = get_ref(DialogRef)
            el = Child()
            result = el.ref(holder)
            element_refs.append(result is el)

        capture = capture_patches(Parent)
        capture.render()

        assert element_refs == [True]

    def test_parent_ref_connects_to_child(self, capture_patches: type[PatchCapture]) -> None:
        """Parent get_ref + child set_ref + Element.ref() -> holder proxies methods."""

        @component
        def Dialog() -> None:
            ref = DialogRef()
            set_ref(ref)

        @component
        def Parent() -> None:
            dialog = get_ref(DialogRef)
            Dialog().ref(dialog)

        capture = capture_patches(Parent)
        capture.render()

        # Get the holder from parent's state
        parent_state = capture.session.states.get(capture.session.root_element.id)
        holder = parent_state.local_state[(_RefHolder, 0)]

        assert holder
        assert holder.is_open() is False
        holder.open()
        assert holder.is_open() is True

    def test_ref_wiring_survives_rerender(self, capture_patches: type[PatchCapture]) -> None:
        """After re-render, holder is still connected."""

        @component
        def Dialog() -> None:
            ref = DialogRef()
            set_ref(ref)

        @component
        def Parent() -> None:
            dialog = get_ref(DialogRef)
            Dialog().ref(dialog)

        capture = capture_patches(Parent)
        capture.render()

        # Re-render
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        parent_state = capture.session.states.get(capture.session.root_element.id)
        holder = parent_state.local_state[(_RefHolder, 0)]
        assert holder

    def test_set_ref_without_holder_is_noop(self, capture_patches: type[PatchCapture]) -> None:
        """Child calls set_ref with no parent holder — no error."""

        @component
        def Dialog() -> None:
            ref = DialogRef()
            set_ref(ref)

        @component
        def Parent() -> None:
            Dialog()  # No .ref() call

        capture = capture_patches(Parent)
        capture.render()  # Should not raise

    def test_ref_with_container_and_with_block(self, capture_patches: type[PatchCapture]) -> None:
        """with MyContainer().ref(holder): works."""

        class PanelRef(Ref):
            def __init__(self) -> None:
                self._collapsed = False

            def collapse(self) -> None:
                self._collapsed = True

            def is_collapsed(self) -> bool:
                return self._collapsed

        @component
        def Panel(children: list | None = None) -> None:
            ref = PanelRef()
            set_ref(ref)

        @component
        def Child() -> None:
            pass

        @component
        def Parent() -> None:
            panel = get_ref(PanelRef)
            with Panel().ref(panel):
                Child()

        capture = capture_patches(Parent)
        capture.render()

        parent_state = capture.session.states.get(capture.session.root_element.id)
        holder = parent_state.local_state[(_RefHolder, 0)]
        assert holder
        assert holder.is_collapsed() is False


# =============================================================================
# Ref lifecycle hooks
# =============================================================================


class TestRefLifecycle:
    def test_ref_on_mount_called(self, capture_patches: type[PatchCapture]) -> None:
        """Ref subclass on_mount() called after initial render."""
        mount_calls: list[str] = []

        class MountTrackingRef(Ref):
            def on_mount(self) -> None:
                mount_calls.append("mounted")

        @component
        def Child() -> None:
            set_ref(MountTrackingRef())

        @component
        def Parent() -> None:
            holder = get_ref(MountTrackingRef)
            Child().ref(holder)

        capture = capture_patches(Parent)
        capture.render()

        assert mount_calls == ["mounted"]

    def test_ref_on_mount_called_once(self, capture_patches: type[PatchCapture]) -> None:
        """on_mount not called again on re-render."""
        mount_calls: list[str] = []

        class MountOnceRef(Ref):
            def on_mount(self) -> None:
                mount_calls.append("mounted")

        @component
        def Child() -> None:
            set_ref(MountOnceRef())

        @component
        def Parent() -> None:
            holder = get_ref(MountOnceRef)
            Child().ref(holder)

        capture = capture_patches(Parent)
        capture.render()
        assert mount_calls == ["mounted"]

        # Re-render parent (and child)
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        # on_mount should NOT have been called again
        assert mount_calls == ["mounted"]

    def test_ref_on_unmount_called_on_removal(self, capture_patches: type[PatchCapture]) -> None:
        """Conditional render: remove child -> on_unmount fires."""
        unmount_calls: list[str] = []
        show_child = [True]

        class UnmountTrackingRef(Ref):
            def on_unmount(self) -> None:
                unmount_calls.append("unmounted")

        @component
        def Child() -> None:
            set_ref(UnmountTrackingRef())

        @component
        def Parent() -> None:
            holder = get_ref(UnmountTrackingRef)
            if show_child[0]:
                Child().ref(holder)

        capture = capture_patches(Parent)
        capture.render()
        assert unmount_calls == []

        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert unmount_calls == ["unmounted"]

    def test_ref_holder_detached_on_unmount(self, capture_patches: type[PatchCapture]) -> None:
        """Holder becomes falsy when child unmounts."""
        show_child = [True]

        @component
        def Child() -> None:
            set_ref(DialogRef())

        @component
        def Parent() -> None:
            holder = get_ref(DialogRef)
            if show_child[0]:
                Child().ref(holder)

        capture = capture_patches(Parent)
        capture.render()

        parent_state = capture.session.states.get(capture.session.root_element.id)
        holder = parent_state.local_state[(_RefHolder, 0)]
        assert holder  # attached

        show_child[0] = False
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert not holder  # detached after unmount

    def test_async_ref_on_mount(self, capture_patches: type[PatchCapture]) -> None:
        """Async on_mount is scheduled as background task."""
        mount_calls: list[str] = []
        done_event = asyncio.Event()

        class AsyncMountRef(Ref):
            async def on_mount(self) -> None:
                mount_calls.append("async_mounted")
                done_event.set()

        @component
        def Child() -> None:
            set_ref(AsyncMountRef())

        @component
        def Parent() -> None:
            holder = get_ref(AsyncMountRef)
            Child().ref(holder)

        capture = capture_patches(Parent)

        async def test() -> None:
            capture.render()
            await asyncio.wait_for(done_event.wait(), timeout=1.0)
            assert mount_calls == ["async_mounted"]

        asyncio.run(test())

    def test_ref_on_mount_can_access_context(self, capture_patches: type[PatchCapture]) -> None:
        """Stateful.from_context() works in Ref.on_mount()."""
        retrieved_values: list[str] = []

        @dataclass(kw_only=True)
        class AppState(Stateful):
            value: str = ""

        class ContextRef(Ref):
            def on_mount(self) -> None:
                state = AppState.from_context()
                retrieved_values.append(state.value)

        @component
        def Child() -> None:
            set_ref(ContextRef())

        @component
        def Parent() -> None:
            with AppState(value="from_context_works"):
                holder = get_ref(ContextRef)
                Child().ref(holder)

        capture = capture_patches(Parent)
        capture.render()

        assert retrieved_values == ["from_context_works"]


# =============================================================================
# Edge cases
# =============================================================================


class TestRefEdgeCases:
    def test_ref_detached_when_child_stops_calling_set_ref(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Child conditionally calls set_ref. When it stops, holder detaches."""
        expose_ref = [True]

        @dataclass(kw_only=True)
        class ChildState(Stateful):
            trigger: int = 0

        @component
        def Child() -> None:
            state = ChildState()
            _ = state.trigger  # register dependency for dirty tracking
            if expose_ref[0]:
                set_ref(DialogRef())

        @component
        def Parent() -> None:
            holder = get_ref(DialogRef)
            Child().ref(holder)

        capture = capture_patches(Parent)
        capture.render()

        parent_state = capture.session.states.get(capture.session.root_element.id)
        holder = parent_state.local_state[(_RefHolder, 0)]
        assert holder  # attached

        # Get child element_id and its state to trigger a re-render of the child
        child_id = capture.session.root_element.child_ids[0]
        child_es = capture.session.states.get(child_id)
        child_stateful = child_es.local_state[(ChildState, 0)]

        expose_ref[0] = False
        child_stateful.trigger = 1  # marks child dirty
        capture.render()

        assert not holder  # detached because child stopped calling set_ref

    def test_holder_swap(self, capture_patches: type[PatchCapture]) -> None:
        """Parent switches which holder is attached to a child."""
        which_holder = [0]

        @component
        def Child() -> None:
            set_ref(DialogRef())

        @component
        def Parent() -> None:
            holder_a = get_ref(DialogRef)
            holder_b = get_ref(DialogRef)
            if which_holder[0] == 0:
                Child().ref(holder_a)
            else:
                Child().ref(holder_b)

        capture = capture_patches(Parent)
        capture.render()

        parent_state = capture.session.states.get(capture.session.root_element.id)
        holder_a = parent_state.local_state[(_RefHolder, 0)]
        holder_b = parent_state.local_state[(_RefHolder, 1)]
        assert holder_a
        assert not holder_b

        which_holder[0] = 1
        capture.session.dirty.mark(capture.session.root_element.id)
        capture.render()

        assert not holder_a  # old detached
        assert holder_b  # new attached

    def test_multiple_holders_multiple_children(self, capture_patches: type[PatchCapture]) -> None:
        """Two get_ref calls, two children, each wired independently."""

        @component
        def Dialog() -> None:
            set_ref(DialogRef())

        @component
        def Parent() -> None:
            dialog_a = get_ref(DialogRef)
            dialog_b = get_ref(DialogRef)
            Dialog().ref(dialog_a)
            Dialog().ref(dialog_b)

        capture = capture_patches(Parent)
        capture.render()

        parent_state = capture.session.states.get(capture.session.root_element.id)
        holder_a = parent_state.local_state[(_RefHolder, 0)]
        holder_b = parent_state.local_state[(_RefHolder, 1)]

        assert holder_a
        assert holder_b
        # They should be attached to different DialogRef instances
        ref_a = object.__getattribute__(holder_a, "_ref")
        ref_b = object.__getattribute__(holder_b, "_ref")
        assert ref_a is not ref_b

    def test_stateful_as_ref(self, capture_patches: type[PatchCapture]) -> None:
        """Stateful subclass exposed via set_ref, holder proxies, tracking suppressed."""

        @dataclass(kw_only=True)
        class DialogState(Stateful):
            _open: bool = False

            def open(self) -> None:
                self._open = True

            def is_open(self) -> bool:
                return self._open

        @component
        def Dialog() -> None:
            state = DialogState()
            set_ref(state)

        @component
        def Parent() -> None:
            dialog = get_ref(DialogState)
            Dialog().ref(dialog)

        capture = capture_patches(Parent)
        capture.render()

        parent_state = capture.session.states.get(capture.session.root_element.id)
        holder = parent_state.local_state[(_RefHolder, 0)]

        assert holder
        assert holder.is_open() is False
        # Reading through holder should not create watchers on parent
        # INTERNAL TEST: verify no watchers registered through proxy
        ref = object.__getattribute__(holder, "_ref")
        if hasattr(ref, "_state_props") and "_open" in ref._state_props:
            watcher_ids = {e.id for e in ref._state_props["_open"].watchers}
            parent_id = capture.session.root_element.id
            assert parent_id not in watcher_ids

    def test_ref_holder_reattaches_on_child_rerender(
        self, capture_patches: type[PatchCapture]
    ) -> None:
        """Child re-renders, ref re-attaches to same holder."""
        ref_ids: list[int] = []

        @dataclass(kw_only=True)
        class ChildState(Stateful):
            trigger: int = 0

        @component
        def Child() -> None:
            state = ChildState()
            _ = state.trigger
            ref = DialogRef()
            ref_ids.append(id(ref))
            set_ref(ref)

        @component
        def Parent() -> None:
            holder = get_ref(DialogRef)
            Child().ref(holder)

        capture = capture_patches(Parent)
        capture.render()

        parent_state = capture.session.states.get(capture.session.root_element.id)
        holder = parent_state.local_state[(_RefHolder, 0)]
        assert holder

        # Re-render the child directly
        child_id = capture.session.root_element.child_ids[0]
        child_es = capture.session.states.get(child_id)
        child_stateful = child_es.local_state[(ChildState, 0)]
        child_stateful.trigger = 1
        capture.render()

        assert holder  # still attached after child re-render
        assert len(ref_ids) == 2  # child executed twice


# =============================================================================
# E2E pattern test
# =============================================================================


class TestDialogRefPattern:
    def test_dialog_ref_pattern(self, capture_patches: type[PatchCapture]) -> None:
        """Full dialog ref pattern: parent holds handle to child dialog state."""

        @dataclass(kw_only=True)
        class _DialogState(Stateful):
            is_open: bool = False

        class FullDialogRef(Ref):
            """Ref exposed by the dialog to its parent."""

            def __init__(self, state: _DialogState) -> None:
                self._state = state

            def open(self) -> None:
                self._state.is_open = True

            def close(self) -> None:
                self._state.is_open = False

        # Track what the dialog renders
        dialog_renders: list[bool] = []

        @component
        def MyDialog() -> None:
            state = _DialogState()
            set_ref(FullDialogRef(state))
            _ = state.is_open  # register dependency
            dialog_renders.append(state.is_open)

        @component
        def App() -> None:
            dialog = get_ref(FullDialogRef)
            MyDialog().ref(dialog)

        capture = capture_patches(App)
        capture.render()

        # Initial render: dialog is closed
        assert dialog_renders == [False]

        # Get holder and call open()
        app_state = capture.session.states.get(capture.session.root_element.id)
        holder = app_state.local_state[(_RefHolder, 0)]
        assert holder

        holder.open()

        # Dialog's state changed, should be marked dirty
        capture.render()
        assert dialog_renders == [False, True]

        # Close it
        holder.close()
        capture.render()
        assert dialog_renders == [False, True, False]
