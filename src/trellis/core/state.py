"""Reactive state management for the Trellis UI framework.

This module provides the `Stateful` base class for creating reactive state
objects. Stateful objects automatically track which components read their
properties and trigger re-renders when those properties change.

Key Features:
    - **Fine-grained reactivity**: Only components that read a specific property
      re-render when that property changes
    - **Component-local caching**: State instances are cached per-component,
      similar to React hooks
    - **Context API**: Share state with descendants via `with state:` blocks
    - **Lifecycle hooks**: `on_mount()` and `on_unmount()` for setup/cleanup

Example:
    ```python
    @dataclass(kw_only=True)
    class CounterState(Stateful):
        count: int = 0

    @component
    def Counter() -> None:
        state = CounterState()  # Cached across re-renders
        Text(f"Count: {state.count}")  # Registers dependency
        Button(text="+", on_click=lambda: setattr(state, 'count', state.count + 1))
    ```

When `state.count` is modified, only components that accessed `state.count`
will be marked dirty and re-rendered.

Context API example:
    ```python
    @dataclass(kw_only=True)
    class AppState(Stateful):
        user: str = ""

    @component
    def App() -> None:
        with AppState(user="alice"):  # Provide state to descendants
            ChildComponent()

    @component
    def ChildComponent() -> None:
        state = AppState.from_context()  # Retrieve ancestor state
        Label(text=f"Hello, {state.user}!")
    ```
"""

import threading
import typing as tp
from dataclasses import dataclass, field
from types import TracebackType

from trellis.core.rendering import Element, get_active_render_context

# Thread-local context stacks for each Stateful subclass.
# When using `with state:`, the instance is pushed onto its class's stack.
_context_stacks: dict[type["Stateful"], list["Stateful"]] = {}
_context_lock = threading.Lock()


def clear_context_stacks() -> None:
    """Clear all context stacks. For testing only."""
    with _context_lock:
        _context_stacks.clear()


@dataclass(kw_only=True)
class StatePropertyInfo:
    """Tracks which elements depend on a specific state property.

    When a component reads a state property during execution, the element
    is added to this property's dependency set. When the property changes,
    all dependent elements are marked dirty.

    Attributes:
        name: The property name being tracked
        elements: Set of elements that depend on this property
    """

    name: str
    elements: set[Element] = field(default_factory=set)


