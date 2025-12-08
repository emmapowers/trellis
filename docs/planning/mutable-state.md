# Mutable[T] Two-Way Binding Implementation

## Overview

Add `Mutable[T]` wrapper enabling two-way data binding between Python state and client form inputs.

**Target API:**
```python
@component
def IncrementButton(counter: Mutable[int]):
    def on_click():
        counter.value += 1
    Button("Increment!", on_click=on_click)

# Usage:
state = AppState()
IncrementButton(counter=mutable(state.count))
```

**Key Design Decision:** `Stateful.__getattribute__` returns `Mutable[T]` wrappers with `immutable=True` by default. The `mutable()` function sets `immutable=False`. Framework unwraps immutable wrappers before passing props to components.

## Files to Modify

| File | Change |
|------|--------|
| `src/trellis/core/mutable.py` | **New** - `Mutable[T]` class and `mutable()` function |
| `src/trellis/core/state.py:169-205` | Return `Mutable` wrapper from `__getattribute__` |
| `src/trellis/core/reconcile.py:157` | Unwrap immutable `Mutable` values before component execution |
| `src/trellis/core/serialization.py:62-82` | Serialize `Mutable` with setter callback |
| `src/trellis/client/src/types.ts` | Add `MutableRef` type |
| `src/trellis/client/src/TreeRenderer.tsx:63-77` | Handle `__mutable__` refs in prop processing |
| `src/trellis/__init__.py` | Export `Mutable`, `mutable` |

## Implementation Steps

### 1. Create `Mutable[T]` wrapper (`src/trellis/core/mutable.py`)

```python
@dataclass(frozen=True)
class Mutable(Generic[T]):
    _owner: "Stateful"
    _attr: str
    _immutable: bool = True

    @property
    def value(self) -> T:
        return object.__getattribute__(self._owner, self._attr)

    @value.setter
    def value(self, new_value: T) -> None:
        setattr(self._owner, self._attr, new_value)

def mutable(m: Mutable[T]) -> Mutable[T]:
    """Returns copy with _immutable=False"""
    return Mutable(_owner=m._owner, _attr=m._attr, _immutable=False)
```

Add proxy methods (`__str__`, `__int__`, `__add__`, etc.) so `state.count + 1` still works.

### 2. Modify `Stateful.__getattribute__` (`state.py:169-205`)

After dependency tracking, wrap return value:
```python
# At end of __getattribute__, replace `return value` with:
from trellis.core.mutable import Mutable
return Mutable(_owner=self, _attr=name, _immutable=True)
```

Skip wrapping for callables (methods).

### 3. Unwrap props in reconcile (`reconcile.py:157`)

Before `element.component.execute(element, **props)`:
```python
from trellis.core.mutable import Mutable

processed_props = {}
for key, value in props.items():
    if isinstance(value, Mutable) and value._immutable:
        processed_props[key] = value.value  # Unwrap
    else:
        processed_props[key] = value  # Keep Mutable wrapper
```

### 4. Serialize `Mutable` (`serialization.py`)

In `_serialize_value()`:
```python
if isinstance(value, Mutable):
    if value._immutable:
        return _serialize_value(value.value)
    else:
        def setter(new_val): value.value = new_val
        return {"__mutable__": register_callback(setter), "value": _serialize_value(value.value)}
```

### 5. Client types (`client/src/types.ts`)

```typescript
export interface MutableRef {
  __mutable__: string;
  value: unknown;
}

export function isMutableRef(value: unknown): value is MutableRef { ... }
```

### 6. Client prop processing (`client/src/TreeRenderer.tsx`)

In `processProps()`:
```typescript
if (isMutableRef(value)) {
  result[key] = value.value;
  // Auto-generate onChange if this is a 'value' prop
  if (key === "value" && !("onChange" in props)) {
    result["onChange"] = (e) => client.sendEvent(value.__mutable__, [e.target.value]);
  }
}
```

### 7. Exports (`__init__.py`)

```python
from trellis.core.mutable import Mutable, mutable
```

## Testing

1. Basic usage: `mutable(state.text)` creates non-immutable Mutable
2. Unwrapping: immutable Mutable becomes raw value in component props
3. Proxy methods: `state.count + 1` works via `__add__`
4. Serialization: mutable props serialize with `__mutable__` callback
5. Round-trip: client value change updates Python state
