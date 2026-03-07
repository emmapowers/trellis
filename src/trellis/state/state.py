"""Typed local state helper built on Stateful."""

from __future__ import annotations

import inspect
import typing as tp

from trellis.core.state.stateful import Stateful

T = tp.TypeVar("T")

__all__ = ["StateCell", "state"]


class _Missing:
    """Sentinel for a missing initial value."""

    pass


_MISSING = _Missing()


class StateCell[T]:
    """Typed wrapper around a tracked state value."""

    __slots__ = ("_backing",)

    def __init__(self, backing: "_StateValue") -> None:
        self._backing = backing

    @property
    def value(self) -> T:
        """Get the current value."""
        return tp.cast("T", self._backing.value)

    @value.setter
    def value(self, value: T) -> None:
        """Replace the current value."""
        self._backing.value = value

    def set(self, value: T) -> None:
        """Replace the current value."""
        self.value = value

    def update(self, fn: tp.Callable[[T], T]) -> None:
        """Replace the current value with a function of the previous value."""
        self.value = fn(self.value)

    def __repr__(self) -> str:
        return f"StateCell({self.value!r})"


class _StateValue(Stateful):
    """Private tracked backing object for StateCell."""

    value: object
    if tp.TYPE_CHECKING:
        _cell: StateCell[object] | None
    _cell = None

    def __init__(
        self,
        initial: object | _Missing = _MISSING,
        *,
        factory: tp.Callable[[], object] | None = None,
    ) -> None:
        if factory is not None:
            if inspect.iscoroutinefunction(factory):
                raise TypeError("state(factory=...) does not support async factories")
            value = factory()
            if inspect.isawaitable(value):
                raise TypeError("state(factory=...) does not support async factories")
        else:
            value = initial

        if value is _MISSING:
            raise TypeError("state() requires an initial value or factory=...")

        self.value = value
        self._cell = StateCell[object](self)

    def cell(self) -> StateCell[object]:
        """Return the stable wrapper for this backing state."""
        existing = self._cell
        if existing is not None:
            return existing

        cell = StateCell[object](self)
        self._cell = cell
        return cell


@tp.overload
def state(initial: T, /) -> StateCell[T]: ...


@tp.overload
def state(*, factory: tp.Callable[[], T]) -> StateCell[T]: ...


def state(
    initial: T | _Missing = _MISSING,
    /,
    *,
    factory: tp.Callable[[], T] | None = None,
) -> StateCell[T]:
    """Create slot-local reactive state for the current component."""
    if initial is not _MISSING and factory is not None:
        raise TypeError("state() accepts either an initial value or factory=..., not both")

    backing = _StateValue(initial, factory=factory)
    return tp.cast("StateCell[T]", backing.cell())
