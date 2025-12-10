"""Core rendering primitives for the Trellis UI framework.

This module implements the two-phase rendering architecture:

1. **Descriptor Phase**: Components create lightweight `ElementDescriptor` objects
   that describe what should be rendered, without actually executing anything.

2. **Execution Phase**: The reconciler compares descriptors with existing elements
   and only executes components when necessary (props changed or marked dirty).

Key Types:
    - `ElementDescriptor`: Immutable description of a component invocation
    - `Element`: Runtime tree node with state, lifecycle hooks, and children
    - `RenderContext`: Manages the render lifecycle and element tree

Example:
    ```python
    @component
    def Counter() -> None:
        state = CounterState()
        Text(f"Count: {state.count}")

    ctx = RenderContext(Counter)
    tree = ctx.render()  # Render and serialize
    # After state changes, call render() again for updated tree
    ```
"""

from __future__ import annotations

import contextvars
import threading
import typing as tp
from dataclasses import dataclass, field, fields

from trellis.utils.lock_helper import ClassWithLock, with_lock

__all__ = [
    "Element",
    "ElementDescriptor",
    "FrozenProps",
    "IComponent",
    "RenderContext",
    "get_active_render_context",
    "set_active_render_context",
]

# Immutable props type for ElementDescriptor - tuple of (key, value) pairs
type FrozenProps = tuple[tuple[str, tp.Any], ...]

# Thread-safe, task-local storage for the active render context.
# Using contextvars ensures each asyncio task or thread has its own context,
# enabling concurrent rendering (e.g., multiple WebSocket connections).
_active_render_context: contextvars.ContextVar[RenderContext | None] = contextvars.ContextVar(
    "active_render_context", default=None
)


def freeze_props(props: dict[str, tp.Any]) -> FrozenProps:
    """Convert a props dictionary to an immutable tuple for comparison.

    Props are frozen so that ElementDescriptor can be immutable and props
    can be compared for equality to determine if re-execution is needed.

    Args:
        props: Dictionary of component properties

    Returns:
        Sorted tuple of (key, value) pairs
    """
    return tuple(sorted(props.items()))


def unfreeze_props(frozen: FrozenProps) -> dict[str, tp.Any]:
    """Convert frozen props back to a mutable dictionary.

    Args:
        frozen: Immutable tuple of (key, value) pairs

    Returns:
        Mutable dictionary of props
    """
    return dict(frozen)


def get_active_render_context() -> RenderContext | None:
    """Get the currently active render context, if any.

    Returns:
        The active RenderContext, or None if not currently rendering
    """
    return _active_render_context.get()


def set_active_render_context(ctx: RenderContext | None) -> None:
    """Set the active render context.

    This is called internally by RenderContext.render_tree() to establish
    the current context for component execution.

    Args:
        ctx: The RenderContext to make active, or None to clear
    """
    _active_render_context.set(ctx)


class IComponent(tp.Protocol):
    """Protocol defining the component interface.

    All components (functional or class-based) must implement this protocol.
    Components are callable and return ElementDescriptors when invoked.
    """

    name: str
    """Human-readable name of the component (used for debugging)."""

    @property
    def react_type(self) -> str:
        """The React component type name used to render this on the client."""
        ...

    def __call__(self, /, **props: tp.Any) -> ElementDescriptor:
        """Create a descriptor for this component with the given props.

        This does NOT execute the component - it only creates a description
        of what should be rendered. Execution happens later during reconciliation.

        Args:
            **props: Properties to pass to the component

        Returns:
            An ElementDescriptor describing this component invocation
        """
        ...

    def execute(self, /, node: Element, **props: tp.Any) -> None:
        """Execute the component to produce child descriptors.

        Called by the reconciler when this component needs to render.
        The component should create child descriptors by calling other
        components or using `with` blocks for containers.

        Args:
            node: The Element this component is rendering into
            **props: Properties passed to the component
        """
        ...


