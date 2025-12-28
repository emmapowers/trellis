"""Core rendering primitives for the Trellis UI framework.

This module implements the two-phase rendering architecture:

1. **Node Phase**: Components create lightweight `ElementNode` objects
   that describe what should be rendered, without actually executing anything.

2. **Execution Phase**: The reconciler compares nodes with existing state
   and only executes components when necessary (props changed or marked dirty).

Key Types:
    - `ElementNode`: Immutable tree node representing a component invocation
    - `ElementState`: Mutable runtime state for an ElementNode (keyed by node.id)

Example:
    ```python
    @component
    def Counter() -> None:
        state = CounterState()
        Text(f"Count: {state.count}")

    session = RenderSession(Counter)
    patches = render(session)  # Returns list of Patch objects
    # Initial render returns single AddPatch with full tree
    # Subsequent renders return patches for changed nodes
    ```
"""

from __future__ import annotations

import logging
import time

from trellis.core.rendering.active import ActiveRender
from trellis.core.rendering.element import ElementNode, props_equal
from trellis.core.rendering.element_state import ElementState
from trellis.core.rendering.patches import (
    RenderAddPatch,
    RenderPatch,
    RenderRemovePatch,
    RenderUpdatePatch,
)
from trellis.core.rendering.reconcile import reconcile_children
from trellis.core.rendering.session import (
    RenderSession,
    get_active_session,
    set_active_session,
)
from trellis.utils.logger import logger

__all__ = [
    "render",
]


# =============================================================================
# Execution Functions (Free Functions)
# =============================================================================


def render(session: RenderSession) -> list[RenderPatch]:
    """Render and return patches describing the session state.

    This is the main public API for rendering. It:
    1. Builds tree via eager execution (initial) or re-renders dirty nodes
    2. Processes any pending mount/unmount hooks
    3. Returns render patches (not serialized)

    For initial render, returns a single RenderAddPatch containing the root node.
    For incremental renders, returns patches for nodes that changed.

    Args:
        session: The RenderSession to render

    Returns:
        List of RenderPatch objects. Caller (MessageHandler) serializes to wire format.
    """
    with session.lock:
        return _render_impl(session)


def _render_impl(session: RenderSession) -> list[RenderPatch]:
    """Internal render implementation (called with lock held)."""
    if get_active_session() is not None:
        raise RuntimeError("Attempted to render with another context active!")

    # Increment render count at the start of every render pass
    session.render_count += 1

    # Create render-scoped state
    session.active = ActiveRender(old_elements=session.elements.clone())
    is_initial = session.root_node_id is None
    root_node: ElementNode | None = None

    try:
        set_active_session(session)

        if is_initial:
            # Initial render - create root node (no execution yet)
            start_time = time.perf_counter()
            logger.debug("Initial render starting (root: %s)", session.root_component.name)

            root_node = session.root_component()
            session.root_node_id = root_node.id

            # Execute the entire tree depth-first
            _execute_tree(session, root_node.id, None)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "Initial render complete: %d nodes in %.2fms",
                len(session.elements),
                elapsed_ms,
            )

        # Process dirty nodes one at a time. We pop individually because
        # re-rendering a parent may also render its dirty children inline,
        # clearing their dirty state before we get to them in the loop.
        while session.dirty.has_dirty():
            node_id = session.dirty.pop()
            if node_id is None:
                break

            logger.debug("Rendering dirty node: %s", node_id)

            state = session.states.get(node_id)
            if state:
                old_node = session.elements.get(node_id)
                if old_node:
                    # Create NEW node for re-render. This ensures the old node
                    # can be GC'd and removed from any WeakSets (dependency tracking).
                    new_node = ElementNode(
                        component=old_node.component,
                        _session_ref=old_node._session_ref,
                        render_count=session.render_count,
                        props=old_node.props,
                        key=old_node.key,
                        child_ids=list(old_node.child_ids),
                        id=old_node.id,
                    )
                    session.elements.store(new_node)
                _execute_tree(session, node_id, state.parent_id)

        # Process hooks after tree is fully built
        _process_pending_hooks(session)

        # Build result patches
        root_node = session.elements.get(session.root_node_id) if session.root_node_id else None
        if is_initial and root_node is not None:
            # Initial render: single RenderAddPatch with root node
            return [
                RenderAddPatch(
                    parent_id=None,
                    children=(session.root_node_id,) if session.root_node_id else (),
                    node=root_node,
                )
            ]

        # Incremental render: return accumulated patches
        patches = session.active.patches.get_all()
        if patches:
            logger.debug("render complete: %d patches", len(patches))
        return patches

    finally:
        set_active_session(None)
        session.active = None


