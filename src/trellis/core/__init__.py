"""Core rendering primitives for the Trellis UI framework.

This package provides the fundamental building blocks for Trellis applications:

Components:
    - `Component`: Abstract base class for all components
    - `FunctionalComponent`: Component implementation using render functions
    - `component`: Decorator to create components from functions

Rendering:
    - `Element`: Runtime tree node representing a mounted component
    - `ElementDescriptor`: Immutable description of a component invocation
    - `RenderContext`: Manages the render lifecycle and element tree

State:
    - `Stateful`: Base class for reactive state with automatic dependency tracking

Example:
    ```python
    from trellis.core import component, RenderContext
    from trellis.core.state import Stateful

    @dataclass(kw_only=True)
    class AppState(Stateful):
        message: str = "Hello"

    @component
    def App() -> None:
        state = AppState()
        Text(state.message)

    ctx = RenderContext(App)
    ctx.render_tree(from_element=None)
    ```

See Also:
    - `trellis.core.rendering`: Core rendering types and context
    - `trellis.core.base_component`: Abstract component base class
    - `trellis.core.functional_component`: @component decorator
    - `trellis.core.state`: Reactive state management
    - `trellis.core.reconcile`: Tree reconciliation algorithm
"""

from trellis.core.base_component import *
from trellis.core.functional_component import *
from trellis.core.react_component import *
from trellis.core.rendering import *
