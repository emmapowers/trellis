"""Render function and tree execution."""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
import typing as tp

from trellis.core.callback_context import callback_context
from trellis.core.rendering.active import ActiveRender
from trellis.core.rendering.child_ref import ChildRef
from trellis.core.rendering.element import Element, props_equal
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
from trellis.core.state.ref import Ref, _RefHolder
from trellis.utils.logger import logger

__all__ = [
    "render",
]


# =============================================================================
# Execution Functions (Free Functions)
# =============================================================================


def render(session: RenderSession) -> list[RenderPatch]:
    """Render the session and return patches."""
    with session.lock:
        patches, pending_mounts, pending_unmounts = _render_impl(session)

    # Process hooks AFTER session.active is cleared and lock is released.
    # This allows hooks to safely modify state (which marks elements dirty).
    _process_pending_hooks(session, pending_mounts, pending_unmounts)
    return patches


def _render_impl(
    session: RenderSession,
) -> tuple[list[RenderPatch], list[str], list[str]]:
    """Internal render implementation (called with lock held).

    Returns:
        Tuple of (patches, pending_mounts, pending_unmounts).
        Hooks are processed by the caller after session.active is cleared.
    """
    if get_active_session() is not None:
        raise RuntimeError("Attempted to render with another context active!")

    # Increment render count at the start of every render pass
    session.render_count += 1

    # Create render-scoped state
    session.active = ActiveRender(old_elements=session.elements.clone())
    is_initial = session.root_element_id is None
    root_element: Element | None = None

    try:
        set_active_session(session)

        if is_initial:
            # Initial render - create root element (no execution yet)
            start_time = time.perf_counter()
            logger.debug("Initial render starting (root: %s)", session.root_component.name)

            root_element = session.root_component()
            session.root_element_id = root_element.id

            # Execute the entire tree depth-first
            _execute_tree(session, root_element.id, None)

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.debug(
                "Initial render complete: %d elements in %.2fms",
                len(session.elements),
                elapsed_ms,
            )

        # Process dirty elements one at a time. We pop individually because
        # re-rendering a parent may also render its dirty children inline,
        # clearing their dirty state before we get to them in the loop.
        while session.dirty.has_dirty():
            element_id = session.dirty.pop()
            if element_id is None:
                break

            logger.debug("Rendering dirty element: %s", element_id)

            state = session.states.get(element_id)
            if state:
                old_element = session.elements.get(element_id)
                if old_element:
                    # Create NEW element for re-render. This ensures the old element
                    # can be GC'd and removed from any WeakSets (dependency tracking).
                    # Preserve the element class from the component.
                    element_class = old_element.component.element_class
                    new_element = element_class(
                        component=old_element.component,
                        _session_ref=old_element._session_ref,
                        render_count=session.render_count,
                        props=old_element.props,
                        _key=old_element._key,
                        child_ids=list(old_element.child_ids),
                        id=old_element.id,
                    )
                    session.elements.store(new_element)
                _execute_tree(session, element_id, state.parent_id)
        # Extract pending hooks before clearing session.active
        pending_mounts = session.active.lifecycle.pop_mounts()
        pending_unmounts = session.active.lifecycle.pop_unmounts()

        # Build result patches
        root_element = (
            session.elements.get(session.root_element_id) if session.root_element_id else None
        )
        if is_initial and root_element is not None:
            # Initial render: single RenderAddPatch with root element
            return (
                [
                    RenderAddPatch(
                        parent_id=None,
                        children=(session.root_element_id,) if session.root_element_id else (),
                        element=root_element,
                    )
                ],
                pending_mounts,
                pending_unmounts,
            )

        # Incremental render: return accumulated patches
        patches = session.active.patches.get_all()
        if patches:
            logger.debug("render complete: %d patches", len(patches))
        return patches, pending_mounts, pending_unmounts

    finally:
        set_active_session(None)
        session.active = None


