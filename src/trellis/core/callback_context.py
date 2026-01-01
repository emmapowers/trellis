"""Callback context for accessing session state outside render.

This module provides context management for callbacks and hooks that execute
outside the normal render context. When a callback fires (e.g., onClick),
there's no active render session, but the callback may need to access
context-based state like RouterState.

The callback_context context manager sets up the necessary context and
acquires the session lock to prevent concurrent rendering.
"""

from __future__ import annotations

import contextvars
import typing as tp
from contextlib import contextmanager
from dataclasses import dataclass

if tp.TYPE_CHECKING:
    from trellis.core.rendering.element_state import ElementState
    from trellis.core.rendering.session import RenderSession

__all__ = [
    "callback_context",
    "get_callback_element_state",
    "get_callback_node_id",
    "get_callback_session",
]


@dataclass
class _CallbackContext:
    """Internal container for callback context data."""

    session: RenderSession
    node_id: str


# Task-local storage for callback context
_callback_ctx: contextvars.ContextVar[_CallbackContext | None] = contextvars.ContextVar(
    "callback_context", default=None
)


@contextmanager
def callback_context(session: RenderSession, node_id: str) -> tp.Generator[None]:
    """Set up callback context with session lock.

    This context manager should be used when invoking callbacks or hooks
    to provide access to session state. It acquires the session lock to
    prevent concurrent rendering.

    Args:
        session: The render session
        node_id: The ID of the element that triggered the callback

    Yields:
        None

    Example:
        with callback_context(session, node_id):
            callback(*args)
    """
    # Acquire session lock
    session.lock.acquire()
    try:
        # Set callback context
        ctx = _CallbackContext(session=session, node_id=node_id)
        token = _callback_ctx.set(ctx)
        try:
            yield
        finally:
            _callback_ctx.reset(token)
    finally:
        session.lock.release()


def get_callback_session() -> RenderSession:
    """Get the session from the current callback context.

    Returns:
        The RenderSession for the current callback

    Raises:
        RuntimeError: If called outside of callback context
    """
    ctx = _callback_ctx.get()
    if ctx is None:
        raise RuntimeError(
            "Cannot get session outside of callback context. "
            "This function must be called within a callback_context block."
        )
    return ctx.session


def get_callback_node_id() -> str | None:
    """Get the node ID from the current callback context, if any.

    Unlike get_callback_session(), this returns None instead of raising
    when not in callback context. This allows callers to check if they're
    in callback context without try/except.

    Returns:
        The node ID for the current callback, or None if not in callback context
    """
    ctx = _callback_ctx.get()
    if ctx is None:
        return None
    return ctx.node_id


def get_callback_element_state() -> ElementState:
    """Get the element state from the current callback context.

    Returns:
        The ElementState for the element that triggered the callback

    Raises:
        RuntimeError: If called outside of callback context
    """
    ctx = _callback_ctx.get()
    if ctx is None:
        raise RuntimeError(
            "Cannot get element state outside of callback context. "
            "This function must be called within a callback_context block."
        )
    state = ctx.session.states.get(ctx.node_id)
    if state is None:
        # Create state if it doesn't exist (shouldn't happen in practice)
        state = ctx.session.states.get_or_create(ctx.node_id)
    return state
