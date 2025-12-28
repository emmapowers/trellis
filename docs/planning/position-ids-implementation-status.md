# Rendering Refactor Implementation Status

## Overview

This document tracks the implementation of the [rendering refactor plan](./rendering-refactor-plan.md).

**Progress:**
- ✅ Phase 1: Position-Based IDs
- ✅ Phase 2: Flat Node Storage
- ✅ Phase 3: Pure Reconciler
- ✅ Phase 4: Inline Patch Generation
- ✅ Phase 5: Eager Execution

## ✅ Phase 1 Complete

All items from Phase 1 have been implemented:

### 1. Frame Tracking (`rendering.py`)
- Added `parent_id` and `position` counter to `Frame` dataclass
- `push_frame()` now accepts `parent_id` parameter
- `next_position_id(component, key)` computes position-based IDs with component identity

### 2. ID Assignment at Creation (`base_component.py`)
- `_place()` now calls `ctx.next_position_id(self, key)` to get the ID
- Node is created with ID already assigned (no longer empty)

### 3. Mount Changes (`rendering.py`)
- `mount_new_node()` uses existing `node.id` - no longer assigns IDs
- Just creates ElementState and marks dirty

### 4. Reconciler Changes (`reconcile.py`)
- Matching is now by ID (position + component identity encodes identity)
- Added check: if node has ID but no ElementState, treat as new mount
- Removed ID transfer logic

### 5. Serialization (`serialization.py`)
- `serialize_node()` uses `node.id` directly for the `key` field

### 6. Container Components (`rendering.py`)
- `Element.__enter__()` passes `self.id` as parent_id to `push_frame()`
- `execute_node()` passes `node.id` as parent_id to `push_frame()`

### 7. Component Identity in IDs
- IDs now include `@{id(component)}` to encode component type
- Different component types at the same position get different IDs
- No state collision when types change at a position

### 8. Key Escaping
- Special characters (`:`, `@`, `/`, `%`) in user keys are URL-encoded
- `_escape_key()` helper function handles escaping

### 9. Cleanup of Workarounds
- `_pending_unmounts` simplified to `list[str]` (no longer saves local_state)
- `track_unmount()` simplified - just appends node_id
- `_process_pending_hooks()` now safely pops ElementState after unmount
- Removed `_call_unmount_hooks_with_state()` method

## ID Format (Current - Position + Component Identity)

```
/@140234567890                    # root (with component id)
/@140234567890/0@140234567891     # first child of root
/@140234567890/0@140234567891/1@140234567892   # grandchild
/@140234567890/:submit@140234567891            # keyed child
```

Each segment includes `@{id(component)}` where `id(component)` is the Python object ID of the component instance. This ensures different component types at the same position get different IDs.

## Test Status

- 482 tests passing
- 0 tests failing
- All type checks pass
- All linting passes

## Files Modified

| File | Changes |
|------|---------|
| `src/trellis/core/rendering.py` | `_escape_key()`, updated `next_position_id()`, simplified `track_unmount()`, simplified `_process_pending_hooks()`, removed `_call_unmount_hooks_with_state()` |
| `src/trellis/core/base_component.py` | `_place()` passes `self` to `next_position_id()` |
| `src/trellis/core/reconcile.py` | ID-based matching, minor type fix |
| `tests/test_serialization.py` | Updated 2 tests for new ID format (see below) |

### Test Changes

Two assertions in `tests/test_serialization.py` were updated to match the new ID format:

1. **`test_serialize_simple_node`**: Changed from checking `startswith("e")` to `startswith("/@")`
2. **`test_serialize_node_with_key`**: Changed from checking `== "my-key"` to `":my-key@" in result["key"]`

## ✅ Phase 2 Complete: Flat Node Storage

All items from Phase 2 have been implemented:

### 1. Child ID References
- Changed `Element.children: tuple[Element, ...]` to `Element.child_ids: tuple[str, ...]`
- Child nodes are now referenced by ID instead of nested directly

### 2. Flat Node Storage
- Added `_nodes: dict[str, Element]` to RenderTree
- All nodes stored flat, accessible via `get_node(id)`
- `add_to_current_frame()` stores nodes in flat dict and adds ID to frame

### 3. Frame Updates
- `Frame.children` renamed to `Frame.child_ids`
- Frames collect string IDs, not Element objects

### 4. Serialization Updates
- `serialize_node()` builds tree by looking up children via `ctx.get_node()`
- Props exclude `child_ids` (children serialized separately)