def _execute_single_element(
    session: RenderSession,
    element: Element,
    parent_id: str | None,
) -> Element:
    """Execute a single element and collect its children."""
    assert session.active is not None
    element_id = element.id

    logger.debug(
        "Executing (single) %s (%s), parent=%s",
        element_id,
        element.component.name,
        parent_id,
    )

    # Get or create ElementState. State may already exist if Element.ref()
    # was called before execution (which creates state to store ref_holder).
    state = session.states.get_or_create(element_id)
    if not state.mounted:
        state.parent_id = parent_id
        state.mounted = True
        # Track mount hook (called after render completes)
        session.active.lifecycle.track_mount(element_id)
    else:
        # Re-executing existing element
        state.parent_id = parent_id

    # Clear from dirty tracker - we're executing now
    session.dirty.discard(element_id)

    # Store element early so get_element() works during render for dependency tracking
    session.elements.store(element)

    state.state_call_count = 0

    # Reset exposed_ref before execute so we detect if child calls set_ref()
    state.exposed_ref = None

    # Get props including children if component accepts them
    props = element.props.copy()

    # Set up execution context
    old_element_id = session.active.current_element_id
    session.active.current_element_id = element_id

    # Push a frame for child IDs created during execution
    session.active.frames.push(parent_id=element_id)
    try:
        # Execute the component - children are created via _place() but NOT executed yet
        element.component.execute(**props)

        # Get child IDs from current frame before popping
        frame = session.active.frames.current()
        new_child_ids = list(frame.child_ids) if frame else []

        logger.debug("Execution (single) produced %d children", len(new_child_ids))

        # Wire ref: connect holder to exposed ref, or detach if child stopped exposing
        if state.exposed_ref is not None and state.ref_holder is not None:
            state.ref_holder._attach(state.exposed_ref)
        elif state.exposed_ref is None and state.ref_holder is not None:
            if state.ref_holder:  # was previously attached
                state.ref_holder._detach()

        # Update element in-place with child_ids (execution of children happens in _execute_tree)
        element.child_ids = new_child_ids
        session.elements.store(element)
        return element

    finally:
        session.active.frames.pop()
        session.active.current_element_id = old_element_id


def _execute_tree(
    session: RenderSession,
    element_id: str,
    parent_id: str | None,
    in_added_subtree: bool = False,
) -> None:
    """Execute a element and recursively execute its children."""
    assert session.active is not None
    element = session.elements.get(element_id)
    if element is None:
        return

    old_element = session.active.old_elements.get(element_id)
    state = session.states.get(element_id)

    # REUSE CHECK: If same element object (from _place() reuse), skip execution
    # Just recurse to children in case any were marked dirty independently
    if element is old_element and state and state.mounted and element.id not in session.dirty:
        logger.debug("_execute_tree: reusing %s, recursing to children", element_id)
        for child_id in element.child_ids:
            _execute_tree(session, child_id, element_id, in_added_subtree)
        return

    # Get old children for reconciliation
    old_child_ids = list(old_element.child_ids) if old_element else []

    # Execute this element
    executed_element = _execute_single_element(session, element, parent_id)
    new_child_ids = list(executed_element.child_ids)

    # Clear dirty flag since we just rendered this element
    session.dirty.discard(element_id)

    # Emit UpdatePatch if props or children changed (for incremental re-renders)
    _emit_update_patch_if_changed(session, element_id)

    # Mark this element as processed by updating old_elements snapshot.
    # This prevents double-execution when parent re-renders a child that was
    # already processed in this render pass (element is old_element check will pass).
    session.active.old_elements.store(executed_element)

    # Reconcile children
    if new_child_ids or old_child_ids:
        result = reconcile_children(old_child_ids, new_child_ids)

        logger.debug(
            "_execute_tree reconcile for %s: added=%s, removed=%s, matched=%s",
            element_id,
            [cid.split("/")[-1] for cid in result.added] if result.added else [],
            [cid.split("/")[-1] for cid in result.removed] if result.removed else [],
            [cid.split("/")[-1] for cid in result.matched] if result.matched else [],
        )

        # Process removals first
        # Check if child is still collected (in props["children"]) but just not rendered
        collected_ids = {
            c.id for c in executed_element.props.get("children", []) if isinstance(c, ChildRef)
        }

        for removed_id in result.removed:
            session.active.patches.emit(RenderRemovePatch(element_id=removed_id))
            if removed_id in collected_ids:
                # Still collected, just hidden by container → unmount only
                _unmount_element_tree(session, removed_id)
            else:
                # Not collected anymore → unmount and remove from storage
                _unmount_element_tree(session, removed_id)
                _remove_element_tree(session, removed_id)

        # Build set of added IDs for quick lookup
        added_set = set(result.added)

        # Execute children (added and matched)
        for child_id in result.child_order:
            child_is_added = child_id in added_set

            # Emit AddPatch for newly added subtree roots BEFORE recursing.
            # This ensures parent AddPatch comes before child AddPatch.
            # Skip if we're already inside an added subtree (to avoid duplicates).
            if child_is_added and not in_added_subtree:
                child_element = session.elements.get(child_id)
                if child_element:
                    session.active.patches.emit(
                        RenderAddPatch(
                            parent_id=element_id,
                            children=tuple(result.child_order),
                            element=child_element,
                        )
                    )

            # Recurse into child. If this child is added (or we're already in
            # an added subtree), propagate the flag to skip AddPatch emission.
            _execute_tree(
                session,
                child_id,
                element_id,
                in_added_subtree=(in_added_subtree or child_is_added),
            )


