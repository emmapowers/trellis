from __future__ import annotations

import typing as tp
import weakref
from dataclasses import dataclass, field

from trellis.core.rendering.session import (
    RenderSession,
    get_active_session,
)
from trellis.core.state.mutable import Mutable
from trellis.utils.logger import logger

if tp.TYPE_CHECKING:
    from trellis.core.components.base import Component

__all__ = [
    "ElementNode",
    "props_equal",
]


@dataclass
class ElementNode:
    """Mutable tree node representing a component invocation.

    ElementNode represents component nodes in the render tree. It is mutable
    to allow in-place updates during rendering. Runtime state is stored
    separately in ElementState (keyed by node.id in RenderSession.states).

    Nodes can be used as context managers for container components:

    ```python
    with Column():      # Creates node, pushes to collection stack
        Button()        # Creates node, added to Column's children
        Text("hello")   # Same
    # __exit__ pops Column, stores children, adds to parent
    ```

    When reconciling, nodes are matched by ID (position + component identity).
    Different component types at the same position get different IDs.

    Attributes:
        component: The component that will be/was executed
        _session_ref: Weak reference to the RenderSession that owns this node
        render_count: The render pass when this node was created (for hash stability)
        props: Component properties as a dictionary
        key: Optional stable identifier for reconciliation
        child_ids: IDs of child nodes. Nodes are stored flat in
            RenderSession.elements and accessed by ID.
        id: Position-based ID assigned at creation time
    """

    component: Component
    _session_ref: weakref.ref[RenderSession]
    render_count: int  # Required, no default - must be set from session.render_count
    props: dict[str, tp.Any] = field(default_factory=dict)
    key: str | None = None
    child_ids: list[str] = field(default_factory=list)
    id: str = ""  # Position-based ID assigned at creation

    def __hash__(self) -> int:
        """Hash based on id, session, and render_count for stable identity.

        This allows nodes to be used in WeakSets for dependency tracking,
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

    def __enter__(self) -> ElementNode:
        """Enter a `with` block to collect children for a container component.

        This validates that the component accepts children and that no children
        prop was provided, then pushes a new collection frame.

        Returns:
            self, for use in `with ... as` patterns

        Raises:
            TypeError: If the component doesn't accept children
            RuntimeError: If called outside of a render context, or if both
                children prop and with block are used
        """
        # Ensure we're inside a render context - containers cannot be used
        # in callbacks or other code outside of rendering
        session = get_active_session()
        if session is None or session.active is None:
            raise RuntimeError(
                f"Cannot use 'with {self.component.name}()' outside of render context. "
                f"Container components must be created during rendering, not in callbacks."
            )

        # Validate that the component accepts children
        if not self.component._has_children_param:
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

        # Push new collection list for children created in this scope
        # parent_id is this node's ID for computing child position IDs
        session.active.frames.push(parent_id=self.id)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: tp.Any,
    ) -> None:
        """Exit the `with` block, storing child_ids for later execution.

        This:
        1. Pops the collection list from the stack (input children from with block)
        2. Stores input children in child_ids (for render() to access via children prop)
        3. Re-stores the node with updated child_ids

        Execution happens later via _execute_tree in rendering.py.
        The node was already auto-collected in _place().

        Args:
            exc_type: Exception type if an error occurred, else None
            exc_val: Exception value if an error occurred, else None
            exc_tb: Traceback if an error occurred, else None
        """
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

        # Store collected child IDs as input for render()
        self.child_ids = list(child_ids)

        # Re-store node with child_ids set (execution happens later in _execute_tree)
        session.elements.store(self)

    def __call__(self) -> None:
        """Mount this node at the current position (the "child() rule").

        This implements the key behavior for container components:
        - If called inside a `with` block: add to that block's pending children
        - If called outside any `with` block: actually mount via reconciler

        This allows container components to control when and where children
        are mounted by iterating over their `children` prop and calling
        `child()` on each node.

        Raises:
            RuntimeError: If called outside both `with` block and render context
        """
        session = get_active_session()
        if (
            session is not None
            and session.active is not None
            and session.active.frames.has_active()
        ):
            # Inside a `with` block - just add to pending children
            session.active.frames.add_child(self.id)
        elif session is not None:
            # Inside render context but outside any component execution frame
            raise RuntimeError(
                "Cannot call child() outside component execution. "
                "Ensure you're inside a component function or with block."
            )
        else:
            raise RuntimeError("Cannot mount node outside of render context")


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

    All callables are considered equal since they serialize identically
    (to {"__callback__": "cb_xxx"}). Mutables use their __eq__ which
    compares owner identity and attr name.

    Args:
        old: Previous value
        new: New value

    Returns:
        True if values are semantically equal for rendering purposes
    """
    # Callables: all callbacks are equal (we don't care about identity)
    if callable(old) and callable(new):
        return True

    # Mutables: use their __eq__ (compares owner+attr)
    if isinstance(old, Mutable) and isinstance(new, Mutable):
        return old == new

    # Everything else: standard equality
    return bool(old == new)
