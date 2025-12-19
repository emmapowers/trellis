"""Mutable wrapper and functions for two-way data binding in Trellis.

This module provides:
- mutable() for automatic two-way binding (auto-generates setter)
- callback() for explicit callback binding (custom processing)

Both functions create a Mutable[T] wrapper.

Example:
    @dataclass(kw_only=True)
    class FormState(Stateful):
        name: str = ""

        def set_name(self, value: str) -> None:
            self.name = value.strip()  # Custom processing

    @component
    def Form() -> None:
        state = FormState()
        # Automatic two-way binding
        TextInput(value=mutable(state.name))
        # Explicit callback for custom processing
        TextInput(value=callback(state.name, state.set_name))
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering import get_active_render_tree

if tp.TYPE_CHECKING:
    from trellis.core.state import Stateful

T = tp.TypeVar("T")

__all__ = ["Mutable", "callback", "mutable"]


def record_property_access(owner: Stateful, attr: str, value: tp.Any) -> None:
    """Record a property access for potential use by mutable().

    Called by Stateful.__getattribute__ during render to track the most
    recent property access. This enables mutable() to capture the reference.
    """
    tree = get_active_render_tree()
    if tree is not None:
        tree._last_property_access = (owner, attr, value)


def clear_property_access() -> None:
    """Clear the last recorded property access."""
    tree = get_active_render_tree()
    if tree is not None:
        tree._last_property_access = None


def _get_last_property_access() -> tuple[tp.Any, str, tp.Any] | None:
    """Get the last recorded property access from the active render tree."""
    tree = get_active_render_tree()
    if tree is None:
        return None
    return tree._last_property_access


class Mutable(tp.Generic[T]):
    """Reference to a Stateful property for two-way data binding.

    Mutable objects wrap a reference to a Stateful instance and attribute name,
    enabling widgets to both read and write the property value.

    Created via mutable() or callback() functions, not directly instantiated.

    Attributes:
        _owner: The Stateful instance that owns the property
        _attr: The attribute name on the owner
        _on_change: Optional custom callback (if None, uses auto-generated setter)
    """

    __slots__ = ("_attr", "_on_change", "_owner")

    def __init__(
        self,
        owner: Stateful,
        attr: str,
        on_change: tp.Callable[[T], tp.Any] | None = None,
    ) -> None:
        self._owner = owner
        self._attr = attr
        self._on_change = on_change

    @property
    def value(self) -> T:
        """Get the current value of the wrapped property."""
        return object.__getattribute__(self._owner, self._attr)  # type: ignore

    @value.setter
    def value(self, new_value: T) -> None:
        """Set the value of the wrapped property."""
        if self._on_change is not None:
            self._on_change(new_value)
        else:
            setattr(self._owner, self._attr, new_value)

    @property
    def on_change(self) -> tp.Callable[[T], tp.Any] | None:
        """Get the custom callback, if any."""
        return self._on_change

    def __hash__(self) -> int:
        """Hash based on owner identity and attribute name."""
        return hash((id(self._owner), self._attr))

    def __eq__(self, other: object) -> bool:
        """Compare by reference identity (same owner instance and attr)."""
        if not isinstance(other, Mutable):
            return NotImplemented
        return self._owner is other._owner and self._attr == other._attr

    def __repr__(self) -> str:
        if self._on_change:
            return f"Mutable({self._attr}={self.value!r}, on_change={self._on_change!r})"
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
    last = _get_last_property_access()
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


def callback(value: T, on_change: tp.Callable[[T], tp.Any]) -> Mutable[T]:
    """Create a mutable reference with a custom callback for two-way binding.

    Use this when you need custom logic (validation, transformation, side effects)
    when the value changes, rather than a simple property assignment.

    Must be called immediately after accessing a Stateful property, like mutable().

    Args:
        value: The value from a Stateful property access (e.g., state.name)
        on_change: Function to call when the value changes

    Returns:
        A Mutable wrapper with the custom callback

    Raises:
        TypeError: If not called immediately after a Stateful property access

    Example:
        def set_name(value: str) -> None:
            state.name = value.strip().title()  # Custom processing

        TextInput(value=callback(state.name, set_name))
    """
    last = _get_last_property_access()
    if last is None:
        raise TypeError(
            "callback() must be called immediately after accessing a Stateful property. "
            "Use: callback(state.property, handler), not callback(some_variable, handler)"
        )

    owner, attr, last_value = last

    # Verify the value matches what was just accessed
    if last_value is not value:
        raise TypeError(
            "callback() must be called immediately after accessing a Stateful property. "
            f"Expected value from {attr!r}, got a different value."
        )

    # Clear the recorded access so it can't be reused
    clear_property_access()

    return Mutable(owner, attr, on_change=on_change)
