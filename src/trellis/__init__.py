"""Trellis - A reactive UI framework for Python.

Canonical import style for applications::

    from trellis import App, component, Stateful
    from trellis import widgets as w
    from trellis import html as h
    from trellis.widgets import IconName

The trellis package exports core rendering primitives (component, Stateful, etc.)
plus App. Widgets and HTML elements are accessed via their respective
submodules. Icons are available via ``trellis.widgets.IconName``.
"""

from trellis.app import App
from trellis.core import (
    ActiveRender,
    Component,
    CompositionComponent,
    ContainerElement,
    ContainerTrait,
    DirtyTracker,
    Element,
    ElementState,
    ElementStateStore,
    ElementStore,
    Frame,
    FrameStack,
    LifecycleTracker,
    Mutable,
    PatchCollector,
    ReactComponentBase,
    Ref,
    RenderAddPatch,
    RenderPatch,
    RenderRemovePatch,
    RenderSession,
    RenderUpdatePatch,
    Stateful,
    Tracked,
    TrackedDict,
    TrackedList,
    TrackedSet,
    callback,
    component,
    convert_to_tracked,
    get_ref,
    get_render_session,
    is_render_active,
    mutable,
    props_equal,
    react,
    reconcile_children,
    render,
    set_ref,
    set_render_session,
)
from trellis.core.state import state_var
from trellis.routing import Route, RouterState, Routes, router
from trellis.state import load, on_mount

__version__ = "0.1.0"
__all__ = [
    "ActiveRender",
    "App",
    "Component",
    "CompositionComponent",
    "ContainerElement",
    "ContainerTrait",
    "DirtyTracker",
    "Element",
    "ElementState",
    "ElementStateStore",
    "ElementStore",
    "Frame",
    "FrameStack",
    "LifecycleTracker",
    "Mutable",
    "PatchCollector",
    "ReactComponentBase",
    "Ref",
    "RenderAddPatch",
    "RenderPatch",
    "RenderRemovePatch",
    "RenderSession",
    "RenderUpdatePatch",
    "Route",
    "RouterState",
    "Routes",
    "Stateful",
    "Tracked",
    "TrackedDict",
    "TrackedList",
    "TrackedSet",
    "callback",
    "component",
    "convert_to_tracked",
    "get_ref",
    "get_render_session",
    "is_render_active",
    "load",
    "mutable",
    "on_mount",
    "props_equal",
    "react",
    "reconcile_children",
    "render",
    "router",
    "set_ref",
    "set_render_session",
    "state_var",
]