@dataclass(frozen=True)
class ElementDescriptor:
    """Immutable description of a component invocation.

    ElementDescriptor is the core of the lazy rendering system. When you call
    a component like `Button(text="Click me")`, it returns an ElementDescriptor
    rather than immediately executing. The reconciler later decides whether
    to execute based on whether props have changed.

    Descriptors can be used as context managers for container components:

    ```python
    with Column():      # Creates descriptor, pushes to collection stack
        Button()        # Creates descriptor, added to Column's children
        Text("hello")   # Same
    # __exit__ pops Column, stores children, adds to parent
    ```

    Attributes:
        component: The component that will be executed
        key: Optional stable identifier for reconciliation
        props: Immutable tuple of (key, value) property pairs
        children: Child descriptors collected via `with` block
    """

    component: IComponent
    key: str = ""
    props: FrozenProps = ()
    children: tuple[ElementDescriptor, ...] = ()
    _auto_collected: bool = False  # Track if already added to parent

    def __enter__(self) -> ElementDescriptor:
        """Enter a `with` block to collect children for a container component.

        This validates that the component accepts a `children` parameter,
        then pushes a new collection list onto the descriptor stack.

        Returns:
            self, for use in `with ... as` patterns

        Raises:
            TypeError: If the component doesn't have a `children` parameter
            RuntimeError: If called outside of a render context
        """
        import inspect

        # Ensure we're inside a render context - containers cannot be used
        # in callbacks or other code outside of rendering
        ctx = get_active_render_context()
        if ctx is None:
            raise RuntimeError(
                f"Cannot use 'with {self.component.name}()' outside of render context. "
                f"Container components must be created during rendering, not in callbacks."
            )

        # Validate that the component accepts a 'children' parameter
        render_func = getattr(self.component, "render_func", None)
        if render_func is not None:
            sig = inspect.signature(render_func)
            if "children" not in sig.parameters:
                raise TypeError(
                    f"Component '{self.component.name}' cannot be used with 'with' statement: "
                    f"it does not have a 'children' parameter"
                )

        # Push new collection list for children created in this scope
        ctx.push_descriptor_frame()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: tp.Any,
    ) -> None:
        """Exit the `with` block, collecting children and registering with parent.

        Pops the collection list from the stack, stores the collected children
        on this descriptor, and adds this descriptor to the parent's collection
        (if there is a parent scope).

        Args:
            exc_type: Exception type if an error occurred, else None
            exc_val: Exception value if an error occurred, else None
            exc_tb: Traceback if an error occurred, else None
        """
        ctx = get_active_render_context()
        if ctx is None:
            return

        children = ctx.pop_descriptor_frame()

        # Don't process children if an exception occurred
        if exc_type is not None:
            return

        # Validate: can't provide children as both prop and via with block
        if "children" in dict(self.props):
            raise RuntimeError(
                f"Cannot provide 'children' prop and use 'with' block. "
                f"Component: {self.component.name}"
            )

        # Store collected children (use object.__setattr__ since frozen=True)
        object.__setattr__(self, "children", tuple(children))

        # Add self to parent's collection (if inside another with block)
        # Skip if already auto-collected to prevent double-collection
        if ctx.has_active_frame() and not self._auto_collected:
            ctx.add_to_current_frame(self)

    def __call__(self) -> None:
        """Mount this descriptor at the current position (the "child() rule").

        This implements the key behavior for container components:
        - If called inside a `with` block: add to that block's pending children
        - If called outside any `with` block: actually mount via reconciler

        This allows container components to control when and where children
        are mounted by iterating over their `children` prop and calling
        `child()` on each descriptor.

        Raises:
            RuntimeError: If called outside both `with` block and render context
        """
        ctx = get_active_render_context()
        if ctx is not None and ctx.has_active_frame():
            # Inside a `with` block - just add to pending children
            ctx.add_to_current_frame(self)
        elif ctx is not None:
            # Outside `with` block - actually mount via reconciler
            ctx.mount_descriptor(self)
        else:
            raise RuntimeError("Cannot mount descriptor outside of render context")