def _execute_single_node(
    session: RenderSession,
    node: ElementNode,
    parent_id: str | None,
) -> ElementNode:
    """Execute a single node's execute() and collect its children.

    This is the new execution model where execution is separated from tree traversal.
    Called by _execute_tree() for each node that needs execution.

    Args:
        session: The RenderSession
        node: The node to execute (must have id assigned)
        parent_id: Parent node's ID

    Returns:
        Node with child_ids populated from execution, stored in nodes
    """
    assert session.active is not None
    node_id = node.id

    logger.debug(
        "Executing (single) %s (%s), parent=%s",
        node_id,
        node.component.name,
        parent_id,
    )

    # Create ElementState if this is a new node
    state = session.states.get(node_id)
    if state is None:
        state = ElementState(parent_id=parent_id, mounted=True)
        session.states.set(node_id, state)
        # Track mount hook (called after render completes)
        session.active.lifecycle.track_mount(node_id)
    else:
        # Re-executing existing node
        state.parent_id = parent_id

    # Clear from dirty tracker - we're executing now
    session.dirty.discard(node_id)

    # Store node early so get_node() works during render for dependency tracking
    session.elements.store(node)

    state.state_call_count = 0

    # Get props including children if component accepts them
    props = node.props.copy()
    if node.component._has_children_param:
        props["children"] = session.elements.get_children(node)

    # Set up execution context
    old_node_id = session.active.current_node_id
    session.active.current_node_id = node_id

    # Push a frame for child IDs created during execution
    session.active.frames.push(parent_id=node_id)

    try:
        # Execute the component - children are created via _place() but NOT executed yet
        node.component.execute(**props)

        # Get child IDs from current frame before popping
        frame = session.active.frames.current()
        new_child_ids = list(frame.child_ids) if frame else []

        logger.debug("Execution (single) produced %d children", len(new_child_ids))

        # Update node in-place with child_ids (execution of children happens in _execute_tree)
        node.child_ids = new_child_ids
        session.elements.store(node)
        return node

    finally:
        session.active.frames.pop()
        session.active.current_node_id = old_node_id


def _execute_tree(
    session: RenderSession,
    node_id: str,
    parent_id: str | None,
) -> None:
    """Execute a node and recursively execute its children.

    This drives all execution after nodes are created by _place()/__exit__().
    Handles reconciliation at the tree level rather than per-node.

    Args:
        session: The RenderSession
        node_id: The ID of the node to execute
        parent_id: Parent node's ID (for ElementState.parent_id)
    """
    assert session.active is not None
    node = session.elements.get(node_id)
    if node is None:
        return

    old_node = session.active.old_elements.get(node_id)
    state = session.states.get(node_id)

    # REUSE CHECK: If same node object (from _place() reuse), skip execution
    # Just recurse to children in case any were marked dirty independently
    if node is old_node and state and state.mounted and node.id not in session.dirty:
        logger.debug("_execute_tree: reusing %s, recursing to children", node_id)
        for child_id in node.child_ids:
            _execute_tree(session, child_id, node_id)
        return

    # Get old children for reconciliation
    old_child_ids = list(old_node.child_ids) if old_node else []

    # Execute this node
    executed_node = _execute_single_node(session, node, parent_id)
    new_child_ids = list(executed_node.child_ids)

    # Clear dirty flag since we just rendered this node
    session.dirty.discard(node_id)

    # Emit UpdatePatch if props or children changed (for incremental re-renders)
    _emit_update_patch_if_changed(session, node_id)

    # Mark this node as processed by updating old_elements snapshot.
    # This prevents double-execution when parent re-renders a child that was
    # already processed in this render pass (node is old_node check will pass).
    session.active.old_elements.store(executed_node)

    # Reconcile children
    if new_child_ids or old_child_ids:
        result = reconcile_children(old_child_ids, new_child_ids)

        logger.debug(
            "_execute_tree reconcile for %s: added=%s, removed=%s, matched=%s",
            node_id,
            [cid.split("/")[-1] for cid in result.added] if result.added else [],
            [cid.split("/")[-1] for cid in result.removed] if result.removed else [],
            [cid.split("/")[-1] for cid in result.matched] if result.matched else [],
        )

        # Process removals first
        for removed_id in result.removed:
            session.active.patches.emit(RenderRemovePatch(node_id=removed_id))
            _unmount_node_tree(session, removed_id)

        # Execute children (added and matched)
        for child_id in result.child_order:
            _execute_tree(session, child_id, node_id)

        # Emit patches for added nodes
        for added_id in result.added:
            child_node = session.elements.get(added_id)
            if child_node:
                session.active.patches.emit(
                    RenderAddPatch(
                        parent_id=node_id,
                        children=tuple(result.child_order),
                        node=child_node,
                    )
                )


