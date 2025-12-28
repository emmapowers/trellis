# Trellis Core Reference

> **Terminology note**: The codebase uses "node" and "element" interchangeably. Prefer "element" in new code.

## Architecture Overview

```
State change → dirty.mark(node_id) → render() → patches → frontend
```

**Render loop**: Session holds element tree. State mutations mark nodes dirty. `render()` processes dirty nodes, creating patches (Add/Update/Remove) sent to frontend.

---

## Core Data Structures

### Element
Immutable tree node representing a component invocation.

```python
@dataclass
class Element:
    component: Component
    props: dict
    key: str | None
    child_ids: tuple[str, ...]  # Populated after execution
    id: str                      # Position-based: "{parent_id}/{pos}@{id(component)}"
    render_count: int            # Session's render_count at creation
```

**ID format**: `{parent_id}/{position}@{id(component)}` or `{parent_id}/:{key}@{id(component)}`

Component identity in ID enables reuse optimization: same component + same props + mounted + not dirty → skip re-execution.

### ElementState
Mutable runtime state for each Element, keyed by `node.id`.

```python
@dataclass
class ElementState:
    mounted: bool
    local_state: dict[(type, int), Stateful]  # (class, call_index) → cached instance
    state_call_count: int                      # Counter for hook-like ordering
    context: dict[type, Stateful]              # Context API storage
    parent_id: str | None                      # For context walking
```

### RenderSession
Container managing entire render lifecycle.

```python
class RenderSession:
    root_component: Component
    elements: ElementStore      # Flat storage: id → Element
    states: ElementStateStore   # Flat storage: id → ElementState
    dirty: DirtyTracker         # Set of node IDs needing re-render
    active: ActiveRender | None # Only set during render pass
    render_count: int           # Incremented each render
    lock: RLock                 # Thread-safe concurrent renders
```

---

## Component System

### Hierarchy

| Class | Purpose | Created By |
|-------|---------|------------|
| `Component` | Abstract base | — |
| `CompositionComponent` | User render functions | `@component` decorator |
| `ReactComponentBase` | Widgets with React impl | `@react_component_base(name)` |

### CompositionComponent
Created via `@component` decorator. Wraps a render function.

```python
@component
def MyComponent(label: str, children: list[Element] = []):
    with Column():
        Label(text=label)
        for child in children:
            child()
```

**Children**: Function has `children` param → supports `with` block → children collected in Frame.

### ReactComponentBase
Base for widgets. Sets `_element_name` for frontend. Provides style prop merging.

```python
@react_component_base("Button", has_children=True)
class Button(ReactComponentBase):
    def __call__(self, text: str = "", on_click: Callback = None, ...):
        return super().__call__(text=text, on_click=on_click, ...)
```

---

## State System

### Stateful Base Class
Automatic dependency tracking for fine-grained reactivity.

**Instance caching** (hooks pattern):
- `Stateful()` during render → cached by `(class, call_index)` on ElementState
- Same instance returned across re-renders
- Order matters: call index incremented per call

**Dependency tracking** (`__getattribute__`):
- Property access during render → node added to `StatePropertyInfo.watchers` WeakSet
- WeakSet auto-cleans when nodes GC

**Mutation** (`__setattr__`):
- Marks all watcher nodes dirty
- Raises `RuntimeError` if called during render
- Auto-converts collections to Tracked versions

### Context API

```python
# Provider
with my_state:  # Stores on current node's ElementState.context
    ChildComponent()

# Consumer
state = MyState.from_context()  # Walks parent_id chain
```

### Tracked Collections
Fine-grained reactivity within collections.

| Type | Tracks By | Example |
|------|-----------|---------|
| `TrackedList` | Item identity | `lst[i]` → dependency on `id(item)` |
| `TrackedDict` | Key | `d[key]` → dependency on key |
| `TrackedSet` | Value | `s.add(x)` → dependency on x |

