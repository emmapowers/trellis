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
    """Typed slot-local reactive value.

    Example:
        ```python
        @component
        def Counter() -> None:
            count = state_var(0)
            w.Button(text="+", on_click=lambda: count.update(lambda value: value + 1))
            w.Label(text=f"Count: {count.value}")
        ```
    """

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

    def set(self, value: T) -> None:
        """Replace the current value."""
        self.value = value

    def update(self, fn: tp.Callable[[T], T]) -> None:
        """Replace the current value with a function of the previous value."""
        self.value = fn(self.value)

    def __repr__(self) -> str:
        return f"StateVar({self.value!r})"


@tp.overload
def state_var(initial: T, /) -> StateVar[T]: ...


@tp.overload
def state_var(*, factory: tp.Callable[[], T]) -> StateVar[T]: ...


def state_var(
    initial: T | _Missing = _MISSING,
    /,
    *,
    factory: tp.Callable[[], T] | None = None,
) -> StateVar[T]:
    """Create slot-local reactive state for the current component.

    Example:
        ```python
        @component
        def Greeting() -> None:
            name = state_var("Ada")

            w.TextInput(value=mutable(name.value))
            w.Label(text=f"Hello, {name.value}")
        ```
    """

    return StateVar(initial, factory=factory)
