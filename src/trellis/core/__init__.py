"""Core rendering primitives for the Trellis UI framework.

This package provides the fundamental building blocks for Trellis applications:

Components:
    - `Component`: Abstract base class for all components
    - `CompositionComponent`: Component implementation using render functions
    - `component`: Decorator to create components from functions

Rendering:
    - `ElementNode`: Immutable tree node representing a component invocation
    - `ElementState`: Mutable runtime state for a node (keyed by node.id)
    - `RenderTree`: Manages the render lifecycle and node tree

State:
    - `Stateful`: Base class for reactive state with automatic dependency tracking

Example:
    ```python
    from trellis.core import component, RenderTree, Stateful

    @dataclass(kw_only=True)
    class AppState(Stateful):
        message: str = "Hello"

    @component
    def App() -> None:
        state = AppState()
        Text(state.message)

    tree = RenderTree(App)
    tree.render()  # Returns serialized tree
    ```

See Also:
    - `trellis.core.rendering`: Core rendering types and tree
    - `trellis.core.base_component`: Abstract component base class
    - `trellis.core.composition_component`: @component decorator
    - `trellis.core.state`: Reactive state management
    - `trellis.core.reconcile`: Tree reconciliation algorithm
"""

from trellis.core.base_component import Component
from trellis.core.composition_component import CompositionComponent, component
from trellis.core.message_handler import MessageHandler
from trellis.core.mutable import Mutable, callback, mutable
from trellis.core.platform import Platform, PlatformArgumentError, PlatformType
from trellis.core.react_component import ReactComponentBase, react_component_base
from trellis.core.rendering import ElementNode, ElementState, RenderTree
from trellis.core.state import Stateful
from trellis.core.style_props import Height, Margin, Padding, Width

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
    "RenderTree",
    "Stateful",
    "Width",
    "callback",
    "component",
    "mutable",
    "react_component_base",
]
