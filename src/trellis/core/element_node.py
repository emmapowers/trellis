from __future__ import annotations

import typing as tp
import weakref
from dataclasses import dataclass

from trellis.core.component import Component
from trellis.core.mutable import Mutable
from trellis.core.session import (
    RenderSession,
    get_active_session,
)
from trellis.utils.logger import logger

if tp.TYPE_CHECKING:
    from trellis.core.component import Component
    from trellis.core.rendering import execute_node

__all__ = [
    "ElementNode",
    "freeze_props",
    "props_equal",
    "unfreeze_props",
]


@dataclass(frozen=True)
class ElementNode:
    """Immutable tree node representing a component invocation.

    ElementNode is the immutable type for component nodes in the tree.
    It is frozen for safe comparison and serialization, while mutable runtime
    state is stored separately in ElementState (keyed by node.id in
    RenderSession._element_state).

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
        props: Immutable tuple of (key, value) property pairs
        key: Optional stable identifier for reconciliation
        child_ids: IDs of child nodes (tuple for immutability). Nodes are
            stored flat in RenderSession._nodes and accessed by ID.
        id: Position-based ID assigned at creation time
    """

    component: Component
    _session_ref: weakref.ref[RenderSession]
    props: FrozenProps = ()
    key: str | None = None
    child_ids: tuple[str, ...] = ()
    id: str = ""  # Position-based ID assigned at creation

    # Internal flag for child collection (set via object.__setattr__)
    _auto_collected: bool = False

    @property
    def properties(self) -> dict[str, tp.Any]:
        """Get props as a mutable dictionary, including child_ids if present."""
        props = unfreeze_props(self.props)
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
        if "children" in dict(self.props):
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
        """Exit the `with` block, executing container and registering with parent.

        With eager execution, this:
        1. Pops the collection list from the stack (input children from with block)
        2. Stores input children in child_ids (for render() to access via children prop)
        3. Executes the container's render() method
        4. Adds the executed node to the parent's collection

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

        # Get parent_id from current frame (the grandparent in tree structure)
        frame = session.active.frames.current()
        parent_id = frame.parent_id if frame else None

        # Get old child IDs BEFORE mutating self.child_ids
        # (self may be reused, so self could be the same object as in old_nodes)
        old_output_child_ids = list(self.child_ids) if self.child_ids else None

        logger.debug(
            "Container __exit__ %s: new_input=%s, old_output=%s",
            self.component.name,
            [cid.split("/")[-1] for cid in child_ids] if child_ids else None,
            [cid.split("/")[-1] for cid in old_output_child_ids] if old_output_child_ids else None,
        )

        # Store collected child IDs as input for render()
        object.__setattr__(self, "child_ids", tuple(child_ids))

        executed_node = execute_node(session, self, parent_id, old_child_ids=old_output_child_ids)

        # Add to parent's collection (if inside another with block)
        # Skip if already auto-collected to prevent double-collection
        if session.active.frames.has_active() and not self._auto_collected:
            session.active.frames.add_child(executed_node.id)

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


# Immutable props type for ElementNode - tuple of (key, value) pairs
type FrozenProps = tuple[tuple[str, tp.Any], ...]


def freeze_props(props: dict[str, tp.Any]) -> FrozenProps:
    """Convert a props dictionary to an immutable tuple for comparison.

    Props are frozen so that ElementNode can be immutable and props
    can be compared for equality to determine if re-execution is needed.

    Args:
        props: Dictionary of component properties

    Returns:
        Sorted tuple of (key, value) pairs
    """
    return tuple(sorted(props.items()))


def unfreeze_props(frozen: FrozenProps) -> dict[str, tp.Any]:
    """Convert frozen props back to a mutable dictionary.

    Args:
        frozen: Immutable tuple of (key, value) pairs

    Returns:
        Mutable dictionary of props
    """
    return dict(frozen)


def props_equal(old_props: FrozenProps, new_props: FrozenProps) -> bool:
    """Compare props without serialization.

    Maintains the same semantics as serialized comparison:
    - All callables are considered equal (they serialize to {"__callback__": ...})
    - Mutables compare by owner identity and attr name (their __eq__)
    - Other values compare normally

    Args:
        old_props: Previous props tuple
        new_props: New props tuple

    Returns:
        True if props are semantically equal for rendering purposes
    """
    if len(old_props) != len(new_props):
        return False
    old_dict = dict(old_props)
    new_dict = dict(new_props)
    if old_dict.keys() != new_dict.keys():
        return False
    for key in old_dict:
        if not _values_equal(old_dict[key], new_dict[key]):
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
