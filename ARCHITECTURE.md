# Trellis Architecture Reference

**What**: Reactive UI framework for Python. Python owns state/structure, React renders. Write Python, get web/desktop apps.

**Use cases**: Instrument control, internal tools, admin panels, line-of-business apps.

---

## Core Files Map

### Python Core (`src/trellis/core/`)

| File | Key Classes | Responsibility |
|------|-------------|----------------|
| `rendering.py` | `ElementNode`, `ElementState`, `RenderTree` | Tree structure, render lifecycle coordinator |
| `state.py` | `Stateful` | Reactive state with property-level dependency tracking |
| `reconcile.py` | `reconcile_node()` | React-like diffing: preserve IDs, match components, cascade updates |
| `serialization.py` | `serialize_element_node()` | Tree → JSON, callbacks → IDs, Mutable wrapping |
| `message_handler.py` | `MessageHandler` | Render/event loop, transport-agnostic protocol handler |
| `base_component.py` | `Component` | Base for composition components |
| `functional_component.py` | `@component` | Decorator for composition components, frame-based child collection |
| `react_component.py` | `ReactComponentBase` | Base for widgets (Button, TextInput, etc.) |

### Platforms (`src/trellis/platforms/`)

| Platform | Transport | Location | Files |
|----------|-----------|----------|-------|
| **server** | WebSocket | Remote server | `server_app.py`, `server_message_handler.py` |
| **desktop** | PyTauri IPC | Local process | `desktop_app.py`, `desktop_message_handler.py` |
| **browser** | postMessage | Pyodide/WASM | `browser_app.py`, `browser_message_handler.py` |

### Frontend (`src/trellis/platforms/common/client/src/`)

| File | Responsibility |
|------|----------------|
| `TreeRenderer.tsx` | Render serialized tree to React |
| `core/renderTree.tsx` | `renderNode()`: ElementKind → React elements |
| `core/componentRegistry.tsx` | Widget name → React component lookup |
| `core/Mutable.tsx` | Two-way binding wrapper |

---

## Key Data Structures

```python
# Immutable tree node
@dataclass(frozen=True)
class ElementNode:
    component: Component
    props: dict
    key: Any
    children: list[ElementNode]
    id: str  # e.g., "e5"

# Mutable runtime state (keyed by node.id)
@dataclass
class ElementState:
    dirty: bool
    mounted: bool
    local_state: list[Stateful]  # Component-local state instances
    context: dict[type, Stateful]  # Context providers
    parent_id: str | None

# Central coordinator
class RenderTree:
    root: ElementNode
    _element_state: dict[str, ElementState]  # node.id → state
    _dirty_ids: set[str]
    _callback_registry: dict[str, Callable]  # "e5:on_click" → function
```

---

## Data Flow Diagrams

### Initial Render
```
Component call → ElementNode descriptor
    ↓
reconcile_node() → assign ID, create ElementState
    ↓
execute_node() → run component.render()
    ↓
Create child descriptors → recursive reconcile/execute
    ↓
serialize_element_node() → JSON + callback IDs
    ↓
RenderMessage → msgpack → transport
    ↓
renderNode() → React tree
    ↓
React → DOM
```

### User Interaction → Update
```
DOM event → onClick handler
    ↓
onEvent("e5:on_click", args) → EventMessage
    ↓
Server: lookup callback in registry
    ↓
Execute: state.count += 1
    ↓
Stateful.__setattr__ → mark dependent nodes dirty
    ↓
tree.render() → re-render dirty nodes only
    ↓
reconcile_node_children() → preserve IDs where match
    ↓
serialize → RenderMessage
    ↓
React reconciles virtual DOM → update DOM
```

### Fine-Grained Reactivity
```
Component execution:
  state.count  →  register dependency: node_id → "count" property

State change:
  state.count = 5  →  mark all nodes reading "count" dirty
  state.name unchanged  →  nodes reading only "name" NOT dirty
```

---

## Message Protocol (All Platforms)

```typescript
HelloMessage:         { client_id }
HelloResponseMessage: { session_id, server_version }
RenderMessage:        { tree: SerializedNode }
EventMessage:         { callback_id: str, args: list }
ErrorMessage:         { error: str, context: dict }
```

**Transport**: msgpack-encoded, same types everywhere. Only transport layer differs per platform.

---

## Key Patterns

### 1. Immutable Tree + Mutable State
- `ElementNode`: frozen, regenerated each render
- `ElementState`: mutable, keyed by ID, persists across renders

### 2. Component-Local State (Hook-Like)
```python
@component
def Counter():
    state = CounterState()  # Cached at (class, call_index) in ElementState.local_state
    # Same instance on re-render (like React useState)
```

