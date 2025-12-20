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


# =============================================================================
# Core Types
# =============================================================================


@dataclass
class Frame:
    """Scope that collects child ElementNodes.

    Used during component execution to collect children created in `with` blocks.
    Each `with` block pushes a new Frame onto the stack, and children created
    within are added to that frame.
    """

    children: list[ElementNode] = field(default_factory=list)


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
    key: str | None = None
    children: tuple[ElementNode, ...] = ()
    id: str = ""  # Assigned by RenderTree.next_element_id() during reconciliation

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
        state_call_count: Counter for consistent Stateful() instantiation ordering
        context: State context from `with state:` blocks
        parent_id: Parent node's ID (for context walking)
    """

    dirty: bool = False
    mounted: bool = False
    local_state: dict[tuple[type, int], tp.Any] = field(default_factory=dict)
    state_call_count: int = 0
    context: dict[type, tp.Any] = field(default_factory=dict)
    parent_id: str | None = None
    watched_deps: dict[int, tuple[tp.Any, set[str | tuple[int, tp.Any]]]] = field(
        default_factory=dict
    )
    """Maps id(obj) -> (obj, {dep_keys}) for cleanup on re-render/unmount.

    For Stateful objects: dep_keys contains property name strings (str)
    For TrackedList/Dict/Set: dep_keys contains composite tuples (int, Any)
        where the int is id(collection) and Any is the actual key

    Before each render, these are cleared from each tracked object.
    During render, access methods re-register fresh dependencies.
    Uses id() as key since objects may not be hashable.
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
    """

    root_component: IComponent
    root_node: ElementNode | None  # Root of ElementNode tree
    _dirty_ids: set[str]  # Dirty node IDs
    lock: threading.RLock
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
        self._current_node_id: str | None = None
        # Last property access for mutable()/callback() to capture.
        # Stores (owner, attr_name, value) when a Stateful property is accessed.
        self._last_property_access: tuple[tp.Any, str, tp.Any] | None = None
        # Frame stack for collecting children during `with` blocks.
        # Each entry is a Frame that collects nodes created within that scope.
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
        self._pending_unmounts: list[str] = []

    def push_frame(self) -> Frame:
        """Push a new frame for collecting child nodes.

        Called when entering a `with` block on a container component.
        Child nodes created in that scope will be added to this frame.

        Returns:
            The new Frame
        """
        frame = Frame()
        self._frame_stack.append(frame)
        return frame

    def pop_frame(self) -> Frame:
        """Pop and return the current frame.

        Called when exiting a `with` block. Returns the Frame containing
        all child nodes collected in that scope.

        Returns:
            The completed Frame
        """
        return self._frame_stack.pop()

    def current_frame(self) -> Frame | None:
        """Get the current frame if one exists.

        Returns:
            The current Frame, or None if not in a `with` block
        """
        return self._frame_stack[-1] if self._frame_stack else None

    def add_to_current_frame(self, node: ElementNode) -> None:
        """Add a node to the current frame if one exists.

        Called when a child component is invoked inside a `with` block.

        Args:
            node: The child node to add
        """
        if self._frame_stack:
            self._frame_stack[-1].children.append(node)

    def has_active_frame(self) -> bool:
        """Check if there's an active frame for collecting children.

        Returns:
            True if inside a `with` block, False otherwise
        """
        return bool(self._frame_stack)

    # Legacy aliases for backwards compatibility during transition
    def push_descriptor_frame(self) -> None:
        """Push a new frame. Deprecated: use push_frame() instead."""
        self.push_frame()

    def pop_descriptor_frame(self) -> list[ElementNode]:
        """Pop the current frame. Deprecated: use pop_frame() instead."""
        return self.pop_frame().children

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
        """Render the component tree starting from a specific node or root.

        Sets up the render context, creates or reconciles node descriptors,
        and executes components whose props changed or are marked dirty.

        Args:
            from_node_id: Node ID to re-render from, or None for initial render

        Raises:
            RuntimeError: If another render is already in progress
        """
        from trellis.core.reconcile import reconcile_node

        if get_active_render_tree():
            raise RuntimeError("Attempted to start rendering with another context active!")

        try:
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
                if node.children and node.component._has_children_param:
                    props["children"] = list(node.children)
                new_node = node.component(**props)

                # Reconcile and update tree
                updated_node = reconcile_node(node, new_node, parent_id, self)
                self.root_node = self._replace_node_in_tree(
                    self.root_node, from_node_id, updated_node
                )

        finally:
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
        """Replace a node in the tree by ID, returning the new tree.

        Uses parent_id chain for O(depth) traversal.

        Raises:
            RuntimeError: If the node cannot be found via parent_id chain
        """
        if root.id == target_id:
            return replacement

        # Build path using parent_id chain
        path = self._build_path_to_root(target_id)
        if not path:
            raise RuntimeError(
                f"Cannot find node {target_id} via parent_id chain. "
                f"This indicates a bug in ElementState.parent_id management."
            )

        return self._replace_along_path(root, path, replacement)

    def _build_path_to_root(self, target_id: str) -> list[str]:
        """Build path from target node to root using parent_id chain.

        Returns list of node IDs from root to target (inclusive), or
        empty list if chain is broken.
        """
        path: list[str] = []
        current_id: str | None = target_id

        while current_id is not None:
            path.append(current_id)
            state = self._element_state.get(current_id)
            if state is None:
                return []  # Chain broken
            current_id = state.parent_id

        path.reverse()  # Now root-to-target order
        return path

    def _replace_along_path(
        self, root: ElementNode, path: list[str], replacement: ElementNode
    ) -> ElementNode:
        """Replace node by rebuilding only ancestors along the path.

        O(depth * avg_children) instead of O(nodes).

        Raises:
            RuntimeError: If path doesn't match tree structure
        """
        if not path or root.id != path[0]:
            raise RuntimeError(
                f"Path mismatch: expected root ID {root.id} but path starts with "
                f"{path[0] if path else 'empty path'}"
            )

        if len(path) == 1:
            # Target is the root
            return replacement

        # Find which child is on the path
        next_id = path[1]
        new_children = []
        found = False

        for child in root.children:
            if child.id == next_id:
                found = True
                # Recurse down the path
                new_child = self._replace_along_path(child, path[1:], replacement)
                new_children.append(new_child)
            else:
                new_children.append(child)

        if not found:
            raise RuntimeError(
                f"Path mismatch: node {root.id} has no child with ID {next_id}. "
                f"This indicates a bug in ElementState.parent_id management."
            )

        return dataclass_replace(root, children=tuple(new_children))

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
        """Render a single dirty node by ID.

        Finds the node in the tree, executes it, and updates the tree
        with the result. Must be called with active render context.
        """
        if self.root_node is None:
            return

        # Find the node and its parent
        node, parent_id = self._find_node_with_parent(self.root_node, node_id)
        if node is None:
            return

        # Get state and reset state call count
        state = self._element_state.get(node_id)
        if state:
            state.state_call_count = 0

        # Determine old_children for reconciliation
        # Children with empty IDs are descriptors from the with block (first render)
        # Children with IDs are previously mounted nodes (re-render)
        old_children: list[ElementNode] | None = None
        if node.children:
            # Check if children are mounted (have IDs) or just descriptors
            first_has_id = bool(node.children[0].id)
            if __debug__:
                # Verify all children have consistent ID state (invariant)
                all_have_id = all(bool(c.id) for c in node.children)
                assert first_has_id == all_have_id, (
                    f"Inconsistent child ID state for node {node.id}: "
                    f"first_has_id={first_has_id}, all_have_id={all_have_id}"
                )
            if first_has_id:
                old_children = list(node.children)
            # else: children are descriptors, treat as no old_children

        rendered_node = self.execute_node(node, parent_id, old_children=old_children)

        # Update tree with rendered result
        self.root_node = self._replace_node_in_tree(self.root_node, node_id, rendered_node)

    def execute_node(
        self,
        node: ElementNode,
        parent_id: str | None,
        old_children: list[ElementNode] | None = None,
        *,
        call_hooks: bool = True,
    ) -> ElementNode:
        """Execute a component and collect its children.

        This is the core rendering operation that calls component.render()
        and reconciles the resulting children.

        Args:
            node: The node to execute (must have id assigned)
            parent_id: Parent node's ID
            old_children: Previous children to reconcile against (None for initial mount)
            call_hooks: Whether to call mount hooks for children. Set False when
                       parent will call mount_node_tree to handle all hooks.

        Returns:
            Node with children populated from execution
        """
        from trellis.core.reconcile import reconcile_node_children

        # Get state for this node
        state = self.get_element_state(node.id)
        state.parent_id = parent_id

        # Get props including children if component accepts them
        props = unfreeze_props(node.props)
        if node.component._has_children_param:
            props["children"] = list(node.children)

        # Set up execution context
        old_node_id = self._current_node_id
        self._current_node_id = node.id

        # Reset state call count for consistent hook ordering
        state.state_call_count = 0

        # Clear existing dependency tracking before re-execution
        # Dependencies will be re-registered fresh during execution
        self.clear_node_dependencies(node.id)

        # Push a frame for child nodes created during execution
        self.push_descriptor_frame()
        frame_popped = False

        try:
            # Render the component (creates child nodes via component calls)
            node.component.render(**props)

            # Get child nodes created during execution
            child_nodes = self.pop_descriptor_frame()
            frame_popped = True

            # Reconcile or mount children
            if child_nodes:
                # Reconcile with old children if this is a re-execution
                if old_children:
                    new_children = reconcile_node_children(old_children, child_nodes, node.id, self)
                else:
                    # Initial mount - mount all new children
                    # Don't call hooks here - parent will call mount_node_tree
                    new_children = [
                        self.mount_new_node(child, node.id, call_hooks=False)
                        for child in child_nodes
                    ]

                # Call mount hooks for any newly created children during re-render
                # For initial mount (old_children is None), parent's mount_node_tree handles this
                # mount_node_tree checks state.mounted and skips already-mounted nodes
                if call_hooks and old_children is not None:
                    for child in new_children:
                        self.mount_node_tree(child)

                return dataclass_replace(node, children=tuple(new_children))

            # No new children created
            if old_children:
                # Had children before but none now - unmount all
                for child in old_children:
                    self.unmount_node_tree(child)
            return dataclass_replace(node, children=())

        except BaseException:
            if not frame_popped:
                self.pop_descriptor_frame()
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

    def track_mount(self, node_id: str) -> None:
        """Track a node for mount hook to be called after render.

        Args:
            node_id: The ID of the newly mounted node
        """
        self._pending_mounts.append(node_id)

    def track_unmount(self, node_id: str) -> None:
        """Track a node for unmount hook to be called after render.

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
            # Now clean up state (deferred from unmount_node_tree so hooks could access it)
            self.clear_node_dependencies(node_id)
            self.clear_callbacks_for_node(node_id)
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

    def render(self) -> dict[str, tp.Any]:
        """Render and return the serialized node tree.

        This is the main public API for rendering. It:
        1. Builds tree structure (initial) or identifies dirty nodes (re-render)
        2. Renders all dirty nodes until none remain
        3. Processes any pending mount/unmount hooks
        4. Serializes the result for transmission

        Callbacks use deterministic IDs (node_id:prop_name) and are
        automatically overwritten on re-render, so no clearing is needed.

        Returns:
            Serialized node tree as a dict, suitable for JSON/msgpack encoding.
            Callbacks are replaced with {"__callback__": "e5:on_click"} references.
        """
        from trellis.core.serialization import serialize_node

        if self.root_node is None:
            # Initial render - build tree structure (marks nodes dirty)
            self._render_node_tree(from_node_id=None)

        # Render all dirty nodes (loops until no more dirty)
        self._render_dirty_nodes()

        # Process hooks after tree is fully built
        self._process_pending_hooks()

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

    def mount_new_node(
        self,
        node: ElementNode,
        parent_id: str | None,
        *,
        call_hooks: bool = True,
    ) -> ElementNode:
        """Create and mount a new node.

        Assigns a new ID, creates ElementState, marks dirty for later rendering.
        The actual component execution happens in _render_dirty_nodes.

        Args:
            node: The node to mount (will have empty id)
            parent_id: Parent node's ID
            call_hooks: Whether to track mount hooks. Set False for internal
                       reconciliation where parent handles hook tracking.

        Returns:
            The mounted node with ID assigned (children empty until rendered)
        """
        # Assign new ID (keep original children - they're descriptors from with block
        # that will be passed to render(), then replaced with mounted children)
        new_id = self.next_element_id()
        node_with_id = dataclass_replace(node, id=new_id)

        # Create ElementState and mark as mounted
        # (hooks are deferred but node is conceptually mounted now)
        state = ElementState(parent_id=parent_id, mounted=True)
        self._element_state[new_id] = state

        # Mark dirty so _render_dirty_nodes will render this node
        self.mark_dirty_id(new_id)

        # Track for mount hooks (called after render completes)
        self.track_mount(new_id)

        # Return node - children are descriptors from with block, will be replaced when rendered
        return node_with_id

    def mount_node_tree(self, node: ElementNode) -> None:
        """Mount a node and all its descendants.

        Mounting is performed parent-first. Hooks are tracked for deferred
        execution after the render phase completes.

        Args:
            node: The node to mount
        """
        state = self._element_state.get(node.id)
        if state is None or state.mounted:
            return

        state.mounted = True
        # Track mount hook (called after render completes)
        self.track_mount(node.id)

        for child in node.children:
            self.mount_node_tree(child)

    def unmount_node_tree(self, node: ElementNode) -> None:
        """Unmount a node and all its descendants.

        Unmounting is performed children-first. Hooks are tracked for deferred
        execution after the render phase completes. State cleanup is also deferred
        so hooks can access local_state.

        Args:
            node: The node to unmount
        """
        state = self._element_state.get(node.id)
        if state is None or not state.mounted:
            return

        # Unmount children first (depth-first)
        for child in node.children:
            self.unmount_node_tree(child)

        # Track unmount hook (called after render completes)
        # State cleanup is deferred to _process_pending_hooks so hooks can access local_state
        self.track_unmount(node.id)

        state.mounted = False
        self._dirty_ids.discard(node.id)

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
            if isinstance(obj, Trackable):
                # Handle tracked collections - dep_keys contains (id(collection), actual_key) tuples
                for composite_key in dep_keys:
                    if (
                        isinstance(composite_key, tuple)
                        and len(composite_key) == 2  # noqa: PLR2004
                    ):
                        _, actual_key = composite_key
                        obj._clear_dep(node_id, actual_key)
            else:
                # Handle Stateful objects (existing logic)
                try:
                    deps = object.__getattribute__(obj, "_state_props")
                    for prop_name in dep_keys:
                        if prop_name in deps:
                            state_info = deps[prop_name]
                            state_info.node_ids.discard(node_id)
                            state_info.node_trees.pop(node_id, None)
                except AttributeError:
                    pass  # Stateful may not have _state_props yet
        watched_deps.clear()
