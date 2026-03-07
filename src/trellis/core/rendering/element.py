from __future__ import annotations

import typing as tp
import weakref
from dataclasses import dataclass, field

from trellis.core.rendering.on_key_trait import OnKeyTrait
from trellis.core.rendering.traits import ContainerTrait, KeyTrait
from trellis.core.state.mutable import Mutable
from trellis.core.state.ref import RefTrait

if tp.TYPE_CHECKING:
    from trellis.core.components.base import Component
    from trellis.core.rendering.session import RenderSession

__all__ = [
    "_REMOVED",
    "ContainerElement",
    "Element",
    "diff_props",
]


@dataclass
class Element(OnKeyTrait, KeyTrait, RefTrait):
    """Tree node representing a component invocation (leaf — no `with` block)."""

    component: Component
    _session_ref: weakref.ref[RenderSession]
    render_count: int  # Required, no default - must be set from session.render_count
    props: dict[str, tp.Any] = field(default_factory=dict)
    _key: str | None = None
    child_ids: list[str] = field(default_factory=list)
    id: str = ""  # Position-based ID assigned at creation

    def __hash__(self) -> int:
        """Hash based on id, session, and render_count for stable identity.

        This allows elements to be used in WeakSets for dependency tracking,
        where identity matters more than content equality.
        """
        return hash(
            (self.id, id(self._session_ref()) if self._session_ref() else None, self.render_count)
        )

    @property
    def properties(self) -> dict[str, tp.Any]:
        """Get props as a mutable dictionary, including child_ids if present."""
        # TODO: we need to re-evaluate this design; having child_ids sometimes in props
        # sometimes separate is confusing. See the serializer for an example of why.
        props = self.props.copy()
        if self.child_ids:
            props["child_ids"] = list(self.child_ids)
        return props


@dataclass(eq=False)
class ContainerElement(ContainerTrait, Element):
    """Element that supports `with` blocks for collecting children.

    Convenience composition of ContainerTrait + Element. Decorators that need
    container behavior can also dynamically compose ContainerTrait into any
    custom element_class via type().
    """


class _RemovedType:
    """Sentinel marking a prop as removed in a diff."""

    _instance = None

    def __new__(cls) -> _RemovedType:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "_REMOVED"


_REMOVED = _RemovedType()

_MISSING = object()


def diff_props(old_props: dict[str, tp.Any], new_props: dict[str, tp.Any]) -> dict[str, tp.Any]:
    """Compute the diff between old and new props dicts.

    Returns only changed/added/removed keys:
    - Added or changed keys map to their new value
    - Removed keys map to _REMOVED sentinel

    Maintains the same semantics as the old props_equal:
    - All callables are considered equal (they serialize to {"__callback__": ...})
    - Mutables compare by snapshot (their __eq__)
    - Other values compare normally
    """
    diff: dict[str, tp.Any] = {}

    for key, new_val in new_props.items():
        old_val = old_props.get(key, _MISSING)
        if old_val is _MISSING or not _values_equal(old_val, new_val):
            diff[key] = new_val

    for key in old_props:
        if key not in new_props:
            diff[key] = _REMOVED

    return diff


def _values_equal(old: tp.Any, new: tp.Any) -> bool:
    """Compare values with callback-equivalence semantics.

    Mutables compare by snapshot (value at creation time) to detect changes.
    Other callables are considered equal since they serialize identically.

    Args:
        old: Previous value
        new: New value

    Returns:
        True if values are semantically equal for rendering purposes
    """
    # Mutables: compare by snapshot (must check before callable since Mutable is callable)
    if isinstance(old, Mutable) and isinstance(new, Mutable):
        return old == new

    # Callables: all callbacks are equal (we don't care about identity)
    if callable(old) and callable(new):
        return True

    # Everything else: standard equality
    return bool(old == new)
