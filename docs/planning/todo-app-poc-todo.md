# Todo App POC - Remaining Work

Features needed to fully implement `docs/planning/examples/todo/` after the current POC.

## Event System (Client → Server)

**What**: User interactions (click, input, etc.) need to invoke Python callbacks.

**Implementation**:
1. Callback registry (partially done in serialization) maps IDs to Python callables
2. Add `EventMessage` type: `{callback_id: str, args: list[Any]}`
3. Client sends EventMessage when user interacts with widget
4. Server receives, looks up callback, invokes it
5. After callback, re-render dirty elements, send updated tree

**Widgets affected**: Button (onClick), TextInput (onChange, onEnter, onEscape, onBlur), Checkbox (onChange)

## Diff/Patch System

**What**: Currently send full tree on every render. Should send minimal patches.

**Implementation**:
1. After re-render, diff old serialized tree vs new
2. Generate patch operations: `{path: [...], op: "replace"|"insert"|"remove", value: ...}`
3. Client applies patches to React state

**Benefit**: Reduced bandwidth, faster updates for large trees

## mutable() Two-Way Binding

**What**: Allow form inputs to directly update Stateful properties.

**Usage**:
```python
@dataclass
class FormState(Stateful):
    text: str = ""

state = FormState()
TextInput(value=mutable(state.text))  # Changes sync back automatically
```

**Implementation**:
1. `mutable(obj, attr)` returns a `MutableRef` with getter/setter
2. Serialize as `{"__mutable__": callback_id}`
3. Client input onChange sends value to server
4. Server updates property, triggers re-render

## Observable Collections

**What**: Track mutations to lists/dicts and trigger re-renders.

**Current workaround**: Reassign entire collection: `self.items = [*self.items, new_item]`

**Implementation** (if needed):
1. `ObservableList(Stateful)` wrapping a list
2. Override `append`, `insert`, `remove`, `__setitem__`, etc.
3. Each mutation marks dependent elements dirty

## Additional Widgets

**Needed for todo example**:
- TextInput (with value, placeholder, onEnter, onEscape, onBlur)
- Checkbox (with checked, onChange)
- DatePicker (with value, placeholder)
- TagInput (with tags, suggestions, placeholder)
- Badge (with text, size)

**Styling props** (for all widgets):
- gap, padding, flex, maxWidth
- backgroundColor, textColor, borderRadius
- hAlign with Align enum (CENTER, SPACE_BETWEEN, etc.)

## Async Integration

**What**: Event handlers can be async functions.

**Implementation**:
1. Detect if callback is async
2. Schedule on event loop: `asyncio.create_task(callback(...))`
3. Re-render after task completes

## Priority Order

1. Event System - makes POC interactive
2. TextInput widget - needed for basic forms
3. Additional widgets as needed
4. Diff/patch - performance optimization
5. mutable() - convenience
6. Observable collections - convenience
