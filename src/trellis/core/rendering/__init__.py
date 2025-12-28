"""Render pipeline for the Trellis UI framework.

This package provides the core rendering infrastructure:
- `Element`: Immutable tree node representing a component invocation
- `ElementState`: Mutable runtime state for an Element
- `RenderSession`: Manages the render lifecycle and element tree
- `render`: Main render function
"""

from trellis.core.rendering.active import ActiveRender
from trellis.core.rendering.dirty_tracker import DirtyTracker
from trellis.core.rendering.element import Element, props_equal
from trellis.core.rendering.element_state import ElementState, ElementStateStore
from trellis.core.rendering.elements import ElementStore
from trellis.core.rendering.frames import Frame, FrameStack
from trellis.core.rendering.lifecycle import LifecycleTracker
from trellis.core.rendering.patches import (
    PatchCollector,
    RenderAddPatch,
    RenderPatch,
    RenderRemovePatch,
    RenderUpdatePatch,
)
from trellis.core.rendering.reconcile import reconcile_children
from trellis.core.rendering.render import render
from trellis.core.rendering.session import (
    RenderSession,
    get_active_session,
    is_render_active,
    set_active_session,
)

__all__ = [
    "ActiveRender",
    "DirtyTracker",
    "Element",
    "ElementState",
    "ElementStateStore",
    "ElementStore",
    "Frame",
    "FrameStack",
    "LifecycleTracker",
    "PatchCollector",
    "RenderAddPatch",
    "RenderPatch",
    "RenderRemovePatch",
    "RenderSession",
    "RenderUpdatePatch",
    "get_active_session",
    "is_render_active",
    "props_equal",
    "reconcile_children",
    "render",
    "set_active_session",
]
