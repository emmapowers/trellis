"""ChildRef - stable reference to a child element for deferred rendering.

ChildRef provides a stable reference to a child that was collected during a
parent's `with` block. The container can call the ChildRef to render the child
at any position in its render tree.

This solves the problem where conditional containers lose their children when
they don't render them on a subsequent pass. With ChildRef:
- props["children"] contains ChildRefs (stable references)
- child_ids reflects what was actually rendered (for frontend)
"""

from __future__ import annotations

import typing as tp
import weakref
from dataclasses import dataclass

from trellis.core.rendering.session import get_active_session

if tp.TYPE_CHECKING:
    from trellis.core.rendering.element import Element
    from trellis.core.rendering.session import RenderSession

__all__ = ["ChildRef"]


@dataclass(frozen=True)
class ChildRef:
    """Reference to a child element for deferred rendering.

    ChildRef provides a stable reference to a child that was collected
    during a parent's `with` block. The container can call the ChildRef
    to render the child at any position in its render tree.

    Attributes:
        id: The element ID of the referenced child
        _session_ref: Weak reference to the RenderSession
    """

    id: str
    _session_ref: weakref.ref[RenderSession]

    def __call__(self) -> None:
        """Render this child at the current position.

        Adds this child's ID to the current frame's child list,
        causing it to be rendered at this position in the tree.

        Raises:
            RuntimeError: If called outside of render context
        """
        session = get_active_session()
        if session is None or session.active is None:
            raise RuntimeError("Cannot render child outside of render context")
        if not session.active.frames.has_active():
            raise RuntimeError(
                "Cannot call child() outside component execution. "
                "Ensure you're inside a component function or with block."
            )
        session.active.frames.add_child(self.id)

    @property
    def element(self) -> Element | None:
        """Look up the current Element for this child.

        Returns:
            The Element if it exists in the session, None otherwise.
            This may return None if the element was removed from the session
            (e.g., if the parent re-rendered and no longer collects this child).
        """
        session = self._session_ref()
        if session is None:
            return None
        return session.elements.get(self.id)
