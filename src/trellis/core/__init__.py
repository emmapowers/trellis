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

from trellis.core import components, rendering, state
from trellis.core.components import *
from trellis.core.rendering import *
from trellis.core.state import *

__all__ = [  # noqa: PLE0604
    *components.__all__,
    *rendering.__all__,
    *state.__all__,
]