@dataclass(kw_only=True)
class Element:
    """Runtime tree node representing a mounted component instance.

    Elements are the "live" nodes in the component tree. They hold:
    - Reference to the descriptor that created them
    - Tree structure (parent, children, depth)
    - Local state for Stateful instances
    - Lifecycle state (mounted, dirty)

    Elements are created by the reconciler when mounting new components,
    and are reused across re-renders when props haven't changed.

    Attributes:
        descriptor: The ElementDescriptor that created this element
        children: Child elements in the tree
        parent: Parent element, or None for root
        depth: Depth in the tree (0 for root)
        render_context: The RenderContext managing this element
        dirty: Whether this element needs re-rendering
        stable_id: Server-assigned stable identifier for React reconciliation
    """

    # The descriptor that created this element
    descriptor: ElementDescriptor

    # Runtime tree structure
    children: list[Element] = field(default_factory=list)
    parent: Element | None = None
    depth: int = 0

    # Render context and state
    render_context: RenderContext | None = None
    dirty: bool = False
    _mounted: bool = False

    # Server-assigned stable identifier, used as React key when no user key provided
    stable_id: str = ""

    # Local state storage for Stateful instances.
    # Key is (StateClass, call_index) to ensure consistent ordering.
    _local_state: dict[tuple[type, int], tp.Any] = field(default_factory=dict)
    _state_call_count: int = 0

    # Context storage for state provided via `with state:` blocks.
    # Maps state class to the state instance provided in this element's scope.
    _context: dict[type, tp.Any] = field(default_factory=dict)

    @property
    def component(self) -> IComponent:
        """The component that created this element."""
        return self.descriptor.component

    @property
    def key(self) -> str:
        """The stable key for reconciliation, if any."""
        return self.descriptor.key

    @property
    def properties(self) -> dict[str, tp.Any]:
        """Get props as a mutable dictionary.

        This includes both regular props and children (if any were
        collected via a `with` block).

        Returns:
            Dictionary of all properties including children
        """
        props = unfreeze_props(self.descriptor.props)
        if self.descriptor.children:
            props["children"] = list(self.descriptor.children)
        return props

    def __hash__(self) -> int:
        """Hash by identity since elements are mutable."""
        return id(self)

    def replace(self, other: Element) -> None:
        """Replace all fields of this element with another's values.

        Used during reconciliation to update an element in place while
        preserving its identity (important for external references).

        Args:
            other: Element to copy values from

        Raises:
            AssertionError: If other is a different Element subclass
        """
        assert type(self) is type(
            other
        ), "Can only replace an element with another of the same type!"
        for f in fields(self):
            setattr(self, f.name, getattr(other, f.name))

    def on_mount(self) -> None:
        """Lifecycle hook called when element is added to the tree.

        Override in Element subclasses to perform initialization.
        Called after the element is fully constructed and added to parent.
        """
        pass

    def on_unmount(self) -> None:
        """Lifecycle hook called when element is removed from the tree.

        Override in Element subclasses to perform cleanup.
        Called before the element is removed, while parent is still accessible.
        """
        pass

    def __rich_repr__(self) -> tp.Iterator[tp.Any]:
        """Rich library representation for pretty printing."""
        if self.key:
            yield self.component.name + f" (d={self.depth}, key={self.key})"
        else:
            yield self.component.name + f" (d={self.depth})"
        yield "properties", self.properties
        yield "children", self.children