Iteration/length tracked via special `ITER_KEY`.

### Mutable References
Two-way data binding for form inputs.

```python
TextInput(value=mutable(state.text))  # Reads and writes state.text
```

`mutable(state.prop)` captures property reference immediately after access.

---

## Render Flow

### Initial Render
1. Increment `session.render_count`
2. Create root Element via `_place()`
3. `_execute_tree()` recursively executes all nodes
4. Return `RenderAddPatch` with root

### Node Execution (`_execute_single_node`)
1. Create/reuse Element
2. Get/create ElementState
3. Set `current_node_id` in ActiveRender (for dependency tracking)
4. Push Frame for child collection
5. `component.execute(**props)` — component function runs
6. Pop Frame, collect child IDs
7. Reconcile children (diff old vs new)
8. Recursively execute children

### Node Reuse Check
At `_place()`:
- Same position + same component + same props + mounted + not dirty → **reuse old node** (skip execution)
- Otherwise → create new Element

### Incremental Render
1. Process dirty nodes one at a time from `session.dirty`
2. Create NEW Element instances (enables GC of old)
3. Generate patches for changes
4. Return patch list

### Reconciliation (`reconcile.py`)
Two-pointer algorithm (head + tail) for fast matching, set-based for middle.

Returns: `added`, `removed`, `matched`, `child_order`

---

## Patches

| Type | Fields | When |
|------|--------|------|
| `RenderAddPatch` | `parent_id`, `children`, `node` | New node |
| `RenderUpdatePatch` | `node_id`, `props?`, `children?` | Props or children changed |
| `RenderRemovePatch` | `node_id` | Node removed |

Initial render: one AddPatch. Updates: mix of Add/Update/Remove.

---

## Dirty Tracking

```
state.x = 5
  → Stateful.__setattr__
    → for node in StatePropertyInfo.watchers:
        session.dirty.mark(node.id)
  → next render() picks up dirty nodes
```

`DirtyTracker`: Set-based. `mark()` acquires session lock to synchronize with ongoing renders.

---

## Frame Stack
Child collection via `with` blocks.

```python
with Column():     # Push Frame
    Button(...)    # child_id added to Frame
    Button(...)    # child_id added to Frame
# Pop Frame → child_ids stored in Element
```

---

## Lifecycle

Mount/unmount tracked in `LifecycleTracker` (pending lists). Processed AFTER `session.active` is cleared and lock is released. Unmounts first, then mounts.

Hooks can safely modify state because `is_render_active()` returns False (session.active is None).

---

## Critical Invariants

1. **Components run during render** — no side effects, use callbacks/hooks
2. **State instances cached per component** — call order matters (like React hooks)
3. **Dependencies tracked by property access** — reading registers dependency
4. **State mutations forbidden during render** — raises RuntimeError
5. **WeakSets auto-cleanup** — dead nodes removed from watchers automatically
6. **One render per session at a time** — lock prevents concurrent renders
7. **Element recreation on re-render** — new objects so old ones GC

---

## File Map

| File | Purpose |
|------|---------|
| `rendering/render.py` | Main render loop, tree execution, patches |
| `rendering/element.py` | Element definition, with-block protocol |
| `rendering/element_state.py` | Runtime state per node |
| `rendering/session.py` | Session container, context vars |
| `rendering/reconcile.py` | Tree diffing algorithm |
| `rendering/dirty_tracker.py` | Dirty node set |
| `rendering/active.py` | Render-scoped state |
| `rendering/frames.py` | Frame stack for children |
| `rendering/patches.py` | Patch types |
| `rendering/lifecycle.py` | Mount/unmount tracking |
| `components/base.py` | Component base, placement logic |
| `components/composition.py` | @component decorator |
| `components/react.py` | ReactComponentBase |
| `state/stateful.py` | Reactive state, dependency tracking |
| `state/tracked.py` | Tracked collections |
| `state/mutable.py` | Two-way binding |
