"""Ref API for imperative handles to child components.

Allows parent components to hold refs to children for imperative operations
like focus management, dialog.close(), etc.

Usage:
    class DialogRef(Ref):
        def open(self) -> None: ...
        def close(self) -> None: ...

    @component
    def Parent() -> None:
        dialog = get_ref(DialogRef)
        MyDialog().ref(dialog)
        Button(on_click=lambda: dialog.open())

    @component
    def MyDialog() -> None:
        state = DialogState()
        set_ref(state)
"""

from __future__ import annotations

import typing as tp
import weakref
from dataclasses import dataclass

from trellis.core.rendering.lifecycle import invoke_lifecycle_hook
from trellis.core.rendering.session import get_active_session

if tp.TYPE_CHECKING:
    from typing import Self

    from trellis.core.rendering.element import Element
    from trellis.core.rendering.element_state import ElementState
    from trellis.core.rendering.session import RenderSession

T = tp.TypeVar("T")

__all__ = [
    "Ref",
    "RefTrait",
    "RefTraitState",
    "_RefHolder",
    "get_ref",
    "set_ref",
]


class Ref:
    """Base class for ref objects exposed by child components.

    Subclass this to define the imperative interface a child exposes.
    Override on_mount/on_unmount for lifecycle hooks.
    """

    def on_mount(self) -> None | tp.Coroutine[tp.Any, tp.Any, None]:
        """Called after the owning element mounts. Override for initialization."""
        pass

    def on_unmount(self) -> None | tp.Coroutine[tp.Any, tp.Any, None]:
        """Called before the owning element unmounts. Override for cleanup."""
        pass


class _RefHolder(tp.Generic[T]):
    """Proxy that holds a reference to a child's exposed ref.

    Forwards attribute access to the underlying ref while bypassing
    Stateful's dependency tracking (uses object.__getattribute__).
    """

    __slots__ = ("_ref", "_ref_type")

    def __init__(self, ref_type: type[T]) -> None:
        object.__setattr__(self, "_ref", None)
        object.__setattr__(self, "_ref_type", ref_type)

    def __bool__(self) -> bool:
        return object.__getattribute__(self, "_ref") is not None

    def __getattr__(self, name: str) -> tp.Any:
        ref = object.__getattribute__(self, "_ref")
        if ref is None:
            ref_type = object.__getattribute__(self, "_ref_type")
            raise RuntimeError(
                f"Ref holder for {ref_type.__name__} is not attached. "
                f"Ensure the child component calls set_ref() and is mounted."
            )
        # Bypass Stateful.__getattribute__ to avoid registering watchers
        return object.__getattribute__(ref, name)

    def _attach(self, ref: T) -> None:
        ref_type = object.__getattribute__(self, "_ref_type")
        if not isinstance(ref, ref_type):
            raise TypeError(f"Expected {ref_type.__name__}, got {type(ref).__name__}")
        object.__setattr__(self, "_ref", ref)

    def _detach(self) -> None:
        object.__setattr__(self, "_ref", None)


@dataclass
class RefTraitState:
    """Per-element state for RefTrait, stored via ElementState.trait()."""

    exposed_ref: tp.Any = None
    ref_holder: tp.Any = None


