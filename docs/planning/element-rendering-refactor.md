# Lazy Rendering: Two-Phase Architecture

## Goal
Separate "declaring what to render" from "actually rendering" by introducing:
1. **ElementDescriptor** - lightweight, immutable description (`Button(text="hi")` returns this)
2. **ElementNode** - runtime tree node with state/lifecycle (created by reconciler)

## Core Concept

```
Current:  Button(text="hi") → immediately executes → creates Element with children

Proposed: Button(text="hi") → returns ElementDescriptor (no execution)
          Reconciler sees descriptor → decides to execute or skip → creates/updates ElementNode
```

## New Types

```python
@dataclass(frozen=True)
class ElementDescriptor:
    """Immutable description of what to render."""
    component: IComponent
    key: str = ""
    props: FrozenDict[str, Any]  # immutable for comparison

@dataclass
class ElementNode:
    """Runtime tree node with state and lifecycle."""
    descriptor: ElementDescriptor
    parent: ElementNode | None
    children: list[ElementNode]
    depth: int
    mounted: bool
    local_state: dict[tuple[type, int], Any]  # Stateful instances
    state_call_count: int
    dirty: bool
```

## Component API Change

```python
class Component:
    def __call__(self, **props) -> ElementDescriptor:
        """Create descriptor only - NO execution."""
        return ElementDescriptor(component=self, props=freeze(props), ...)

    def execute(self, node: ElementNode, **props) -> Elements:
        """Called by reconciler when this component needs to render."""
        ...
```

## Reconciler Flow

```python
def reconcile(old_node: ElementNode | None, new_desc: ElementDescriptor) -> ElementNode:
    if old_node is None:
        return mount_new(new_desc)

    if old_node.descriptor.component != new_desc.component:
        unmount(old_node)
        return mount_new(new_desc)

    # OPTIMIZATION: skip if props unchanged and not dirty
    if old_node.descriptor.props == new_desc.props and not old_node.dirty:
        return old_node  # reuse without re-executing

    # Re-execute component
    old_node.descriptor = new_desc
    execute_and_reconcile_children(old_node)
    return old_node
```

## State Simplification

Current `Stateful.__new__()` has complex `_rerender_target` logic to figure out which element owns the state. With lazy rendering:

```python
def __new__(cls, *args, **kwargs):
    ctx = get_active_render_context()
    if not ctx.rendering:
        return object.__new__(cls)

    # SIMPLE: current_node is always correct during execute()
    node = ctx.current_node
    key = (cls, node.state_call_count)
    node.state_call_count += 1

    if key in node.local_state:
        return node.local_state[key]

    instance = object.__new__(cls)
    node.local_state[key] = instance
    return instance
```

## BlockComponent with Lazy Rendering

Keep `with` syntax but collect descriptors instead of executing:

```python
class BlockDescriptor(ElementDescriptor):
    """Descriptor that collects children via context manager."""
    children: list[ElementDescriptor]  # Mutable during collection phase

    def __enter__(self):
        # Push self onto descriptor collection stack
        _descriptor_stack.append(self)
        return self

    def __exit__(self, *exc):
        _descriptor_stack.pop()
        # Parent descriptor (if any) gets us as a child
        if _descriptor_stack:
            _descriptor_stack[-1].children.append(self)
```

Usage unchanged:
```python
with Column():      # Creates BlockDescriptor, pushes to stack
    Button()        # Creates descriptor, appends to Column's children
    Text()          # Same
# __exit__ pops Column, it becomes child of its parent (or root)
```

Key insight: Children collection happens at descriptor level (no execution).
The reconciler later executes the component function with `props["children"] = collected_descriptors`.

## Files to Modify

1. **rendering.py** - Add `ElementDescriptor`, `BlockDescriptor`, rename `Element` → `ElementNode`, update `RenderContext`
2. **base_component.py** - Split `render()` into `__call__()` (descriptor) and `execute()` (runtime)
3. **functional_component.py** - Implement `execute()` to call render function
4. **block_component.py** - Return `BlockDescriptor` from `__call__()`, simplify to just collect children
5. **reconcile.py** - Rewrite to reconcile descriptors vs nodes, add props comparison
6. **state.py** - Simplify `__new__()` to use `current_node` only, remove `_rerender_target`

## Implementation Order

1. Add `ElementDescriptor` type (additive, no breaking changes)
2. Rename `Element` → `ElementNode`, add descriptor field
3. Update `Component.__call__()` to return descriptors
4. Add `Component.execute()` method
5. Rewrite `RenderContext.render()` with reconcile-then-commit flow
6. Simplify `Stateful.__new__()`
7. Update tests

## Benefits

- **Performance**: Skip execution when props unchanged
- **Simpler state**: No `_rerender_target` heuristics
- **Cleaner mental model**: Describe vs Execute separation
- **Future-proof**: Foundation for async/concurrent rendering
