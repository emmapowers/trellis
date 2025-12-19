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

from __future__ import annotations

import typing as tp
import weakref
from dataclasses import dataclass, field
from types import TracebackType

if tp.TYPE_CHECKING:
    from trellis.core.rendering import RenderTree

from trellis.core.rendering import get_active_render_tree


# Sentinel for missing default argument
class _Missing:
    """Sentinel to distinguish 'no default provided' from 'default=None'."""

    pass


_MISSING = _Missing()


@dataclass(kw_only=True)
class StatePropertyInfo:
    """Tracks which nodes depend on a specific state property.

    When a component reads a state property during execution, the node
    is added to this property's dependency set. When the property changes,
    all dependent nodes are marked dirty.

    Attributes:
        name: The property name being tracked
        node_ids: Set of node IDs that depend on this property
        node_trees: Dict mapping node_id to RenderTree for dirty marking
    """

    name: str
    node_ids: set[str] = field(default_factory=set)
    # Map node_id to weakref of RenderTree so we can mark dirty outside of render
    # Uses weakref so sessions can be garbage collected when closed
    node_trees: dict[str, weakref.ref[RenderTree]] = field(default_factory=dict)


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

    _state_props: dict[str, StatePropertyInfo]
    _initialized: bool

    def __new__(cls, *args: tp.Any, **kwargs: tp.Any) -> Stateful:
        """Create or retrieve a cached Stateful instance.

        During component execution, state instances are cached on the
        current node's ElementState. This implements React-like hooks behavior
        where the same state instance is returned across re-renders.

        The cache key is (class, call_index), ensuring that:
        - Different state classes don't collide
        - Multiple instances of the same class are distinguished by call order

        Outside of execution context, creates a new uncached instance.

        Returns:
            A new or cached Stateful instance
        """
        # One-time setup: wrap __init__ to skip re-initialization on cached instances.
        # Done here (not __init_subclass__) so @dataclass has finished setting up __init__.
        # Check __dict__ directly to avoid inheriting from parent class.
        if "_init_wrapped" not in cls.__dict__:
            original_init = cls.__init__

            def wrapped_init(self: Stateful, *a: tp.Any, **kw: tp.Any) -> None:
                if getattr(self, "_initialized", False):
                    return  # Skip - cached instance
                original_init(self, *a, **kw)
                object.__setattr__(self, "_initialized", True)

            cls.__init__ = wrapped_init  # type: ignore[assignment]
            cls._init_wrapped = True

        ctx = get_active_render_tree()

        # Outside execution context - create normally
        # _current_node_id being set indicates we're executing a component
        if ctx is None or ctx._current_node_id is None:
            return object.__new__(cls)

        # Use _current_node_id and _element_state for caching
        node_id = ctx._current_node_id

        state = ctx.get_element_state(node_id)
        call_idx = state.state_call_count
        state.state_call_count += 1
        key = (cls, call_idx)

        if key in state.local_state:
            return tp.cast("Stateful", state.local_state[key])

        instance = object.__new__(cls)
        state.local_state[key] = instance
        return instance

    def __getattribute__(self, name: str) -> tp.Any:
        """Get an attribute, tracking dependencies and recording access for mutable().

        During component execution, property accesses are tracked for:
        1. Dependency registration - so state changes trigger re-renders
        2. Property recording - so mutable() can capture the reference

        Private attributes (starting with '_') and callables are not tracked.

        Args:
            name: The attribute name to access

        Returns:
            The actual attribute value
        """
        value = object.__getattribute__(self, name)

        # Skip internal attributes - no tracking
        if name.startswith("_"):
            return value

        # Skip callables - methods shouldn't be tracked
        if callable(value):
            return value

        # Get render context
        context = get_active_render_tree()

        # Outside render context - return raw value without tracking
        if context is None or context._current_node_id is None:
            return value

        # Inside render context - register dependency

        # Lazy init _state_props (needed when @dataclass doesn't call super().__init__)
        try:
            deps = object.__getattribute__(self, "_state_props")
        except AttributeError:
            deps = {}
            object.__setattr__(self, "_state_props", deps)

        if name not in deps:
            deps[name] = StatePropertyInfo(name=name)
        state_info = deps[name]

        # Track by node ID and store weakref to RenderTree for dirty marking
        node_id = context._current_node_id
        if node_id is not None:
            state_info.node_ids.add(node_id)
            state_info.node_trees[node_id] = weakref.ref(context)

            # Register reverse mapping for cleanup on re-render/unmount
            element_state = context.get_element_state(node_id)
            stateful_id = id(self)
            if stateful_id in element_state.watched_deps:
                element_state.watched_deps[stateful_id][1].add(name)
            else:
                element_state.watched_deps[stateful_id] = (self, {name})

        # Record access for mutable() to capture
        from trellis.core.mutable import record_property_access

        record_property_access(self, name, value)

        return value

    def __setattr__(self, name: str, value: tp.Any) -> None:
        """Set an attribute, marking dependent nodes as dirty.

        When a public attribute is modified, all nodes that previously
        read that attribute are marked dirty and will re-render.

        Args:
            name: The attribute name to set
            value: The new value

        Raises:
            RuntimeError: If called during component rendering. State changes
                must happen outside render (in callbacks, hooks, timers, etc.)
        """
        # Skip internal attributes - no dirty marking needed
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # Check if this is initialization vs modification
        # Use __dict__ to check instance attributes only (not class defaults from @dataclass)
        instance_dict = object.__getattribute__(self, "__dict__")
        if name in instance_dict:
            old_value = instance_dict[name]
            is_modification = True
            # Check if value actually changed
            if old_value == value:
                return  # Value unchanged, skip dirty marking
        else:
            is_modification = False

        # Prevent state modifications during render (but allow initialization)
        if is_modification:
            ctx = get_active_render_tree()
            if ctx is not None and ctx._current_node_id is not None:
                raise RuntimeError(
                    f"Cannot modify state '{name}' during render. "
                    f"State changes must happen outside of component execution "
                    f"(e.g., in callbacks, mount/unmount hooks, or timers)."
                )

        # Set the value
        object.__setattr__(self, name, value)

        # Mark dependent nodes as dirty (if we have deps tracking initialized)
        try:
            deps = object.__getattribute__(self, "_state_props")
        except AttributeError:
            return  # Not initialized yet

        if name in deps:
            state_info = deps[name]

            # Mark node IDs dirty using stored RenderTree weakrefs
            stale_node_ids: list[str] = []
            for node_id in state_info.node_ids:
                tree_ref = state_info.node_trees.get(node_id)
                if tree_ref is not None:
                    tree = tree_ref()
                    if tree is not None:
                        tree.mark_dirty_id(node_id)
                    else:
                        stale_node_ids.append(node_id)

            # Clean up references to garbage-collected RenderTrees
            for node_id in stale_node_ids:
                state_info.node_ids.discard(node_id)
                state_info.node_trees.pop(node_id, None)

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
        `from_context()`. Context is stored on the current node's ElementState.

        Example:
            ```python
            @component
            def Parent() -> None:
                state = AppState(user="alice")
                with state:
                    # Descendants can access via AppState.from_context()
                    ChildComponent()
            ```

        Returns:
            This instance (for use in `with ... as` pattern)

        Raises:
            RuntimeError: If called outside of a render context
        """
        ctx = get_active_render_tree()
        if ctx is None or ctx._current_node_id is None:
            raise RuntimeError(
                f"Cannot use 'with {type(self).__name__}()' outside of render context. "
                f"Context API is only available within component execution."
            )

        node_id = ctx._current_node_id
        state = ctx.get_element_state(node_id)
        state.context[type(self)] = self
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit the context block.

        Note: Context stored on nodes is NOT removed here - it persists
        for the lifetime of the node so child components can find it.
        """
        # Context is stored on the node, not on a stack, so nothing to pop
        pass

    @tp.overload
    @classmethod
    def from_context(cls) -> tp.Self: ...

    @tp.overload
    @classmethod
    def from_context(cls, *, default: None) -> tp.Self | None: ...

    @tp.overload
    @classmethod
    def from_context(cls, *, default: tp.Self) -> tp.Self: ...

    @classmethod
    def from_context(cls, *, default: tp.Self | None | _Missing = _MISSING) -> tp.Self | None:
        """Retrieve the nearest ancestor instance of this state type.

        Walks up the node tree looking for context. Must be called during
        component execution within a render context.

        Example:
            ```python
            @component
            def Child() -> None:
                state = AppState.from_context()  # Get ancestor AppState
                Label(text=state.user)

            @component
            def OptionalChild() -> None:
                # Returns None if no AppState provided
                state = AppState.from_context(default=None)
                if state:
                    Label(text=state.user)
            ```

        Args:
            default: Value to return if no context found. If not provided,
                raises LookupError when context is missing.

        Returns:
            The nearest ancestor instance of this type, or default if not found

        Raises:
            RuntimeError: If called outside of a render context
            LookupError: If no instance of this type is in the context stack
                and no default was provided
        """
        ctx = get_active_render_tree()
        if ctx is None or ctx._current_node_id is None:
            raise RuntimeError(
                f"Cannot call {cls.__name__}.from_context() outside of render context. "
                f"Context API is only available within component execution."
            )

        # Walk up the parent_id chain with cycle detection
        node_id: str | None = ctx._current_node_id
        visited: set[str] = set()
        while node_id is not None:
            if node_id in visited:
                break  # Cycle detected
            visited.add(node_id)
            state = ctx._element_state.get(node_id)
            if state is not None and cls in state.context:
                return tp.cast("tp.Self", state.context[cls])
            node_id = state.parent_id if state else None

        # No context found - return default or raise
        if not isinstance(default, _Missing):
            return default

        raise LookupError(
            f"No {cls.__name__} found in context. "
            f"Ensure a {cls.__name__} instance is provided via "
            f"'with {cls.__name__}():'"
        )
