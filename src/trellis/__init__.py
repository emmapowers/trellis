"""Trellis - A reactive UI framework for Python.

Canonical import style for applications::

    from trellis import component, Stateful, async_main
    from trellis import widgets as w
    from trellis import html as h
    from trellis.widgets import IconName

The trellis package exports core rendering primitives (component, Stateful, etc.)
plus async_main. Widgets and HTML elements are accessed via their respective
submodules. Icons are available via ``trellis.widgets.IconName``.
"""

from trellis.core import (
    ActiveRender,
    Component,
    CompositionComponent,
    DirtyTracker,
    Element,
    ElementState,
    ElementStateStore,
    ElementStore,
    Frame,
    FrameStack,
    Height,
    LifecycleTracker,
    Margin,
    Mutable,
    Padding,
    PatchCollector,
    ReactComponentBase,
    RenderAddPatch,
    RenderPatch,
    RenderRemovePatch,
    RenderSession,
    RenderUpdatePatch,
    Stateful,
    TrackedDict,
    TrackedList,
    TrackedSet,
    Width,
    callback,
    component,
    convert_to_tracked,
    get_active_session,
    is_render_active,
    mutable,
    props_equal,
    react_component_base,
    reconcile_children,
    render,
    set_active_session,
)
from trellis.routing import Route, RouterState, Routes, router
from trellis.utils import async_main

__version__ = "0.1.0"
__all__ = [
    "ActiveRender",
    "Component",
    "CompositionComponent",
    "DirtyTracker",
    "Element",
    "ElementState",
    "ElementStateStore",
    "ElementStore",
    "Frame",
    "FrameStack",
    "Height",
    "LifecycleTracker",
    "Margin",
    "Mutable",
    "Padding",
    "PatchCollector",
    "ReactComponentBase",
    "RenderAddPatch",
    "RenderPatch",
    "RenderRemovePatch",
    "RenderSession",
    "RenderUpdatePatch",
    "Route",
    "RouterState",
    "Routes",
    "Stateful",
    "TrackedDict",
    "TrackedList",
    "TrackedSet",
    "Width",
    "async_main",
    "callback",
    "component",
    "convert_to_tracked",
    "get_active_session",
    "is_render_active",
    "mutable",
    "props_equal",
    "react_component_base",
    "reconcile_children",
    "render",
    "router",
    "set_active_session",
]
