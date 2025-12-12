"""Core rendering primitives for the Trellis UI framework.

This package provides the fundamental building blocks for Trellis applications:

Components:
    - `Component`: Abstract base class for all components
    - `FunctionalComponent`: Component implementation using render functions
    - `component`: Decorator to create components from functions

Rendering:
    - `ElementNode`: Immutable tree node representing a component invocation
    - `ElementState`: Mutable runtime state for a node (keyed by node.id)
    - `RenderTree`: Manages the render lifecycle and node tree

State:
    - `Stateful`: Base class for reactive state with automatic dependency tracking

Example:
    ```python
    from trellis.core import component, RenderTree
    from trellis.core.state import Stateful

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
    - `trellis.core.functional_component`: @component decorator
    - `trellis.core.state`: Reactive state management
    - `trellis.core.reconcile`: Tree reconciliation algorithm
"""

from trellis.core.base_component import *
from trellis.core.functional_component import *
from trellis.core.react_component import *
from trellis.core.rendering import *
