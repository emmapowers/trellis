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

from trellis.core.rendering.session import get_active_session

if tp.TYPE_CHECKING:
    from trellis.core.rendering.element_state import ElementState

T = tp.TypeVar("T")

__all__ = [
    "Ref",
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

    state: ElementState = session.states.get_or_create(element_id)
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

    state: ElementState = session.states.get_or_create(element_id)
    if state.exposed_ref is not None:
        raise RuntimeError(
            "set_ref() can only be called once per component per render. "
            "Multiple refs are not supported."
        )
    state.exposed_ref = ref
