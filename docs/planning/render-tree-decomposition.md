# RenderTree Decomposition Plan

## Goal

Replace monolithic `RenderTree` with composable, single-responsibility classes:
- **RenderSession** - session-scoped container (contextvar target)
- **ActiveRender** - render-scoped container
- Fine-grained classes for each responsibility

## New Class Structure

### Fine-Grained Classes

#### NodeStore (`node_store.py`)
```python
class NodeStore:
    _nodes: dict[str, ElementNode]

    def get(self, node_id: str) -> ElementNode | None
    def store(self, node: ElementNode) -> None
    def remove(self, node_id: str) -> None
    def get_children(self, node: ElementNode) -> list[ElementNode]
    def clone(self) -> NodeStore  # For old_nodes snapshot
    def clear(self) -> None
    def __len__(self) -> int
    def __contains__(self, node_id: str) -> bool
```

#### StateStore (`state_store.py`)
```python
class StateStore:
    _state: dict[str, ElementState]

    def get(self, node_id: str) -> ElementState | None
    def get_or_create(self, node_id: str) -> ElementState
    def remove(self, node_id: str) -> None
    def __contains__(self, node_id: str) -> bool
```

#### DirtyTracker (`dirty_tracker.py`)
```python
class DirtyTracker:
    _dirty_ids: set[str]

    def mark(self, node_id: str) -> None
    def clear(self, node_id: str) -> None
    def discard(self, node_id: str) -> None
    def has_dirty(self) -> bool
    def pop_all(self) -> list[str]
    def __contains__(self, node_id: str) -> bool
```

#### FrameStack (`frame_stack.py`)
```python
class FrameStack:
    _frames: list[Frame]

    def push(self, parent_id: str) -> Frame
    def pop(self) -> list[str]
    def current(self) -> Frame | None
    def add_child(self, node_id: str) -> None
    def has_active(self) -> bool
    def next_child_id(self, component: IComponent, key: str | None) -> str
    def root_id(self, component: IComponent) -> str  # For no-frame case
```

#### PatchCollector (`patch_collector.py`)
```python
class PatchCollector:
    _patches: list[Patch]

    def emit(self, patch: Patch) -> None
    def get_all(self) -> list[Patch]
    def clear(self) -> None
```

#### LifecycleTracker (`lifecycle_tracker.py`)
```python
class LifecycleTracker:
    _pending_mounts: list[str]
    _pending_unmounts: list[str]

    def track_mount(self, node_id: str) -> None
    def track_unmount(self, node_id: str) -> None
    def pop_mounts(self) -> list[str]
    def pop_unmounts(self) -> list[str]
```

### Container Classes

#### RenderSession (`session.py`)
Session-scoped state. ContextVar points here.

```python
class RenderSession:
    # Root component info
    root_component: IComponent
    root_node_id: str | None

    # Fine-grained stores
    nodes: NodeStore
    state: StateStore
    dirty: DirtyTracker

    # Render-scoped (None when not rendering)
    active: ActiveRender | None

    # Thread safety
    lock: RLock
```

#### ActiveRender (`active_render.py`)
Render-scoped state. Created at start of render(), discarded at end.

```python
class ActiveRender:
    # Fine-grained components
    frames: FrameStack
    patches: PatchCollector
    lifecycle: LifecycleTracker
    old_nodes: NodeStore  # Snapshot via clone()

    # Execution context
    current_node_id: str | None
    last_property_access: tuple[Any, str, Any] | None
```

### ElementState Changes

Add callbacks storage:
```python
@dataclass
class ElementState:
    # Existing fields...
    callbacks: dict[str, Callable] = field(default_factory=dict)
```

Callback lookup function (free function or method):
```python
def get_callback(session: RenderSession, node_id: str, prop_name: str) -> Callable | None:
    state = session.state.get(node_id)
    if state is None:
        return None
    return state.callbacks.get(prop_name)
```

## Files to Modify/Create

### New Files
| File | Contents |
|------|----------|
| `src/trellis/core/node_store.py` | NodeStore class |
| `src/trellis/core/state_store.py` | StateStore class |
| `src/trellis/core/dirty_tracker.py` | DirtyTracker class |
| `src/trellis/core/frame_stack.py` | Frame + FrameStack classes |
| `src/trellis/core/patch_collector.py` | PatchCollector class |
| `src/trellis/core/lifecycle_tracker.py` | LifecycleTracker class |
| `src/trellis/core/session.py` | RenderSession class |
| `src/trellis/core/active_render.py` | ActiveRender class |

### Modified Files
| File | Changes |
|------|---------|
| `src/trellis/core/rendering.py` | Remove RenderTree, keep ElementNode/ElementState, add free functions for execution, update contextvar |
| `src/trellis/core/__init__.py` | Export RenderSession instead of RenderTree |
| `src/trellis/core/base_component.py` | Update to use RenderSession/ActiveRender |
| `src/trellis/core/state.py` | Update get_active_render_tree → get_active_session |
| `src/trellis/core/tracked.py` | Update context access |
| `src/trellis/core/mutable.py` | Update context access |
| `src/trellis/core/serialization.py` | Update callback registration |
| `src/trellis/core/reconcile.py` | Update type hints and context access |
| `src/trellis/core/message_handler.py` | Update RenderTree → RenderSession |
| `tests/test_rendering.py` | Update all tests |
| `tests/*.py` | Update RenderTree → RenderSession in ~155 test instantiations |

## Execution Functions (Free Functions in rendering.py)

