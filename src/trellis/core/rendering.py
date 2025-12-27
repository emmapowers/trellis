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
from dataclasses import replace as dataclass_replace

from trellis.core.active_render import ActiveRender
from trellis.core.element_node import ElementNode, props_equal

# Import shared types from base module to avoid circular imports
from trellis.core.element_state import ElementState
from trellis.core.reconcile import ReconcileResult, reconcile_children
from trellis.core.render_patches import (
    RenderAddPatch,
    RenderPatch,
    RenderRemovePatch,
    RenderUpdatePatch,
)
from trellis.core.session import (
    RenderSession,
    get_active_session,
    set_active_session,
)
from trellis.utils.logger import logger

__all__ = [
    "execute_node",
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

    # Create render-scoped state
    session.active = ActiveRender(old_nodes=session.nodes.clone())
    is_initial = session.root_node_id is None
    root_node: ElementNode | None = None

    try:
        set_active_session(session)

        if is_initial:
            # Initial render - eager execution builds entire tree
            start_time = time.perf_counter()
            logger.debug("Initial render starting (root: %s)", session.root_component.name)

            root_node = session.root_component()
            session.root_node_id = root_node.id

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "Initial render complete: %d nodes in %.2fms",
                len(session.nodes),
                elapsed_ms,
            )

        # Process any dirty nodes (handles incremental re-renders,
        # and any nodes marked dirty during initial render)
        while session.dirty.has_dirty():
            dirty_ids = session.dirty.pop_all()

            if dirty_ids:
                logger.debug("Rendering dirty nodes: %s", dirty_ids)

            for node_id in dirty_ids:
                state = session.state.get(node_id)
                if state and state.dirty:
                    state.dirty = False
                    _render_single_node(session, node_id)

        # Process hooks after tree is fully built
        _process_pending_hooks(session)

        # Build result patches
        root_node = session.nodes.get(session.root_node_id) if session.root_node_id else None
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


def _render_single_node(session: RenderSession, node_id: str) -> None:
    """Re-render a single dirty node by ID.

    Uses eager execution to re-render the node. Emits patches for
    any changes during incremental render.

    Args:
        session: The RenderSession
        node_id: The node ID to re-render
    """
    # Get current node (will be re-executed)
    current_node = session.nodes.get(node_id)
    if current_node is None:
        return

    # Get state
    state = session.state.get(node_id)
    if state is None:
        return
    parent_id = state.parent_id

    logger.debug("Re-rendering node %s (%s)", node_id, current_node.component.name)

    # Get old child IDs from snapshot for reconciliation
    assert session.active is not None
    old_node = session.active.old_nodes.get(node_id)
    old_child_ids = list(old_node.child_ids) if old_node and old_node.child_ids else None

    # Re-execute using eager execution
    # _eagerexecute_node handles state reset and child reconciliation
    execute_node(session, current_node, parent_id, old_child_ids=old_child_ids)

    # Emit UpdatePatch if props or children changed (for incremental render)
    _emit_update_patch_if_changed(session, node_id)


def execute_node(
    session: RenderSession,
    node: ElementNode,
    parent_id: str | None,
    old_child_ids: list[str] | None = None,
) -> ElementNode:
    """Execute a component immediately during placement (eager execution).

    This is called from Component._place() when a node cannot be reused.
    It combines mounting and execution in a single operation.

    Args:
        session: The RenderSession
        node: The node to execute (must have id assigned)
        parent_id: Parent node's ID
        old_child_ids: Previous child IDs to reconcile against (None for new node)

    Returns:
        Node with child_ids populated from execution, stored in nodes
    """
    assert session.active is not None
    node_id = node.id

    logger.debug(
        "Executing %s (%s), parent=%s",
        node_id,
        node.component.name,
        parent_id,
    )

    # Create ElementState if this is a new node
    state = session.state.get(node_id)
    if state is None:
        state = ElementState(parent_id=parent_id, mounted=True)
        session.state.set(node_id, state)
        # Track mount hook (called after render completes)
        session.active.lifecycle.track_mount(node_id)
    else:
        # Re-executing existing node
        state.parent_id = parent_id

    # Clear dirty flag - we're executing now, no need to process again
    state.dirty = False
    session.dirty.discard(node_id)

    # Store node early so get_node() works during render for dependency tracking
    session.nodes.store(node)

    # Keep node alive for WeakSet references registered during render.
    # After render, dataclass_replace creates a new result node, but the
    # WeakSet still references this original node. Without this reference,
    # the node would be GC'd and removed from the WeakSet.
    state._render_node = node

    state.state_call_count = 0

    # Get props including children if component accepts them
    props = unfreeze_props(node.props)
    if node.component._has_children_param:
        props["children"] = session.nodes.get_children(node)

    # Set up execution context
    old_node_id = session.active.current_node_id
    session.active.current_node_id = node_id

    # Push a frame for child IDs created during execution
    session.active.frames.push(parent_id=node_id)
    frame_popped = False

    try:
        # Render the component (creates child nodes via component calls)
        node.component.render(**props)

        # Get child IDs created during execution
        new_child_ids = session.active.frames.pop()
        frame_popped = True

        logger.debug("Execution produced %d children", len(new_child_ids))

        # Reconcile or mount children
        if new_child_ids:
            if old_child_ids:
                logger.debug(
                    "Reconciling children for %s: old=%s, new=%s",
                    node.component.name,
                    [cid.split("/")[-1] for cid in old_child_ids],
                    [cid.split("/")[-1] for cid in new_child_ids],
                )
                # Reconcile with old children
                reconcile_result = reconcile_children(old_child_ids, new_child_ids)
                final_child_ids = process_reconcile_result(session, reconcile_result, node_id)
            else:
                # All new children - already executed during creation
                final_child_ids = new_child_ids

            result = dataclass_replace(node, child_ids=tuple(final_child_ids))
        else:
            # No children - unmount any old children
            if old_child_ids:
                for child_id in old_child_ids:
                    _unmount_node_tree(session, child_id)
            result = dataclass_replace(node, child_ids=())

        # Store the executed node
        session.nodes.store(result)

        # Don't update previous state here - let the caller handle it
        # after emitting patches (in _render_single_node)

        return result

    except BaseException:
        if not frame_popped:
            session.active.frames.pop()
        raise

    finally:
        session.active.current_node_id = old_node_id


