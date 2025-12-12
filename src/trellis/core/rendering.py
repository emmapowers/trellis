"""Core rendering primitives for the Trellis UI framework.

This module implements the two-phase rendering architecture:

1. **Node Phase**: Components create lightweight `ElementNode` objects
   that describe what should be rendered, without actually executing anything.

2. **Execution Phase**: The reconciler compares nodes with existing state
   and only executes components when necessary (props changed or marked dirty).

Key Types:
    - `ElementNode`: Immutable tree node representing a component invocation
    - `ElementState`: Mutable runtime state for an ElementNode (keyed by node.id)
    - `RenderTree`: Manages the render lifecycle and node tree

Example:
    ```python
    @component
    def Counter() -> None:
        state = CounterState()
        Text(f"Count: {state.count}")

    tree = RenderTree(Counter)
    result = tree.render()  # Render and serialize
    # After state changes, call render() again for updated tree
    ```
"""

from __future__ import annotations

import contextvars
import threading
import typing as tp
from dataclasses import dataclass, field
from dataclasses import replace as dataclass_replace

from trellis.utils.lock_helper import ClassWithLock, with_lock

__all__ = [
    "ElementNode",
    "ElementState",
    "FrozenProps",
    "IComponent",
    "RenderTree",
    "get_active_render_tree",
    "set_active_render_tree",
]

# Immutable props type for ElementNode - tuple of (key, value) pairs
type FrozenProps = tuple[tuple[str, tp.Any], ...]

# Thread-safe, task-local storage for the active render tree.
# Using contextvars ensures each asyncio task or thread has its own context,
# enabling concurrent rendering (e.g., multiple WebSocket connections).
_active_render_tree: contextvars.ContextVar[RenderTree | None] = contextvars.ContextVar(
    "active_render_tree", default=None
)


