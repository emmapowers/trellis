"""Core rendering primitives for the Trellis UI framework.

This package provides the fundamental building blocks for Trellis applications:

Components:
    - `Component`: Abstract base class for all components
    - `CompositionComponent`: Component implementation using render functions
    - `component`: Decorator to create components from functions

Rendering:
    - `ElementNode`: Immutable tree node representing a component invocation
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

# Components
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

# Rendering
from trellis.core.rendering import (
    ElementNode,
    ElementState,
    RenderSession,
    render,
)

# State
from trellis.core.state import (
    Mutable,
    Stateful,
    TrackedDict,
    TrackedList,
    TrackedSet,
    callback,
    mutable,
)

# Platform (moved to platforms/common/)
from trellis.platforms.common.base import Platform, PlatformArgumentError, PlatformType
from trellis.platforms.common.handler import MessageHandler

__all__ = [
    "Component",
    "CompositionComponent",
    "ElementNode",
    "ElementState",
    "Height",
    "Margin",
    "MessageHandler",
    "Mutable",
    "Padding",
    "Platform",
    "PlatformArgumentError",
    "PlatformType",
    "ReactComponentBase",
    "RenderSession",
    "Stateful",
    "TrackedDict",
    "TrackedList",
    "TrackedSet",
    "Width",
    "callback",
    "component",
    "mutable",
    "react_component_base",
    "render",
]