class RenderContext(ClassWithLock):
    """Manages the rendering lifecycle for a component tree.

    RenderContext is the main entry point for rendering. It:
    - Holds the root component and element tree
    - Tracks which elements are dirty and need re-rendering
    - Manages the render/execute phases
    - Provides thread-safe rendering via locking

    Example:
        ```python
        ctx = RenderContext(MyApp)
        tree = ctx.render()  # Initial render, returns serialized tree

        # After state changes...
        tree = ctx.render()  # Re-renders dirty elements and serializes
        ```

    Attributes:
        root_component: The top-level component
        root_element: The root of the element tree (after first render)
        dirty_elements: Set of elements needing re-render
        rendering: True during descriptor creation phase
        executing: True during component execution phase
    """

    root_component: IComponent
    root_element: Element | None
    dirty_elements: set[Element]
    lock: threading.RLock

    # Render state flags
    rendering: bool  # In descriptor creation phase
    executing: bool  # In execution phase
    _current_node: Element | None  # Element being executed (for state lookup)

    def __init__(self, root: IComponent) -> None:
        """Create a new render context for a root component.

        Args:
            root: The root component to render
        """
        self.root_component = root
        self.root_element = None
        self.dirty_elements = set()
        self.lock = threading.RLock()
        self.rendering = False
        self.executing = False
        self._current_node = None
        # Descriptor stack for collecting children during `with` blocks.
        # Each entry is a list that collects descriptors created within that scope.
        self._descriptor_stack: list[list[ElementDescriptor]] = []
        # Callback registry for this session - maps callback IDs to callables.
        # Scoped to RenderContext to ensure proper cleanup on session end.
        self._callback_registry: dict[str, tp.Callable[..., tp.Any]] = {}
        self._callback_counter: int = 0
        # Element ID counter for stable IDs used as React keys
        self._element_counter: int = 0

    def push_descriptor_frame(self) -> None:
        """Push a new frame for collecting child descriptors.

        Called when entering a `with` block on a container component.
        Child descriptors created in that scope will be added to this frame.
        """
        self._descriptor_stack.append([])

    def pop_descriptor_frame(self) -> list[ElementDescriptor]:
        """Pop and return the current descriptor frame.

        Called when exiting a `with` block. Returns the list of child
        descriptors collected in that scope.

        Returns:
            List of child descriptors from the completed frame
        """
        return self._descriptor_stack.pop()

    def add_to_current_frame(self, descriptor: ElementDescriptor) -> None:
        """Add a descriptor to the current frame if one exists.

        Called when a child component is invoked inside a `with` block.

        Args:
            descriptor: The child descriptor to add
        """
        if self._descriptor_stack:
            self._descriptor_stack[-1].append(descriptor)

    def has_active_frame(self) -> bool:
        """Check if there's an active descriptor collection frame.

        Returns:
            True if inside a `with` block, False otherwise
        """
        return bool(self._descriptor_stack)

    def next_element_id(self) -> str:
        """Generate a unique stable ID for an element.

        IDs are assigned once at element creation and remain stable
        for the element's lifetime. Used as React keys when no
        user-provided key exists.

        Returns:
            A unique string ID (e.g., "e1", "e2", ...)
        """
        self._element_counter += 1
        return f"e{self._element_counter}"

    @with_lock
    def render_tree(self, from_element: Element | None) -> None:
        """Render the component tree, starting from a specific element.

        This is the internal render entry point. It:
        1. Creates descriptors by calling components
        2. Reconciles descriptors against existing elements
        3. Executes components that need updating
        4. Mounts new elements and unmounts removed ones

        For the public API that returns serialized output, use render().

        Args:
            from_element: Element to re-render from, or None for initial render

        Raises:
            RuntimeError: If another render is already in progress
        """
        from trellis.core.reconcile import reconcile

        if get_active_render_context():
            raise RuntimeError("Attempted to start rendering with another context active!")

        try:
            self.rendering = True
            set_active_render_context(self)

            if from_element is None:
                # Initial render - create descriptor tree from root component
                root_desc = self.root_component()
                # Reconcile against None to mount the entire tree
                self.root_element = reconcile(None, root_desc, None, self)
            else:
                # Re-render from a dirty element
                from_element._state_call_count = 0  # Reset for consistent hook ordering
                # Create new descriptor tree for this component with current props
                new_desc = from_element.component(**from_element.properties)
                # Reconcile against the existing element
                reconcile(from_element, new_desc, from_element.parent, self)

        finally:
            self.rendering = False
            set_active_render_context(None)

    @with_lock
    def render_dirty(self) -> None:
        """Re-render all elements marked as dirty.

        Elements are rendered in depth order (shallowest first) to ensure
        parents are updated before children. An element may be skipped if
        it was already rendered as part of its parent's render.
        """
        elements = list(self.dirty_elements)
        # Sort by depth - render parents before children
        elements.sort(key=lambda e: e.depth)

        for element in elements:
            # Check dirty flag again - may have been rendered as part of parent
            if element.dirty:
                self.render_tree(from_element=element)
                element.dirty = False
        self.dirty_elements.clear()

    @with_lock
    def mark_dirty(self, element: Element) -> None:
        """Mark an element as needing re-render.

        Called automatically when state that an element depends on changes.

        Args:
            element: The element to mark dirty
        """
        self.dirty_elements.add(element)
        element.dirty = True

    def mount_descriptor(self, desc: ElementDescriptor) -> Element:
        """Mount a descriptor during component execution.

        This is called by ElementDescriptor.__call__() when a child descriptor
        is invoked outside of any `with` block, meaning it should be mounted
        immediately at the current position in the tree.

        Args:
            desc: The descriptor to mount

        Returns:
            The newly mounted Element

        Raises:
            RuntimeError: If called outside of execution phase
        """
        from trellis.core.reconcile import reconcile

        if not self.executing:
            raise RuntimeError("mount_descriptor called outside of execution phase")

        parent = self._current_node
        return reconcile(None, desc, parent, self)

    @property
    def current_node(self) -> Element | None:
        """The Element currently being executed.

        Used by Stateful to determine which element to cache state on.

        Returns:
            The current element during execution, or None
        """
        return self._current_node

    @property
    def current_element(self) -> Element | None:
        """Alias for current_node (backwards compatibility)."""
        return self._current_node

    def register_callback(self, callback: tp.Callable[..., tp.Any]) -> str:
        """Register a callback and return its ID.

        Callbacks are stored on this RenderContext, ensuring they are
        scoped to the current session and cleaned up properly.

        Args:
            callback: The callable to register

        Returns:
            A unique string ID for this callback (e.g., "cb_1")
        """
        self._callback_counter += 1
        cb_id = f"cb_{self._callback_counter}"
        self._callback_registry[cb_id] = callback
        return cb_id

    def get_callback(self, cb_id: str) -> tp.Callable[..., tp.Any] | None:
        """Retrieve a callback by ID.

        Args:
            cb_id: The callback ID to look up

        Returns:
            The registered callback, or None if not found
        """
        return self._callback_registry.get(cb_id)

    def clear_callbacks(self) -> None:
        """Clear all registered callbacks.

        Called between renders to ensure stale callbacks don't accumulate.
        """
        self._callback_registry.clear()
        self._callback_counter = 0

    def render(self) -> dict[str, tp.Any]:
        """Render and return the serialized element tree.

        This is the main public API for rendering. It:
        1. Clears stale callbacks from the previous render
        2. Renders the tree (initial or re-render of dirty elements)
        3. Serializes the result for transmission

        Returns:
            Serialized element tree as a dict, suitable for JSON/msgpack encoding.
            Callbacks are replaced with {"__callback__": "cb_N"} references.
        """
        from trellis.core.serialization import serialize_element

        self.clear_callbacks()

        if self.root_element is None:
            self.render_tree(from_element=None)
        else:
            self.render_dirty()

        assert self.root_element is not None
        return serialize_element(self.root_element)
