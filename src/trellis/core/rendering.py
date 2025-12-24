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
import logging
import threading
import typing as tp
from dataclasses import dataclass, field
from dataclasses import replace as dataclass_replace

# Import shared types from base module to avoid circular imports
from trellis.core.base import (
    ElementKind,
    FrozenProps,
    IComponent,
    Trackable,
    freeze_props,
    unfreeze_props,
)
from trellis.core.messages import AddPatch, Patch, RemovePatch, UpdatePatch
from trellis.core.reconcile import ReconcileResult
from trellis.utils.lock_helper import ClassWithLock, with_lock

__all__ = [
    "ElementKind",
    "ElementNode",
    "ElementState",
    "Frame",
    "FrozenProps",
    "IComponent",
    "RenderTree",
    "freeze_props",
    "get_active_render_tree",
    "is_render_active",
    "set_active_render_tree",
    "unfreeze_props",
]


# Thread-safe, task-local storage for the active render tree.
# Using contextvars ensures each asyncio task or thread has its own context,
# enabling concurrent rendering (e.g., multiple WebSocket connections).
_active_render_tree: contextvars.ContextVar[RenderTree | None] = contextvars.ContextVar(
    "active_render_tree", default=None
)


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


def is_render_active() -> bool:
    """Check if currently inside a render context.

    Returns True if there is an active render tree with a node being executed.
    Used by Stateful and tracked collections to determine if dependency
    tracking should occur.

    Returns:
        True if inside render context, False otherwise
    """
    ctx = _active_render_tree.get()
    return ctx is not None and ctx._current_node_id is not None


def _escape_key(key: str) -> str:
    """URL-encode special characters in user-provided keys.

    Keys may contain characters that have special meaning in position IDs:
    - ':' separates keyed prefix from key value
    - '@' separates position from component ID
    - '/' separates path segments

    These are URL-encoded to avoid ambiguity:
    - 'my:key' → 'my%3Akey'
    - 'row/5' → 'row%2F5'
    - 'item@home' → 'item%40home'

    Args:
        key: The user-provided key string

    Returns:
        The key with special characters URL-encoded
    """
    # Only escape the three special characters used in position IDs
    return key.replace("%", "%25").replace(":", "%3A").replace("@", "%40").replace("/", "%2F")


# =============================================================================
# Core Types
# =============================================================================