class Stateful:
    """Base class for reactive state objects.

    Subclasses can use @dataclass or plain classes - your choice:

        @dataclass
        class MyState(Stateful):
            count: int = 0

        # or

        class MyState(Stateful):
            def __init__(self):
                self.count = 0

    State instances are cached per-component during render (like React hooks).
    Accessing state during render registers dependencies for fine-grained updates.
    """

    _state_deps: dict[str, StatePropertyInfo]
    _initialized: bool

    def __init_subclass__(cls, **kwargs: tp.Any) -> None:
        """Set up subclass to skip re-initialization on cached instances.

        When a Stateful subclass is defined, this wraps its `__init__` to
        check if the instance is already initialized (from cache). If so,
        initialization is skipped to preserve existing state values.

        This allows the pattern:
            state = MyState()  # Returns cached instance on re-render
        without re-initializing the state each time.
        """
        super().__init_subclass__(**kwargs)
        original_init = cls.__init__

        def wrapped_init(self: Stateful, *args: tp.Any, **kw: tp.Any) -> None:
            if getattr(self, "_initialized", False):
                return  # Skip - already initialized (cached instance)
            original_init(self, *args, **kw)
            object.__setattr__(self, "_initialized", True)

        cls.__init__ = wrapped_init  # type: ignore[assignment,method-assign]

    def __new__(cls, *args: tp.Any, **kwargs: tp.Any) -> "Stateful":
        """Create or retrieve a cached Stateful instance.

        During component execution, state instances are cached on the
        current element. This implements React-like hooks behavior where
        the same state instance is returned across re-renders.

        The cache key is (class, call_index), ensuring that:
        - Different state classes don't collide
        - Multiple instances of the same class are distinguished by call order

        Outside of execution context, creates a new uncached instance.

        Returns:
            A new or cached Stateful instance
        """
        ctx = get_active_render_context()

        # Outside execution context - create normally
        if ctx is None or not ctx.executing:
            return object.__new__(cls)

        # With lazy rendering, current_node is always correct during execute()
        element = ctx.current_node
        if element is None:
            return object.__new__(cls)

        # Simple key: (class, call_index) - ensures consistent hook ordering
        call_idx = element._state_call_count
        element._state_call_count += 1
        key = (cls, call_idx)

        if key in element._local_state:
            return tp.cast("Stateful", element._local_state[key])  # Return cached instance

        # Create new instance and cache it on the element
        instance = object.__new__(cls)
        element._local_state[key] = instance
        return instance

    def __getattribute__(self, name: str) -> tp.Any:
        """Get an attribute, registering dependencies for public attributes.

        When a public attribute (not starting with '_') is accessed during
        component execution, the current element is registered as dependent
        on that attribute. This enables fine-grained reactivity.

        Args:
            name: The attribute name to access

        Returns:
            The attribute value
        """
        value = object.__getattribute__(self, name)

        # Skip internal attributes - no dependency tracking
        if name.startswith("_"):
            return value

        # Register dependency during execution
        context = get_active_render_context()
        if context is not None and context.executing:
            current_element = context.current_node
            if current_element is not None:
                # Lazy init _state_deps (needed when @dataclass doesn't call super().__init__)
                try:
                    deps = object.__getattribute__(self, "_state_deps")
                except AttributeError:
                    deps = {}
                    object.__setattr__(self, "_state_deps", deps)

                if name not in deps:
                    deps[name] = StatePropertyInfo(name=name)
                state_info = deps[name]
                state_info.elements.add(current_element)

        return value

    def __setattr__(self, name: str, value: tp.Any) -> None:
        """Set an attribute, marking dependent elements as dirty.

        When a public attribute is modified, all elements that previously
        read that attribute are marked dirty and will re-render.

        Args:
            name: The attribute name to set
            value: The new value
        """
        # Always set the value first
        object.__setattr__(self, name, value)

        # Skip internal attributes - no dirty marking
        if name.startswith("_"):
            return

        # Mark dependent elements as dirty (if we have deps tracking initialized)
        try:
            deps = object.__getattribute__(self, "_state_deps")
        except AttributeError:
            return  # Not initialized yet

        if name in deps:
            state_info = deps[name]
            for element in state_info.elements:
                if element.render_context is not None:
                    element.render_context.mark_dirty(element)

    def on_mount(self) -> None:
        """Called after owning element mounts. Override for initialization."""
        pass

    def on_unmount(self) -> None:
        """Called before owning element unmounts. Override for cleanup."""
        pass

    # -------------------------------------------------------------------------
    # Context API - share state with descendant components
    # -------------------------------------------------------------------------

    def __enter__(self) -> tp.Self:
        """Push this state instance onto the context stack for its type.

        This makes the instance retrievable by descendant components via
        `from_context()`. Context is stored on the current element (if rendering)
        so that child components can find it by walking up the element tree.

        Example:
            ```python
            state = AppState(user="alice")
            with state:
                # Descendants can access via AppState.from_context()
                ChildComponent()
            ```

        Returns:
            This instance (for use in `with ... as` pattern)
        """
        cls = type(self)

        # If we're inside a render context, store on the current element
        ctx = get_active_render_context()
        if ctx is not None and ctx.executing and ctx.current_node is not None:
            ctx.current_node._context[cls] = self

        # Also push to global stack for non-render usage
        with _context_lock:
            if cls not in _context_stacks:
                _context_stacks[cls] = []
            _context_stacks[cls].append(self)

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Pop this state instance from the context stack.

        Note: Context stored on elements is NOT removed here - it persists
        for the lifetime of the element so child components can find it.
        """
        with _context_lock:
            cls = type(self)
            stack = _context_stacks.get(cls)
            if stack:
                stack.pop()

    @classmethod
    def from_context(cls) -> tp.Self:
        """Retrieve the nearest ancestor instance of this state type.

        During rendering, walks up the element tree looking for context.
        Outside rendering, uses the global context stack.

        Example:
            ```python
            @component
            def Child() -> None:
                state = AppState.from_context()  # Get ancestor AppState
                Label(text=state.user)
            ```

        Returns:
            The nearest ancestor instance of this type

        Raises:
            LookupError: If no instance of this type is in the context stack
        """
        # During render, walk up the element tree
        ctx = get_active_render_context()
        if ctx is not None and ctx.executing and ctx.current_node is not None:
            element = ctx.current_node
            while element is not None:
                if cls in element._context:
                    return element._context[cls]  # type: ignore[return-value]
                element = element.parent

        # Fall back to global stack (for non-render usage)
        with _context_lock:
            stack = _context_stacks.get(cls)
            if stack:
                return stack[-1]  # type: ignore[return-value]

        raise LookupError(
            f"No {cls.__name__} found in context. "
            f"Ensure a {cls.__name__} instance is provided via "
            f"'with {cls.__name__}():'"
        )

    @classmethod
    def try_from_context(cls) -> tp.Self | None:
        """Retrieve ancestor instance if available, else None.

        Like `from_context()`, but returns None instead of raising if
        no instance is in the context stack.

        Returns:
            The nearest ancestor instance, or None if not found
        """
        # During render, walk up the element tree
        ctx = get_active_render_context()
        if ctx is not None and ctx.executing and ctx.current_node is not None:
            element = ctx.current_node
            while element is not None:
                if cls in element._context:
                    return element._context[cls]  # type: ignore[return-value]
                element = element.parent

        # Fall back to global stack
        with _context_lock:
            stack = _context_stacks.get(cls)
            return stack[-1] if stack else None  # type: ignore[return-value]