def _mount_node_tree(session: RenderSession, node_id: str) -> None:
    """Mount a node and all its descendants.

    Mounting is performed parent-first. Hooks are tracked for deferred
    execution after the render phase completes.

    Args:
        session: The RenderSession
        node_id: The ID of the node to mount
    """
    assert session.active is not None
    state = session.state.get(node_id)
    if state is None or state.mounted:
        return

    state.mounted = True
    # Track mount hook (called after render completes)
    session.active.lifecycle.track_mount(node_id)

    # Mount children
    node = session.nodes.get(node_id)
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
    state = session.state.get(node_id)
    if state is None or not state.mounted:
        return

    # Unmount children first (depth-first)
    node = session.nodes.get(node_id)
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

    # Note: RemovePatch is emitted in process_reconcile_result before calling
    # unmount_node_tree, so we don't need to track removed IDs here.

    state.mounted = False
    session.dirty.discard(node_id)


def _call_mount_hooks(session: RenderSession, node_id: str) -> None:
    """Call on_mount() for all Stateful instances on a node.

    Exceptions are logged but not propagated, to ensure all mount hooks run.

    Args:
        session: The RenderSession
        node_id: The node's ID
    """
    state = session.state.get(node_id)
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
    state = session.state.get(node_id)
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
        session.state.remove(node_id)

    # Process mounts
    for node_id in session.active.lifecycle.pop_mounts():
        _call_mount_hooks(session, node_id)


def _emit_update_patch_if_changed(session: RenderSession, node_id: str) -> None:
    """Emit a RenderUpdatePatch if props or children changed.

    Compares current node (in nodes) to old node (in old_nodes snapshot)
    and emits RenderUpdatePatch if there are differences.

    Args:
        session: The RenderSession
        node_id: The node's ID
    """
    assert session.active is not None
    node = session.nodes.get(node_id)
    if not node:
        return

    # Look up old node from the snapshot taken at start of render
    old_node = session.active.old_nodes.get(node_id)

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
                props_changed=props_changed,
                children=node.child_ids if children_changed else None,
            )
        )