@dataclass
class Frame:
    """Scope that collects child node IDs during rendering.

    Used during component execution to collect children created in `with` blocks.
    Each `with` block pushes a new Frame onto the stack, and children created
    within have their IDs added to that frame.

    Attributes:
        child_ids: IDs of child nodes collected in this frame
        parent_id: ID of the parent node (for computing child position IDs)
        position: Counter for the next child's position index
    """

    child_ids: list[str] = field(default_factory=list)
    parent_id: str = ""
    position: int = 0


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

    When reconciling, nodes are matched by ID (position + component identity).
    Different component types at the same position get different IDs.

    Attributes:
        component: The component that will be/was executed
        props: Immutable tuple of (key, value) property pairs
        key: Optional stable identifier for reconciliation
        child_ids: IDs of child nodes (tuple for immutability). Nodes are
            stored flat in RenderTree._nodes and accessed by ID.
        id: Position-based ID assigned at creation time
    """

    component: IComponent
    props: FrozenProps = ()
    key: str | None = None
    child_ids: tuple[str, ...] = ()
    id: str = ""  # Position-based ID assigned at creation

    # Internal flag for child collection (set via object.__setattr__)
    _auto_collected: bool = False

    @property
    def properties(self) -> dict[str, tp.Any]:
        """Get props as a mutable dictionary, including child_ids if present."""
        props = unfreeze_props(self.props)
        if self.child_ids:
            props["child_ids"] = list(self.child_ids)
        return props

    def __enter__(self) -> ElementNode:
        """Enter a `with` block to collect children for a container component.

        This validates that the component accepts children and that no children
        prop was provided, then pushes a new collection frame.

        Returns:
            self, for use in `with ... as` patterns

        Raises:
            TypeError: If the component doesn't accept children
            RuntimeError: If called outside of a render context, or if both
                children prop and with block are used
        """
        # Ensure we're inside a render context - containers cannot be used
        # in callbacks or other code outside of rendering
        ctx = get_active_render_tree()
        if ctx is None:
            raise RuntimeError(
                f"Cannot use 'with {self.component.name}()' outside of render context. "
                f"Container components must be created during rendering, not in callbacks."
            )

        # Validate that the component accepts children
        if not self.component._has_children_param:
            raise TypeError(
                f"Component '{self.component.name}' cannot be used with 'with' statement: "
                f"it does not accept children"
            )

        # Validate: can't provide children as both prop and via with block
        if "children" in dict(self.props):
            raise RuntimeError(
                f"Cannot provide 'children' prop and use 'with' block. "
                f"Component: {self.component.name}"
            )

        # Push new collection list for children created in this scope
        # parent_id is this node's ID for computing child position IDs
        ctx.push_frame(parent_id=self.id)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: tp.Any,
    ) -> None:
        """Exit the `with` block, executing container and registering with parent.

        With eager execution, this:
        1. Pops the collection list from the stack (input children from with block)
        2. Stores input children in child_ids (for render() to access via children prop)
        3. Executes the container's render() method
        4. Adds the executed node to the parent's collection

        Args:
            exc_type: Exception type if an error occurred, else None
            exc_val: Exception value if an error occurred, else None
            exc_tb: Traceback if an error occurred, else None
        """
        ctx = get_active_render_tree()
        if ctx is None:
            return

        child_ids = ctx.pop_frame()

        # Don't process children if an exception occurred
        if exc_type is not None:
            return

        # Store collected child IDs as input for render()
        # (render() will replace these with its output children)
        object.__setattr__(self, "child_ids", tuple(child_ids))

        # Get parent_id from current frame (the grandparent in tree structure)
        frame = ctx.current_frame()
        parent_id = frame.parent_id if frame else None

        # Get old node and state for reconciliation
        # Note: Container reuse optimization is skipped for now
        # (input children have already been reuse-checked, and container execution is cheap)
        old_node = ctx.get_node(self.id)

        # Execute the container with its input children
        # old_child_ids is the OLD output children (for reconciliation)
        old_output_child_ids = list(old_node.child_ids) if old_node else None

        executed_node = ctx.eager_execute_node(self, parent_id, old_child_ids=old_output_child_ids)

        # Add to parent's collection (if inside another with block)
        # Skip if already auto-collected to prevent double-collection
        if ctx.has_active_frame() and not self._auto_collected:
            ctx.add_to_current_frame(executed_node)

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
        state_call_count: Counter for consistent Stateful() instantiation ordering
        context: State context from `with state:` blocks
        parent_id: Parent node's ID (for context walking)
        serialized_props: Previous serialized props (for inline patch generation)
        previous_child_ids: Previous child IDs (for inline patch generation)
    """

    dirty: bool = False
    mounted: bool = False
    local_state: dict[tuple[type, int], tp.Any] = field(default_factory=dict)
    state_call_count: int = 0
    context: dict[type, tp.Any] = field(default_factory=dict)
    parent_id: str | None = None
    watched_deps: dict[int, tuple[Trackable, set[tuple[int, tp.Any]]]] = field(default_factory=dict)
    """Maps id(obj) -> (obj, {composite_keys}) for cleanup on re-render/unmount.

    All tracked objects (Stateful, TrackedList, TrackedDict, TrackedSet) use
    the same composite key format: (id(obj), actual_key) where actual_key is
    the property name for Stateful or the collection key for tracked collections.

    Before each render, these are cleared from each tracked object.
    During render, access methods re-register fresh dependencies.
    Uses id() as key since objects may not be hashable.
    """
    # Previous state for inline patch generation (Phase 4)
    serialized_props: dict[str, tp.Any] | None = None
    previous_child_ids: list[str] | None = None