def _unmount_element_tree(session: RenderSession, element_id: str) -> None:
    """Unmount an element tree: call hooks and mark unmounted, but keep Element in storage.

    Used when a container hides a child but the child is still in props["children"].
    The Element stays in session.elements so ChildRef.element still works and the
    child can be rendered again later.
    """
    assert session.active is not None
    state = session.states.get(element_id)
    if state is None or not state.mounted:
        return

    # Unmount children first (depth-first)
    element = session.elements.get(element_id)
    child_count = len(element.child_ids) if element else 0

    logger.debug(
        "Soft unmounting subtree at %s (%d descendants)",
        element_id,
        child_count,
    )

    if element:
        for child_id in element.child_ids:
            _unmount_element_tree(session, child_id)

    # Track unmount hook (called after render completes)
    session.active.lifecycle.track_unmount(element_id)
    state.mounted = False
    session.dirty.discard(element_id)
    # Note: Do NOT remove from session.elements - element can be rendered again


def _remove_element_tree(session: RenderSession, element_id: str) -> None:
    """Remove an element and all its descendants from storage."""
    element = session.elements.get(element_id)
    if element:
        for child_id in element.child_ids:
            _remove_element_tree(session, child_id)
    session.elements.remove(element_id)


def _invoke_lifecycle_hook(
    session: RenderSession,
    element_id: str,
    hook: tp.Any,
    label: str,
) -> None:
    """Invoke a lifecycle hook (sync or async) with proper error handling."""
    if inspect.iscoroutinefunction(hook):

        async def run_async_hook(h: tp.Any = hook) -> None:
            try:
                with callback_context(session, element_id):
                    await h()
            except Exception:
                logging.exception("Error in async %s", label)

        task = asyncio.create_task(run_async_hook())
        session._background_tasks.add(task)
        task.add_done_callback(session._background_tasks.discard)
    else:
        try:
            with callback_context(session, element_id):
                hook()
        except Exception:
            logging.exception("Error in %s", label)


def _call_mount_hooks(session: RenderSession, element_id: str) -> None:
    """Call on_mount() for all Stateful instances on a element."""
    state = session.states.get(element_id)
    if state is None:
        return

    # Get states sorted by call index
    items = list(state.local_state.items())
    items.sort(key=lambda x: x[0][1])

    if items:
        logger.debug("Calling on_mount for %s (%d states)", element_id, len(items))

    for _, stateful in items:
        if isinstance(stateful, _RefHolder):
            continue
        if hasattr(stateful, "on_mount"):
            _invoke_lifecycle_hook(session, element_id, stateful.on_mount, "on_mount")

    # Call Ref.on_mount if exposed_ref is a Ref instance
    if state.exposed_ref is not None and isinstance(state.exposed_ref, Ref):
        _invoke_lifecycle_hook(session, element_id, state.exposed_ref.on_mount, "Ref.on_mount")


def _call_unmount_hooks(session: RenderSession, element_id: str) -> None:
    """Call on_unmount() for all Stateful instances and Ref on a element."""
    state = session.states.get(element_id)
    if state is None:
        return

    # Call Ref.on_unmount if exposed_ref is a Ref instance
    if state.exposed_ref is not None and isinstance(state.exposed_ref, Ref):
        _invoke_lifecycle_hook(session, element_id, state.exposed_ref.on_unmount, "Ref.on_unmount")
        state.exposed_ref = None

    # Detach ref holder on unmount
    if state.ref_holder is not None:
        state.ref_holder._detach()

    # Get states sorted by call index, reversed
    items = list(state.local_state.items())
    items.sort(key=lambda x: x[0][1], reverse=True)

    if items:
        logger.debug("Calling on_unmount for %s", element_id)

    for _, stateful in items:
        if isinstance(stateful, _RefHolder):
            continue
        if hasattr(stateful, "on_unmount"):
            _invoke_lifecycle_hook(session, element_id, stateful.on_unmount, "on_unmount")


def _process_pending_hooks(
    session: RenderSession,
    pending_mounts: list[str],
    pending_unmounts: list[str],
) -> None:
    """Process all pending mount/unmount hooks.

    Called AFTER session.active is cleared, so hooks can safely modify state.
    """
    # Process unmounts first (cleanup before new mounts)
    for element_id in pending_unmounts:
        _call_unmount_hooks(session, element_id)
        # With component identity in IDs, we can safely remove ElementState
        session.states.remove(element_id)

    # Process mounts
    for element_id in pending_mounts:
        _call_mount_hooks(session, element_id)


def _emit_update_patch_if_changed(session: RenderSession, element_id: str) -> None:
    """Emit a RenderUpdatePatch if props or children changed."""
    assert session.active is not None
    element = session.elements.get(element_id)
    if not element:
        return

    # Look up old element from the snapshot taken at start of render
    old_element = session.active.old_elements.get(element_id)

    # New elements should get AddPatch (via reconciliation), not UpdatePatch
    if not old_element:
        return

    # Compare props without serialization
    props_changed = not props_equal(old_element.props, element.props)
    # Check if children order changed
    children_changed = old_element.child_ids != element.child_ids

    # Emit update patch if anything changed
    if props_changed or children_changed:
        session.active.patches.emit(
            RenderUpdatePatch(
                element_id=element_id,
                props=dict(element.props) if props_changed else None,
                children=tuple(element.child_ids) if children_changed else None,
            )
        )
