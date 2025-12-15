---
sidebar_position: 2
title: UI and Rendering
---

# UI and Rendering Design Document

**Related:** [Design Overview](./overview), [State Management](./state), [Web Server](./web-server)

---

## Table of Contents

1. [Purpose](#purpose)
2. [Overview](#overview)
3. [Component Model](#component-model)
   - [What is a Component?](#what-is-a-component)
   - [CompositionComponent](#compositioncomponent)
   - [ReactComponentBase](#reactcomponentbase)
   - [HTMLElement](#htmlelement)
4. [ReactComponent Developer Experience](#reactcomponent-developer-experience)
   - [Two Approaches](#two-approaches)
   - [Using @react_component Decorator](#using-react_component-decorator)
   - [Using @react_component_from_files](#using-react_component_from_files)
5. [Element Tree Architecture](#element-tree-architecture)
   - [ElementNode](#elementnode)
   - [ElementState](#elementstate)
   - [RenderTree](#rendertree)
6. [Rendering Pipeline](#rendering-pipeline)
   - [How Components Become Nodes](#how-components-become-nodes)
   - [Rendering and Reconciliation](#rendering-and-reconciliation)
   - [Render Triggers](#render-triggers)
7. [Reconciliation Algorithm](#reconciliation-algorithm)
   - [Tree Matching Strategy](#tree-matching-strategy)
   - [Head/Tail Scan](#headtail-scan)
   - [Key-Based Matching](#key-based-matching)
   - [ID Preservation](#id-preservation)
   - [Mount/Unmount Lifecycle](#mountunmount-lifecycle)
8. [Diff Algorithm](#diff-algorithm)
   - [Computing Minimal Updates](#computing-minimal-updates)
   - [Patch Generation](#patch-generation)
   - [Delta vs Full Tree](#delta-vs-full-tree)
9. [React Client Integration](#react-client-integration)
   - [Component Type Mapping](#component-type-mapping)
   - [CompositionComponent on Client](#compositioncomponent-on-client)
   - [ReactComponentBase Rendering](#reactcomponentbase-rendering)
   - [HTMLElement Rendering](#htmlelement-rendering)
10. [Callbacks and Events](#callbacks-and-events)
    - [Callback Registration](#callback-registration)
    - [Event Serialization](#event-serialization)
    - [Server Execution](#server-execution)
    - [Async Callback Support](#async-callback-support)
11. [Serialization and Communication](#serialization-and-communication)
    - [Tree Serialization](#tree-serialization)
    - [Callback ID Injection](#callback-id-injection)
    - [Message Format](#message-format)
    - [WebSocket Protocol](#websocket-protocol)
12. [Preventing User Errors](#preventing-user-errors)
    - [API Design Principles](#api-design-principles)
    - [Type Checking](#type-checking)
    - [Runtime Validation](#runtime-validation)
    - [Layered Defense Examples](#layered-defense-examples)
    - [Developer Experience](#developer-experience)

---

## Purpose

This document describes the UI and rendering system in Trellis—how components are defined, how the element tree is structured, how rendering works, and how the server communicates with the React client.

**Scope:** This document covers the component model, rendering pipeline, reconciliation, and React integration. State management, routing, and server architecture are covered in separate documents.

**Related Documents:**
- [Design Overview](./overview) (overview and philosophy)
- [State Management](./state) (reactive state, dependency tracking)
- [Web Server](./web-server) (WebSocket communication, sessions)

---

## Overview

Trellis applications run as a Python server that owns application state and renders a component tree. The React client displays the UI and sends user interactions back to the server.

**Key concepts:**
- **Components** are factories for creating different types of UI elements (HTML elements, React components, etc.)
- Component instances create **ElementNodes** that form a tree describing the UI
- The **RenderTree** reconciles changes and tracks which nodes are dirty
- Only changed components re-render; unchanged subtrees are skipped
- A **diff algorithm** generates minimal patches sent to the client
- User interactions trigger **callbacks** on the server, which modify state and trigger re-renders

**Rendering flow:**

```
User Interaction (click button)
        ↓
Client sends callback ID to server
        ↓
Server executes callback, modifies state
        ↓
State marks dependent elements dirty
        ↓
RenderTree reconciles and re-renders dirty elements
        ↓
Diff algorithm generates patch
        ↓
Patch sent to client via WebSocket
        ↓
React updates DOM
```

The document covers each of these concepts in detail: component types, tree architecture, rendering pipeline, reconciliation, diffing, and client integration.

---

## Component Model

### What is a Component?

A component is a factory that produces nodes in the UI tree. When called, a component creates an `ElementNode` describing what should be rendered at that position in the tree.

There are three types of components in Trellis:

1. **CompositionComponent** (user-defined with `@component`) — For organizing and composing other components
2. **ReactComponentBase** (base class for React components) — Low-level primitive for React component integration
3. **HTMLElement** (native HTML tags) — Standard HTML elements like `div`, `button`, `span`

**Key characteristics:**
- All components are class-based under the hood
- All components can be called via `__call__()`
- Decorators like `@component` and `@react_component` are convenience wrappers that create component classes from your definitions
- HTMLElement and ReactComponentBase can be leaf nodes (no children)
- CompositionComponents cannot be leaf nodes—they exist to compose other components
- While every component produces at least one React/JSX element in the client-side tree, the relationship varies by type

### CompositionComponent

CompositionComponents are user-defined components created with the `@component` decorator. They're used for organizing application structure, encapsulating logic, and composing other components together.

**Purpose:**
- Group related UI and behavior
- Encapsulate state and logic
- Create reusable abstractions
- Compose smaller components into larger structures

**Characteristics:**
- No direct React representation—wrapped in a generic client-side component
- Contain children (empty components are technically allowed but unusual)
- Can hold state via `Stateful` objects
- Render when props change or state marks them dirty
- Children added through execution order

**Using @component:**

Components use a declarative API where you describe what the UI should look like. Child components are added through execution order and context blocks, not by returning values.

```python
from trellis import component, html as h
from trellis.widgets import Button

@component
def Counter(count: int, on_increment: Callable[[], None]) -> None:
    with h.Div():
        h.Span(f"Count: {count}")
        Button(text="Increment", on_click=on_increment)
```

**Key design points:**
- **Execution-based composition:** Child position determined by execution order and which `with` block they're in
- **Type-safe:** Full type hints for IDE autocomplete and type checking
- **Context-manager syntax:** Hierarchical nesting uses `with` blocks
- **Return None:** Components don't return values; they add nodes via execution
- **Limited side effects:** Components cannot modify state during rendering—only callbacks can modify state, and this happens outside the rendering process. This prevents components from triggering re-renders just by rendering.

**Execution model:**

Component functions render when:
- Their props change
- State they depend on changes (marks them dirty)
- They're newly mounted

They're not pure functions—rendering has side effects (adding nodes to the collection frame), but these side effects are strictly limited to tree construction.

**Example:**
```python
@component
def UserCard(user: User, on_delete: Callable[[str], None]) -> None:
    with Card():
        with Row():
            Avatar(src=user.avatar_url)
            with Column():
                h.H3(user.name)
                h.P(user.email)
        Button(text="Delete", on_click=lambda: on_delete(user.id))
```

**Children and context blocks:**

When components are called inside a `with` block, they are collected as children and passed to the parent component. The parent component receives these as `ElementNode` objects and controls where they appear in the tree by calling them.

```python
@component
def MyApp():
    with Column():
        WidgetA()
        WidgetB()
        WidgetC()

@component
def Column(children: list[ElementNode]):
    with h.Div(style={"display": "flex", "flexDirection": "column"}):
        for child in children:
            child()  # Position child here in the tree
```

**Frame-based child collection:**

The RenderTree uses a "frame" mechanism to collect children during `with` blocks:

1. **Frame stack:** RenderTree maintains a stack of frames. Each frame collects ElementNodes created within its scope.

2. **Entering a block:** When `with Column():` runs, a new frame is pushed onto the stack before entering the `with` block.

3. **Child creation:** Components called inside the block (WidgetA, WidgetB, WidgetC) create `ElementNode` objects that are added to the current (topmost) frame.

4. **Exiting the block:** When the `with` block exits, the frame is popped. The collected children are passed to the parent component as the `children` prop.

5. **Positioning:** Inside `Column`, calling `child()` renders that node and positions the resulting element at the current location in the tree—in this case, inside the `h.Div`. Components called in a `with` block defer their final position in the tree; the parent decides where they appear by calling them. This enables flexible layout components that wrap and arrange their children.

**Direct calls vs context blocks:**

```python
# Direct call - positions immediately at current location
Button(text="Click")

# Inside with block - node collected, parent positions it later
with Card():
    Button(text="Click")  # Collected, positioned when Card calls it
```

**Type safety:**

Components without a `children` parameter cannot be used in `with` blocks. Both the type checker and runtime will raise an error:

```python
@component
def NoChildren():
    h.P("I don't accept children")

# Type error and runtime error
with NoChildren():  # Error: NoChildren doesn't accept children
    Button(text="Click")
```

### ReactComponentBase

ReactComponentBase is the low-level base class for all React component integration in Trellis. It provides the interface between the Trellis rendering system and React components on the client.

**Purpose:**
- Provide the primitive that the rendering system understands
- Define the contract between server-side Python and client-side React
- Enable 1:1 mapping between Python component calls and React component instances
- Support components with and without children

**Characteristics:**
- Base class in `trellis.core.rendering`
- No registry or bundling concerns (those are handled by subclasses in `trellis.react`)
- Each component has a `name` that maps to the React component on the client
- Props defined through `__call__` method signatures with full type hints
- Rendered client-side as the actual React component
- If a component accepts a `children` property, it can be used with `with` blocks (same as CompositionComponents)

**The @react_component_base decorator:**

For built-in widgets and low-level component integration, Trellis provides the `@react_component_base` decorator:

```python
from trellis.core.react_component import react_component_base

@react_component_base("Button")
def Button(
    text: str = "",
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
) -> ElementNode:
    """A button widget."""
    ...
```

This decorator:

1. Creates a `ReactComponentBase` subclass with the given element name ("Button")
2. Uses the function signature to define the component's props
3. Creates a singleton instance and wrapper function for calling the component
4. Supports `has_children=True` parameter for container components

```python
@react_component_base("Card", has_children=True)
def Card(
    title: str | None = None,
    elevated: bool = False,
) -> ElementNode:
    """A card container widget."""
    ...

# Can be used as a container:
with Card(title="Settings"):
    Button("Save")
```

**Higher-level decorators:**

For user-defined React components, developers use higher-level tools from `trellis.react`:

- `@react_component` decorator (creates component with inline TSX)
- `@react_component_from_files` decorator (for components with separate .tsx files)

Both of these build on `@react_component_base` and add registry/bundling capabilities.

**Client-side mapping:**

`ReactComponentBase` defines how Python components map to React:

```python
# Python side (conceptual - users don't write this directly)
class SomeReactComponent(ReactComponentBase):
    name: str = "Button"

    def __call__(self, text: str, on_click: Callable[[], None] | None = None) -> ElementNode:
        ...
```

Maps to:

```typescript
// TypeScript side
export function Button({ text, on_click }: ButtonProps): React.ReactElement {
  // ...
}
```

**Components with children:**

Components that accept a `children` property enable context-manager syntax:

```python
# Any ReactComponentBase subclass with children prop
with SomeContainer(elevated=True):
    h.H2("Title")
    h.P("Content")
```

### HTMLElement

HTMLElements represent native HTML tags with typed props and event handlers. They map directly to JSX elements on the client.

**Purpose:**

- Provide full HTML support
- Type-safe DOM events
- Styling via inline styles and CSS classes
- Building blocks for custom layouts

**Characteristics:**

- Defined in `trellis.html` module
- Extends `Component` directly (like `ReactComponentBase`)
- Uses `ElementKind.JSX_ELEMENT` to indicate native DOM rendering
- Props mirror HTML attributes
- Event handlers are typed (MouseEvent, KeyboardEvent, etc.)
- Can be leaf nodes OR containers
- Rendered directly as JSX on client

**The @html_element decorator:**

HTML elements are defined using the `@html_element` decorator, which follows the same pattern as `@react_component_base`:

```python
from trellis.html.base import html_element, Style
from trellis.core.rendering import ElementNode

@html_element("div", is_container=True)
def Div(
    *,
    className: str | None = None,
    style: Style | None = None,
    id: str | None = None,
    key: str | None = None,
    **props: Any,
) -> ElementNode:
    """A div container element."""
    ...
```

This decorator:

1. Creates an `HtmlElement` subclass with the given tag name ("div")
2. Sets `is_container=True` for elements that accept children via `with` blocks
3. Creates a singleton instance and wrapper function
4. Optionally accepts a `name` parameter to override the display name

**Example usage:**

```python
from trellis import html as h

# Leaf usage
h.H1("Title", style={"color": "#333"})

# Container usage
with h.Div(className="container", style={"padding": "20px"}):
    h.P("Content inside div")
    h.Span("Some text")
```

The HTML element API will be documented in detail in a separate [HTML Components](./html-components) design document.

---

## ReactComponent Developer Experience

This section covers how developers create React components for use in Trellis. While the rendering system works with `ReactComponentBase` (covered in Component Model), developers use higher-level tools from `trellis.react` that add registry and bundling capabilities.

### Two Approaches

There are two ways to define React components for Trellis:

1. **@react_component decorator** — Creates `FunctionalReactComponent` for inline TSX definitions
2. **@react_component_from_files decorator** — For components with separate .tsx files, CSS, and dependencies

Both approaches:
- Use decorators on Python functions (function signature = component props)
- Create subclasses of `ReactComponentBase`
- Register components in a global registry (for bundler discovery)
- Generate TypeScript type definitions
- Provide type-safe Python API

### Using @react_component Decorator

The `@react_component` decorator creates a `FunctionalReactComponent` — ideal for simple components where you want to write TSX inline.

**Basic usage:**

```python
from trellis.react import react_component

@react_component
def AlertBanner(
    message: str,
    severity: Literal["info", "warning", "error"] = "info",
    dismissible: bool = True,
    on_dismiss: Callable[[], None] | None = None,
):
    return """
    const colors = {
        info: "bg-blue-100 text-blue-800",
        warning: "bg-yellow-100 text-yellow-800",
        error: "bg-red-100 text-red-800"
    };

    return (
        <div className={`p-4 rounded ${colors[severity]}`}>
            <span>{message}</span>
            {dismissible && (
                <button onClick={on_dismiss} className="ml-4">
                    ×
                </button>
            )}
        </div>
    );
    """
```

**What the decorator does:**

1. **Registers the component** in the global registry for bundler discovery
2. **Extracts the function signature** using AST analysis
3. **Generates TypeScript props interface** from Python type hints using py-typescript-generator
4. **Generates the React function wrapper** with proper destructuring and defaults
5. **Returns a FunctionalReactComponent** (subclass of ReactComponentBase) with matching `__call__` signature

**Generated output:**

```typescript
// TypeScript props interface (generated from Python types)
interface AlertBannerProps {
    message: string;
    severity?: "info" | "warning" | "error";
    dismissible?: boolean;
    on_dismiss?: () => void;
}

// React function (signature generated, body from your Python string)
export function AlertBanner({
    message,
    severity = "info",
    dismissible = true,
    on_dismiss
}: AlertBannerProps): React.ReactElement {
    const colors = {
        info: "bg-blue-100 text-blue-800",
        warning: "bg-yellow-100 text-yellow-800",
        error: "bg-red-100 text-red-800"
    };

    return (
        <div className={`p-4 rounded ${colors[severity]}`}>
            <span>{message}</span>
            {dismissible && (
                <button onClick={on_dismiss} className="ml-4">
                    ×
                </button>
            )}
        </div>
    );
}
```

**Benefits:**
- Single source of truth for types
- Minimal boilerplate
- Fast iteration for simple components
- Automatic TypeScript generation

### Using @react_component_from_files

For more complex components with separate .tsx files, CSS, and dependencies, use the `@react_component_from_files` decorator.

**Basic pattern:**

```python
from trellis.react import react_component_from_files

@react_component_from_files(
    sources=[
        "components/Button.tsx",
        "components/Button.css",
    ],
    esm_modules=[
        "https://esm.sh/some-library@1.0.0",
    ],
)
def Button(
    text: str = "",
    on_click: Callable[[], None] | None = None,
    disabled: bool = False,
    variant: Literal["primary", "secondary", "outline", "ghost", "danger"] = "primary",
    size: Literal["sm", "md", "lg"] = "md",
) -> ElementNode:
    """Button component - implementation in Button.tsx"""
    ...
```

**Usage:**

```python
# Use just like any other component
Button(text="Click me", on_click=handler, variant="primary")

with Container():
    Button(text="Submit", disabled=False)
```

**File structure:**

```
components/
  Button.tsx    # React component implementation
  Button.css    # Component styles
```

**Button.tsx:**

```typescript
import "./Button.css";

export interface ButtonProps {
    text: string;
    on_click?: () => void;
    disabled?: boolean;
    variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
    size?: "sm" | "md" | "lg";
}

export function Button({
    text,
    on_click,
    disabled = false,
    variant = "primary",
    size = "md"
}: ButtonProps): React.ReactElement {
    return (
        <button
            className={`btn btn-${variant} btn-${size}`}
            onClick={on_click}
            disabled={disabled}
        >
            {text}
        </button>
    );
}
```

**Decorator parameters:**

- **sources** (list[str]): Paths to source files (.tsx, .css, etc.) relative to project root
- **esm_modules** (list[str], optional): External ESM dependencies (from esm.sh or local)

**Function body:**

The function body typically contains `...` (ellipsis) since the implementation lives in the .tsx file. However, you can add Python logic if needed:

```python
@react_component_from_files(sources=["components/Button.tsx"])
def Button(
    text: str,
    variant: str = "primary",
) -> ElementNode:
    """Button with runtime validation"""
    # Runtime validation beyond type checking
    if variant not in ["primary", "secondary", "danger"]:
        raise ValueError(f"Invalid variant: {variant}")
    ...
```

**Benefits:**

- Consistent decorator pattern (like `@react_component`)
- Function signature is directly inspectable
- Type checker validates call sites
- Full control over implementation
- Can use complex TypeScript features
- Import external libraries
- Include assets and resources
- Optional Python validation/logic in function body

**Registry and bundling:**

Both `@react_component` and `@react_component_from_files` register components in the global registry. The bundler:
1. Discovers all registered components
2. Generates TypeScript types (for @react_component inline TSX)
3. Collects source files (for @react_component_from_files)
4. Bundles everything into the client application

---

## Element Tree Architecture

The element tree is represented by two separate concerns: structure (ElementNode) and runtime state (ElementState). This separation keeps the tree immutable while allowing mutable state to live alongside it.

### ElementNode

ElementNode is a frozen dataclass representing a node in the component tree. It's immutable and contains only structural information.

```python
@dataclass(frozen=True)
class ElementNode:
    component: IComponent         # The component definition
    props: FrozenProps           # Immutable props dictionary
    key: str | None = None       # Optional key for reconciliation
    children: tuple[ElementNode, ...] = ()  # Child nodes
    id: str = ""                 # Unique ID assigned by RenderTree
```

**Characteristics:**
- **Immutable:** `frozen=True` prevents modification
- **Structural:** Describes what to render, not runtime state
- **Serializable:** Can be converted to JSON for transmission
- **ID-based:** Each node has a unique ID for state lookup

**Usage:**
```python
# Created when component is called
node = ElementNode(
    component=Button,
    props={"text": "Click", "on_click": handler},
    children=(),
    id="e42"
)
```

### ElementState

ElementState is a mutable dataclass holding per-element runtime state. It's stored separately from the tree, keyed by ElementNode.id.

```python
@dataclass
class ElementState:
    dirty: bool = False                           # Needs re-render?
    mounted: bool = False                         # Lifecycle state
    local_state: dict[tuple[type, int], Any]      # Stateful instances
    state_call_count: int = 0                     # Hook-style counter
    context: dict[type, Any]                      # Provided context
    parent_id: str | None = None                  # For context walking
```

**Fields Explained:**
- **dirty:** Set when state changes; triggers re-render
- **mounted:** Tracks component lifecycle (mounted → unmounted)
- **local_state:** Stores `Stateful` instances by (type, index) key
- **state_call_count:** Incremented each render for hook-style state storage
- **context:** State provided via `with state:` for descendant lookup
- **parent_id:** Link to parent for walking context tree

**State Storage Pattern:**
```python
# First render: state_call_count = 0
counter = CounterState()  # Stored at (CounterState, 0)
# state_call_count incremented to 1

# Second render:
counter = CounterState()  # Retrieved from (CounterState, 0)
# state_call_count reset to 0 for next render
```

### RenderTree

RenderTree (formerly RenderContext) orchestrates rendering, reconciliation, and lifecycle management.

```python
class RenderTree:
    root_node: ElementNode | None               # Current tree root
    _element_state: dict[str, ElementState]     # State by node ID
    _callback_registry: dict[str, Callable]     # Callback ID → function
    _dirty_ids: set[str]                        # Elements needing render
    _next_id: int = 0                           # ID counter
    _lock: RLock                                # Thread safety
```

**Key Responsibilities:**
1. **Tree Management:** Maintains root_node and element state
2. **ID Generation:** Assigns unique IDs via `next_id()`
3. **State Lookup:** Maps node.id → ElementState
4. **Dirty Tracking:** Marks and tracks elements needing re-render
5. **Callbacks:** Registers and executes event handlers
6. **Reconciliation:** Compares old and new trees, preserves IDs
7. **Serialization:** Converts tree to JSON for client

**ID Generation:**
```python
def next_element_id(self) -> str:
    self._node_counter += 1
    return f"e{self._node_counter}"
```

Simple counter provides unique, stable IDs (e.g., `e1`, `e2`, `e3`). IDs are assigned during reconciliation and preserved when nodes match.

**State Lifecycle:**
```python
# Mount: Create state
self._element_state[node.id] = ElementState(mounted=True, parent_id=parent_id)

# Update: State persists, node may change
# (ID preserved during reconciliation)

# Unmount: Delete state
del self._element_state[node.id]
```

---

## Rendering Pipeline

### How Components Become Nodes

When you call a component, it creates an ElementNode describing what should be rendered:

```python
@component
def Greeting(name: str) -> None:
    h.P(f"Hello, {name}!")

# Calling the component creates an ElementNode
node = Greeting(name="Alice")
# node is ElementNode(component=Greeting, props={"name": "Alice"})
# The function body hasn't run yet
```

**For React components:**
```python
button = Button(text="Click", on_click=handler)
# button is ElementNode(component=Button, props={...})
```

**Context-Manager Collection:**
```python
with Card():          # Card().__enter__() starts collection
    Button("A")       # Creates node, adds to collection
    Button("B")       # Creates node, adds to collection
                      # Card().__exit__() creates Card node with children

# Result: ElementNode(component=Card, children=(Button_A, Button_B))
```

The component function doesn't execute when called—it only creates a node descriptor. The actual rendering happens later in the RenderTree.

### Rendering and Reconciliation

`RenderTree.render()` performs the actual rendering work. It iterates through dirty nodes, renders them, and reconciles changes.

**Process:**
1. **Clear callbacks:** Previous render's callbacks are invalid
2. **Loop until no dirty nodes remain:**
   - Pick a dirty node
   - Render the node → component function executes, produces updated ElementNode
   - Reconcile old node vs new node
   - Reconciliation compares children and marks changed children dirty (but doesn't render them yet)
   - Update tree structure (swap old/new nodes, add/remove children)
3. **After rendering completes:** Call mount/unmount hooks (no guaranteed order)
4. **Serialize:** Convert tree to JSON for client

**Key insight:** Reconciliation happens **after each node renders**. When reconciling a node's children, changed children are marked dirty and will be rendered in a subsequent loop iteration. This continues until no nodes are dirty.

**Rendering Logic:**
```python
def should_render(old_node: ElementNode | None, new_node: ElementNode) -> bool:
    if old_node is None:
        return True  # New mount
    if old_node.component != new_node.component:
        return True  # Different component type
    if old_node.props != new_node.props:
        return True  # Props changed
    if new_node.id in self._dirty_ids:
        return True  # State marked it dirty
    return False  # Skip rendering, reuse old tree
```

**State Reading:**
During rendering, components read state:
```python
@component
def Counter() -> None:
    state = CounterState()  # Retrieves from element_state
    h.P(f"Count: {state.count}")  # __getattribute__ tracks dependency
```

The `state.count` read:
1. Triggers `__getattribute__` in Stateful base class
2. Registers this element as dependent on `count` property
3. Returns the value

When `state.count = new_value`:
1. `__setattr__` checks if value actually changed (optimization)
2. If changed, marks all dependent elements dirty
3. Next render cycle will re-render those elements

**State change optimization:**
Setting state to its current value doesn't trigger re-renders:
```python
state.count = 5
state.count = 5  # No re-render - value unchanged
```

### Render Triggers

Renders are triggered by:

**1. Initial Render:**
```python
app = Trellis(top=App)
await app.serve()  # Triggers initial render on connection
```

**2. State Changes:**
```python
state.count += 1  # Marks dependent elements dirty
# Next render cycle picks up dirty elements
```

**3. Callback Execution:**
```python
def on_click():
    state.value = "new"  # Marks elements dirty
# Framework automatically renders after callback completes
```

**4. Manual Render (rare):**
```python
render_tree.render()  # Force render
```

**Batching:**
Renders are batched at 30fps. Multiple state changes within a frame coalesce into a single render:

```python
state.a = 1  # Marks elements dirty
state.b = 2  # Marks more elements dirty
state.c = 3  # Marks more elements dirty
# Single render happens at next frame
```

If no elements are dirty, render is skipped entirely.

---

## Reconciliation Algorithm

Reconciliation is the process of matching new ElementNodes (produced by rendering) to existing ElementNodes in the tree, preserving IDs and state for unchanged components.

### Tree Matching Strategy

The reconciler walks both trees simultaneously, matching nodes using:
1. Component type equality
2. Key matching (if keys provided)
3. Position-based matching (fallback)

**High-Level Algorithm:**
```python
def reconcile(
    old_children: tuple[ElementNode, ...],
    new_children: tuple[ElementNode, ...]
) -> tuple[ElementNode, ...]:
    # 1. Head scan: match from start
    # 2. Tail scan: match from end
    # 3. Key-based matching: use keys for middle
    # 4. Position fallback: match by index
    # 5. Unmount unmatched old nodes
    # 6. Mount new nodes
    return final_children
```

### Head/Tail Scan

Most updates append, prepend, or modify ends of lists. Head/tail scan handles these efficiently without key matching.

**Head Scan:**
```python
old = [A, B, C, D]
new = [A, B, X, Y]

# Scan from start
i = 0
while old[i].matches(new[i]):
    new[i] = preserve_id(old[i], new[i])
    i += 1
# Matched: A, B
# Remaining: old=[C, D], new=[X, Y]
```

**Tail Scan:**
```python
old = [A, B, C, D]
new = [X, Y, C, D]

# Scan from end (after head scan)
old_end = len(old) - 1
new_end = len(new) - 1
while old[old_end].matches(new[new_end]):
    new[new_end] = preserve_id(old[old_end], new[new_end])
    old_end -= 1
    new_end -= 1
# Matched: C, D
# Remaining: old=[A, B], new=[X, Y]
```

**Benefits:**
- O(n) complexity for common cases (append, prepend)
- No key requirement for simple lists
- Fast path for static content at ends

### Key-Based Matching

For complex reorderings, deletions, and insertions, keys provide stable identity.

**Usage:**
```python
for item in items:
    with Card(key=item.id):  # Stable key
        h.P(item.name)
```

**Matching Algorithm:**
```python
# After head/tail scan, remaining nodes:
old_remaining = {node.key: node for node in old_middle if node.key}
new_remaining = [node for node in new_middle]

for new_node in new_remaining:
    if new_node.key and new_node.key in old_remaining:
        old_node = old_remaining[new_node.key]
        if old_node.component == new_node.component:
            # Match found, preserve ID
            new_node = preserve_id(old_node, new_node)
```

**Key Rules:**
- Keys must be unique within siblings
- Keys should be stable across renders
- Use entity IDs, not array indices
- Keys optional but recommended for dynamic lists

**Example - List Reordering:**
```python
# Old list
items = ["A", "B", "C"]

# New list (reordered)
items = ["C", "A", "B"]

# Without keys: All three unmount/remount (state lost)
# With keys: Nodes reordered, state preserved
```

### ID Preservation

When nodes match, the new node receives the old node's ID:

```python
def preserve_id(old_node: ElementNode, new_node: ElementNode) -> ElementNode:
    return dataclass.replace(new_node, id=old_node.id)
```

This ensures:
- State lookup continues working (same ID)
- Callbacks reference correct state
- React reconciliation identifies node correctly

**State Transfer:**
```python
# Old node: id="el_42"
# State: element_state["el_42"] = ElementState(...)

# New node matches, gets id="el_42"
# State preserved: element_state["el_42"] still valid
```

### Mount/Unmount Lifecycle

**Mount:**
When a new node appears (no match in old tree):
```python
def mount_node(node: ElementNode) -> ElementNode:
    # Assign new ID
    node_id = self.next_id()
    node = dataclass.replace(node, id=node_id)

    # Create state
    self._element_state[node_id] = ElementState(
        mounted=True,
        parent_id=parent_node_id
    )

    # Render component
    self.render(node)

    return node
```

**Unmount:**
When an old node has no match in new tree:
```python
def unmount_node(node: ElementNode) -> None:
    # Recursively unmount children
    for child in node.children:
        unmount_node(child)

    # Clean up state
    del self._element_state[node.id]

    # Clean up callbacks
    remove_callbacks_for_element(node.id)
```

**Component Replacement:**
When component type changes at same position:
```python
# Old: Button at position 0
# New: Input at position 0

# Unmount Button (different type, can't match)
unmount_node(old_button_node)

# Mount Input
mount_node(new_input_node)
```

---

## Diff Algorithm

The diff algorithm computes minimal updates between renders, generating patches that contain only what changed.

### Computing Minimal Updates

After reconciliation, we have two trees:
- **Previous tree:** Last rendered tree sent to client
- **Current tree:** Newly reconciled tree

The diff algorithm compares these trees and produces a patch describing changes.

**Diff Strategy:**
```python
def diff_tree(old: ElementNode, new: ElementNode) -> Patch | None:
    # Same ID means potentially same node
    if old.id != new.id:
        return Replace(new)  # Different node, full replace

    if old.component != new.component:
        return Replace(new)  # Type changed, full replace

    # Same component, check props
    props_diff = diff_props(old.props, new.props)

    # Recursively diff children
    children_patches = diff_children(old.children, new.children)

    if not props_diff and not children_patches:
        return None  # No changes

    return Update(
        node_id=new.id,
        props=props_diff,
        children=children_patches
    )
```

**Optimization:** Only walk tree where IDs changed or nodes are known dirty. Unchanged subtrees (same ID, not dirty) are skipped entirely.

### Patch Generation

Patches are structured updates describing changes:

**Patch Types:**

1. **Update:** Modify existing node
```python
@dataclass
class Update:
    node_id: str                          # Which node to update
    props: dict[str, Any] | None = None   # Changed props only
    children: list[ChildPatch] | None = None  # Child changes
```

2. **Replace:** Replace node entirely
```python
@dataclass
class Replace:
    node: ElementNode  # New node tree
```

3. **Insert:** Add new child
```python
@dataclass
class Insert:
    index: int         # Where to insert
    node: ElementNode  # What to insert
```

4. **Remove:** Delete child
```python
@dataclass
class Remove:
    index: int  # Which child to remove
```

5. **Move:** Reorder child
```python
@dataclass
class Move:
    from_index: int  # Current position
    to_index: int    # New position
```

**Example Patch:**
```python
# Change button text and add child
patch = Update(
    node_id="el_42",
    props={"text": "Updated"},
    children=[
        Insert(index=1, node=new_child_node)
    ]
)
```

### Delta vs Full Tree

The system uses two modes:

**1. Delta Patches (normal):**
After initial render, send only changes:
```python
{
    "type": "patch",
    "updates": [
        {"node_id": "el_42", "props": {"text": "New"}},
        {"node_id": "el_50", "children": [...]}
    ]
}
```

**Benefits:**
- Minimal bandwidth usage
- Fast transmission
- Efficient React reconciliation (only changed nodes)

**2. Full Tree (fallback):**
Send complete tree in certain cases:
- Initial render (client has no tree)
- After error (resync state)
- Large changes (diff overhead > tree size)

```python
{
    "type": "render",
    "tree": {
        "type": "App",
        "id": "el_1",
        "children": [...]
    }
}
```

**Heuristic:**
```python
if len(patches) > len(new_tree) * 0.5:
    # More than 50% of tree changed, send full tree
    send_full_tree(new_tree)
else:
    send_patches(patches)
```

---

## React Client Integration

The React client receives serialized trees from the server and renders them to the DOM.

### Component Type Mapping

Three component types map differently to React:

| Server Type | Client Representation | Example |
|-------------|----------------------|---------|
| CompositionComponent | Generic wrapper | `<FunctionalComponent {...props} />` |
| ReactComponentBase | Specific component | `<Button text="Click" />` |
| HTMLElement | JSX element | `<div className="container">...</div>` |

**Serialized Format:**
```typescript
interface SerializedNode {
    kind: "react_component" | "jsx_element" | "text";  // Element kind
    type: string;    // Component or tag name to render
    name: string;    // Python component name (for debugging)
    key: string;     // User key or server-assigned ID
    props: Record<string, any>;
    children: SerializedNode[];
}
```

### CompositionComponent on Client

CompositionComponents have no direct React equivalent. The client uses a generic wrapper:

**Server:**
```python
@component
def UserCard(name: str, email: str) -> None:
    with Card():
        h.H3(name)
        h.P(email)
```

**Serialized:**
```json
{
    "kind": "react_component",
    "type": "CompositionComponent",
    "name": "UserCard",
    "key": "e42",
    "props": {},
    "children": [...]
}
```

**Client Rendering:**
```typescript
function FunctionalComponent({ children, ...props }: Props) {
    // Generic wrapper just renders children
    return <>{children}</>;
}

// Rendered as:
<FunctionalComponent key="e42">
    <Card>...</Card>
</FunctionalComponent>
```

**Purpose:**

- Provides React key for reconciliation (e42)
- Maintains tree structure
- No logic—pure passthrough

### ReactComponentBase Rendering

ReactComponentBase subclasses (created via `@react_component` or `react_component_from_files`) map directly to their React counterparts:

**Server:**
```python
Button(text="Click", on_click=handler, variant="primary")
```

**Serialized:**
```json
{
    "kind": "react_component",
    "type": "Button",
    "name": "Button",
    "key": "e50",
    "props": {
        "text": "Click",
        "on_click": {"__callback__": "e50:on_click"},
        "variant": "primary"
    },
    "children": []
}
```

**Client Rendering:**
```typescript
import { Button } from "@blueprintjs/core";

function renderNode(node: SerializedNode) {
    if (node.type === "react") {
        const Component = COMPONENT_MAP[node.name];  // Button
        const props = transformProps(node.props);     // Handle callbacks
        return <Component key={node.id} {...props} />;
    }
}
```

**Component Registry:**
```typescript
const COMPONENT_MAP: Record<string, React.ComponentType> = {
    "Button": Button,
    "Card": Card,
    "Input": Input,
    // ... all Blueprint components
};
```

**Props Transformation:**
Callbacks are transformed from `{__callback__: "cb_123"}` to actual functions:
```typescript
function transformProps(props: Record<string, any>) {
    const transformed = { ...props };

    for (const [key, value] of Object.entries(props)) {
        if (isCallback(value)) {
            // value = {__callback__: "cb_123"}
            transformed[key] = (...args) => {
                sendEvent(value.__callback__, args);
            };
        }
    }

    return transformed;
}
```

### HTMLElement Rendering

HTMLElements map to JSX elements:

**Server:**
```python
h.Div(
    class_name="container",
    style={"padding": "20px"},
    on_click=handler
)
```

**Serialized:**
```json
{
    "kind": "jsx_element",
    "type": "div",
    "name": "Div",
    "key": "e60",
    "props": {
        "className": "container",
        "style": {"padding": "20px"},
        "onClick": {"__callback__": "e60:onClick"}
    },
    "children": []
}
```

**Client Rendering:**
```typescript
function renderNode(node: SerializedNode) {
    if (node.type === "html") {
        const tag = node.name;  // "div"
        const props = transformProps(node.props);
        const children = node.children?.map(renderNode);

        return React.createElement(tag, {
            key: node.id,
            ...props
        }, children);
    }
}

// Equivalent JSX:
<div key="el_60" className="container" style={{padding: "20px"}} onClick={...}>
    {children}
</div>
```

---

## Callbacks and Events

### Callback Registration

During serialization, callback functions are registered with the RenderTree and replaced with IDs:

**Server:**
```python
def on_click():
    state.count += 1

Button(text="Click", on_click=on_click)
```

**Serialization:**
```python
def serialize_element(node: ElementNode) -> dict:
    props = {}
    for key, value in node.props.items():
        if callable(value):
            # Register callback, get ID
            callback_id = render_tree.register_callback(value)
            props[key] = {"__callback__": callback_id}
        else:
            props[key] = value

    return {
        "type": get_type(node.component),
        "name": get_name(node.component),
        "id": node.id,
        "props": props,
        "children": [serialize_element(c) for c in node.children]
    }
```

**Registry:**
```python
class RenderTree:
    _callback_registry: dict[str, Callable]

    def register_callback(
        self, func: Callable, node_id: str, prop_name: str
    ) -> str:
        # Deterministic ID based on node and prop name
        callback_id = f"{node_id}:{prop_name}"
        self._callback_registry[callback_id] = func
        return callback_id
```

**Deterministic IDs:** Callback IDs are based on node ID and property name (e.g., `e5:on_click`). This ensures:

- Same callback location always gets same ID (stability)
- Callbacks are automatically overwritten on re-render
- Easy cleanup on unmount by node_id prefix

### Event Serialization

When events fire on the client, relevant properties are serialized and sent to server:

**Client-Side:**
```typescript
function transformCallback(callbackId: string) {
    return (...args: any[]) => {
        const serializedArgs = args.map(arg => {
            if (arg instanceof Event) {
                return serializeEvent(arg);
            }
            return arg;
        });

        sendEvent(callbackId, serializedArgs);
    };
}

function serializeEvent(event: Event): SerializedEvent {
    if (event instanceof MouseEvent) {
        return {
            type: "MouseEvent",
            clientX: event.clientX,
            clientY: event.clientY,
            button: event.button,
            altKey: event.altKey,
            ctrlKey: event.ctrlKey,
            shiftKey: event.shiftKey,
            metaKey: event.metaKey,
        };
    }
    // ... other event types
}
```

**Message Format:**
```json
{
    "type": "event",
    "callback_id": "e42:on_click",
    "args": [
        {
            "type": "MouseEvent",
            "clientX": 150,
            "clientY": 200,
            "button": 0
        }
    ]
}
```

### Server Execution

The server receives the event message, looks up the callback, and executes it:

```python
async def handle_event(message: EventMessage):
    callback = render_tree.get_callback(message.callback_id)

    if callback is None:
        # Stale callback ID (from previous render)
        logger.warning(f"Unknown callback: {message.callback_id}")
        return

    # Deserialize event objects
    args = deserialize_args(message.args)

    # Execute callback
    try:
        if asyncio.iscoroutinefunction(callback):
            await callback(*args)
        else:
            callback(*args)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        # Send error to client
        await send_error(str(e))

    # Render changes
    await render_tree.render()
```

**State Changes:**
```python
def on_click():
    state.count += 1  # __setattr__ marks elements dirty
    # render() picks up dirty elements and re-renders
```

### Async Callback Support

Callbacks can be async functions:

```python
async def on_save():
    await database.save(state.data)
    state.saved = True
    state.save_time = datetime.now()

Button(text="Save", on_click=on_save)
```

**Execution:**
- Async callbacks are awaited
- Render happens after async completes
- UI remains responsive during await
- Errors are caught and reported

**Use Cases:**
- API calls
- Database operations
- File I/O
- External service integration

---

## Serialization and Communication

### Tree Serialization

The RenderTree serializes ElementNodes to JSON-compatible dictionaries:

```python
def serialize_element(node: ElementNode) -> dict:
    """Serialize an ElementNode to JSON-compatible dict."""
    return {
        "type": get_component_type(node.component),  # "functional"|"react"|"html"
        "name": get_component_name(node.component),  # Component/tag name
        "id": node.id,                                # Unique ID
        "props": serialize_props(node.props),         # With callbacks → IDs
        "children": [serialize_element(c) for c in node.children],
    }
```

**Type Determination:**
```python
def get_component_type(component: IComponent) -> str:
    if isinstance(component, CompositionComponent):
        return "functional"
    elif isinstance(component, ReactComponentBase):
        return "react"
    elif isinstance(component, HTMLElement):
        return "html"
    else:
        raise ValueError(f"Unknown component type: {component}")
```

**Serialization Flow:**
1. Walk tree depth-first
2. For each node, serialize props (replace callbacks with IDs)
3. Recursively serialize children
4. Build nested dict structure

### Callback ID Injection

As described in [Callback Registration](#callback-registration), callbacks are replaced with callback IDs during serialization:

```python
def serialize_props(props: dict[str, Any]) -> dict[str, Any]:
    serialized = {}

    for key, value in props.items():
        if callable(value):
            callback_id = render_tree.register_callback(value)
            serialized[key] = {"__callback__": callback_id}
        elif isinstance(value, dict):
            serialized[key] = serialize_props(value)  # Recurse
        elif isinstance(value, (list, tuple)):
            serialized[key] = [
                serialize_props({"_": v})["_"] if callable(v) else v
                for v in value
            ]
        else:
            serialized[key] = value  # Primitive, pass through

    return serialized
```

**Callback Marker:**
The `{"__callback__": "cb_123"}` format is recognized by the client as a callback reference.

### Message Format

All messages are msgpack-encoded for efficiency.

**Message Types:**

1. **HelloMessage (client → server):**
```python
@dataclass
class HelloMessage:
    type: Literal["hello"] = "hello"
    client_id: str
```

2. **HelloResponseMessage (server → client):**
```python
@dataclass
class HelloResponseMessage:
    type: Literal["hello_response"] = "hello_response"
    session_id: str
```

3. **RenderMessage (server → client):**
```python
@dataclass
class RenderMessage:
    type: Literal["render"] = "render"
    tree: dict  # Serialized ElementNode tree
```

4. **PatchMessage (server → client):**
```python
@dataclass
class PatchMessage:
    type: Literal["patch"] = "patch"
    patches: list[dict]  # List of patches
```

5. **EventMessage (client → server):**
```python
@dataclass
class EventMessage:
    type: Literal["event"] = "event"
    callback_id: str
    args: list[Any]
```

6. **ErrorMessage (server → client):**
```python
@dataclass
class ErrorMessage:
    type: Literal["error"] = "error"
    message: str
    traceback: str | None = None
```

**Encoding:**
```python
import msgspec

# Encode
encoded = msgspec.msgpack.encode(RenderMessage(tree=serialized_tree))

# Decode
message = msgspec.msgpack.decode(encoded)
```

### WebSocket Protocol

Communication happens over a single WebSocket connection:

**Connection Flow:**
1. Client connects to `/ws`
2. Client sends HelloMessage
3. Server responds with HelloResponseMessage
4. Server sends initial RenderMessage
5. Bidirectional communication:
   - Server sends RenderMessage/PatchMessage on updates
   - Client sends EventMessage on user interaction

**Concurrency:**
- Server uses async/await for WebSocket handling
- Multiple connections (users) are independent
- Each connection has its own RenderTree instance
- Messages are processed sequentially per connection

**Error Handling:**
- Connection errors → reconnect with exponential backoff
- Message decode errors → log, ignore message
- Callback errors → ErrorMessage to client
- Unrecognized message types → log, ignore

**Keep-Alive:**
- Ping/pong frames maintain connection
- Timeout after 30s of inactivity
- Client reconnects on timeout

---

## Preventing User Errors

Trellis uses a layered approach to prevent common mistakes: API design makes correct usage natural, type checking catches errors during development, and runtime validation catches errors that can't be statically checked.

### API Design Principles

**Make incorrect usage hard to express:**

The API is designed so that common mistakes are either impossible or awkward to write.

**Context managers enforce structure:**
```python
# Correct: Children naturally nested
with Card():
    Button(text="A")
    Button(text="B")

# Wrong: Syntactically invalid
Card():  # SyntaxError: requires 'with'
    Button(text="A")
```

**Components return None:**
Components don't return values, preventing confusion about what to do with the result:
```python
@component
def MyComponent():
    h.Div()  # Side effect: adds to tree
    # No return statement needed or expected
```

**Ellipsis for unimplemented bodies:**
For React components defined with `@react_component_from_files`, using `...` makes it clear the function body isn't meant to execute:
```python
@react_component_from_files(sources=["Button.tsx"])
def Button(text: str) -> ElementNode:
    ...  # Clear: implementation is in .tsx file
```

**Frozen dataclasses:**
ElementNode is frozen, preventing accidental mutation:
```python
node = Button(text="Click")
node.props["text"] = "New"  # Error: can't modify frozen dataclass
```

### Type Checking

**Static analysis catches errors before runtime:**

Type hints enable comprehensive type checking with mypy or similar tools.

**Missing required props:**
```python
@react_component_from_files(sources=["Input.tsx"])
def Input(value: str, on_change: Callable[[str], None]) -> ElementNode:
    ...

# Type error: missing required arguments
Input()  # Error: value and on_change required

# Correct
Input(value="text", on_change=handler)
```

**Wrong callback signatures:**
```python
def wrong_handler():  # Missing parameter
    pass

def correct_handler(value: str):
    pass

# Type error: incompatible callback signature
Input(value="", on_change=wrong_handler)  # Error: Expected Callable[[str], None]

# Correct
Input(value="", on_change=correct_handler)
```

**Invalid Literal values:**
```python
@react_component_from_files(sources=["Button.tsx"])
def Button(variant: Literal["primary", "secondary", "danger"] = "primary") -> ElementNode:
    ...

# Type error: invalid literal
Button(variant="extra-large")  # Error: not in Literal values

# Correct
Button(variant="primary")
```

**Components without children:**
The type system enforces that only components with `children` parameters can be used in `with` blocks:
```python
@component
def NoChildren():
    h.P("No children accepted")

# Type error: NoChildren doesn't accept children
with NoChildren():  # Error: can't use with block
    Button(text="A")
```

**Missing type hints:**
Functions without type hints can't be used as components:
```python
@component
def BadComponent(value):  # Error: missing type hint
    ...

# The decorator or type checker will flag this
```

### Runtime Validation

**Validation for cases type checking can't catch:**

Some errors are only detectable at runtime—dynamic values, configuration mismatches, or constraint violations.

**Children parameter enforcement:**
```python
@component
def NoChildren():
    h.P("Text")

# Runtime error
with NoChildren():  # RuntimeError: NoChildren() doesn't accept children
    Button(text="A")
```

**State modification during render:**
```python
@component
def Counter():
    state = CounterState()
    state.count += 1  # RuntimeError: Cannot modify state during render
    h.P(f"Count: {state.count}")
```

This is caught because `Stateful.__setattr__` checks if we're currently rendering and raises an error.

**Non-unique keys:**
```python
for item in items:
    with Card(key="duplicate"):  # RuntimeWarning: Duplicate key "duplicate"
        h.P(item.name)
```

The reconciler detects duplicate keys within siblings and warns the developer.

**Component name mismatch:**
```python
@react_component_from_files(
    sources=["components/MyButton.tsx"]  # Exports "MyButton"
)
def Button(...) -> ElementNode:  # Function named "Button"
    ...

# RuntimeError at bundle time: No export named "Button" found in MyButton.tsx
```

The bundler validates that the component name matches the .tsx export.

**Invalid prop values:**
Optional runtime validation in function body:
```python
@react_component_from_files(sources=["Button.tsx"])
def Button(
    text: str,
    variant: str = "primary",
) -> ElementNode:
    # Runtime validation beyond type checking
    if variant not in ["primary", "secondary", "danger", "ghost"]:
        raise ValueError(f"Invalid variant: {variant}")
    ...
```

This catches cases where `variant` is dynamically computed or comes from external data.

**Context access outside components:**
```python
state = CounterState()  # RuntimeError: Cannot create state outside component context

@component
def Counter():
    state = CounterState()  # Correct: inside component
    ...
```

### Layered Defense Examples

These examples show how multiple layers work together:

**Example 1: Wrong callback signature**
```python
@react_component_from_files(sources=["Input.tsx"])
def Input(on_change: Callable[[str], None]) -> ElementNode:
    ...

def handler():  # Wrong: missing str parameter
    print("changed")

# Layer 1 (Type checker): Error - incompatible type
Input(on_change=handler)

# If type checking is disabled:
# Layer 2 (Runtime): When callback fires, Python raises TypeError
# because handler() doesn't accept the str argument
```

**Example 2: Using component without children in with block**
```python
@component
def Leaf():
    h.P("I'm a leaf")

# Layer 1 (Type checker): Error - Leaf doesn't support context manager protocol
with Leaf():
    Button(text="A")

# If type checking is disabled:
# Layer 2 (Runtime): AttributeError - Leaf has no __enter__ method
```

**Example 3: Modifying state during render**
```python
@component
def Counter():
    state = CounterState()

    # Layer 1 (API design): This looks wrong - state changes in render
    state.count += 1

    # Layer 2 (Runtime): RuntimeError - Cannot modify state during render
    # Stateful.__setattr__ checks render context and raises
```

### Developer Experience

The goal is fast feedback:

1. **Type checker (seconds)**: Catches most errors during development
2. **Runtime validation (immediate)**: Catches remaining errors with clear messages
3. **API design (preventative)**: Makes correct usage natural and incorrect usage awkward

Error messages are designed to be actionable:
```
RuntimeError: Cannot use NoChildren() in a 'with' block - it doesn't accept children.
Did you mean to call it directly? Example: NoChildren()
```

Rather than:
```
AttributeError: 'NoChildren' object has no attribute '__enter__'
```

---

## Implementation Status

This section tracks which features from this design are implemented versus planned.

### Implemented

**Core Rendering:**

- ElementNode (immutable tree nodes with frozen props)
- ElementState (mutable runtime state per node)
- RenderTree (orchestrates rendering, reconciliation, lifecycle)
- Frame-based child collection during `with` blocks

**Component Types:**

- CompositionComponent with `@component` decorator
- ReactComponentBase with `@react_component_base` decorator
- HtmlElement with `@html_element` decorator

**Reconciliation:**

- Head/tail scan for efficient list matching
- Key-based matching for reordered lists
- Type-based matching fallback
- ID preservation across renders
- Mount/unmount lifecycle hooks

**State Management:**

- Stateful base class with automatic dependency tracking
- Context API for descendant state access
- Dirty marking and re-render triggering

**Callbacks:**

- Deterministic callback IDs (`{node_id}:{prop_name}`)
- Callback registration during serialization
- Per-node callback cleanup on unmount

**Serialization:**

- Full tree serialization to JSON
- ElementKind-based type discrimination
- Callback replacement with IDs

**Communication:**

- WebSocket protocol (HelloMessage, RenderMessage, EventMessage, etc.)
- msgpack encoding
- Async callback support

### Not Yet Implemented

**React Component Definition:**

- `@react_component` decorator with inline TSX generation
- `@react_component_from_files` decorator with .tsx bundling
- Component registry and bundler integration

**Diff/Patch Algorithm:**

- Computing minimal updates between renders
- Patch generation (Update, Replace, Insert, Remove, Move)
- Delta vs full tree heuristics

**Performance:**

- 30fps render batching
- Unchanged subtree skipping during diff
