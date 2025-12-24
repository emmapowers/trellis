# Position-Based IDs Implementation Status

## Overview

This document tracks the implementation of Phase 1 (Position-Based IDs) from the [rendering refactor plan](./rendering-refactor-plan.md).

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
- `ElementNode.__enter__()` passes `self.id` as parent_id to `push_frame()`
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
- Changed `ElementNode.children: tuple[ElementNode, ...]` to `ElementNode.child_ids: tuple[str, ...]`
- Child nodes are now referenced by ID instead of nested directly

### 2. Flat Node Storage
- Added `_nodes: dict[str, ElementNode]` to RenderTree
- All nodes stored flat, accessible via `get_node(id)`
- `add_to_current_frame()` stores nodes in flat dict and adds ID to frame

### 3. Frame Updates
- `Frame.children` renamed to `Frame.child_ids`
- Frames collect string IDs, not ElementNode objects

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

## Next Steps

Ready to proceed with:

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