def process_reconcile_result(
    session: RenderSession,
    result: ReconcileResult,
    parent_id: str,
) -> list[str]:
    """Process a ReconcileResult and apply side effects.

    Interprets the ReconcileResult from the pure reconciler and performs:
    - Unmounting removed nodes (emits RenderRemovePatch)
    - Mounting added nodes (emits RenderAddPatch)
    - Emitting RenderUpdatePatch for matched nodes with changed props

    Args:
        session: The RenderSession
        result: The ReconcileResult from reconcile_children()
        parent_id: The parent node's ID

    Returns:
        Final list of child IDs after reconciliation
    """
    assert session.active is not None
    logger.debug(
        "Processing reconcile: added=%s, removed=%s, matched=%s",
        [cid.split("/")[-1] for cid in result.added] if result.added else [],
        [cid.split("/")[-1] for cid in result.removed] if result.removed else [],
        [cid.split("/")[-1] for cid in result.matched] if result.matched else [],
    )

    # 1. REMOVE first (cleanup before new state)
    for node_id in result.removed:
        logger.debug("Emitting RenderRemovePatch for %s", node_id.split("/")[-1])
        session.active.patches.emit(RenderRemovePatch(node_id=node_id))
        _unmount_node_tree(session, node_id)

    # 2. ADD new nodes (already executed, just emit patches)
    for node_id in result.added:
        node = session.nodes.get(node_id)
        if node:
            logger.debug(
                "Emitting RenderAddPatch for %s (parent=%s)",
                node_id.split("/")[-1],
                parent_id.split("/")[-1] if parent_id else None,
            )
            state = session.state.get(node_id)
            if state is None:
                state = ElementState(parent_id=parent_id, mounted=True)
                session.state.set(node_id, state)
                session.active.lifecycle.track_mount(node_id)

            session.active.patches.emit(
                RenderAddPatch(
                    parent_id=parent_id,
                    children=tuple(result.child_order),
                    node=node,
                )
            )

    # 3. MATCHED - emit patches for any prop/children changes
    for node_id in result.matched:
        _emit_update_patch_if_changed(session, node_id)

    return result.child_order


def reconcile_node(
    old_node: ElementNode | None,
    new_node: ElementNode,
    parent_id: str | None,
    session: RenderSession,
    *,
    call_hooks: bool = True,
) -> ElementNode:
    """Reconcile an old node with a new node.

    With position-based IDs, the new node already has its ID assigned based on
    tree position. Matching is now by ID, not by component + key.

    This function decides whether to:
    - Create a new node (if old_node is None or component changed at same position)
    - Skip execution (if props unchanged and not dirty)
    - Re-execute (if props changed or dirty)

    Args:
        old_node: Existing node to reconcile against, or None for new mount
        new_node: The new node describing what to render (already has position-based ID)
        parent_id: Parent node's ID (for ElementState.parent_id)
        session: The render session
        call_hooks: Whether to call mount hooks. Set False for recursive calls.

    Returns:
        The reconciled node (also stored in session._nodes)
    """
    node_id = new_node.id

    # Case 1: No old node - mount new
    if old_node is None:
        return execute_node(session, new_node, parent_id)

    # With position-based IDs, old and new nodes at same position have same ID
    # If IDs don't match, that's a bug in caller - they should use ID for lookup
    assert (
        old_node.id == new_node.id
    ), f"reconcile_node called with mismatched IDs: old={old_node.id}, new={new_node.id}"

    # Case 2: Component changed at same position - unmount old, mount new
    if old_node.component != new_node.component:
        logger.debug(
            "reconcile_node %s: component changed %s → %s, remounting",
            node_id,
            old_node.component.name,
            new_node.component.name,
        )
        _unmount_node_tree(session, old_node.id)
        return execute_node(session, new_node, parent_id)

    # Check if this node has been mounted before (has ElementState)
    # With position-based IDs, nodes created in `with` blocks have IDs but
    # haven't been mounted yet - they need to go through execute_node
    existing_state = session.state.get(node_id)
    if existing_state is None:
        # First time seeing this node - mount it
        return execute_node(session, new_node, parent_id)

    # Case 3: Same component - check if we can skip execution
    if old_node.props == new_node.props and not existing_state.dirty:
        logger.debug("reconcile_node %s: skipping (props unchanged, not dirty)", node_id)
        # Props unchanged and not dirty - skip execution entirely!
        # However, we must reconcile with-block child_ids from the parent's execution.
        # These appear on new_node.child_ids when a parent re-renders and produces
        # nested with-block descriptors (e.g., `with Outer(): with Inner(): Leaf()`).
        # Even though this node's props are unchanged, grandchildren may have new props.
        if new_node.child_ids:
            reconcile_result = reconcile_children(
                list(old_node.child_ids), list(new_node.child_ids)
            )
            new_child_ids = process_reconcile_result(session, reconcile_result, node_id)
            result = dataclass_replace(new_node, child_ids=tuple(new_child_ids))
            session.nodes.store(result)
            return result
        # Preserve old child_ids if new_node has none (it's a descriptor, not executed)
        result = (
            dataclass_replace(new_node, child_ids=old_node.child_ids)
            if old_node.child_ids
            else new_node
        )
        session.nodes.store(result)
        return result

    # Case 4: Props changed or dirty - mark dirty for later rendering
    # Keep old child_ids - they'll be reconciled when this node is rendered
    logger.debug(
        "reconcile_node %s: marking dirty (props changed or dirty flag)",
        node_id,
    )
    session.dirty.mark(node_id)
    result = dataclass_replace(new_node, child_ids=old_node.child_ids)
    session.nodes.store(result)
    return result
