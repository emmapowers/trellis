# Simplifying Dependency Cleanup with WeakRef to ElementNode

## Problem

Currently there's a bidirectional relationship between `Stateful` and `ElementState` for dependency tracking:

**In `Stateful` (state.py):**
```python
@dataclass
class StatePropertyInfo:
    node_ids: set[str]  # Node IDs that depend on this property
    node_trees: dict[str, weakref.ref[RenderTree]]  # node_id -> RenderTree
```

**In `ElementState` (rendering.py):**
```python
watched_deps: dict[int, tuple[tp.Any, set[str]]]  # id(Stateful) -> (Stateful, {prop_names})
```

The `watched_deps` reverse mapping exists so `clear_node_dependencies()` can remove a node from all Stateful instances it was watching. This cleanup is needed:

1. **On unmount**: Prevent stale node IDs from accumulating in Stateful
2. **On re-render**: Unsubscribe from properties the component no longer reads

## Key Insight

`ElementNode` is immutable and replaced on every re-render via `dataclass_replace()`. This ephemeral lifecycle matches exactly what we need:

- **Re-render**: Old `ElementNode` replaced → weakref dies → old registrations gone automatically
- **Reuse (no re-exec)**: Same `ElementNode` persists → weakref valid → registrations correct
- **Unmount**: `ElementNode` removed → weakref dies → registrations gone automatically

## Proposed Solution

Use `weakref.WeakSet[ElementNode]` instead of storing node ID strings:

```python
@dataclass
class StatePropertyInfo:
    name: str
    watchers: weakref.WeakSet[ElementNode] = field(default_factory=weakref.WeakSet)
```

### Changes Required

1. **Add `_tree_ref` to `ElementNode`** (set at creation in `_place`):
   ```python
   @dataclass(frozen=True)
   class ElementNode:
       # ... existing fields ...
       _tree_ref: weakref.ref[RenderTree] | None = None
   ```

2. **Add `_current_node` to `RenderTree`** (so `__getattribute__` can access it):
   ```python
   class RenderTree:
       _current_node: ElementNode | None = None  # Set during execution
   ```

3. **Change `StatePropertyInfo`** to use `WeakSet[ElementNode]`:
   ```python
   @dataclass
   class StatePropertyInfo:
       name: str
       watchers: weakref.WeakSet[ElementNode] = field(default_factory=weakref.WeakSet)
   ```

4. **Update `Stateful.__getattribute__`** to register the node:
   ```python
   node = context._current_node
   if node:
       state_info.watchers.add(node)
   ```

5. **Update `Stateful.__setattr__`** to mark dirty via weakrefs:
   ```python
   for node in state_info.watchers:  # WeakSet auto-skips dead refs
       tree = node._tree_ref() if node._tree_ref else None
       if tree:
           tree.mark_dirty_id(node.id)
   ```

6. **Remove from `ElementState`**:
   - `watched_deps` field

7. **Remove from `RenderTree`**:
   - `clear_node_dependencies()` method
   - Calls to `clear_node_dependencies()` in `_process_pending_hooks()` and `eager_execute_node()`

## Lifecycle Analysis

| Scenario | What happens | Result |
|----------|--------------|--------|
| First render | Node executes, registers with WeakSet | Dependency tracked |
| Re-render (props changed) | New ElementNode created, old dies | Old refs gone, fresh registration |
| Re-render (props same, not dirty) | Same ElementNode reused | Existing refs still valid |
| Unmount | ElementNode removed from tree | Refs die, auto-cleaned from WeakSet |

## Benefits

- Eliminates `watched_deps` reverse mapping
- Eliminates `clear_node_dependencies()`
- No explicit cleanup code needed
- WeakSet handles all lifecycle automatically
- Simpler mental model: "Stateful watches ElementNodes, when they die, the watch dies"

## Tradeoffs

- Adds `_tree_ref` field to ElementNode (small memory overhead per node)
- Adds `_current_node` to RenderTree (minimal)
- WeakSet iteration slightly slower than set iteration (negligible)