def freeze_props(props: dict[str, tp.Any]) -> FrozenProps:
    """Convert a props dictionary to an immutable tuple for comparison.

    Props are frozen so that ElementNode can be immutable and props
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


def get_active_render_tree() -> RenderTree | None:
    """Get the currently active render tree, if any.

    Returns:
        The active RenderTree, or None if not currently rendering
    """
    return _active_render_tree.get()


def set_active_render_tree(tree: RenderTree | None) -> None:
    """Set the active render tree.

    This is called internally by RenderTree.render() to establish
    the current tree for component execution.

    Args:
        tree: The RenderTree to make active, or None to clear
    """
    _active_render_tree.set(tree)


class IComponent(tp.Protocol):
    """Protocol defining the component interface.

    All components (functional or class-based) must implement this protocol.
    Components are callable and return ElementNodes when invoked.
    """

    name: str
    """Human-readable name of the component (used for debugging)."""

    @property
    def react_type(self) -> str:
        """The React component type name used to render this on the client."""
        ...

    def __call__(self, /, **props: tp.Any) -> ElementNode:
        """Create a node for this component with the given props.

        This does NOT execute the component - it only creates a description
        of what should be rendered. Execution happens later during reconciliation.

        Args:
            **props: Properties to pass to the component

        Returns:
            An ElementNode describing this component invocation
        """
        ...

    def execute(self, /, **props: tp.Any) -> None:
        """Execute the component to produce child nodes.

        Called by the reconciler when this component needs to render.
        The component should create child nodes by calling other
        components or using `with` blocks for containers.

        Args:
            **props: Properties passed to the component
        """
        ...


# =============================================================================
# Core types: ElementNode (immutable tree) + ElementState (mutable state)
# =============================================================================


@dataclass(frozen=True)
class ElementNode:
    """Immutable tree node representing a component invocation.

    ElementNode is the immutable type for component nodes in the tree.
    It is frozen for safe comparison and serialization, while mutable runtime
    state is stored separately in ElementState (keyed by node.id in
    RenderTree._element_state).

    Nodes can be used as context managers for container components:

    ```python
    with Column():      # Creates node, pushes to collection stack
        Button()        # Creates node, added to Column's children
        Text("hello")   # Same
    # __exit__ pops Column, stores children, adds to parent
    ```

    When reconciling, nodes are matched by component + key. If matched,
    the new node's ID is replaced with the old node's ID via dataclass.replace()
    to preserve state associations.

    Attributes:
        component: The component that will be/was executed
        props: Immutable tuple of (key, value) property pairs
        key: Optional stable identifier for reconciliation
        children: Child nodes (tuple for immutability)
        id: Stable identifier assigned by RenderTree (empty until reconciled)
    """

    component: IComponent
    props: FrozenProps = ()
    key: str = ""
    children: tuple[ElementNode, ...] = ()
    id: str = ""  # Assigned by RenderTree.next_id() during reconciliation

    # Internal flag for child collection (set via object.__setattr__)
    _auto_collected: bool = False

    @property
    def properties(self) -> dict[str, tp.Any]:
        """Get props as a mutable dictionary, including children if present."""
        props = unfreeze_props(self.props)
        if self.children:
            props["children"] = list(self.children)
        return props

    def __enter__(self) -> ElementNode:
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
        ctx = get_active_render_tree()
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
        on this node, and adds this node to the parent's collection
        (if there is a parent scope).

        Args:
            exc_type: Exception type if an error occurred, else None
            exc_val: Exception value if an error occurred, else None
            exc_tb: Traceback if an error occurred, else None
        """
        ctx = get_active_render_tree()
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
        """Mount this node at the current position (the "child() rule").

        This implements the key behavior for container components:
        - If called inside a `with` block: add to that block's pending children
        - If called outside any `with` block: actually mount via reconciler

        This allows container components to control when and where children
        are mounted by iterating over their `children` prop and calling
        `child()` on each node.

        Raises:
            RuntimeError: If called outside both `with` block and render context
        """
        ctx = get_active_render_tree()
        if ctx is not None and ctx.has_active_frame():
            # Inside a `with` block - just add to pending children
            ctx.add_to_current_frame(self)
        elif ctx is not None:
            # Inside render context but outside any component execution frame
            raise RuntimeError(
                "Cannot call child() outside component execution. "
                "Ensure you're inside a component function or with block."
            )
        else:
            raise RuntimeError("Cannot mount node outside of render context")


@dataclass
class ElementState:
    """Mutable runtime state for an ElementNode.

    ElementState holds all per-node mutable data (local state, context, etc.)
    keyed by node.id in RenderTree._element_state.

    Attributes:
        dirty: Whether this node needs re-rendering
        mounted: Whether on_mount() has been called
        local_state: Cached Stateful instances, keyed by (class, call_index)
        state_call_count: Counter for consistent hook ordering
        context: State context from `with state:` blocks
        parent_id: Parent node's ID (for context walking)
    """

    dirty: bool = False
    mounted: bool = False
    local_state: dict[tuple[type, int], tp.Any] = field(default_factory=dict)
    state_call_count: int = 0
    context: dict[type, tp.Any] = field(default_factory=dict)
    parent_id: str | None = None
    watched_deps: dict[int, tuple[tp.Any, set[str]]] = field(default_factory=dict)
    """Maps id(Stateful) -> (Stateful, {prop_names}) for cleanup on re-render/unmount.

    Before each render, these are cleared from each Stateful._state_deps.
    During render, __getattribute__ re-registers fresh dependencies.
    Uses id() as key since Stateful instances may not be hashable.
    """


