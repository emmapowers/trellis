---
sidebar_position: 3
title: State Management
---

# State Management Design Document

This document describes how Trellis manages reactive state and enables two-way data binding.

## Overview

Trellis provides two key abstractions for state management:

1. **Stateful** — A base class for reactive state with automatic dependency tracking
2. **mutable()** — A function for two-way data binding between state and form inputs

## Stateful Base Class

`Stateful` is a base class for reactive state objects. Define state as a dataclass that inherits from `Stateful`:

```python
from dataclasses import dataclass
from trellis import Stateful

@dataclass
class FormState(Stateful):
    name: str = ""
    email: str = ""
    subscribed: bool = False
```

### Automatic Dependency Tracking

When a component reads a state property during render, Trellis automatically tracks that dependency. When the property changes, the component re-renders.

```python
@component
def UserDisplay() -> None:
    state = UserState.from_context()
    # Reading state.name registers this component as a dependency
    w.Label(text=f"Hello, {state.name}!")
```

**How it works:**

1. `Stateful.__getattribute__` intercepts property access during render
2. It records which component (by node ID) accessed which property
3. When `__setattr__` detects a property change, it marks dependent components as dirty
4. On the next render cycle, only dirty components re-render

### Property-Level Granularity

Dependency tracking is per-property, not per-object. A component that only reads `state.name` won't re-render when `state.email` changes.

```python
@dataclass
class AppState(Stateful):
    name: str = ""
    count: int = 0

@component
def NameDisplay() -> None:
    state = AppState.from_context()
    w.Label(text=state.name)  # Only depends on name

@component
def Counter() -> None:
    state = AppState.from_context()
    w.Label(text=str(state.count))  # Only depends on count
```

Modifying `state.count` only re-renders `Counter`, not `NameDisplay`.

### Context Integration

State can be shared across components using context:

```python
@component
def App() -> None:
    state = AppState()
    with state:  # Push to context
        Header()
        Content()
        Footer()

@component
def Header() -> None:
    state = AppState.from_context()  # Retrieve from context
    w.Label(text=state.title)
```

## Two-Way Data Binding with mutable()

For form inputs, Trellis provides `mutable()` to create two-way bindings between state properties and widgets.

### The Problem

Without two-way binding, updating state from form inputs requires explicit callbacks:

```python
# Verbose pattern with widgets
w.TextInput(
    value=state.name,
    on_change=lambda v: setattr(state, "name", v),
)

# Same pattern with HTML elements
h.Input(
    value=state.name,
    on_input=lambda e: setattr(state, "name", e["target"]["value"]),
)
```

### The Solution

With `mutable()`, the binding is automatic:

```python
# Clean two-way binding
w.TextInput(value=mutable(state.name))
```

### How mutable() Works

1. **Property Access Recording**: When you access `state.name`, `Stateful.__getattribute__` records the access in a context variable: `(owner, attr_name, value)`

2. **Reference Capture**: `mutable()` reads this recorded access and creates a `Mutable[T]` wrapper containing the owner and attribute name

3. **Serialization**: During serialization, `Mutable[T]` becomes:
   ```json
   {"__mutable__": "callback_id", "value": "current_value"}
   ```

4. **Client Handling**: The client extracts the value and auto-generates an `on_change` handler that invokes the callback

5. **State Update**: When the user types, the callback sets the new value on the state, triggering re-renders

### Supported Widgets

These widgets support `mutable()` for their primary value props:

| Widget | Property | Type |
|--------|----------|------|
| TextInput | `value` | `str` |
| NumberInput | `value` | `float` |
| Slider | `value` | `float` |
| Checkbox | `checked` | `bool` |
| Select | `value` | `str` |
| Tabs | `selected` | `str` |
| Collapsible | `expanded` | `bool` |

### When to Use mutable() vs callback()

**Use mutable()** for simple bindings where the widget value maps directly to state:

```python
w.TextInput(value=mutable(state.name))
w.Checkbox(checked=mutable(state.enabled))
```

**Use callback()** when you need custom processing:

```python
# Validation and transformation
def set_name(value: str) -> None:
    state.name = value.strip().title()

w.TextInput(value=callback(state.name, set_name))

# Clamping values
def set_slider(value: float) -> None:
    state.percent = max(0.0, min(100.0, value))

w.Slider(value=callback(state.percent, set_slider))
```

Both `mutable()` and `callback()` create a `Mutable[T]` wrapper. The difference is that `callback()` stores a custom handler that's used instead of the auto-generated property setter.

## Implementation Details

### Mutable Class

```python
class Mutable(Generic[T]):
    __slots__ = ("_attr", "_on_change", "_owner")

    def __init__(
        self,
        owner: Stateful,
        attr: str,
        on_change: Callable[[T], Any] | None = None,
    ) -> None:
        self._owner = owner
        self._attr = attr
        self._on_change = on_change  # Custom callback (None = use auto-setter)

    @property
    def value(self) -> T:
        return object.__getattribute__(self._owner, self._attr)

    @value.setter
    def value(self, new_value: T) -> None:
        setattr(self._owner, self._attr, new_value)

    @property
    def on_change(self) -> Callable[[T], Any] | None:
        return self._on_change
```

The `mutable()` function creates a `Mutable` without a custom callback (uses auto-setter). The `callback()` function creates a `Mutable` with a custom callback.

### Property Access Recording

```python
# In RenderTree:
class RenderTree:
    _last_property_access: tuple[Stateful, str, Any] | None = None

# In Stateful.__getattribute__:
def __getattribute__(self, name: str) -> Any:
    value = object.__getattribute__(self, name)

    # Skip internal attrs and callables
    if name.startswith("_") or callable(value):
        return value

    # During render, record access on the RenderTree for mutable()
    tree = get_active_render_tree()
    if tree is not None:
        tree._last_property_access = (self, name, value)

    return value
```

### Serialization Format

Mutable values serialize to a special format that the client recognizes:

```python
# In serialization.py
if isinstance(value, Mutable):
    # Use custom callback if provided, otherwise create a setter
    if value.on_change is not None:
        handler = value.on_change
    else:
        def setter(new_val):
            value.value = new_val
        handler = setter

    cb_id = ctx.register_callback(handler, node_id, f"{prop_name}:mutable")
    return {
        "__mutable__": cb_id,
        "value": serialize(value.value),
    }
```

### Client-Side Handling

The client wraps mutable refs in a `Mutable<T>` object that components use explicitly:

```typescript
// In processProps
if (isMutableRef(value)) {
    result[key] = new Mutable(value, onEvent);
}

// In each widget component
const { value, setValue } = unwrapMutable(valueProp);
const handleChange = setValue ?? on_change;
```

Each widget explicitly handles mutable bindings using `unwrapMutable()`, which returns the current value and an optional `setValue` function.