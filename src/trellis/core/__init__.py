"""Core rendering primitives for the Trellis UI framework.

This package provides the fundamental building blocks for Trellis applications:

Components:
    - `Component`: Abstract base class for all components
    - `CompositionComponent`: Component implementation using render functions
    - `component`: Decorator to create components from functions

Rendering:
    - `Element`: Immutable tree node representing a component invocation
    - `ElementState`: Mutable runtime state for a node (keyed by node.id)
    - `RenderSession`: Manages the render lifecycle and node tree

State:
    - `Stateful`: Base class for reactive state with automatic dependency tracking

Example:
    ```python
    from trellis.core import component, RenderSession, Stateful

    @dataclass(kw_only=True)
    class AppState(Stateful):
        message: str = "Hello"

    @component
    def App() -> None:
        state = AppState()
        Text(state.message)

    session = RenderSession(App)
    render(session)  # Returns patches
    ```

See Also:
    - `trellis.core.rendering`: Core rendering types and tree
    - `trellis.core.components`: Component base classes and decorators
    - `trellis.core.state`: Reactive state management
"""

# components
from trellis.core.components import (
    Component,
    CompositionComponent,
    Height,
    Margin,
    Padding,
    ReactComponentBase,
    Width,
    component,
    react_component_base,
)

# rendering
from trellis.core.rendering import (
    ActiveRender,
    DirtyTracker,
    Element,
    ElementState,
    ElementStateStore,
    ElementStore,
    Frame,
    FrameStack,
    LifecycleTracker,
    PatchCollector,
    RenderAddPatch,
    RenderPatch,
    RenderRemovePatch,
    RenderSession,
    RenderUpdatePatch,
    get_active_session,
    is_render_active,
    props_equal,
    reconcile_children,
    render,
    set_active_session,
)

# state
from trellis.core.state import (
    Mutable,
    Stateful,
    TrackedDict,
    TrackedList,
    TrackedSet,
    callback,
    convert_to_tracked,
    mutable,
)

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
    "Stateful",
    "TrackedDict",
    "TrackedList",
    "TrackedSet",
    "Width",
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
    "set_active_session",
]
