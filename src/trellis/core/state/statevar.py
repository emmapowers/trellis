"""Typed local state helper built on Stateful."""

from __future__ import annotations

import inspect
import typing as tp

from trellis.core.state.stateful import Stateful

T = tp.TypeVar("T")

__all__ = ["StateVar", "state_var"]


class _Missing:
    """Sentinel for a missing initial value."""

    pass


_MISSING = _Missing()


class StateVar[T](Stateful):
    """Typed slot-local reactive value."""

    value: T

    def __init__(
        self,
        initial: T | _Missing = _MISSING,
        *,
        factory: tp.Callable[[], T] | None = None,
    ) -> None:
        if initial is not _MISSING and factory is not None:
            raise TypeError("state_var() accepts either an initial value or factory=..., not both")

        if factory is not None:
            if inspect.iscoroutinefunction(factory):
                raise TypeError("state_var(factory=...) does not support async factories")
            resolved = factory()
            if inspect.isawaitable(resolved):
                raise TypeError("state_var(factory=...) does not support async factories")
        else:
            if initial is _MISSING:
                raise TypeError("state_var() requires an initial value or factory=...")
            resolved = tp.cast("T", initial)

        self.value = resolved

    def __repr__(self) -> str:
        return f"StateVar({self.value!r})"


@tp.overload
def state_var(initial: T, /) -> T: ...


@tp.overload
def state_var(*, factory: tp.Callable[[], T]) -> T: ...


def state_var(
    initial: T | _Missing = _MISSING,
    /,
    *,
    factory: tp.Callable[[], T] | None = None,
) -> T:
    """Create slot-local reactive state for the current component.

    Inside a ``@component`` function, an AST transform rewrites all reads and
    writes of the bound name to go through ``.value`` automatically, so user
    code never needs to mention ``.value``.

    Example:
        ```python
        @component
        def Greeting() -> None:
            name = state_var("Ada")
            count = state_var(0)

            def rename() -> None:
                nonlocal name
                name = "Grace"

            w.TextInput(value=mutable(name))
            w.Button(text="Rename", on_click=rename)
            w.Label(text=f"Hello, {name}")
            w.Label(text=f"Count: {count}")
        ```

    Returns:
        A per-element reactive value that persists across re-renders.
    """

    return tp.cast("T", StateVar(initial, factory=factory))
