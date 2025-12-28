# Complexity Analysis: Trellis Core

## What the Project Does

Trellis is a reactive UI framework for Python that enables building web/desktop applications with a React-like component model. It has:
- Python components that produce an element tree
- A reconciliation algorithm that efficiently updates the tree
- Serialization to send the tree to clients (React)
- Fine-grained reactivity via automatic dependency tracking
- 30fps batched updates via WebSocket

## Core Data Flow

1. **Components** create `Element` descriptors (immutable)
2. **Reconciliation** matches new vs old nodes, preserving IDs
3. **Serialization** converts tree to JSON
4. **Diffing** compares against previous state to generate patches
5. **Client** applies patches to update React tree

---

## Main Sources of Complexity

### 1. Two-Pass Rendering + Diffing (the biggest issue)

The architecture doc (`trellis-diffing-architecture.md` lines 510-796) already identifies this problem:

```
Current:
  1. Reconcile/Execute → build updated tree
  2. compute_patches() → walk tree AGAIN comparing to _previous_props/_previous_children

During reconciliation, we already know which nodes are new/changed/removed—
the second pass re-discovers this information.
```

Looking at `serialization.py:118-160`, `compute_patches()` walks the entire tree comparing current props to `previous_props`. But reconciliation (`reconcile.py:53-115`) already knows:
- If a node is new (no old_node)
- If a node changed (props differ)
- If a node was removed (unmount_node_tree called)

This duplicated work is the largest source of unnecessary complexity.

### 2. Dual Dirty Tracking

Two places track the same information:
- `RenderTree._dirty_ids: set[str]` (rendering.py:317)
- `ElementState.dirty: bool` (rendering.py:277)

In `mark_dirty_id()` (rendering.py:756-773), both are updated:
```python
self._dirty_ids.add(node_id)
if node_id in self._element_state:
    self._element_state[node_id].dirty = True
```

And in `_render_dirty_nodes()` (rendering.py:600-605), both are checked:
```python
if state and state.dirty:
    state.dirty = False
    self._render_single_node(node_id)
```

One could be eliminated.

### 3. Descriptor vs Mounted Children Distinction

Throughout the code, there's a constant check pattern (rendering.py:630-644):
```python
# Check if children are mounted (have IDs) or just descriptors
first_has_id = bool(node.children[0].id)
if __debug__:
    all_have_id = all(bool(c.id) for c in node.children)
    assert first_has_id == all_have_id, ...
```

This distinction exists because:
- **Descriptors**: Created in `with` blocks, no ID yet, will be reconciled
- **Mounted**: Already reconciled, have IDs

This adds mental overhead and is error-prone. Eager ID assignment would eliminate it.

### 4. Three-Way ID Handling

- `node.id`: Server-assigned ID (e.g., "e5")
- `node.key`: User-provided key (optional)
- `_get_stable_id(node)` in serialization.py:162-167 returns `key or id`

The client uses `key` for React reconciliation. This means:
- The server tracks `id`
- The client sees `key or id`
- Diffing must use `_get_stable_id()` everywhere

Could be simplified by treating user keys as the ID from the start.

### 5. Separated State Storage

Four separate dictionaries track node state:
- `_element_state: dict[str, ElementState]` - runtime state
- `_previous_props: dict[str, dict]` - last serialized props
- `_previous_children: dict[str, list[str]]` - last child IDs
- `_callback_registry: dict[str, Callable]` - callbacks

These could be unified into `ElementState` (or a single per-node structure).

### 6. Dependency Tracking with Bi-directional References

`Stateful.__getattribute__` (state.py:168-215) and `__setattr__` (state.py:217-284) manage:
- Forward: `StatePropertyInfo.node_ids` + `node_trees` (weakref)
- Reverse: `ElementState.watched_deps` for cleanup

The reverse mapping exists because we need to clean dependencies when a node unmounts. This adds significant complexity with `id(self)` keys and manual cleanup.

---

## Parts More Complicated Than Necessary

### 1. The Two-Pass Diff System (highest impact)

The current approach:
```python
# Pass 1: Render dirty nodes
self._render_dirty_nodes()

# Pass 2: Walk entire tree computing patches
compute_patches(self.root_node, self, self._previous_props, ...)
```

The architecture doc proposes generating patches inline during reconciliation. This would:
- Eliminate the second tree walk
- Remove `_previous_props`/`_previous_children` storage
- Make the reconciler return structured data (ReconcileResult)

### 2. Dual Dirty Tracking

Either `_dirty_ids` OR `ElementState.dirty` is sufficient. The set is more efficient for iteration; the boolean is more direct for checking. Pick one.

### 3. ID Assignment Timing

Currently:
1. Component creates `Element` with `id=""`
2. During mount, ID assigned: `new_id = self.next_element_id()`
3. Everywhere else checks `if children[0].id` to detect state

Simpler: Assign IDs eagerly in `Element.__init__` or when created by component.

### 4. Key vs ID Duality

The client only needs one stable identifier. The current system:
- Generates internal IDs (`e1`, `e2`, ...)
- Allows user keys
- Sends `key or id` to client

Could just use the ID as the React key unless user provides one, eliminating `_get_stable_id()`.

### 5. Frame Stack for Children

The current design uses `push_frame()`/`pop_frame()` to collect children in `with` blocks. While elegant, it requires:
- A separate stack structure
- Understanding frame lifecycle
- Coordination with frozen dataclass mutation

An alternative: Have `with` return a context object that directly manages the parent's children list.

---

## Recommendations

Based on the architecture doc's "Design Exploration" section and this analysis:

1. **Inline patch generation** - Implement the ReconcileResult approach from the architecture doc. This eliminates the biggest source of complexity.

2. **Unify dirty tracking** - Remove `ElementState.dirty`, keep only `_dirty_ids`. Check `mounted` state in the set iteration.

3. **Eager ID assignment** - Assign IDs when Element is created (in `Component.__call__`). This eliminates the descriptor/mounted distinction.

4. **Consolidate state storage** - Move `_previous_props`/`_previous_children` into `ElementState` if keeping the two-pass approach, or eliminate them with inline patching.

5. **Simplify key handling** - Have the server always use `id` as the stable key. Only use user-provided `key` for matching in reconciliation, not for client identity.
