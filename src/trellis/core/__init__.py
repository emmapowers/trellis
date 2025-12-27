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
    - `trellis.core.base_component`: Abstract component base class
    - `trellis.core.composition_component`: @component decorator
    - `trellis.core.state`: Reactive state management
    - `trellis.core.reconcile`: Tree reconciliation algorithm
"""

from trellis.core.component import Component
from trellis.core.composition_component import CompositionComponent, component
from trellis.core.element_node import ElementNode
from trellis.core.element_state import ElementState
from trellis.core.message_handler import MessageHandler
from trellis.core.mutable import Mutable, callback, mutable
from trellis.core.platform import Platform, PlatformArgumentError, PlatformType
from trellis.core.react_component import ReactComponentBase, react_component_base
from trellis.core.rendering import render
from trellis.core.session import RenderSession
from trellis.core.stateful import Stateful
from trellis.core.style_props import Height, Margin, Padding, Width
from trellis.core.tracked import TrackedDict, TrackedList, TrackedSet

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
