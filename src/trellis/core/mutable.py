"""Mutable wrapper for two-way data binding in Trellis.

This module provides the Mutable[T] class and mutable() function for
bidirectional binding between Stateful properties and form inputs.

Example:
    @dataclass(kw_only=True)
    class FormState(Stateful):
        name: str = ""

    @component
    def Form() -> None:
        state = FormState()
        # Two-way binding - widget updates state automatically
        TextInput(value=mutable(state.name))
        # Normal access - just use the value directly
        Label(text=state.name)
"""

from __future__ import annotations

import contextvars
import typing as tp

if tp.TYPE_CHECKING:
    from trellis.core.state import Stateful

T = tp.TypeVar("T")

__all__ = ["Mutable", "mutable"]

# Context variable tracking the last property access during render.
# Stores (owner, attr_name, value) so mutable() can create a reference.
_last_property_access: contextvars.ContextVar[tuple[Stateful, str, tp.Any] | None] = (
    contextvars.ContextVar("last_property_access", default=None)
)


def record_property_access(owner: Stateful, attr: str, value: tp.Any) -> None:
    """Record a property access for potential use by mutable().

    Called by Stateful.__getattribute__ during render to track the most
    recent property access. This enables mutable() to capture the reference.
    """
    _last_property_access.set((owner, attr, value))


def clear_property_access() -> None:
    """Clear the last recorded property access."""
    _last_property_access.set(None)


class Mutable(tp.Generic[T]):
    """Reference to a Stateful property for two-way data binding.

    Mutable objects wrap a reference to a Stateful instance and attribute name,
    enabling widgets to both read and write the property value.

    Created via the mutable() function, not directly instantiated.

    Attributes:
        _owner: The Stateful instance that owns the property
        _attr: The attribute name on the owner
    """

    __slots__ = ("_attr", "_owner")

    def __init__(self, owner: Stateful, attr: str) -> None:
        self._owner = owner
        self._attr = attr

    @property
    def value(self) -> T:
        """Get the current value of the wrapped property."""
        return object.__getattribute__(self._owner, self._attr)  # type: ignore

    @value.setter
    def value(self, new_value: T) -> None:
        """Set the value of the wrapped property."""
        setattr(self._owner, self._attr, new_value)

    def __hash__(self) -> int:
        """Hash based on owner identity and attribute name."""
        return hash((id(self._owner), self._attr))

    def __eq__(self, other: object) -> bool:
        """Compare by reference identity (same owner instance and attr)."""
        if not isinstance(other, Mutable):
            return NotImplemented
        return self._owner is other._owner and self._attr == other._attr

    def __repr__(self) -> str:
        return f"Mutable({self._attr}={self.value!r})"


def mutable(value: T) -> Mutable[T]:
    """Create a mutable reference for two-way data binding.

    Must be called immediately after accessing a Stateful property.
    The property access records itself, and mutable() captures that reference.

    Args:
        value: The value from a Stateful property access (e.g., state.name)

    Returns:
        A Mutable wrapper enabling two-way binding

    Raises:
        TypeError: If not called immediately after a Stateful property access

    Example:
        TextInput(value=mutable(state.name))  # Two-way binding
    """
    last = _last_property_access.get()
    if last is None:
        raise TypeError(
            "mutable() must be called immediately after accessing a Stateful property. "
            "Use: mutable(state.property), not mutable(some_variable)"
        )

    owner, attr, last_value = last

    # Verify the value matches what was just accessed
    # Use 'is' for identity check to handle cases where == might be overloaded
    if last_value is not value:
        raise TypeError(
            "mutable() must be called immediately after accessing a Stateful property. "
            f"Expected value from {attr!r}, got a different value."
        )

    # Clear the recorded access so it can't be reused
    clear_property_access()

    return Mutable(owner, attr)