class RenderTree(ClassWithLock):
    """Manages the rendering lifecycle for a component tree.

    RenderTree is the main entry point for rendering. It:
    - Holds the root component and flat node storage
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
        root_node_id: ID of the root node (after first render)
    """

    root_component: IComponent
    root_node_id: str | None  # ID of root node
    _nodes: dict[str, ElementNode]  # Flat node storage (current render)
    _dirty_ids: set[str]  # Dirty node IDs
    lock: threading.RLock
    _current_node_id: str | None  # ID of node being executed

    def __init__(self, root: IComponent) -> None:
        """Create a new render context for a root component.

        Args:
            root: The root component to render
        """
        self.root_component = root
        self.root_node_id = None
        self._nodes: dict[str, ElementNode] = {}  # Flat node storage
        self._dirty_ids: set[str] = set()
        self.lock = threading.RLock()
        self._current_node_id: str | None = None
        # Last property access for mutable()/callback() to capture.
        # Stores (owner, attr_name, value) when a Stateful property is accessed.
        self._last_property_access: tuple[tp.Any, str, tp.Any] | None = None
        # Frame stack for collecting child IDs during `with` blocks.
        # Each entry is a Frame that collects IDs created within that scope.
        self._frame_stack: list[Frame] = []
        # Callback registry for this session - maps callback IDs to callables.
        # Scoped to RenderTree to ensure proper cleanup on session end.
        # IDs are deterministic: "{node_id}:{prop_name}" (e.g., "e5:on_click")
        self._callback_registry: dict[str, tp.Callable[..., tp.Any]] = {}
        # Node ID counter for stable IDs used as React keys
        self._node_counter: int = 0
        # State store keyed by node.id
        self._element_state: dict[str, ElementState] = {}
        # Pending hooks to call after render completes
        self._pending_mounts: list[str] = []
        # With component identity in IDs, different component types at the same
        # position get different IDs, so we can safely clean up state on unmount
        self._pending_unmounts: list[str] = []

        # Patches accumulated during render (Phase 4: inline patch generation)
        self._patches: list[Patch] = []
        # Flag to track if we're in incremental render mode (vs initial render)
        self._is_incremental_render: bool = False

    @property
    def root_node(self) -> ElementNode | None:
        """Get the root node (for backwards compatibility during migration)."""
        if self.root_node_id is None:
            return None
        return self._nodes.get(self.root_node_id)

    def get_node(self, node_id: str) -> ElementNode | None:
        """Get a node by ID from flat storage.

        Args:
            node_id: The node's ID

        Returns:
            The ElementNode, or None if not found
        """
        return self._nodes.get(node_id)

    def store_node(self, node: ElementNode) -> None:
        """Store a node in flat storage.

        Args:
            node: The node to store (must have id assigned)
        """
        self._nodes[node.id] = node

    def get_children(self, node: ElementNode) -> list[ElementNode]:
        """Get the child nodes for a parent node.

        Args:
            node: The parent node

        Returns:
            List of child ElementNodes (looked up from flat storage)
        """
        return [self._nodes[cid] for cid in node.child_ids if cid in self._nodes]

    def push_frame(self, parent_id: str = "") -> Frame:
        """Push a new frame for collecting child nodes.

        Called when entering a `with` block on a container component.
        Child nodes created in that scope will be added to this frame.

        Args:
            parent_id: ID of the parent node (for computing child position IDs)

        Returns:
            The new Frame
        """
        frame = Frame(parent_id=parent_id)
        self._frame_stack.append(frame)
        return frame

    def pop_frame(self) -> list[str]:
        """Pop the current frame and return collected child IDs.

        Called when exiting a `with` block. Returns the child node IDs
        collected in that scope.

        Returns:
            List of child node IDs collected in the frame
        """
        frame = self._frame_stack.pop()
        return frame.child_ids

    def current_frame(self) -> Frame | None:
        """Get the current frame if one exists.

        Returns:
            The current Frame, or None if not in a `with` block
        """
        return self._frame_stack[-1] if self._frame_stack else None

    def add_to_current_frame(self, node: ElementNode) -> None:
        """Add a node to the current frame if one exists.

        Called when a child component is invoked inside a `with` block.
        Stores the node in flat storage and adds its ID to the frame.

        Args:
            node: The child node to add (must have id assigned)
        """
        if self._frame_stack:
            self.store_node(node)
            self._frame_stack[-1].child_ids.append(node.id)

    def has_active_frame(self) -> bool:
        """Check if there's an active frame for collecting children.

        Returns:
            True if inside a `with` block, False otherwise
        """
        return bool(self._frame_stack)

    def next_position_id(self, component: IComponent, key: str | None = None) -> str:
        """Get the next position-based ID for a node being created.

        Position IDs encode tree position AND component identity:
        - Root: "/@{id(component)}"
        - First child: "/@{id(root)}/0@{id(child)}"
        - Keyed child: "/@{id(root)}/:key@{id(child)}"

        Including component identity ensures different component types at the
        same position get different IDs, preventing state collisions.

        Args:
            component: The component being placed (for identity in ID)
            key: Optional user-provided key (replaces position index)

        Returns:
            Position-based ID string with component identity

        Note:
            This increments the frame's position counter even for keyed nodes,
            so keyed nodes consume a position index (matching React semantics).
        """
        comp_id = id(component)

        if not self._frame_stack:
            # No active frame - we're at root
            return f"/@{comp_id}"

        frame = self._frame_stack[-1]
        parent_id = frame.parent_id
        position = frame.position
        frame.position += 1

        # Escape special characters in user-provided keys
        escaped_key = _escape_key(key) if key else None

        # Handle root case - parent_id is "/@..." so we append directly
        if escaped_key:
            return f"{parent_id}/:{escaped_key}@{comp_id}"
        return f"{parent_id}/{position}@{comp_id}"

    @with_lock
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
    def _render_node_tree(self) -> None:
        """Build the initial component tree via eager execution.

        With eager execution, calling the root component triggers a cascade:
        1. root_component() calls _place() on the root
        2. _place() calls eager_execute_node() which executes render()
        3. render() creates children via component calls
        4. Each child's _place() calls eager_execute_node() recursively
        5. The entire tree is built before this method returns

        Raises:
            RuntimeError: If another render is already in progress
        """
        if get_active_render_tree():
            raise RuntimeError("Attempted to start rendering with another context active!")

        try:
            set_active_render_tree(self)

            # Initial render - eager execution builds the entire tree
            # root_component() → _place() → eager_execute_node() → tree built
            root_node = self.root_component()
            self.root_node_id = root_node.id

        finally:
            set_active_render_tree(None)

    @with_lock
    def _render_dirty_nodes(self) -> None:
        """Render all nodes marked as dirty.

        Loops until no more dirty nodes exist, since rendering a node may
        mark new nodes dirty (e.g., newly mounted children).

        Nodes are rendered by calling execute_node directly, which:
        1. Calls the component's render() method
        2. Reconciles resulting children against existing children
        3. May mark new children dirty (which get rendered in next iteration)
        """
        if get_active_render_tree() is not None:
            raise RuntimeError("Attempted to render dirty nodes with another context active!")

        try:
            set_active_render_tree(self)

            while self._dirty_ids:
                # Take snapshot of current dirty IDs
                dirty_ids = list(self._dirty_ids)
                self._dirty_ids.clear()

                for node_id in dirty_ids:
                    state = self._element_state.get(node_id)
                    # Check dirty flag - may have been rendered as part of parent
                    if state and state.dirty:
                        state.dirty = False
                        self._render_single_node(node_id)
        finally:
            set_active_render_tree(None)

    def _render_single_node(self, node_id: str) -> None:
        """Re-render a single dirty node by ID.

        Uses eager execution to re-render the node. Emits patches for
        any changes during incremental render.
        """
        old_node = self._nodes.get(node_id)
        if old_node is None:
            return

        # Get state
        state = self._element_state.get(node_id)
        if state is None:
            return
        parent_id = state.parent_id

        # Get old child IDs for reconciliation
        old_child_ids = list(old_node.child_ids) if old_node.child_ids else None

        # Re-execute using eager execution
        # eager_execute_node handles state reset and child reconciliation
        self.eager_execute_node(old_node, parent_id, old_child_ids=old_child_ids)

        # Emit UpdatePatch if props or children changed (for incremental render)
        # Note: _emit_update_patch_if_changed also updates previous state
        self._emit_update_patch_if_changed(node_id, old_node)

    def eager_execute_node(
        self,
        node: ElementNode,
        parent_id: str | None,
        old_child_ids: list[str] | None = None,
    ) -> ElementNode:
        """Execute a component immediately during placement (eager execution).

        This is called from Component._place() when a node cannot be reused.
        It combines mounting and execution in a single operation.

        Args:
            node: The node to execute (must have id assigned)
            parent_id: Parent node's ID
            old_child_ids: Previous child IDs to reconcile against (None for new node)

        Returns:
            Node with child_ids populated from execution, stored in _nodes
        """
        from trellis.core.reconcile import reconcile_node_children

        node_id = node.id

        # Create ElementState if this is a new node
        state = self._element_state.get(node_id)
        if state is None:
            state = ElementState(parent_id=parent_id, mounted=True)
            self._element_state[node_id] = state
            # Track mount hook (called after render completes)
            self.track_mount(node_id)
        else:
            # Re-executing existing node - clear dependencies and reset call count
            self.clear_node_dependencies(node_id)
            state.parent_id = parent_id

        # Clear dirty flag - we're executing now, no need to process again
        state.dirty = False
        self._dirty_ids.discard(node_id)

        state.state_call_count = 0

        # Get props including children if component accepts them
        props = unfreeze_props(node.props)
        if node.component._has_children_param:
            props["children"] = self.get_children(node)

        # Set up execution context
        old_node_id = self._current_node_id
        self._current_node_id = node_id

        # IMPORTANT: Save old child nodes BEFORE render() to avoid overwrites
        old_nodes: dict[str, ElementNode] = {}
        if old_child_ids:
            for old_id in old_child_ids:
                old_node = self._nodes.get(old_id)
                if old_node:
                    old_nodes[old_id] = old_node

        # Push a frame for child IDs created during execution
        self.push_frame(parent_id=node_id)
        frame_popped = False

        try:
            # Render the component (creates child nodes via component calls)
            node.component.render(**props)

            # Get child IDs created during execution
            new_child_ids = self.pop_frame()
            frame_popped = True

            # Reconcile or mount children
            if new_child_ids:
                if old_child_ids:
                    # Reconcile with old children
                    final_child_ids = reconcile_node_children(
                        old_child_ids, new_child_ids, node_id, self, old_nodes
                    )
                else:
                    # All new children - already executed during creation
                    final_child_ids = new_child_ids

                result = dataclass_replace(node, child_ids=tuple(final_child_ids))
            else:
                # No children - unmount any old children
                if old_child_ids:
                    for child_id in old_child_ids:
                        self.unmount_node_tree(child_id)
                result = dataclass_replace(node, child_ids=())

            # Store the executed node
            self.store_node(result)

            # Don't update previous state here - let the caller handle it
            # after emitting patches (in _render_single_node)

            return result

        except BaseException:
            if not frame_popped:
                self.pop_frame()
            raise

        finally:
            self._current_node_id = old_node_id

    def execute_node(
        self,
        node: ElementNode,
        parent_id: str | None,
        old_child_ids: list[str] | None = None,
        *,
        call_hooks: bool = True,
    ) -> ElementNode:
        """Execute a component and collect its children.

        This is the core rendering operation that calls component.render()
        and reconciles the resulting children.

        Args:
            node: The node to execute (must have id assigned)
            parent_id: Parent node's ID
            old_child_ids: Previous child IDs to reconcile against (None for initial mount)
            call_hooks: Whether to call mount hooks for children. Set False when
                       parent will call mount_node_tree to handle all hooks.

        Returns:
            Node with child_ids populated from execution
        """
        from trellis.core.reconcile import reconcile_node_children

        # Get state for this node
        state = self.get_element_state(node.id)
        state.parent_id = parent_id

        # Get props including children if component accepts them
        props = unfreeze_props(node.props)
        if node.component._has_children_param:
            props["children"] = self.get_children(node)

        # Set up execution context
        old_node_id = self._current_node_id
        self._current_node_id = node.id

        # Reset state call count for consistent hook ordering
        state.state_call_count = 0

        # Clear existing dependency tracking before re-execution
        # Dependencies will be re-registered fresh during execution
        self.clear_node_dependencies(node.id)

        # IMPORTANT: Save old child nodes BEFORE render() to avoid overwrites
        # During render(), new child descriptors are stored in _nodes via
        # add_to_current_frame(), which may overwrite old nodes with the same
        # position-based ID. We need the old node's child_ids for reconciliation.
        old_nodes: dict[str, ElementNode] = {}
        if old_child_ids:
            for old_id in old_child_ids:
                old_node = self._nodes.get(old_id)
                if old_node:
                    old_nodes[old_id] = old_node

        # Push a frame for child IDs created during execution
        self.push_frame(parent_id=node.id)
        frame_popped = False

        try:
            # Render the component (creates child nodes via component calls)
            node.component.render(**props)

            # Get child IDs created during execution
            new_child_ids = self.pop_frame()
            frame_popped = True

            # Reconcile or mount children
            if new_child_ids:
                # Reconcile with old children if this is a re-execution
                if old_child_ids:
                    final_child_ids = reconcile_node_children(
                        old_child_ids, new_child_ids, node.id, self, old_nodes
                    )
                else:
                    # Initial mount - mount all new children
                    # Don't call hooks here - parent will call mount_node_tree
                    final_child_ids = []
                    for child_id in new_child_ids:
                        child_node = self._nodes.get(child_id)
                        if child_node:
                            self.mount_new_node(child_node, node.id, call_hooks=False)
                            final_child_ids.append(child_id)

                # Call mount hooks for any newly created children during re-render
                # For initial mount (old_child_ids is None), parent's mount_node_tree handles this
                # mount_node_tree checks state.mounted and skips already-mounted nodes
                if call_hooks and old_child_ids is not None:
                    for child_id in final_child_ids:
                        self.mount_node_tree(child_id)

                return dataclass_replace(node, child_ids=tuple(final_child_ids))

            # No new children created
            if old_child_ids:
                # Had children before but none now - unmount all
                for child_id in old_child_ids:
                    self.unmount_node_tree(child_id)
            return dataclass_replace(node, child_ids=())

        except BaseException:
            if not frame_popped:
                self.pop_frame()
            raise

        finally:
            self._current_node_id = old_node_id

    @property
    def current_node_id(self) -> str | None:
        """The ID of the node currently being executed.

        Used by Stateful to look up state in _element_state.

        Returns:
            The current node ID during execution, or None
        """
        return self._current_node_id

    def is_active(self) -> bool:
        """Check if currently executing a component.

        Returns:
            True if a node is currently being executed, False otherwise
        """
        return self._current_node_id is not None

    @with_lock
    def mark_dirty_id(self, node_id: str) -> None:
        """Mark a node ID as needing re-render.

        If the node is currently being executed, this is a no-op since
        the current render will already reflect the new state.

        Args:
            node_id: The ID of the node to mark dirty
        """
        # Skip if this node is currently being rendered - state changes during
        # execution are reflected in the current render, no re-render needed
        if node_id == self._current_node_id:
            return

        self._dirty_ids.add(node_id)
        if node_id in self._element_state:
            self._element_state[node_id].dirty = True

    @with_lock
    def track_mount(self, node_id: str) -> None:
        """Track a node for mount hook to be called after render.

        Args:
            node_id: The ID of the newly mounted node
        """
        self._pending_mounts.append(node_id)

    @with_lock
    def track_unmount(self, node_id: str) -> None:
        """Track a node for unmount hook to be called after render.

        With component identity in IDs, different component types at the same
        position get different IDs, so there's no risk of state collision.

        Args:
            node_id: The ID of the node being unmounted
        """
        self._pending_unmounts.append(node_id)

    def _process_pending_hooks(self) -> None:
        """Process all pending mount/unmount hooks.

        Called at the end of render() after the tree is fully built.
        Hooks are called in no particular order since they are just
        convenience methods and don't interact with DOM.
        """
        # Process unmounts first (cleanup before new mounts)
        for node_id in self._pending_unmounts:
            self.call_unmount_hooks(node_id)
            self.clear_node_dependencies(node_id)
            self.clear_callbacks_for_node(node_id)
            # With component identity in IDs, we can safely remove ElementState
            self._element_state.pop(node_id, None)
        self._pending_unmounts.clear()

        # Process mounts
        for node_id in self._pending_mounts:
            self.call_mount_hooks(node_id)
        self._pending_mounts.clear()

    def register_callback(
        self,
        callback: tp.Callable[..., tp.Any],
        node_id: str,
        prop_name: str,
    ) -> str:
        """Register a callback with a deterministic ID.

        Callbacks are stored on this RenderTree with IDs based on
        node_id and prop_name. This ensures:
        - Same callback location always gets same ID (stability)
        - Callbacks are automatically overwritten on re-render (no clearing needed)
        - Easy cleanup on unmount by node_id prefix

        Args:
            callback: The callable to register
            node_id: The node ID (e.g., "e5")
            prop_name: The property name (e.g., "on_click")

        Returns:
            A deterministic callback ID (e.g., "e5:on_click")
        """
        cb_id = f"{node_id}:{prop_name}"
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

    def clear_callbacks_for_node(self, node_id: str) -> None:
        """Remove all callbacks for a specific node.

        Called on unmount to clean up callbacks that will never be invoked.

        Args:
            node_id: The node ID whose callbacks should be removed
        """
        prefix = f"{node_id}:"
        to_remove = [k for k in self._callback_registry if k.startswith(prefix)]
        for k in to_remove:
            del self._callback_registry[k]

    def clear_callbacks(self) -> None:
        """Clear all registered callbacks.

        Generally not needed with deterministic IDs, but available for
        complete session cleanup.
        """
        self._callback_registry.clear()

    @with_lock
    def render(self) -> dict[str, tp.Any]:
        """Render and return the serialized node tree.

        This is the main public API for rendering. It:
        1. Builds tree via eager execution (initial) or re-renders dirty nodes
        2. Processes any pending mount/unmount hooks
        3. Serializes the result for transmission
        4. Populates previous state in ElementState for subsequent diffs

        With eager execution, the initial render builds the entire tree
        during root_component() call - no separate dirty node processing needed.

        Callbacks use deterministic IDs (node_id:prop_name) and are
        automatically overwritten on re-render, so no clearing is needed.

        Returns:
            Serialized node tree as a dict, suitable for JSON/msgpack encoding.
            Callbacks are replaced with {"__callback__": "e5:on_click"} references.
        """
        from trellis.core.serialization import serialize_node

        if self.root_node is None:
            # Initial render - eager execution builds entire tree
            self._render_node_tree()
        else:
            # Re-render - process any dirty nodes from state changes
            self._render_dirty_nodes()

        # Process hooks after tree is fully built
        self._process_pending_hooks()

        assert self.root_node is not None
        result = serialize_node(self.root_node, self)

        # Populate previous state in ElementState for subsequent diffs
        self._populate_subtree_state(self.root_node_id or "")

        return result

    def has_dirty_nodes(self) -> bool:
        """Check if there are any nodes that need re-rendering.

        Returns:
            True if there are dirty nodes, False otherwise
        """
        return bool(self._dirty_ids)

    @with_lock
    def render_and_diff(self) -> list[Patch]:
        """Render dirty nodes and return patches describing changes.

        This is the incremental render API. It:
        1. Clears accumulated patches
        2. Renders all dirty nodes (patches emitted inline during reconciliation)
        3. Processes any pending mount/unmount hooks
        4. Returns accumulated patches

        Returns:
            List of Patch objects to send to client. Empty if nothing changed.
        """
        if self.root_node is None:
            # Initial render - should use render() instead
            return []

        # Clear patches and enable incremental render mode
        self._patches.clear()
        self._is_incremental_render = True

        try:
            # Render all dirty nodes (patches emitted inline)
            self._render_dirty_nodes()

            # Process hooks after tree is fully built
            self._process_pending_hooks()

            # Return accumulated patches
            return list(self._patches)
        finally:
            self._is_incremental_render = False

    @with_lock
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

    @with_lock
    def mount_new_node(
        self,
        node: ElementNode,
        parent_id: str | None,
        *,
        call_hooks: bool = True,
    ) -> ElementNode:
        """Mount a new node.

        Creates ElementState and marks dirty for later rendering.
        The actual component execution happens in _render_dirty_nodes.

        With position-based IDs, the node already has its ID assigned at creation
        time in _place(). This method just sets up the state.

        Args:
            node: The node to mount (already has position-based ID)
            parent_id: Parent node's ID
            call_hooks: Whether to track mount hooks. Set False for internal
                       reconciliation where parent handles hook tracking.

        Returns:
            The mounted node (unchanged, ID already assigned)
        """
        node_id = node.id

        # Create ElementState and mark as mounted
        # (hooks are deferred but node is conceptually mounted now)
        state = ElementState(parent_id=parent_id, mounted=True)
        self._element_state[node_id] = state

        # Mark dirty so _render_dirty_nodes will render this node
        self.mark_dirty_id(node_id)

        # Track for mount hooks (called after render completes)
        self.track_mount(node_id)

        # Return node unchanged - children are descriptors from with block,
        # will be replaced when rendered
        return node

    def mount_node_tree(self, node_id: str) -> None:
        """Mount a node and all its descendants.

        Mounting is performed parent-first. Hooks are tracked for deferred
        execution after the render phase completes.

        Args:
            node_id: The ID of the node to mount
        """
        state = self._element_state.get(node_id)
        if state is None or state.mounted:
            return

        state.mounted = True
        # Track mount hook (called after render completes)
        self.track_mount(node_id)

        # Mount children
        node = self._nodes.get(node_id)
        if node:
            for child_id in node.child_ids:
                self.mount_node_tree(child_id)

    @with_lock
    def unmount_node_tree(self, node_id: str) -> None:
        """Unmount a node and all its descendants.

        Unmounting is performed children-first. Hooks are tracked for deferred
        execution after the render phase completes. State cleanup is also deferred
        so hooks can access local_state.

        Args:
            node_id: The ID of the node to unmount
        """
        state = self._element_state.get(node_id)
        if state is None or not state.mounted:
            return

        # Unmount children first (depth-first)
        node = self._nodes.get(node_id)
        if node:
            for child_id in node.child_ids:
                self.unmount_node_tree(child_id)

        # Track unmount hook (called after render completes)
        # State cleanup is deferred to _process_pending_hooks so hooks can access local_state
        self.track_unmount(node_id)

        # Note: RemovePatch is emitted in process_reconcile_result before calling
        # unmount_node_tree, so we don't need to track removed IDs here.

        state.mounted = False
        self._dirty_ids.discard(node_id)

    def call_mount_hooks(self, node_id: str) -> None:
        """Call on_mount() for all Stateful instances on a node.

        Exceptions are logged but not propagated, to ensure all mount hooks run.

        Args:
            node_id: The node's ID
        """
        state = self._element_state.get(node_id)
        if state is None:
            return

        # Get states sorted by call index
        items = list(state.local_state.items())
        items.sort(key=lambda x: x[0][1])
        for _, stateful in items:
            if hasattr(stateful, "on_mount"):
                try:
                    stateful.on_mount()
                except Exception as e:
                    logging.exception(f"Error in Stateful.on_mount: {e}")

    def call_unmount_hooks(self, node_id: str) -> None:
        """Call on_unmount() for all Stateful instances on a node (reverse order).

        Args:
            node_id: The node's ID
        """
        state = self._element_state.get(node_id)
        if state is None:
            return
        # Get states sorted by call index, reversed
        items = list(state.local_state.items())
        items.sort(key=lambda x: x[0][1], reverse=True)
        for _, stateful in items:
            if hasattr(stateful, "on_unmount"):
                try:
                    stateful.on_unmount()
                except Exception as e:
                    logging.exception(f"Error in Stateful.on_unmount: {e}")

    def clear_node_dependencies(self, node_id: str) -> None:
        """Clear a node's dependency registrations from all watched Stateful/Tracked instances.

        Called before a node re-renders (to allow fresh registration) and on unmount
        (to prevent stale references).

        Args:
            node_id: The node ID to remove from dependencies
        """
        state = self._element_state.get(node_id)
        if state is None:
            return

        watched_deps = state.watched_deps
        for obj, dep_keys in watched_deps.values():
            # All tracked objects (Stateful, TrackedList, etc.) implement Trackable
            # and use composite keys: (id(obj), actual_key)
            for composite_key in dep_keys:
                _, actual_key = composite_key
                obj._clear_dep(node_id, actual_key)
        watched_deps.clear()

    # -------------------------------------------------------------------------
    # Inline patch generation helpers (Phase 4)
    # -------------------------------------------------------------------------

    def _emit_patch(self, patch: Patch) -> None:
        """Add a patch to the accumulated patches list.

        Only adds patches during incremental render mode.

        Args:
            patch: The patch to emit
        """
        if self._is_incremental_render:
            self._patches.append(patch)

    def _serialize_node_for_patch(self, node: ElementNode) -> dict[str, tp.Any]:
        """Serialize a node and its subtree for an AddPatch.

        Args:
            node: The node to serialize

        Returns:
            Serialized node dict suitable for AddPatch.node
        """
        from trellis.core.serialization import serialize_node

        return serialize_node(node, self)

    def _serialize_props_for_state(self, node: ElementNode) -> dict[str, tp.Any]:
        """Serialize a node's props for state tracking.

        Args:
            node: The node whose props to serialize

        Returns:
            Serialized props dict
        """
        from trellis.core.serialization import _serialize_node_props

        return _serialize_node_props(node, self)

    def _update_node_previous_state(self, node_id: str) -> None:
        """Update a node's previous state for subsequent diff comparisons.

        Called after a node is rendered to store its serialized props and
        child_ids in ElementState.

        Args:
            node_id: The node's ID
        """
        node = self._nodes.get(node_id)
        state = self._element_state.get(node_id)
        if node and state:
            state.serialized_props = self._serialize_props_for_state(node)
            state.previous_child_ids = list(node.child_ids)

    def _emit_update_patch_if_changed(
        self,
        node_id: str,
        old_node: ElementNode | None,
    ) -> None:
        """Emit an UpdatePatch if props or children changed.

        Compares current node to previous state and emits UpdatePatch if needed.
        Updates the previous state in ElementState.

        Args:
            node_id: The node's ID
            old_node: The old node (for comparison during reconciliation)
        """
        node = self._nodes.get(node_id)
        state = self._element_state.get(node_id)
        if not node or not state:
            return

        # Serialize current props
        current_props = self._serialize_props_for_state(node)
        current_child_ids = list(node.child_ids)

        # Get previous state
        prev_props = state.serialized_props or {}
        prev_child_ids = state.previous_child_ids or []

        # Compute prop diff (only changed props)
        props_diff: dict[str, tp.Any] = {
            key: value
            for key, value in current_props.items()
            if key not in prev_props or prev_props[key] != value
        }
        # Add removed props (signal removal with None)
        props_diff.update({key: None for key in prev_props if key not in current_props})

        # Check if children order changed
        children_changed = current_child_ids != prev_child_ids

        # Emit update patch if anything changed
        if props_diff or children_changed:
            self._emit_patch(
                UpdatePatch(
                    id=node_id,
                    props=props_diff if props_diff else None,
                    children=current_child_ids if children_changed else None,
                )
            )

        # Update stored state
        state.serialized_props = current_props
        state.previous_child_ids = current_child_ids

    def process_reconcile_result(
        self,
        result: ReconcileResult,
        parent_id: str,
        old_nodes: dict[str, ElementNode],
    ) -> list[str]:
        """Process a ReconcileResult and apply side effects.

        This is the "impure" counterpart to the pure reconcile_children() function.
        It interprets the ReconcileResult and performs:
        - Unmounting removed nodes (emits RemovePatch)
        - Mounting added nodes (emits AddPatch)
        - Emitting UpdatePatch for matched nodes with changes

        With eager execution, matched nodes have already been handled by their
        _place() calls. We just need to emit patches for any changes.

        Args:
            result: The ReconcileResult from reconcile_children()
            parent_id: The parent node's ID
            old_nodes: Saved old node data for props comparison

        Returns:
            Final list of child IDs after reconciliation
        """
        # 1. REMOVE first (cleanup before new state)
        # Emit RemovePatch for each removed node
        for node_id in result.removed:
            self._emit_patch(RemovePatch(id=node_id))
            self.unmount_node_tree(node_id)

        # 2. ADD second (mount new nodes)
        # With eager execution, nodes are already executed in _place()
        # We just need to ensure ElementState exists and emit patches
        for node_id in result.added:
            node = self._nodes.get(node_id)
            if node:
                # Node was already executed in _place(), just ensure state exists
                state = self._element_state.get(node_id)
                if state is None:
                    state = ElementState(parent_id=parent_id, mounted=True)
                    self._element_state[node_id] = state
                    self.track_mount(node_id)

                # Emit AddPatch with serialized subtree
                self._emit_patch(
                    AddPatch(
                        parent_id=parent_id,
                        children=result.child_order,
                        node=self._serialize_node_for_patch(node),
                    )
                )
                # Initialize previous state for the new node and its subtree
                self._populate_subtree_state(node_id)

        # 3. MATCHED - with eager execution, nodes already handled in _place()
        # Just emit patches for any changes detected
        for node_id in result.matched:
            old_node = old_nodes.get(node_id)
            if old_node:
                # Emit UpdatePatch if props or children changed
                self._emit_update_patch_if_changed(node_id, old_node)

        return result.child_order

    def _populate_subtree_state(self, node_id: str) -> None:
        """Initialize previous state for a node and all its descendants.

        Called after a new subtree is added to initialize state tracking
        for subsequent diff comparisons.

        Args:
            node_id: The root node ID of the subtree
        """
        node = self._nodes.get(node_id)
        state = self._element_state.get(node_id)
        if node and state:
            state.serialized_props = self._serialize_props_for_state(node)
            state.previous_child_ids = list(node.child_ids)
            # Recurse into children
            for child_id in node.child_ids:
                self._populate_subtree_state(child_id)
