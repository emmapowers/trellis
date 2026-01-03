from __future__ import annotations

import typing as tp
import weakref
from dataclasses import dataclass, field

from trellis.core.rendering.child_ref import ChildRef
from trellis.core.rendering.session import (
    RenderSession,
    get_active_session,
)
from trellis.core.rendering.traits import KeyTrait
from trellis.core.state.mutable import Mutable
from trellis.utils.logger import logger

if tp.TYPE_CHECKING:
    from trellis.core.components.base import Component

__all__ = [
    "Element",
    "props_equal",
]


@dataclass
class Element(KeyTrait):
    """Tree nod e representing a component invocation."""

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

    def __enter__(self) -> Element:
        """Enter a `with` block to collect children for a container component."""
        # Ensure we're inside a render context - containers cannot be used
        # in callbacks or other code outside of rendering
        session = get_active_session()
        if session is None or session.active is None:
            raise RuntimeError(
                f"Cannot use 'with {self.component.name}()' outside of render context. "
                f"Container components must be created during rendering, not in callbacks."
            )

        # Validate that the component accepts children
        if not self.component.is_container:
            raise TypeError(
                f"Component '{self.component.name}' cannot be used with 'with' statement: "
                f"it does not accept children"
            )

        # Validate: can't provide children as both prop and via with block
        if "children" in self.props:
            raise RuntimeError(
                f"Cannot provide 'children' prop and use 'with' block. "
                f"Component: {self.component.name}"
            )

        # Push new frame for children created in this scope
        session.active.frames.push(parent_id=self.id)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: tp.Any,
    ) -> None:
        """Exit the `with` block, storing ChildRefs in props["children"]."""
        session = get_active_session()
        if session is None or session.active is None:
            return

        child_ids = session.active.frames.pop()

        # Don't process children if an exception occurred
        if exc_type is not None:
            return

        logger.debug(
            "Container __exit__ %s: collected %d children",
            self.component.name,
            len(child_ids),
        )

        # Store collected child IDs (for initial render/reconciliation)
        self.child_ids = list(child_ids)

        # Create ChildRefs for the container to use during execution.
        # These are stable references that survive container re-renders.
        children = [ChildRef(id=cid, _session_ref=self._session_ref) for cid in child_ids]
        self.props["children"] = children

        # Re-store element with child_ids and children props set
        session.elements.store(self)


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