### 5. Re-render Bug Fix
- Fixed critical bug: old nodes saved BEFORE `render()` to prevent overwriting
- `reconcile_node_children()` accepts `old_nodes` parameter for safe lookup

## ✅ Batched Updates / Patch System Complete

Incremental update system for efficient client updates:

### 1. New Message Types (`messages.py`)
- `UpdatePatch`: Update props and/or children order
- `RemovePatch`: Remove a node from tree
- `AddPatch`: Add new node with full subtree
- `PatchMessage`: Container for list of patches

### 2. Patch Computation (`serialization.py`)
- `compute_patches()`: Compares current tree to previous state
- Generates minimal patches for props changes, child reordering, additions, removals
- Tracks `_previous_props` and `_previous_children` on RenderTree

### 3. Render Loop (`message_handler.py`)
- Background render loop at configurable frame rate (default 30fps)
- Callbacks no longer trigger immediate re-render
- `batch_delay` parameter controls frame period

### 4. Client-Side Updates
- New `TrellisStore` class: ID-keyed state store with per-node subscriptions
- New `ClientMessageHandler`: Common message protocol handler
- `TreeRenderer` updated to read from store and apply patches
- All platform clients (browser, desktop, server) updated

## Test Status

- 482 tests passing
- 0 tests failing
- All type checks pass

## Files Modified

### Core Changes
| File | Changes |
|------|---------|
| `src/trellis/core/rendering.py` | Flat storage, `child_ids`, Frame updates, `render_and_diff()` |
| `src/trellis/core/reconcile.py` | Works with child_ids, accepts `old_nodes` param |
| `src/trellis/core/serialization.py` | Tree from flat storage, `compute_patches()` |
| `src/trellis/core/messages.py` | Patch types, `PatchMessage` |
| `src/trellis/core/message_handler.py` | Render loop, `batch_delay` |
| `src/trellis/core/base_component.py` | Uses `child_ids` |

### Platform Changes
| File | Changes |
|------|---------|
| `src/trellis/platforms/common/client/src/core/store.ts` | New TrellisStore |
| `src/trellis/platforms/common/client/src/ClientMessageHandler.ts` | New common handler |
| `src/trellis/platforms/common/client/src/TreeRenderer.tsx` | Store integration, patch handling |
| `src/trellis/platforms/*/client/src/*.ts` | All clients use new handler |
| `src/trellis/platforms/*/handler.py` | Platform handler updates |

### Test Changes
Many test files updated to use `.child_ids` and `ctx.get_node()` pattern.

## ✅ Phase 3 Complete: Pure Reconciler

The reconciliation logic has been extracted into a pure function:

### 1. ReconcileResult Dataclass (`reconcile.py`)
- New `ReconcileResult` dataclass containing:
  - `added`: Node IDs that are new (not in old list)
  - `removed`: Node IDs that were removed (in old, not in new)
  - `matched`: Node IDs that exist in both lists
  - `child_order`: Final order of child IDs

### 2. Pure `reconcile_children` Function (`reconcile.py`)
- Pure function that compares old and new child ID lists
- Returns `ReconcileResult` with categorized changes
- No side effects - doesn't access RenderTree or modify any state
- Preserves the multi-phase optimization (head scan, tail scan, middle lookup)

### 3. `process_reconcile_result` Method (`rendering.py`)
- New method in RenderTree that interprets ReconcileResult
- Applies side effects in correct order:
  1. REMOVE first (unmount removed nodes)
  2. ADD second (mount new nodes)
  3. MATCHED last (reconcile to check props and mark dirty)
- Returns final child order

### 4. Updated `reconcile_node_children` (`reconcile.py`)
- Now uses pure `reconcile_children()` to compare lists
- Delegates side effects to `ctx.process_reconcile_result()`
- Much simpler implementation

## ✅ Phase 4 Complete: Inline Patch Generation

Patches are now generated inline during reconciliation instead of a separate tree walk:

### 1. Patch Accumulation Infrastructure (`rendering.py`)
- Added `_patches: list[Patch]` to RenderTree for accumulating patches during render
- Added `_is_incremental_render: bool` flag to control patch emission
- Added `serialized_props` and `previous_child_ids` fields to ElementState

### 2. Inline Patch Generation (`rendering.py`)
- New helper methods: `_emit_patch()`, `_serialize_node_for_patch()`, `_serialize_props_for_state()`
- `_emit_update_patch_if_changed()` compares current vs previous state and emits UpdatePatch
- `_populate_subtree_state()` initializes previous state for new subtrees

### 3. Updated `process_reconcile_result()` (`rendering.py`)
- Emits `RemovePatch` for removed nodes
- Emits `AddPatch` with serialized subtree for added nodes
- Emits `UpdatePatch` for matched nodes with changed props

