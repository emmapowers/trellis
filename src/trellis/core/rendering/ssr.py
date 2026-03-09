"""SSR-specific rendering: deferred hooks for server-side rendering."""

from __future__ import annotations

from dataclasses import dataclass, field

from trellis.core.rendering.patches import RenderPatch
from trellis.core.rendering.render import _process_pending_hooks, _render_impl
from trellis.core.rendering.session import RenderSession

__all__ = [
    "SSRRenderResult",
    "execute_deferred_hooks",
    "render_for_ssr",
]


@dataclass
class SSRRenderResult:
    """Result of an SSR render pass.

    Contains the render patches plus deferred mount/unmount lists
    that should be replayed when the WebSocket connects.
    """

    patches: list[RenderPatch]
    deferred_mounts: list[str] = field(default_factory=list)
    deferred_unmounts: list[str] = field(default_factory=list)


def render_for_ssr(session: RenderSession) -> SSRRenderResult:
    """Render the session for SSR, deferring mount/unmount hooks.

    Like render(), calls _render_impl() to build the element tree and produce
    patches, but does NOT call _process_pending_hooks(). The deferred hooks
    are returned so they can be replayed when the WebSocket connects.
    """
    with session.lock:
        patches, pending_mounts, pending_unmounts = _render_impl(session)

    return SSRRenderResult(
        patches=patches,
        deferred_mounts=pending_mounts,
        deferred_unmounts=pending_unmounts,
    )


def execute_deferred_hooks(
    session: RenderSession,
    deferred_mounts: list[str],
    deferred_unmounts: list[str],
) -> None:
    """Replay deferred mount/unmount hooks from an SSR render.

    Called when the WebSocket connects and the SSR session is resumed.
    """
    _process_pending_hooks(session, deferred_mounts, deferred_unmounts)
