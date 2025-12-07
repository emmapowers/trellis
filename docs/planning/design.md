# Trellis Design

Reactive UI framework for Python with fine-grained state tracking.

## Goals

- **Ergonomic API**: Great developer experience for Python developers, especially non-frontend specialists
- **Scalability**: Support large, data-intensive applications with many interactive controls
- **Error Prevention**: Consistent state management to help developers avoid common mistakes

## Use Cases

- **Complex UIs**: Dense interfaces with many controls that update frequently
- **Real-Time Data Visualization**: Stream and display waveforms, images, etc.
- **Connection Handling**: Detect disconnects and re-sync UI state on reconnection

## Architecture

### Element Tree

- **Element**: Node in the component tree
  - `component`: Reference to the component that created it
  - `properties`: Dict of props passed to the component
  - `children`: List of child elements
  - `parent`: Parent element reference
  - `depth`: Nesting level in tree
  - `key`: Optional stable identifier for reconciliation
  - `dirty`: Whether element needs re-rendering

- **RenderContext**: Manages the element tree
  - Tracks dirty elements for efficient updates
  - Handles re-rendering with automatic locking
  - Maintains element stack during rendering
  - Sorts dirty elements by depth (shallowest first) for efficient updates

### Component Types

- **Functional components** (`@component`): Simple render functions
  ```python
  @component
  def ErrorText(message: str) -> Elements:
      return w.Label(text=message, textColor='red')
  ```

- **Block components** (`@blockComponent`): Use `with` syntax to collect children
  ```python
  with w.Column() as out:
      w.Label("First")
      w.Label("Second")
  ```

- **React components** (`@reactComponent`): Inline TSX or file-based
  ```python
  @reactComponent()
  def Column(children: Elements) -> Elements:
      return t"""
      function Column(props) {
          return <div style={{ display: 'flex', flexDirection: 'column' }}>
              {props.children}
          </div>;
      }
      """
  ```

## State Management

### Stateful Base Class

- Subclass `Stateful` with `@dataclass` decorator
- All fields become reactive properties with automatic dependency tracking
- When a property is read during render, the element is registered as dependent
- When a property changes, all dependent elements are marked dirty

```python
@dataclass
class FormState(Stateful):
    text: str
    enabled: bool
    submitting: bool = False
    error: str = ""
```

### Reactivity Patterns

- **Property-granular tracking**: Only re-render when accessed properties change
- **Automatic dependency tracking**: Framework notes which state is used in render
- **Nested state**: Tracking applies to nested `Stateful` objects as well

### Observable Collections

`Stateful` auto-wraps `list`, `dict`, and `set` fields in observable wrappers that track mutations:

```python
@dataclass
class TodosState(Stateful):
    todos: list[Todo] = field(default_factory=list)  # Auto-wrapped

# Mutations trigger re-renders automatically
state.todos.append(new_todo)
state.todos.remove(old_todo)
state.todos[0] = updated_todo
```

**Wrapped types:**
- `list` → `ObservableList` (tracks `append`, `insert`, `remove`, `pop`, `__setitem__`, `__delitem__`, `clear`, `extend`, etc.)
- `dict` → `ObservableDict` (tracks `__setitem__`, `__delitem__`, `pop`, `clear`, `update`, etc.)
- `set` → `ObservableSet` (tracks `add`, `remove`, `discard`, `pop`, `clear`, `update`, etc.)

**Auto-wrapping in StatefulProperty setter:**
```python
WRAPPABLE_TYPES = {
    list: ObservableList,
    dict: ObservableDict,
    set: ObservableSet,
}

def __set__(self, instance, value):
    wrapper_cls = WRAPPABLE_TYPES.get(type(value))
    if wrapper_cls and not isinstance(value, wrapper_cls):
        value = wrapper_cls(value, owner=instance, name=self.name)
    # ... store and notify
```

**Nested Stateful objects:** If list/dict contains `Stateful` items, their property changes also trigger re-renders automatically - no wrapper needed for that.

### Bidirectional Binding

- `Mutable[T]` type for two-way data binding
- `mutable(state.field)` to create a mutable reference
- Widgets can read and write through the mutable

```python
TextWithLabel(
    label="Name",
    text=mutable(state.text)  # Child can update state.text
)
```