class RefTrait:
    """Trait providing fluent ref attachment for parent-child handles.

    Allows a parent component to attach a ref holder to a child element,
    so the parent can access the child's imperative handle after rendering.

    Lifecycle hooks handle ref wiring/unwiring automatically:
    - _before_execute: resets exposed_ref so we detect if child calls set_ref()
    - _after_execute: reads _ref_holder, reconciles with trait state, wires/detaches
    - _on_trait_mount: calls Ref.on_mount if exposed_ref is a Ref
    - _on_trait_unmount: calls Ref.on_unmount, clears state, detaches holder
    """

    id: str  # Provided by Element
    _session_ref: weakref.ref[RenderSession]  # Provided by Element

    def ref(self, holder: _RefHolder[tp.Any]) -> Self:
        """Attach a ref holder to this element.

        Sets _ref_holder as a plain instance attribute. The _after_execute
        hook reads it to wire the ref after execution completes.

        For already-mounted elements (reuse case where _after_execute won't
        fire), wires immediately if exposed_ref is available.

        Args:
            holder: A _RefHolder obtained from get_ref()

        Returns:
            self, for method chaining (e.g. MyChild().ref(holder))
        """
        session = self._session_ref()
        if session is None:
            raise RuntimeError("Cannot attach ref: session has been garbage collected")

        self._ref_holder = holder

        # For already-mounted elements, update trait state and wire immediately
        state = session.states.get(self.id)
        if state is not None and state.mounted:
            ts = state.trait(RefTraitState)
            old_holder = ts.ref_holder
            if old_holder is not None and old_holder is not holder:
                old_holder._detach()
            ts.ref_holder = holder
            if ts.exposed_ref is not None:
                holder._attach(ts.exposed_ref)

        return self

    def _before_execute(
        self, element: Element, state: ElementState, session: RenderSession
    ) -> None:
        """Reset exposed_ref before execute so we detect if child calls set_ref()."""
        ts = state.trait(RefTraitState)
        ts.exposed_ref = None

    def _after_execute(self, element: Element, state: ElementState, session: RenderSession) -> None:
        """Wire ref holder to exposed ref after component executes."""
        ts = state.trait(RefTraitState)
        holder_attr: _RefHolder[tp.Any] | None = getattr(element, "_ref_holder", None)

        if holder_attr is not None:
            # Detach old holder if swapping
            old_holder = ts.ref_holder
            if old_holder is not None and old_holder is not holder_attr:
                old_holder._detach()
            ts.ref_holder = holder_attr

        # Wire ref: connect holder to exposed ref, or detach if child stopped exposing
        if ts.exposed_ref is not None and ts.ref_holder is not None:
            ts.ref_holder._attach(ts.exposed_ref)
        elif ts.exposed_ref is None and ts.ref_holder is not None:
            if ts.ref_holder:  # was previously attached
                ts.ref_holder._detach()

    def _on_trait_mount(
        self, element: Element, state: ElementState, session: RenderSession
    ) -> None:
        """Call Ref.on_mount if exposed_ref is a Ref instance."""
        ts = state.trait(RefTraitState)
        if ts.exposed_ref is not None and isinstance(ts.exposed_ref, Ref):
            invoke_lifecycle_hook(session, element.id, ts.exposed_ref.on_mount, "Ref.on_mount")

    def _on_trait_unmount(
        self, element: Element | None, state: ElementState, session: RenderSession
    ) -> None:
        """Call Ref.on_unmount, clear exposed_ref, detach holder."""
        ts = state.trait(RefTraitState)
        if ts.exposed_ref is not None and isinstance(ts.exposed_ref, Ref):
            element_id = element.id if element is not None else ""
            invoke_lifecycle_hook(session, element_id, ts.exposed_ref.on_unmount, "Ref.on_unmount")
            ts.exposed_ref = None

        if ts.ref_holder is not None:
            ts.ref_holder._detach()


def get_ref(ref_type: type[T]) -> _RefHolder[T]:
    """Get or create a ref holder for a child component's ref.

    Must be called during component execution (render context).
    Returns a cached _RefHolder that persists across re-renders,
    using the same state_call_count mechanism as Stateful.

    Args:
        ref_type: The expected ref type (Ref subclass or Stateful subclass)

    Returns:
        A _RefHolder proxy. Falsy until the child calls set_ref() and
        Element.ref() wires them together.

    Raises:
        RuntimeError: If called outside render context
    """
    session = get_active_session()
    if session is None or not session.is_executing():
        raise RuntimeError(
            "get_ref() can only be called during component execution (render context)."
        )

    element_id = session.current_element_id
    assert element_id is not None

    state = session.states.get_or_create(element_id)
    call_idx = state.state_call_count
    state.state_call_count += 1
    key = (_RefHolder, call_idx)

    if key in state.local_state:
        return tp.cast("_RefHolder[T]", state.local_state[key])

    holder = _RefHolder(ref_type)
    state.local_state[key] = holder
    return holder


def set_ref(ref: tp.Any) -> None:
    """Expose a ref from a child component to its parent.

    Must be called during component execution (render context).
    Only one set_ref() call is allowed per component per render.

    Args:
        ref: The ref object to expose (Ref subclass or Stateful instance)

    Raises:
        RuntimeError: If called outside render context or called twice
    """
    session = get_active_session()
    if session is None or not session.is_executing():
        raise RuntimeError(
            "set_ref() can only be called during component execution (render context)."
        )

    element_id = session.current_element_id
    assert element_id is not None

    state = session.states.get_or_create(element_id)
    ts = state.trait(RefTraitState)
    if ts.exposed_ref is not None:
        raise RuntimeError(
            "set_ref() can only be called once per component per render. "
            "Multiple refs are not supported."
        )
    ts.exposed_ref = ref
