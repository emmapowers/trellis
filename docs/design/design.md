# Trellis Design

This document describes the current and planned design for Trellis. It serves both as documentation of what exists and as a place to plan future work.

## Table of Contents

- [Overview](#overview)
- [Use Cases](#use-cases)
- [Goals](#goals)
- [Design Philosophy](#design-philosophy)
- [Architecture](#architecture)
- [Component Patterns](#component-patterns)
- [Widgets](#widgets)
- [Navigation](#navigation)
- [React Integration](#react-integration)
- [Architectural Decisions](#architectural-decisions)

## Overview

Trellis is a reactive UI framework for Python with fine-grained state tracking. `App()` starts a web server hosting static files, a WebSocket endpoint, and a `/` route. When `/` is hit, a render occurs and a page is sent with React and bundled components. The page connects via WebSocket for updates. User actions or server-side I/O trigger re-renders, sending diffs over WebSocket to update the UI.

## Use Cases

### What It's For

- **Complex UIs**: Dense interfaces with many controls that update frequently
- **Real-Time Data Visualization**: Stream and display waveforms, images, etc.
- **Connection Handling**: Detect disconnects and re-sync UI state on reconnection

### What It's **Not** For

- **Static websites**: No reactivity needed; use a static site generator
- **Simple forms**: Standard HTML forms with page reloads are simpler
- **Mobile apps**: Browser-based only; not a native mobile framework
- **Public-facing web apps**: Optimized for internal tools, not SEO or first-load performance

## Goals

- **Ergonomic API**: Great developer experience for Python developers, especially non-frontend specialists
- **Scalability**: Support large, data-intensive applications with many interactive controls
- **Error Prevention**: Consistent state management to help developers avoid common mistakes

## Design Philosophy

- **Fine-grained reactivity**: Property-level dependency tracking, not component-level. Only re-render what actually changed.
- **Implicit child collection**: Components don't return children—they're auto-collected via the element stack.
- **Thread safety by default**: State changes can happen from any thread; the framework handles locking.
- **Python-first API**: Leverage `with` blocks, dataclasses, and type hints for a natural Python feel.

## Architecture

### Tech Stack

**Python (3.14)**
- FastAPI — Async web framework with WebSocket support
- msgspec — Fast serialization/validation (Pydantic alternative)
- watchfiles — Hot reload during development
- pytest — Testing

**JavaScript/TypeScript**
- esbuild — Fast bundling (pip-installable)
- React — UI framework
- Blueprint — Desktop-first component library (Palantir)
- uPlot — High-performance time-series charts
- Recharts — General-purpose charts
- Vitest — Testing
- Playwright — E2E testing

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

### Component Model

- **Functional components** (`@component`): Simple render functions
  ```python
  @component
  def ErrorText(message: str) -> Elements:
      return w.Label(text=message, textColor='red')
  ```

- **Container components**: Use `with` syntax to collect children
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

### State Management

#### Stateful Base Class

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

#### Reactivity Patterns

- **Property-granular tracking**: Only re-render when accessed properties change
- **Automatic dependency tracking**: Framework notes which state is used in render
- **Nested state**: Tracking applies to nested `Stateful` objects as well

#### Observable Collections

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

#### Bidirectional Binding

- `Mutable[T]` type for two-way data binding
- `mutable(state.field)` to create a mutable reference
- Widgets can read and write through the mutable

```python
TextWithLabel(
    label="Name",
    text=mutable(state.text)  # Child can update state.text
)
```

### Reconciliation

- Shallowest-first re-rendering for efficient updates
- Key-based matching for list items
- Tree diffing to minimize client updates

## Component Patterns

### Stateless Components

Receive all data via props, no internal state.

```python
@component
def TextWithLabel(label: str, text: Mutable[str]) -> Elements:
    with w.Row() as out:
        w.Label(label=label, width=150)
        w.TextInput(text=text)
    return out
```

### Stateful Components

Create local state in render function; state persists across re-renders.

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

## Architectural Decisions

### Implicit child collection over return values

Components don't return their children—instead, children are automatically collected via an element stack during rendering. This enables natural `with` block syntax and removes boilerplate, at the cost of some "magic" behavior.

### Property-level reactivity

Dependencies are tracked at the property level, not the component level. Reading `state.name` only creates a dependency on `name`, not on the entire state object. This minimizes unnecessary re-renders for data-intensive UIs.

### Thread safety by default

State updates can happen from any thread (e.g., async callbacks, background tasks). The framework uses `RLock` internally so developers don't need to manage concurrency manually.

### msgspec over Pydantic

msgspec provides faster serialization/validation with lower overhead, which matters for high-frequency state updates over WebSocket.

### Python 3.14

Using the latest Python version for performance improvements and language features. Type hints are first-class throughout the codebase.