### 3. Frame-Based Child Collection
```python
with Column():    # Push Frame to stack
    Button("A")   # Add to current Frame
    Button("B")   # Add to current Frame
# Pop Frame, store on Column node
```

### 4. Deterministic Callback IDs
- Format: `"{node_id}:{prop_name}"` (e.g., `"e5:on_click"`)
- Auto-registered in `tree._callback_registry`
- Auto-overwritten on re-render, no manual cleanup

### 5. Property-Level Dependency Tracking
```python
# In Stateful.__getattribute__
if render_tree := get_current_render_tree():
    current_node_id = render_tree.get_executing_node_id()
    state_info.node_ids.add(current_node_id)

# In Stateful.__setattr__
for node_id in state_info.node_ids:
    tree.mark_dirty_id(node_id)
```

### 6. Context API (Provider/Consumer)
```python
with AppState(user="alice"):  # Sets context in ElementState
    Child()

state = AppState.from_context()  # Walks parent_id chain
```

### 7. Reconciliation Phases (Preserves State)
1. **Head scan**: Match sequential prefix
2. **Tail scan**: Match sequential suffix
3. **Key-based**: `key_to_old_node[child.key]`
4. **Type-based**: `type_to_old_node[child.component]`
5. **Create new**: No match found

### 8. Callback Serialization
**Python**:
```python
tree.register_callback(on_click, node_id="e5", prop_name="on_click")
# Returns: "e5:on_click"
# Serializes: {"on_click": {"__callback__": "e5:on_click"}}
```

**TypeScript**:
```typescript
if (isCallbackRef(value)) {
  result[key] = (...args) => onEvent(value.__callback__, serialize(args));
}
```

### 9. Two-Way Binding (Mutable)
**Python**:
```python
TextInput(value=mutable(state.name))
# Serializes: {"__mutable__": "e7:value:mutable", "value": "alice"}
```

**TypeScript**:
```typescript
class Mutable<T> {
  get value(): T { return this._ref.value }
  setValue(v: T) { this._onEvent(this._ref.__mutable__, [v]) }
}
```

---

## Component Types

| Type | Created By | Rendered As | Use Case |
|------|------------|-------------|----------|
| **CompositionComponent** | `@component` | Generic wrapper | Organize/compose other components |
| **ReactComponentBase** | Subclass | Actual React component | Widgets (Button, TextInput, etc.) |
| **HTMLElement** | `h.Div()` etc. | JSX element | Native HTML tags |

---

## Platform Differences

**Shared**: Component model, render algorithm, message protocol, React frontend

**Different**:
| Aspect | Server | Desktop | Browser |
|--------|--------|---------|---------|
| Python runs | Remote server | Local process | WebAssembly in Worker |
| Transport | WebSocket | PyTauri IPC | postMessage |
| Sessions | Multi (per connection) | Single | Single |
| Event loop | asyncio main thread | Blocking portal bridge | Pyodide asyncio |

---

## Entry Point Flow

```python
app = Trellis(top=MyApp)  # Auto-detects platform or explicit
await app.serve()
    ↓
Platform.run():
    - Bundle client (if needed)
    - Start transport (WebSocket/IPC/postMessage)
    - Wait for HelloMessage
    - Create RenderTree(root_component)
    - Initial render → RenderMessage
    - Event loop: EventMessage → callback → re-render
```

---

## Quick File Lookup

**Need to understand...**
- How components work? → `functional_component.py`, `base_component.py`
- How state tracking works? → `state.py` (see `StatePropertyInfo`)
- How rendering works? → `rendering.py:RenderTree.render()`
- How diffing works? → `reconcile.py:reconcile_node()`
- How serialization works? → `serialization.py:serialize_element_node()`
- How events work? → `message_handler.py:handle_event_message()`
- How callbacks work? → `rendering.py:RenderTree.register_callback()`
- How server platform works? → `platforms/server/server_app.py`
- How desktop platform works? → `platforms/desktop/desktop_app.py`
- How browser platform works? → `platforms/browser/browser_app.py`
- How client renders? → `platforms/common/client/src/TreeRenderer.tsx`
- How React components map? → `platforms/common/client/src/core/componentRegistry.tsx`

---

## Mental Model

1. **Python defines UI tree** via component calls → `ElementNode` descriptors
2. **RenderTree reconciles** old vs new → preserve IDs, create/update `ElementState`
3. **Execution creates children** → recursive build
4. **Serialization** → JSON with callback IDs
5. **Transport** → msgpack over WebSocket/IPC/postMessage
6. **React renders** → DOM
7. **User interacts** → event sent to Python
8. **Callback executes** → mutate `Stateful`
9. **Setattr marks dirty** → fine-grained tracking
10. **Re-render dirty nodes** → back to step 2

**Result**: Write Python, get reactive web/desktop apps. Framework handles dependency tracking, diffing, serialization, and platform abstraction.
