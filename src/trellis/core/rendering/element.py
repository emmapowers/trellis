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
    "ContainerElement",
    "Element",
    "props_equal",
]


@dataclass(eq=False)
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

    def notify_dirty(self) -> None:
        """Mark this element as needing re-render. Satisfies StateDependency protocol."""
        session = self._session_ref()
        if session is not None:
            session.dirty.mark(self.id)

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


def props_equal(old_props: dict[str, tp.Any], new_props: dict[str, tp.Any]) -> bool:
    """Compare props without serialization.

    Maintains the same semantics as serialized comparison:
    - All callables are considered equal (they serialize to {"__callback__": ...})
    - Mutables compare by owner identity and attr name (their __eq__)
    - Other values compare normally

    Args:
        old_props: Previous props dict
        new_props: New props dict

    Returns:
        True if props are semantically equal for rendering purposes
    """
    if len(old_props) != len(new_props):
        return False
    if old_props.keys() != new_props.keys():
        return False
    for key, old_val in old_props.items():
        if not _values_equal(old_val, new_props[key]):
            return False
    return True


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