### Public
```python
def render(session: RenderSession) -> list[Patch]
```

### Private (underscore prefix)
```python
def _eager_execute_node(session: RenderSession, node: ElementNode, parent_id: str | None, old_child_ids: list[str] | None) -> ElementNode
def _render_single_node(session: RenderSession, node_id: str) -> None
def _mount_node_tree(session: RenderSession, node_id: str) -> None
def _unmount_node_tree(session: RenderSession, node_id: str) -> None
def _call_mount_hooks(session: RenderSession, node_id: str) -> None
def _call_unmount_hooks(session: RenderSession, node_id: str) -> None
def _process_pending_hooks(session: RenderSession) -> None
def _emit_update_patch_if_changed(session: RenderSession, node_id: str) -> None
def _serialize_node_for_patch(session: RenderSession, node: ElementNode) -> dict
```

## ContextVar Changes

```python
# Before
_active_render_tree: ContextVar[RenderTree | None]
def get_active_render_tree() -> RenderTree | None
def set_active_render_tree(tree: RenderTree | None) -> None

# After
_active_session: ContextVar[RenderSession | None]
def get_active_session() -> RenderSession | None
def set_active_session(session: RenderSession | None) -> None
def is_render_active() -> bool  # Check session.active is not None
```

## Implementation Order

### Phase 1: Create Fine-Grained Classes (no behavior change) ✅ COMPLETE
1. ✅ Create `NodeStore` with tests
2. ✅ Create `StateStore` with tests
3. ✅ Create `DirtyTracker` with tests
4. ✅ Create `FrameStack` (move Frame class here) with tests
5. ✅ Create `PatchCollector` with tests
6. ✅ Create `LifecycleTracker` with tests

### Phase 2: Create Container Classes ✅ COMPLETE
1. ✅ Create `ActiveRender` holding references to render-scoped classes
2. ✅ Create `RenderSession` holding references to session-scoped classes
3. ✅ Add `callbacks` field to `ElementState`

### Phase 3: Migrate RenderTree Internals ✅ COMPLETE
1. ✅ Update `RenderTree.__init__` to create and use the new classes internally
2. ✅ Delegate methods to the appropriate class
3. ✅ All tests should still pass (RenderTree is a facade)

### Phase 4: Extract Execution Functions ✅ COMPLETE
1. ✅ Extract `render()` as free function taking session
2. ✅ Extract `_eager_execute_node()` and related functions
3. ✅ RenderTree becomes thin wrapper calling free functions

### Phase 5: Remove RenderTree
1. Update contextvar to use RenderSession
2. Update all callers of `get_active_render_tree()`
3. Update imports across codebase
4. Update tests to use RenderSession directly
5. Delete RenderTree class

### Phase 6: Cleanup
1. Update documentation
2. Remove any dead code
3. Final test pass

## Migration Strategy for Callers

### Pattern: get_active_render_tree() Access

Before:
```python
ctx = get_active_render_tree()
ctx.push_frame(parent_id)
ctx.store_node(node)
ctx._current_node_id
```

After:
```python
session = get_active_session()
session.active.frames.push(parent_id)
session.nodes.store(node)
session.active.current_node_id
```

### Pattern: RenderTree Instantiation

Before:
```python
tree = RenderTree(root_component)
patches = tree.render()
```

After:
```python
session = RenderSession(root_component)
patches = render(session)
```

## Risk Mitigation

1. **Incremental migration**: Each phase leaves tests passing
2. **Facade pattern**: RenderTree can delegate to new classes during transition (temporary only)
3. **Type hints**: Strong typing catches mismatches early
4. **Test coverage**: 607 existing tests validate behavior preservation

## No Shims Policy

**Critical**: This is a breaking change. We will NOT leave behind:
- Backwards compatibility aliases (e.g., `RenderTree = RenderSession`)
- Wrapper functions that just delegate to new API
- Deprecated but still-functional old patterns
- `# TODO: migrate` comments

**Each phase must fully complete before moving on:**
- Phase 3 (facade): Temporary only - RenderTree delegates to new classes
- Phase 5 (remove): RenderTree is deleted entirely, not aliased
- Tests are migrated to use new API directly, not shimmed to pass

## Final Cleanup Checklist

Before considering this complete, verify:

### No Legacy References
- [ ] `RenderTree` class deleted (not aliased)
- [ ] `get_active_render_tree()` deleted (not aliased to `get_active_session()`)
- [ ] `set_active_render_tree()` deleted
- [ ] No `tree` variables - use `session`
- [ ] No methods like `tree.render()` - use `render(session)`

### All Tests Migrated
- [ ] Tests import `RenderSession`, not `RenderTree`
- [ ] Tests call `render(session)`, not `session.render()`
- [ ] Test helpers updated (no compatibility wrappers)

### Exports Updated
- [ ] `__init__.py` exports `RenderSession`, `render`, `get_active_session`
- [ ] `__init__.py` does NOT export `RenderTree` or old functions
- [ ] No `__all__` entries for removed items

### Documentation Updated
- [ ] `docs/reference/trellis-core.md` updated
- [ ] Docstrings reference new classes/functions
- [ ] No references to "RenderTree" in docs

### Code Quality
- [ ] No `# type: ignore` added for migration
- [ ] No `cast()` added for migration
- [ ] Grep for "RenderTree" returns zero results
- [ ] Grep for "render_tree" returns zero results
- [ ] Grep for "get_active_render_tree" returns zero results
