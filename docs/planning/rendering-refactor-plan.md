# Rendering System Refactor Plan

This document describes the planned refactoring of Trellis's rendering, reconciliation, and diffing systems. The goal is a simpler, more understandable architecture with clear separation of concerns.

## Current Implementation

### Core Data Structures

**ElementNode** (`rendering.py:110`) - Immutable tree node:
```python
@dataclass(frozen=True)
class ElementNode:
    component: IComponent
    props: FrozenProps = ()
    key: str | None = None
    children: tuple[ElementNode, ...] = ()  # Nested children
    id: str = ""  # Assigned during reconciliation
```

**ElementState** (`rendering.py:261`) - Mutable runtime state per node:
```python
@dataclass
class ElementState:
    dirty: bool = False
    mounted: bool = False
    local_state: dict[tuple[type, int], Any]  # Stateful instances
    state_call_count: int = 0
    context: dict[type, Any]
    parent_id: str | None = None
    watched_deps: dict[int, tuple[Any, set[str]]]
```

**RenderTree** (`rendering.py:292`) - Orchestrates rendering:
- `root_node: ElementNode | None` - nested tree
- `_element_state: dict[str, ElementState]` - mutable state by ID
- `_dirty_ids: set[str]` - nodes needing re-render
- `_frame_stack: list[Frame]` - for child collection in `with` blocks
- `_callback_registry: dict[str, Callable]` - callback ID → function
- `_previous_props`, `_previous_children` - for diff computation
- `_removed_ids` - nodes removed since last diff

### Current Render Flow

1. **Initial Render** (`RenderTree.render()`):
   - `_render_node_tree()` creates root ElementNode via `root_component()`
   - `reconcile_node(None, root_node, ...)` assigns IDs and marks dirty
   - `_render_dirty_nodes()` loops until no dirty nodes remain
   - For each dirty node: execute component, collect children, reconcile children
   - `serialize_node()` converts tree to dict for client
   - `_populate_previous_state()` stores props/children for future diffs

2. **Incremental Render** (`RenderTree.render_and_diff()`):
   - `_render_dirty_nodes()` re-executes dirty components
   - `compute_patches()` walks tree comparing to `_previous_props`/`_previous_children`
   - Returns list of patches (AddPatch, UpdatePatch, RemovePatch)

### Current Component Issues

**Reconciler does too much** (`reconcile.py`):
- `reconcile_node()` calls `ctx.mount_new_node()`, `ctx.unmount_node_tree()`, `ctx.mark_dirty_id()` directly
- Mixes "what changed" logic with "what to do about it" actions
- Not testable as a pure function

**`children` has dual meaning**:
- Sometimes descriptors from `with` blocks (no IDs)
- Sometimes mounted nodes after reconciliation (have IDs)
- Code checks `children[0].id` to distinguish (fragile)

**Serializer does too much** (`serialization.py`):
- `serialize_node()` registers callbacks as a side effect
- `compute_patches()` is a separate tree walk duplicating reconciliation work

**Two-pass rendering**:
- First pass: reconcile and execute dirty nodes
- Second pass: `compute_patches()` walks tree again to generate patches
- Information about what changed is discovered twice

**Sequential IDs assigned at mount**:
- IDs like `e1`, `e2` based on mount order, not position
- ID unknown when node created, assigned later in reconciliation
- Reconciler must match old/new nodes and transfer IDs

## Proposed Design

### Design Principles

1. **Each component does one thing**
2. **Reconciler is pure** - returns data, no side effects
3. **Renderer interprets reconciler output** - performs mutations, generates patches
4. **Single pass** - no separate diff computation
5. **Position-based IDs** - known at creation, stable by position
6. **React semantics** - state follows position/key like React

### Position-Based IDs with Component Identity

IDs are assigned at creation based on tree position **and component identity**. The component identity is `id(component)` - the Python object ID of the component instance.

```
/@140234567890                    # root (component id included)
/@140234567890/0@140234567891     # first child
/@140234567890/0@140234567891/1@140234567892   # grandchild
/@140234567890/:submit@140234567891            # keyed child
```

