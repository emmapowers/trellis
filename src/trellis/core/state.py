"""Reactive state management for the Trellis UI framework.

This module provides the `Stateful` base class for creating reactive state
objects. Stateful objects automatically track which components read their
properties and trigger re-renders when those properties change.

Key Features:
    - **Fine-grained reactivity**: Only components that read a specific property
      re-render when that property changes
    - **Component-local caching**: State instances are cached per-component,
      similar to React hooks
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
"""

import typing as tp
from dataclasses import dataclass, field

from trellis.core.rendering import Element, RenderContext, get_active_render_context


@dataclass(kw_only=True)
class StatePropertyInfo:
    """Tracks which elements depend on a specific state property.

    When a component reads a state property during execution, the element
    is added to this property's dependency set. When the property changes,
    all dependent elements are marked dirty.

    Attributes:
        name: The property name being tracked
        elements: Set of (context, element) tuples that depend on this property
    """

    name: str
    elements: set[tuple[RenderContext, Element]] = field(default_factory=set)


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
    _owner_element: Element | None

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
            return element._local_state[key]  # Return cached instance

        # Create new instance and cache it on the element
        instance = object.__new__(cls)
        object.__setattr__(instance, "_owner_element", element)
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
                state_info.elements.add((context, current_element))

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
            for context, element in state_info.elements:
                context.mark_dirty(element)

    def on_mount(self) -> None:
        """Called after owning element mounts. Override for initialization."""
        pass

    def on_unmount(self) -> None:
        """Called before owning element unmounts. Override for cleanup."""
        pass

    @property
    def owner_element(self) -> Element | None:
        """The element that owns this state instance."""
        try:
            return object.__getattribute__(self, "_owner_element")
        except AttributeError:
            return None