def _mount_node_tree(session: RenderSession, node_id: str) -> None:
    """Mount a node and all its descendants.

    Mounting is performed parent-first. Hooks are tracked for deferred
    execution after the render phase completes.

    Args:
        session: The RenderSession
        node_id: The ID of the node to mount
    """
    assert session.active is not None
    state = session.states.get(node_id)
    if state is None or state.mounted:
        return

    state.mounted = True
    # Track mount hook (called after render completes)
    session.active.lifecycle.track_mount(node_id)

    # Mount children
    node = session.elements.get(node_id)
    if node:
        for child_id in node.child_ids:
            _mount_node_tree(session, child_id)


def _unmount_node_tree(session: RenderSession, node_id: str) -> None:
    """Unmount a node and all its descendants.

    Unmounting is performed children-first. Hooks are tracked for deferred
    execution after the render phase completes. State cleanup is also deferred
    so hooks can access local_state.

    Args:
        session: The RenderSession
        node_id: The ID of the node to unmount
    """
    assert session.active is not None
    state = session.states.get(node_id)
    if state is None or not state.mounted:
        return

    # Unmount children first (depth-first)
    node = session.elements.get(node_id)
    child_count = len(node.child_ids) if node else 0

    logger.debug(
        "Unmounting subtree at %s (%d descendants)",
        node_id,
        child_count,
    )

    if node:
        for child_id in node.child_ids:
            _unmount_node_tree(session, child_id)

    # Track unmount hook (called after render completes)
    # State cleanup is deferred to _process_pending_hooks so hooks can access local_state
    session.active.lifecycle.track_unmount(node_id)

    # Note: RemovePatch is emitted in _execute_tree before calling
    # _unmount_node_tree, so we don't need to track removed IDs here.

    # Remove node from storage so it can be garbage collected.
    # This allows WeakSet-based dependency tracking to clean up references.
    session.elements.remove(node_id)

    state.mounted = False
    session.dirty.discard(node_id)


def _call_mount_hooks(session: RenderSession, node_id: str) -> None:
    """Call on_mount() for all Stateful instances on a node.

    Exceptions are logged but not propagated, to ensure all mount hooks run.

    Args:
        session: The RenderSession
        node_id: The node's ID
    """
    state = session.states.get(node_id)
    if state is None:
        return

    # Get states sorted by call index
    items = list(state.local_state.items())
    items.sort(key=lambda x: x[0][1])

    if items:
        logger.debug("Calling on_mount for %s (%d states)", node_id, len(items))

    for _, stateful in items:
        if hasattr(stateful, "on_mount"):
            try:
                stateful.on_mount()
            except Exception as e:
                logging.exception(f"Error in Stateful.on_mount: {e}")


def _call_unmount_hooks(session: RenderSession, node_id: str) -> None:
    """Call on_unmount() for all Stateful instances on a node (reverse order).

    Args:
        session: The RenderSession
        node_id: The node's ID
    """
    state = session.states.get(node_id)
    if state is None:
        return
    # Get states sorted by call index, reversed
    items = list(state.local_state.items())
    items.sort(key=lambda x: x[0][1], reverse=True)

    if items:
        logger.debug("Calling on_unmount for %s", node_id)

    for _, stateful in items:
        if hasattr(stateful, "on_unmount"):
            try:
                stateful.on_unmount()
            except Exception as e:
                logging.exception(f"Error in Stateful.on_unmount: {e}")


def _process_pending_hooks(session: RenderSession) -> None:
    """Process all pending mount/unmount hooks.

    Called at the end of render() after the tree is fully built.
    Hooks are called in no particular order since they are just
    convenience methods and don't interact with DOM.

    Args:
        session: The RenderSession
    """
    assert session.active is not None
    # Process unmounts first (cleanup before new mounts)
    for node_id in session.active.lifecycle.pop_unmounts():
        _call_unmount_hooks(session, node_id)
        # With component identity in IDs, we can safely remove ElementState
        session.states.remove(node_id)

    # Process mounts
    for node_id in session.active.lifecycle.pop_mounts():
        _call_mount_hooks(session, node_id)


def _emit_update_patch_if_changed(session: RenderSession, node_id: str) -> None:
    """Emit a RenderUpdatePatch if props or children changed.

    Compares current node (in nodes) to old node (in old_elements snapshot)
    and emits RenderUpdatePatch if there are differences.

    Args:
        session: The RenderSession
        node_id: The node's ID
    """
    assert session.active is not None
    node = session.elements.get(node_id)
    if not node:
        return

    # Look up old node from the snapshot taken at start of render
    old_node = session.active.old_elements.get(node_id)

    # New nodes should get AddPatch (via reconciliation), not UpdatePatch
    if not old_node:
        return

    # Compare props without serialization
    props_changed = not props_equal(old_node.props, node.props)

    # Check if children order changed
    children_changed = old_node.child_ids != node.child_ids

    # Emit update patch if anything changed
    if props_changed or children_changed:
        session.active.patches.emit(
            RenderUpdatePatch(
                node_id=node_id,
                props=dict(node.props) if props_changed else None,
                children=tuple(node.child_ids) if children_changed else None,
            )
        )
