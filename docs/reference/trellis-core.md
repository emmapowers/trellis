# Trellis Core Reference

Dense reference for `src/trellis/core/`. Read source for implementation details.

---

## Data Structures

### ElementNode (`rendering.py`)
- Immutable (frozen dataclass) tree node representing a component invocation
- Fields: `component`, `props` (frozen tuples), `key`, `child_ids` (tuple of IDs), `id`, `_session_ref` (weakref)
- Children stored flat by ID reference, not nested
- Position-based IDs encode path + component: `/@{parent}/0@{component_id}`
- Keys override position index: `/@{parent}/:my_key@{component_id}`

### ElementState (`rendering.py`)
- Mutable runtime state per node, keyed by `node.id` in `RenderSession._element_state`
- Fields: `dirty`, `mounted`, `local_state` (cached Stateful instances), `state_call_count`, `context`, `parent_id`
- Separates mutable state from immutable node description

### RenderSession (`rendering.py`)
- Orchestrates render lifecycle, owns all nodes and state
- Key fields:
  - `_nodes`: current node dict
  - `_old_nodes`: snapshot before render (for diffing)
  - `_dirty_ids`: nodes needing re-render
  - `_element_state`: mutable state per node
  - `_frame_stack`: collects child IDs during `with` blocks
  - `_callback_registry`: callbacks by deterministic ID
  - `_patches`: accumulated patches during render
  - `_current_node_id`: executing node (for dependency tracking)

---

## Rendering

### Initial Render
- `render(session)` executes root component
- Components execute eagerly (non-containers) or defer to `__exit__` (containers)
- Frame stack tracks parent-child relationships during `with` blocks
- Returns `[AddPatch]` with full serialized tree
- Processes mount hooks after tree built

### Incremental Re-render
- Background loop runs ~30fps, checks `_dirty_ids`
- Snapshot: `_old_nodes = dict(_nodes)`
- Re-execute each dirty node via `_render_single_node()`
- Reconcile old vs new children, emit patches inline
- Returns batch of patches

### Execution Flow
- Non-containers: eager execution on call
- Containers: `__enter__` pushes frame, collects children, `__exit__` executes with children
- Frame pop assigns `child_ids` to parent node

---

## State Management

### Stateful (`state.py`)
- Base dataclass for reactive state
- Auto-cached per component via `(type, call_index)` key in `local_state`
- Same instance returned across re-renders (like React hooks)

### Dependency Tracking
- `StatePropertyInfo` per property holds `watchers: WeakSet[ElementNode]`
- On property read during render: add current node to watchers
- On property write (outside render only): iterate watchers, mark each dirty
- WeakSet auto-cleans when nodes are replaced/GC'd

### Tracked Collections (`tracked.py`)
- `TrackedList`: tracks by item identity + `ITER_KEY` for structure
- `TrackedDict`: tracks by key + `ITER_KEY` for new keys
- `TrackedSet`: tracks by item value + `ITER_KEY`
- Auto-converted from plain collections in Stateful fields

---

## Reconciliation (`reconcile.py`)

### Algorithm
- Pure function: `reconcile_children(old_ids, new_ids) → ReconcileResult`
- Three phases: head scan → tail scan → set lookup for middle
- O(n) typical case

### ReconcileResult
- `added`: new IDs not in old
- `removed`: old IDs not in new
- `matched`: IDs in both (check for prop changes)
- `child_order`: final ordering

### Processing
- Removed: emit `RemovePatch`, unmount subtree
- Added: emit `AddPatch` with serialized subtree
- Matched: compare props, emit `UpdatePatch` if changed

---

## Patches (`messages.py`)

### Types
- `AddPatch(parent_id, children, node)`: add subtree
- `UpdatePatch(id, props, children)`: change props and/or child order
- `RemovePatch(id)`: remove subtree

### Generation
- Inline during reconciliation, accumulated in `_patches`
- Initial render: single `AddPatch` with full tree
- Incremental: batch of mixed patch types

---

## Components

### Base (`base_component.py`)
- Abstract `Component` with `render()` method
- `_place()` handles node creation and eager execution

### CompositionComponent (`composition_component.py`)
- Created via `@component` decorator wrapping user function
- `element_name="CompositionComponent"` on client (layout-only)

### ReactComponentBase (`react_component.py`)
- Leaf components mapping to React widgets
- `_element_name`: React component name
- `_has_children`: accepts children via `with` block

### ElementKind
- `REACT_COMPONENT`: custom component
- `JSX_ELEMENT`: HTML element
- `TEXT`: text node

---

## Serialization (`serialization.py`)

### Node Serialization
- Recursive conversion to JSON-serializable dict
- Fields: `kind`, `type`, `name`, `key` (node ID), `props`, `children`
- CompositionComponent props omitted (layout-only)

### Callback Registration
- Callables → deterministic ID: `"{node_id}:{prop_name}"`
- Stored in `_callback_registry`, overwritten on re-render
- Serialized as `{"__callback__": cb_id}`

### Mutable (`mutable.py`)
- Two-way binding wrapper for state properties
- Serialized as `{"__mutable__": cb_id, "value": current}`
- `mutable()` captures last property access from `_last_property_access`

---

## Messages (`messages.py`, `message_handler.py`)

### Types
- `HelloMessage`: client handshake (client_id)
- `HelloResponseMessage`: server response (session_id, version, debug config)
- `PatchMessage`: batch of patches
- `EventMessage`: user interaction (callback_id, args)
- `ErrorMessage`: exception info (error, context)

### MessageHandler Lifecycle
1. Hello handshake
2. Initial render → send patches
3. Start background render loop
4. Event loop: receive messages, invoke callbacks, send responses

### Render Loop
- ~30fps (configurable batch_delay)
- Check `has_dirty_nodes()`, call `render()`, send `PatchMessage`

---

## Complete Flow

```
User action → EventMessage(callback_id, args)
  → MessageHandler invokes callback
  → Callback mutates state: state.x = y
  → Stateful.__setattr__ marks watchers dirty
  → Background loop detects dirty nodes
  → render(): snapshot → re-execute dirty → reconcile → emit patches
  → PatchMessage sent to client
  → React applies patches
```

---

## Key Files

| File | Purpose |
|------|---------|
| `rendering.py` | ElementNode, ElementState, RenderSession, render lifecycle |
| `reconcile.py` | Pure reconciliation algorithm |
| `state.py` | Stateful base, dependency tracking, StatePropertyInfo |
| `tracked.py` | TrackedList/Dict/Set for fine-grained collection reactivity |
| `serialization.py` | Tree → JSON, callback registration |
| `messages.py` | Message types, Patch types |
| `message_handler.py` | WebSocket lifecycle, render loop |
| `base_component.py` | Component base class |
| `composition_component.py` | @component decorator |
| `react_component.py` | ReactComponentBase for widgets |
| `mutable.py` | Two-way binding wrapper |