## Component Patterns

### Stateless Components

- Receive all data via props
- No internal state

```python
@component
def TextWithLabel(label: str, text: Mutable[str]) -> Elements:
    with w.Row() as out:
        w.Label(label=label, width=150)
        w.TextInput(text=text)
    return out
```

### Stateful Components

- Create local state in render function
- State persists across re-renders

```python
@component
def Notification(message: str, duration: float) -> Elements:
    state = NotificationState(shownTime=time.time())
    if (time.time() - state.shownTime) < duration:
        return ErrorText(message=message)
    return w.Empty()
```

### State Location Options

- **Local**: Created inside component
- **Context**: Provided via `with` block, accessed with `from_context()`
- **Global**: Module-level state object

```python
routerState = nav.RouterState()  # Global

@component
def top() -> Elements:
    with nav.Router(state=routerState):
        nav.Route(path="/", target=Form())
```

### Context Pattern

- `Stateful` objects can be provided as context using `with` syntax
- Children access context with `MyState.from_context()`
- Avoids prop drilling through component hierarchy

```python
@component
def top() -> Elements:
    state = AppState()

    # Provide state as context
    with state:
        TodoApp()  # No props needed!

@component
def TodoApp() -> Elements:
    # Access state from context
    state = AppState.from_context()

    with w.Column():
        TodoInput()   # Also accesses AppState.from_context()
        TodoList()
```

### Async Callbacks

- Callbacks can be async
- State updates trigger re-renders
- Exceptions are logged by default (configurable hook)

```python
async def submit(self):
    try:
        self.error = ""
        result = await doSomethingNetworky(self.text)
        routerState.navigate("/done")
    except RuntimeError as e:
        self.error = e.msg
```

### Conditional Rendering

- Return `w.Empty()` for nothing
- Use standard Python conditionals

```python
if state.error:
    Notification(message=state.error)
```

## Navigation

- `RouterState`: Holds current route
- `Router`: Container for routes
- `Route`: Maps path to component
- `navigate(path)`: Programmatic navigation

```python
routerState = nav.RouterState()

with nav.Router(state=routerState):
    nav.Route(path="/", target=Form(state=formState))
    with nav.Route(path="/done"):
        w.Label("Done!")
        w.Button(label="Back", onClick=lambda: routerState.navigate("/"))
```

## Widgets

### Layout

- `Column`: Vertical stack
- `Row`: Horizontal stack
- `ButtonBar`: Horizontal button container

### Input

- `TextInput`: Text entry, `text` prop is `Mutable[str]`
- `Button`: Clickable button with `label`, `onClick`, `disabled`

### Display

- `Label`: Text display with `text`, `textColor`, `width`
- `Empty`: Renders nothing (for conditional rendering)

### Properties

- `width`: Pixels (number)
- `hAlign`, `vAlign`: Alignment (`w.Align.Center`, etc.)
- `textColor`: Color string
- `disabled`: Boolean
- `placeholderText`: Hint text

## React Integration

### Inline Components

```python
@reactComponent()
def Column(children: Elements) -> Elements:
    # language=html
    return t"""
    function Column(props: ColumnProps): React.ReactElement {
        return (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
                {props.children}
            </div>
        );
    }
    """
```

### File-Based Components

```python
class ColumnFromFiles(ReactComponent):
    _sources = [
        "components/Column.tsx",
        "components/Column.css",
    ]
    _esModules = [
        "https://esm.sh/superAwesomeLib@1.2.3",
        "./vendored/mylib.js",
    ]
```

## Thread Safety

- State updates can happen from any thread
- `RenderContext` uses `RLock` for thread-safe operations
- `@with_lock` decorator for protected methods
- Developers don't need to manage concurrency manually

## Developer Experience

### Two Modes

- **Development**: Hot reloading, source maps, runtime checks
- **Release**: Bundled and optimized for deployment

### App Lifecycle

```python
async def main():
    app = App()
    await app.serve(top)

if __name__ == "__main__":
    asyncio.run(main())
```

### Rendering Cycle

1. Initial render creates the Element tree
2. State changes mark dependent elements dirty
3. Periodically (~20ms), dirty elements are re-rendered shallowest-first
4. Tree is diffed, changes sent to client