class RenderTree(ClassWithLock):
    """Manages the rendering lifecycle for a component tree.

    RenderTree is the main entry point for rendering. It:
    - Holds the root component and node tree
    - Tracks which nodes are dirty and need re-rendering
    - Manages the render/execute phases
    - Provides thread-safe rendering via locking

    Example:
        ```python
        tree = RenderTree(MyApp)
        result = tree.render()  # Initial render, returns serialized tree

        # After state changes...
        result = tree.render()  # Re-renders dirty nodes and serializes
        ```

    Attributes:
        root_component: The top-level component
        root_node: The root of the node tree (after first render)
        rendering: True during descriptor creation phase
        executing: True during component execution phase
    """

    root_component: IComponent
    root_node: ElementNode | None  # Root of ElementNode tree
    _dirty_ids: set[str]  # Dirty node IDs
    lock: threading.RLock

    # Render state flags
    rendering: bool  # In descriptor creation phase
    executing: bool  # In execution phase
    _current_node_id: str | None  # ID of node being executed

    def __init__(self, root: IComponent) -> None:
        """Create a new render context for a root component.

        Args:
            root: The root component to render
        """
        self.root_component = root
        self.root_node = None
        self._dirty_ids: set[str] = set()
        self.lock = threading.RLock()
        self.rendering = False
        self.executing = False
        self._current_node_id: str | None = None
        # Node stack for collecting children during `with` blocks.
        # Each entry is a list that collects nodes created within that scope.
        self._descriptor_stack: list[list[ElementNode]] = []
        # Callback registry for this session - maps callback IDs to callables.
        # Scoped to RenderTree to ensure proper cleanup on session end.
        self._callback_registry: dict[str, tp.Callable[..., tp.Any]] = {}
        self._callback_counter: int = 0
        # Node ID counter for stable IDs used as React keys
        self._node_counter: int = 0
        # State store keyed by node.id
        self._element_state: dict[str, ElementState] = {}

    def push_descriptor_frame(self) -> None:
        """Push a new frame for collecting child nodes.

        Called when entering a `with` block on a container component.
        Child nodes created in that scope will be added to this frame.
        """
        self._descriptor_stack.append([])

    def pop_descriptor_frame(self) -> list[ElementNode]:
        """Pop and return the current node frame.

        Called when exiting a `with` block. Returns the list of child
        nodes collected in that scope.

        Returns:
            List of child nodes from the completed frame
        """
        return self._descriptor_stack.pop()

    def add_to_current_frame(self, node: ElementNode) -> None:
        """Add a node to the current frame if one exists.

        Called when a child component is invoked inside a `with` block.

        Args:
            node: The child node to add
        """
        if self._descriptor_stack:
            self._descriptor_stack[-1].append(node)

    def has_active_frame(self) -> bool:
        """Check if there's an active descriptor collection frame.

        Returns:
            True if inside a `with` block, False otherwise
        """
        return bool(self._descriptor_stack)

    def next_element_id(self) -> str:
        """Generate a unique stable ID for a node.

        IDs are assigned once at node creation and remain stable
        for the node's lifetime. Used as React keys when no
        user-provided key exists.

        Returns:
            A unique string ID (e.g., "e1", "e2", ...)
        """
        self._node_counter += 1
        return f"e{self._node_counter}"

    @with_lock
    def _render_node_tree(self, from_node_id: str | None = None) -> None:
        """Render the component tree using ElementNode architecture.

        This is the new render entry point using ElementNode + ElementState.

        Args:
            from_node_id: Node ID to re-render from, or None for initial render

        Raises:
            RuntimeError: If another render is already in progress
        """
        from trellis.core.reconcile import reconcile_node

        if get_active_render_tree():
            raise RuntimeError("Attempted to start rendering with another context active!")

        try:
            self.rendering = True
            set_active_render_tree(self)

            if from_node_id is None:
                # Initial render - create node tree from root component
                # root_component() returns an ElementNode via Component.__call__
                root_node = self.root_component()

                # Reconcile against None to mount the entire tree
                self.root_node = reconcile_node(None, root_node, None, self)
            else:
                # Re-render from a dirty node
                if self.root_node is None:
                    return

                # Find the node and its parent
                node, parent_id = self._find_node_with_parent(self.root_node, from_node_id)
                if node is None:
                    return

                # Get node state and reset state call count
                state = self._element_state.get(from_node_id)
                if state:
                    state.state_call_count = 0

                # Create new node for this component with current props
                # component(**props) returns an ElementNode via Component.__call__
                # IMPORTANT: Include the key to preserve identity during reconciliation
                props = dict(node.props)
                if node.key:
                    props["key"] = node.key
                has_children_param = getattr(node.component, "_has_children_param", False)
                if node.children and has_children_param:
                    props["children"] = list(node.children)
                new_node = node.component(**props)

                # Reconcile and update tree
                updated_node = reconcile_node(node, new_node, parent_id, self)
                self.root_node = self._replace_node_in_tree(
                    self.root_node, from_node_id, updated_node
                )

        finally:
            self.rendering = False
            set_active_render_tree(None)

    def _find_node_with_parent(
        self, root: ElementNode, target_id: str, parent_id: str | None = None
    ) -> tuple[ElementNode | None, str | None]:
        """Find a node by ID and return it with its parent's ID."""
        if root.id == target_id:
            return root, parent_id
        for child in root.children:
            result, found_parent = self._find_node_with_parent(child, target_id, root.id)
            if result is not None:
                return result, found_parent
        return None, None

    def _replace_node_in_tree(
        self, root: ElementNode, target_id: str, replacement: ElementNode
    ) -> ElementNode:
        """Replace a node in the tree by ID, returning the new tree."""
        if root.id == target_id:
            return replacement

        new_children = tuple(
            self._replace_node_in_tree(child, target_id, replacement) for child in root.children
        )

        if new_children != root.children:
            return dataclass_replace(root, children=new_children)
        return root

    @with_lock
    def _render_dirty_nodes(self) -> None:
        """Re-render all nodes marked as dirty.

        Nodes are rendered in arbitrary order. If a parent and child are both dirty,
        the child's dirty flag will be cleared when the parent re-renders it, so
        we check the dirty flag again before rendering each node.
        """
        dirty_ids = list(self._dirty_ids)

        for node_id in dirty_ids:
            state = self._element_state.get(node_id)
            # Check dirty flag again - may have been rendered as part of parent
            if state and state.dirty:
                self._render_node_tree(from_node_id=node_id)
                state.dirty = False

        self._dirty_ids.clear()

    @property
    def current_node_id(self) -> str | None:
        """The ID of the node currently being executed.

        Used by Stateful to look up state in _element_state.

        Returns:
            The current node ID during execution, or None
        """
        return self._current_node_id

    @with_lock
    def mark_dirty_id(self, node_id: str) -> None:
        """Mark a node ID as needing re-render.

        Args:
            node_id: The ID of the node to mark dirty
        """
        self._dirty_ids.add(node_id)
        if node_id in self._element_state:
            self._element_state[node_id].dirty = True

    def register_callback(self, callback: tp.Callable[..., tp.Any]) -> str:
        """Register a callback and return its ID.

        Callbacks are stored on this RenderTree, ensuring they are
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
        """Render and return the serialized node tree.

        This is the main public API for rendering. It:
        1. Clears stale callbacks from the previous render
        2. Renders the tree (initial or re-render of dirty nodes)
        3. Serializes the result for transmission

        Returns:
            Serialized node tree as a dict, suitable for JSON/msgpack encoding.
            Callbacks are replaced with {"__callback__": "cb_N"} references.
        """
        from trellis.core.serialization import serialize_node

        self.clear_callbacks()

        if self.root_node is None:
            self._render_node_tree(from_node_id=None)
        else:
            self._render_dirty_nodes()

        assert self.root_node is not None
        return serialize_node(self.root_node, self)

    def get_element_state(self, node_id: str) -> ElementState:
        """Get or create ElementState for a node ID.

        Args:
            node_id: The node's stable ID

        Returns:
            The ElementState for this node (created if needed)
        """
        if node_id not in self._element_state:
            self._element_state[node_id] = ElementState()
        return self._element_state[node_id]

    def remove_element_state(self, node_id: str) -> None:
        """Remove ElementState for a node ID (called on unmount).

        Args:
            node_id: The node's stable ID to remove
        """
        self._element_state.pop(node_id, None)