Each path segment includes `@{id(component)}` to encode both position and component type. This ensures that **different component types at the same position get different IDs**.

**Why component identity matters:**

```python
@component
def Parent():
    if show_button:
        Button()   # /0@{id(Button)}
    else:
        Label()    # /0@{id(Label)} - different ID!
```

Without component identity, both would get `/0` and share state incorrectly. With component identity:
- Type change at any position = different ID
- Children also get different IDs (parent's identity is in their path prefix)
- No state collision during unmount/mount at same position

**Key escaping:**

User-provided keys may contain special characters (`:`, `@`, `/`). These must be URL-encoded:
- `my:key` → `my%3Akey`
- `row/5` → `row%2F5`
- `item@home` → `item%40home`

**Implementation:**
- `id(component)` returns a unique integer per component instance
- Component instances are singletons (e.g., `Button`, `Label`, each `@component` function)
- Keys are URL-encoded to escape special characters
- Can later switch to a short ID registry if wire size becomes a concern

**Benefits**:
- ID known when node created (from parent ID + position + component)
- No ID transfer during reconciliation
- No state cleanup collision (different component = different ID)
- Simpler unmount handling (no need to save/restore state)
- Position = identity for non-keyed nodes (React semantics)
- Key = identity for keyed nodes (React semantics)

**Keyed nodes consume an index** (matching React):
```python
with Column():           # /@{id(Column)}
    Button("A")          # /@{id(Column)}/0@{id(Button)}
    Button(key="submit") # /@{id(Column)}/:submit@{id(Button)}
    Label("C")           # /@{id(Column)}/2@{id(Label)}
```

### `child_ids` Instead of Nested `children`

```python
@dataclass(frozen=True)
class ElementNode:
    component: IComponent
    props: FrozenProps = ()
    key: str | None = None
    child_ids: tuple[str, ...] = ()  # References, not nested nodes
    id: str = ""
```

**Flat node storage** in RenderTree:
```python
_nodes: dict[str, ElementNode]  # Current render
_previous_nodes: dict[str, ElementNode]  # Previous render (for comparison)
```

**Benefits**:
- Same model as client (flat store with ID references)
- Clear separation: `props["children"]` = input refs, `child_ids` = output refs
- No "descriptor vs mounted node" ambiguity
- Simpler serialization (already flat)

### Eager Execution with Reuse Check

Children execute immediately when created inside `with` blocks, but with an optimization to skip unchanged nodes:

```python
# In ComponentBase.__call__:
def __call__(self, **props) -> ElementNode:
    position_id = compute_position_id()  # From context
    old_node = tree.get_previous_node(position_id)
    is_dirty = tree.is_dirty(position_id)

    # Reuse check - THE KEY OPTIMIZATION
    if old_node and old_node.component == self and props_equal(old_node.props, props) and not is_dirty:
        tree.register_in_frame(old_node.id)
        return old_node  # Skip execution, reuse entire subtree

    # Create and execute
    node = ElementNode(id=position_id, component=self, props=freeze(props))
    if is_composition_component:
        execute_body()  # Only if not reused
    tree.register_in_frame(node.id)
    tree.store_node(node)
    return node
```

**Benefits**:
- No "mounted but not executed" intermediate state
- Children always have IDs when collected
- Unchanged subtrees reused completely (including their `child_ids`)
- Optimization happens at creation, not in separate reconciliation pass

### Two Entry Points for Re-execution

There are two ways a component gets re-executed:

1. **Parent-triggered**: Parent re-renders, calls child via `__call__`, reuse check runs
2. **Dirty-triggered**: State change marks node dirty, render loop processes it directly

```python
def _process_dirty_nodes(self) -> list[Patch]:
    """Process nodes marked dirty by state changes."""
    patches = []
    while self._dirty_ids:
        node_id = self._dirty_ids.pop()
        state = self._element_state.get(node_id)
        if state and state.mounted:
            patches.extend(self._rerender_node(node_id))
    return patches

def _rerender_node(self, node_id: str) -> list[Patch]:
    """Re-execute a single dirty node."""
    node = self._nodes[node_id]
    # Execute component, collect new children
    # Reconcile against old child_ids
    # Generate patches
    ...
```

**Dirty grandchild when parent doesn't re-render**:
```
A (not dirty)
└── B (not dirty)
    └── C (dirty)
```

C is in `_dirty_ids`. The render loop processes C directly via `_rerender_node()`. A and B are never touched. Dirty node processing is independent of tree structure - we don't walk down from root.

### Reconciliation Optimizations Preserved

The head/tail scan and key-based matching optimizations are preserved in `reconcile_children()`. These are separate from the reuse check in `__call__`:

- **Reuse check** (`__call__`): Skip execution if same component + same props + not dirty
- **Child matching** (`reconcile_children`): Efficiently match old/new child lists using head/tail scan and key lookup

### Pure Reconciler

Reconciler becomes a pure function returning categorized changes:

```python
@dataclass
class ReconcileResult:
    unchanged: list[str]                      # Reused, no action needed
    updated: list[str]                        # Re-executed, needs UpdatePatch
    added: list[str]                          # New nodes, need AddPatch
    removed: list[str]                        # Old nodes gone, need RemovePatch
    child_order: list[str]                    # Final order of children

def reconcile_children(
    old_child_ids: list[str],
    new_child_ids: list[str],
    nodes: dict[str, ElementNode],
    previous_nodes: dict[str, ElementNode],
) -> ReconcileResult:
    """Pure function - no side effects, no RenderTree access."""
    ...
```

**Reconciler responsibilities**:
- Compare old and new child ID lists
- Categorize each ID: unchanged, updated, added, removed
- Determine final child order
- Handle component type changes (same ID, different type = remove + add)

**Reconciler does NOT**:
- Call mount/unmount
- Mark nodes dirty
- Modify any state
- Access RenderTree

### Renderer Processes ReconcileResult

```python
def _process_children(
    self,
    parent_id: str,
    result: ReconcileResult,
) -> list[Patch]:
    patches = []

    # 1. REMOVE first (cleanup before new state)
    for node_id in result.removed:
        patches.append(RemovePatch(id=node_id))
        self._cleanup_node(node_id)  # Clear ElementState
        self._track_unmount_hook(node_id)

    # 2. ADD second (nodes already executed during creation)
    for node_id in result.added:
        node = self._nodes[node_id]
        patches.append(AddPatch(
            parent_id=parent_id,
            node=serialize_subtree(node_id),  # Full nested subtree
            children=result.child_order,
        ))
        self._track_mount_hook(node_id)

    # 3. UPDATE last
    for node_id in result.updated:
        old = self._previous_nodes[node_id]
        new = self._nodes[node_id]
        patches.append(UpdatePatch(
            id=node_id,
            props=diff_props(old.props, new.props),
            children=new.child_ids if new.child_ids != old.child_ids else None,
        ))

    # 4. Check if parent's child order changed
    if result.child_order != old_child_order:
        patches.append(UpdatePatch(id=parent_id, children=result.child_order))

    return patches
```

**Operation ordering**: Remove → Add → Update
- Remove first: cleanup state before creating new state
- Add second: new nodes already executed, just need patches
- Update last: independent of adds/removes

### AddPatch Contains Full Nested Subtree

When a new subtree is added, one AddPatch contains the entire nested serialization:

```python
def serialize_subtree(self, node_id: str) -> dict:
    """Serialize a node and all descendants as nested structure."""
    node = self._nodes[node_id]
    return {
        "id": node.id,
        "kind": node.component.element_kind.value,
        "type": node.component.element_name,
        "props": serialize_props(node.props),
        "children": [self.serialize_subtree(cid) for cid in node.child_ids],
    }
```

This is more efficient for the client - one message for the whole subtree. The flat storage is for server-side comparison; wire format is still nested for new subtrees.

### Unified Render API

Single entry point returning patches:

```python
def render(self) -> list[Patch]:
    """Render and return patches.

    Initial render: returns AddPatch for root with full subtree
    Incremental render: returns patches for changes only
    """
```

**Removes**:
- Separate `render()` vs `render_and_diff()` methods
- `_previous_props`, `_previous_children` dicts
- `_removed_ids` list
- `compute_patches()` function
- `_populate_previous_state()` function

### No Callback Registry Needed

Callback IDs are deterministic: `"{node_id}:{prop_name}"` (e.g., `"/0/1:on_click"`).

Since callback IDs can be constructed from node ID + prop name, we don't need a separate registry. The callable is stored in the node's props. Lookup derives the callback from the node:

```python
def get_callback(self, callback_id: str) -> Callable | None:
    """Look up callback from node props. No registry needed."""
    node_id, prop_name = callback_id.rsplit(":", 1)
    node = self._nodes.get(node_id)
    if node:
        for key, value in node.props:
            if key == prop_name and callable(value):
                return value
    return None
```

**Benefits**:
- No `_callback_registry` dict to maintain
- No registration during serialization
- Unmounted nodes naturally return None (not in `_nodes`)
- Function updates automatically reflected (new function in node.props)

**Serialization** just constructs the ID:
```python
def serialize_props(props: FrozenProps, node_id: str) -> dict:
    result = {}
    for key, value in props:
        if callable(value):
            result[key] = {"__callback__": f"{node_id}:{key}"}
        else:
            result[key] = serialize_value(value)
    return result
```

**Props comparison** treats callables specially - presence matters, not identity:
```python
def props_equal(old_props: FrozenProps, new_props: FrozenProps) -> bool:
    """Compare props, treating callables specially."""
    old_dict = dict(old_props)
    new_dict = dict(new_props)

    for key in old_dict.keys() | new_dict.keys():
        old_val = old_dict.get(key)
        new_val = new_dict.get(key)
        if callable(old_val) and callable(new_val):
            continue  # Both present, consider equal
        if callable(old_val) != callable(new_val):
            return False  # One is callable, other isn't
        if old_val != new_val:
            return False
    return True
```

### Async Hook Execution

Patches are returned immediately; hooks execute asynchronously without blocking:

```python
def render(self) -> list[Patch]:
    """Render and return patches. Does not execute hooks."""
    patches = self._render_and_patch()  # Active render context
    return patches

def get_pending_hooks(self) -> tuple[list[str], list[str]]:
    """Get and clear pending mount/unmount hooks."""
    mounts = self._pending_mounts.copy()
    unmounts = self._pending_unmounts.copy()
    self._pending_mounts.clear()
    self._pending_unmounts.clear()
    return mounts, unmounts
```

In MessageHandler:
```python
async def _render_loop(self) -> None:
    while True:
        await asyncio.sleep(self.batch_delay)
        if not self.tree.has_dirty_nodes():
            continue

        patches = self.tree.render()
        if patches:
            await self.send_message(PatchMessage(patches=patches))

        # Fire and forget - don't block on hooks
        mounts, unmounts = self.tree.get_pending_hooks()
        if mounts or unmounts:
            asyncio.create_task(self._process_hooks(mounts, unmounts))
```

### Reset State

For session reset or error recovery:

```python
def clear(self) -> None:
    """Reset all state for fresh render."""
    self._nodes.clear()
    self._previous_nodes.clear()
    self._element_state.clear()
    self._dirty_ids.clear()
    self._pending_mounts.clear()
    self._pending_unmounts.clear()
    self._current_node_id = None
    self._frame_stack.clear()
```

## Component Responsibilities

| Component | Single Responsibility |
|-----------|----------------------|
| `ElementNode` | Immutable node data (component, props, child_ids, id) |
| `ElementState` | Mutable runtime state (dirty, mounted, local_state, context) |
| `RenderTree` | Orchestration, node storage, frame stack, dirty tracking |
| `ComponentBase.__call__` | Position ID computation, reuse check, node creation |
| `reconcile_children()` | Pure function: compare old/new, categorize changes |
| `RenderTree._process_children` | Interpret ReconcileResult, generate patches, manage lifecycle |
| `serialize_subtree()` | Convert node + descendants to nested wire format |
| `get_callback()` | Derive callback from node props (no registry) |

## State Locations

```python
class RenderTree:
    # Node storage (flat)
    _nodes: dict[str, ElementNode]           # Current render
    _previous_nodes: dict[str, ElementNode]  # Previous render

    # Runtime state
    _element_state: dict[str, ElementState]  # Mutable state per node
    _dirty_ids: set[str]                     # Nodes needing re-render

    # Render context (active during render)
    _current_node_id: str | None             # Node currently rendering
    _frame_stack: list[list[str]]            # Collecting child IDs

    # Lifecycle (processed async after render)
    _pending_mounts: list[str]
    _pending_unmounts: list[str]

    # NO callback registry - callbacks derived from node.props
```

## Migration Strategy

This is a breaking change. No backwards compatibility needed.

### Phase 1: Position-Based IDs

1. Change ID generation to position-based (`/0/1/:key`)
2. Assign IDs at node creation in `ComponentBase.__call__`
3. Update `reconcile_node` to use position-based matching
4. Update serialization to use new ID format

### Phase 2: Flat Node Storage

1. Change `ElementNode.children` to `ElementNode.child_ids`
2. Add `_nodes: dict[str, ElementNode]` to RenderTree
3. Update node creation to store in flat dict
4. Update tree walking to use ID lookups

### Phase 3: Pure Reconciler

1. Extract reconciliation logic to pure function
2. Create `ReconcileResult` dataclass
3. Move mount/unmount/dirty calls to renderer
4. Update `_process_children` to interpret ReconcileResult

### Phase 4: Inline Patch Generation

1. Generate patches in `_process_children`
2. Remove `compute_patches()` and `_compute_node_patches()`
3. Remove `_previous_props`, `_previous_children`, `_removed_ids`
4. Merge `render()` and `render_and_diff()` into single method

### Phase 5: Eager Execution

1. Implement reuse check in `ComponentBase.__call__`
2. Execute children immediately in `with` blocks
3. Remove "mounted but not executed" state handling
4. Update frame collection to use IDs instead of nodes

## Open Questions

1. **Frame collection**: Currently collects `ElementNode` objects. With eager execution, should collect IDs instead. Need to track position counter per frame for non-keyed children.

2. **Error handling**: If execution fails mid-render with inline patching, some patches may be generated for nodes that won't exist. May need rollback or transactional approach.

3. **Testing**: Need comprehensive tests for reconciliation edge cases (reorder, insert, delete, type change, key collision).

4. **Initial render**: First render has no `_previous_nodes`. How do we handle this? Likely: check if `_previous_nodes` is empty, if so all nodes are "added" and we emit one AddPatch for the root subtree.

## Files to Modify

| File | Changes |
|------|---------|
| `rendering.py` | `ElementNode.child_ids`, flat `_nodes`/`_previous_nodes`, position IDs, remove `_callback_registry`, remove `_previous_props`/`_previous_children`/`_removed_ids`, unified `render()` API, `clear()`, `get_pending_hooks()`, `get_callback()` derives from props |
| `reconcile.py` | Pure function returning `ReconcileResult`, no side effects, preserve head/tail/key optimizations |
| `serialization.py` | Remove `compute_patches()`, simplify `serialize_node()` to `serialize_subtree()`, no callback registration |
| `base_component.py` | Position ID computation via `compute_position_id()`, reuse check, call `tree.store_node()` |
| `composition_component.py` | May need updates for eager execution in `with` blocks |
| `messages.py` | No changes needed |
| `message_handler.py` | Use single `render()` API, call `get_pending_hooks()`, async hook execution |

## What Gets Removed

- `_callback_registry` dict
- `register_callback()` method
- `clear_callbacks()` method
- `clear_callbacks_for_node()` method
- `_previous_props` dict
- `_previous_children` dict
- `_removed_ids` list
- `_populate_previous_state()` method
- `compute_patches()` function
- `_compute_node_patches()` function
- Separate `render()` vs `render_and_diff()` methods
- "Mounted but not executed" intermediate state
- Dual meaning of `children` field