### 4. Updated `_render_single_node()` (`rendering.py`)
- Emits `UpdatePatch` for re-rendered nodes if props or children changed

### 5. Updated `render_and_diff()` (`rendering.py`)
- Clears and collects patches during render cycle
- Returns accumulated patches (no longer calls `compute_patches()`)

### 6. Updated `render()` (`rendering.py`)
- Populates previous state in ElementState via `_populate_subtree_state()`

### 7. Removed Old Infrastructure
- Removed `_previous_props`, `_previous_children`, `_removed_ids` from RenderTree
- Removed `compute_patches()`, `_compute_node_patches()`, `_get_stable_id()`, `_populate_subtree_state()` from serialization.py
- Updated `unmount_node_tree()` to no longer track `_removed_ids`

## Test Status

- 482 tests passing
- 0 tests failing
- All type checks pass
- All linting passes

## Files Modified for Phase 4

| File | Changes |
|------|---------|
| `src/trellis/core/rendering.py` | Added `_patches`, `_is_incremental_render`, ElementState fields; added inline patch generation helpers; updated `process_reconcile_result()`, `_render_single_node()`, `render()`, `render_and_diff()`; removed `_previous_props`, `_previous_children`, `_removed_ids` |
| `src/trellis/core/serialization.py` | Removed `compute_patches()`, `_compute_node_patches()`, `_get_stable_id()`, `_populate_subtree_state()` |

## ✅ Phase 5 Complete: Eager Execution

Components now execute immediately when created, with reuse optimization:

### 1. Reuse Check in `_place()` (`base_component.py`)
- Before creating a node, check if old node at same position can be reused
- Reuse conditions: same component, same props, node is mounted, not dirty
- If reusable, return old node (skipping execution entirely)
- Subtree is preserved - no re-execution of children

### 2. Eager Execution for Non-Container Components (`base_component.py`)
- When a node cannot be reused, execute immediately in `_place()`
- Call `ctx.eager_execute_node()` which runs `component.render()`
- Children created during render are also executed eagerly
- No "mounted but not executed" intermediate state

### 3. Eager Execution for Container Components (`rendering.py`)
- Container components (those with `children` parameter) defer execution to `__exit__`
- In `__exit__`, input children are collected from the frame
- Container's render() is executed with input children as props
- Output children (what render() produces) replace input children in child_ids

### 4. Simplified `_render_node_tree()` (`rendering.py`)
- Initial render now just calls `root_component()` which triggers eager execution
- Entire tree is built during this single call
- No separate `reconcile_node` or dirty queue processing for initial render

### 5. `eager_execute_node()` Method (`rendering.py`)
- New method that combines mounting and execution
- Creates ElementState if needed, marks as mounted
- Clears dirty flag to prevent double execution
- Pushes frame, calls render(), reconciles children
- Used by both `_place()` and `_render_single_node()`

### 6. Updated `process_reconcile_result()` (`rendering.py`)
- Removed reconcile_node call for matched nodes (already handled in _place())
- For added nodes, just ensure ElementState exists (node already executed)
- Simplified to handle removals, additions, and patch emission

### Key Benefits
- Single-pass rendering - no separate reconciliation phase
- Subtrees reused completely when props unchanged
- No intermediate "dirty but not executed" state
- Simpler mental model - components execute when created

## Test Status

- 482 tests passing
- 0 tests failing
- All type checks pass
- All linting passes

## Files Modified for Phase 5

| File | Changes |
|------|---------|
| `src/trellis/core/base_component.py` | Added reuse check and eager execution in `_place()` |
| `src/trellis/core/rendering.py` | Added `eager_execute_node()`, updated `__exit__` for containers, simplified `_render_node_tree()`, updated `process_reconcile_result()` |

## Rendering Refactor Complete

All 5 phases of the rendering refactor are now complete:

1. **Position-Based IDs**: IDs assigned at creation based on tree position + component identity
2. **Flat Node Storage**: Nodes stored in flat dict with ID references
3. **Pure Reconciler**: Reconciliation logic extracted to pure function
4. **Inline Patch Generation**: Patches generated during reconciliation, not in separate pass
5. **Eager Execution**: Components execute immediately when created with reuse optimization

## Next Steps

See [test-refactor-plan.md](./test-refactor-plan.md) for planned test improvements:
- Add unit tests for pure `reconcile_children()` function
- Add tests for `_escape_key()` and position ID generation
- Refactor existing reconcile tests to remove redundant lifecycle hook testing
