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

import logging
import typing as tp
import weakref
from dataclasses import dataclass, field
from types import TracebackType

if tp.TYPE_CHECKING:
    from trellis.core.rendering.element import ElementNode

from trellis.core.rendering.session import get_active_session, is_render_active
from trellis.core.state.conversion import convert_to_tracked
from trellis.core.state.mutable import record_property_access

logger = logging.getLogger(__name__)


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

    Uses WeakSet[ElementNode] so dependencies are automatically cleaned up
    when nodes are replaced (on re-render) or removed (on unmount).

    Attributes:
        name: The property name being tracked
        watchers: WeakSet of ElementNodes that depend on this property
    """

    name: str
    watchers: weakref.WeakSet[ElementNode] = field(default_factory=weakref.WeakSet)


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

        session = get_active_session()

        # Outside execution context - create normally
        if session is None or not session.is_executing():
            return object.__new__(cls)

        # Use current_node_id and state store for caching
        node_id = session.current_node_id
        assert node_id is not None  # Guaranteed by is_executing() check above

        state = session.states.get_or_create(node_id)
        call_idx = state.state_call_count
        state.state_call_count += 1
        key = (cls, call_idx)

        if key in state.local_state:
            logger.debug(
                "State %s retrieved from cache (call_idx=%d)",
                cls.__name__,
                call_idx,
            )
            return tp.cast("Stateful", state.local_state[key])

        logger.debug(
            "State %s created (new instance, call_idx=%d)",
            cls.__name__,
            call_idx,
        )
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

        # Get render session
        session = get_active_session()

        # Outside render context - return raw value without tracking
        if session is None or not session.is_executing():
            return value

        # Lazy init _state_props (needed when @dataclass doesn't call super().__init__)
        try:
            deps = object.__getattribute__(self, "_state_props")
        except AttributeError:
            deps = {}
            object.__setattr__(self, "_state_props", deps)

        if name not in deps:
            deps[name] = StatePropertyInfo(name=name)
        state_info = deps[name]

        # Add the current ElementNode to watchers (WeakSet auto-cleans on node death)
        node_id = session.current_node_id
        if node_id is not None:
            node = session.elements.get(node_id)
            if node is not None:
                state_info.watchers.add(node)
                logger.debug(
                    "Dependency: %s reads %s.%s",
                    node_id,
                    type(self).__name__,
                    name,
                )

        # Record access for mutable() to capture
        record_property_access(self, name, value)

        return value

    def __setattr__(self, name: str, value: tp.Any) -> None:
        """Set an attribute, marking dependent nodes as dirty.

        When a public attribute is modified, all nodes that previously
        read that attribute are marked dirty and will re-render.

        Plain list/dict/set values are auto-converted to TrackedList/Dict/Set
        for reactive collection tracking.

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

        # Auto-convert plain collections to tracked versions (recursively)
        value = convert_to_tracked(value, owner=self, attr=name)

        # Check if this is initialization vs modification
        # Use __dict__ to check instance attributes only (not class defaults from @dataclass)
        instance_dict = object.__getattribute__(self, "__dict__")
        if name in instance_dict:
            old_value = instance_dict[name]
            is_modification = True
            # Check if value actually changed
            if old_value == value:
                logger.debug(
                    "%s.%s unchanged, skipping",
                    type(self).__name__,
                    name,
                )
                return  # Value unchanged, skip dirty marking
        else:
            old_value = None
            is_modification = False

        # Prevent state modifications during render (but allow initialization)
        if is_modification and is_render_active():
            raise RuntimeError(
                f"Cannot modify state '{name}' during render. "
                f"State changes must happen outside of component execution "
                f"(e.g., in callbacks, mount/unmount hooks, or timers)."
            )

        # Set the value
        object.__setattr__(self, name, value)

        if is_modification:
            logger.debug(
                "%s.%s = %r (was %r)",
                type(self).__name__,
                name,
                value,
                old_value,
            )

        # Mark dependent nodes as dirty (if we have deps tracking initialized)
        try:
            deps = object.__getattribute__(self, "_state_props")
        except AttributeError:
            return  # Not initialized yet

        if name in deps:
            state_info = deps[name]

            # Mark watcher nodes dirty (WeakSet auto-skips dead refs)
            dirty_nodes = []
            for node in state_info.watchers:
                node_session = node._session_ref()
                if node_session is not None:
                    node_session.dirty.mark(node.id)
                    dirty_nodes.append(node.id)

            if dirty_nodes:
                logger.debug("Marking dirty: %s", dirty_nodes)

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
        session = get_active_session()
        if session is None or not session.is_executing():
            raise RuntimeError(
                f"Cannot use 'with {type(self).__name__}()' outside of render context. "
                f"Context API is only available within component execution."
            )

        node_id = session.current_node_id
        assert node_id is not None  # Guaranteed by is_executing() check above
        state = session.states.get_or_create(node_id)
        state.context[type(self)] = self
        logger.debug("Providing %s context at %s", type(self).__name__, node_id)
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
        session = get_active_session()
        if session is None or not session.is_executing():
            raise RuntimeError(
                f"Cannot call {cls.__name__}.from_context() outside of render context. "
                f"Context API is only available within component execution."
            )

        logger.debug("Looking up %s context", cls.__name__)

        # Walk up the parent_id chain with cycle detection
        node_id: str | None = session.current_node_id
        visited: set[str] = set()
        while node_id is not None:
            if node_id in visited:
                break  # Cycle detected
            visited.add(node_id)
            state = session.states.get(node_id)
            if state is not None and cls in state.context:
                logger.debug("Found %s at ancestor %s", cls.__name__, node_id)
                return tp.cast("tp.Self", state.context[cls])
            node_id = state.parent_id if state else None

        # No context found - return default or raise
        logger.debug("No %s found in context", cls.__name__)
        if not isinstance(default, _Missing):
            return default

        raise LookupError(
            f"No {cls.__name__} found in context. "
            f"Ensure a {cls.__name__} instance is provided via "
            f"'with {cls.__name__}():'"
        )
