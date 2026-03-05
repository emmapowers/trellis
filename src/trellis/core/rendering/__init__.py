"""Render pipeline for the Trellis UI framework."""

from trellis.core.rendering.active import ActiveRender
from trellis.core.rendering.child_ref import ChildRef
from trellis.core.rendering.dirty_tracker import DirtyTracker
from trellis.core.rendering.element import ContainerElement, Element, props_equal
from trellis.core.rendering.element_state import ElementState, ElementStateStore
from trellis.core.rendering.element_store import ElementStore
from trellis.core.rendering.frames import Frame, FrameStack
from trellis.core.rendering.lifecycle import LifecycleTracker
from trellis.core.rendering.on_key_trait import OnKeyTrait
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
    get_render_session,
    get_session_registry,
    is_render_active,
    set_render_session,
)
from trellis.core.rendering.traits import ContainerTrait, KeyTrait

__all__ = [
    "ActiveRender",
    "ChildRef",
    "ContainerElement",
    "ContainerTrait",
    "DirtyTracker",
    "Element",
    "ElementState",
    "ElementStateStore",
    "ElementStore",
    "Frame",
    "FrameStack",
    "KeyTrait",
    "LifecycleTracker",
    "OnKeyTrait",
    "PatchCollector",
    "RenderAddPatch",
    "RenderPatch",
    "RenderRemovePatch",
    "RenderSession",
    "RenderUpdatePatch",
    "get_render_session",
    "get_session_registry",
    "is_render_active",
    "props_equal",
    "reconcile_children",
    "render",
    "set_render_session",
]
