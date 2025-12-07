# Lazy Rendering: Two-Phase Architecture

## Goal
Separate "declaring what to render" from "actually rendering" by introducing:
1. **ElementDescriptor** - lightweight, immutable description (`Button(text="hi")` returns this)
2. **Element** - runtime tree node with state/lifecycle (created by reconciler when mounting)

## Core Concept

```
Current:  Button(text="hi") → immediately executes → creates Element with children

Proposed: Button(text="hi") → returns ElementDescriptor (no execution)
          Reconciler sees descriptor → decides to execute or skip → creates/updates Element
```

## Two Distinct Phases

### Phase 1: Descriptor Creation

Component function body runs, but only creates descriptors - no Elements, no mounting:

```python
@component
def MyComponent() -> None:
    with Column():           # Creates ColumnDescriptor, pushes to descriptor stack
        Text("what")         # Creates TextDescriptor, added to Column's pending children
        Button("Click Me!")  # Creates ButtonDescriptor, added to Column's pending children
    # __exit__: Column descriptor's children = [TextDescriptor, ButtonDescriptor]
    # Column descriptor added to MyComponent's pending children
```

At this point:
- No Elements created yet
- No reconciliation yet
- Just a tree of immutable descriptors

### Phase 2: Execution (Reconciler-driven)

When the reconciler decides to render a component, it calls `component.execute(node, **props)`:

```python
@component
def Column(children: list[ElementDescriptor]) -> None:  # children are DESCRIPTORS
    with html.div():
        for child in children:
            with html.div():  # wrapper
                child()       # still inside a `with` block - adds to wrapper's pending children
            # __exit__: wrapper.children = [child]
    # __exit__: div.children = [all wrappers]

@component
def div(children: list[ElementDescriptor]) -> None:
    for child in children:
        child()  # NOT inside a `with` block → actually mounts!
```

## The `child()` Rule

When `child()` is called on a descriptor:
- **Inside a `with` block** → adds to that block's pending children (still building descriptors)
- **Outside any `with` block** → triggers reconciler to mount/reconcile

This means:
- Containers can nest arbitrarily, just passing descriptors down
- Mounting only happens at the "leaves" of the container chain
- Reconciler can skip entire subtrees if props unchanged

## Dirty Elements and Re-rendering

When state changes, Elements are marked dirty. The reconciler:

1. Finds dirty elements, sorted by depth (shallowest first)
2. For each dirty element:
   - Re-runs descriptor creation for that component (Phase 1)
   - Compares new descriptor tree with old
   - If props unchanged and not dirty → skip execution, reuse Element
   - If props changed or dirty → execute component, reconcile children

```python
def render_dirty() -> None:
    elements = sorted(dirty_elements, key=lambda e: e.depth)
    for element in elements:
        if element.dirty:  # May have been rendered as part of parent
            new_desc = element.component(**element.properties)  # Phase 1: create descriptors
            reconcile(element, new_desc)  # Phase 2: compare, execute if needed
            element.dirty = False
```

### Skipping Unchanged Subtrees

The key optimization:

```python
def reconcile(old_node: Element | None, new_desc: ElementDescriptor) -> Element:
    if old_node is None:
        return mount_new(new_desc)

    if old_node.descriptor.component != new_desc.component:
        unmount(old_node)
        return mount_new(new_desc)

    # OPTIMIZATION: skip if props unchanged and not dirty
    if old_node.descriptor.props == new_desc.props and not old_node.dirty:
        return old_node  # Reuse without re-executing!

    # Props changed or dirty - must re-execute
    old_node.descriptor = new_desc
    execute_and_reconcile_children(old_node)
    return old_node
```

## New Types

```python
@dataclass(frozen=True)
class ElementDescriptor:
    """Immutable description of what to render."""
    component: IComponent
    key: str = ""
    props: tuple[tuple[str, Any], ...]  # Immutable for comparison
    children: tuple[ElementDescriptor, ...] = ()  # Collected via `with` block

    def __enter__(self) -> ElementDescriptor:
        """Push collection stack for children."""
        _descriptor_stack.append([])
        return self

    def __exit__(self, *exc) -> None:
        """Pop children, store in descriptor, add to parent."""
        collected = _descriptor_stack.pop()
        # Validate: can't have children prop AND with block
        if "children" in dict(self.props):
            raise RuntimeError("Cannot provide 'children' prop and use 'with' block")
        object.__setattr__(self, "children", tuple(collected))
        if _descriptor_stack:
            _descriptor_stack[-1].append(self)

    def __call__(self) -> None:
        """Mount this descriptor at current position."""
        if _descriptor_stack:
            # Inside a `with` block - add to pending children
            _descriptor_stack[-1].append(self)
        else:
            # Outside `with` block - actually mount via reconciler
            reconcile_and_mount(self)

@dataclass
class Element:
    """Runtime tree node with state and lifecycle."""
    descriptor: ElementDescriptor
    parent: Element | None
    children: list[Element]
    depth: int
    dirty: bool
    _mounted: bool
    _local_state: dict[tuple[type, int], Any]
    _state_call_count: int
    render_context: RenderContext
```

## Component API

```python
class Component:
    def __call__(self, **props) -> ElementDescriptor:
        """Create descriptor only - NO execution."""
        return ElementDescriptor(
            component=self,
            key=props.pop("key", ""),
            props=freeze_props(props)
        )

    def execute(self, node: Element, **props) -> None:
        """Called by reconciler when this component needs to render."""
        # For FunctionalComponent: calls the render function
        pass
```

## State Simplification

With lazy rendering, during `execute()` the `current_node` is always correct:

```python
def __new__(cls, *args, **kwargs):
    ctx = get_active_render_context()
    if not ctx or not ctx.executing:
        return object.__new__(cls)

    node = ctx.current_node  # Always correct during execute()
    key = (cls, node._state_call_count)
    node._state_call_count += 1

    if key in node._local_state:
        return node._local_state[key]

    instance = object.__new__(cls)
    node._local_state[key] = instance
    return instance
```

No more `_rerender_target` heuristics needed.

## Files to Modify

1. **rendering.py** - Add `ElementDescriptor`, `_descriptor_stack`, update `Element`
2. **base_component.py** - `__call__()` returns descriptor, add `execute()` method
3. **functional_component.py** - Implement `execute()` to call render function
4. **reconcile.py** - Rewrite to reconcile descriptors vs nodes, add props comparison
5. **state.py** - Simplify `__new__()`, remove `_rerender_target`

## Implementation Order

1. Add `ElementDescriptor` type with `__enter__/__exit__/__call__` (additive)
2. Add `freeze_props`/`unfreeze_props` helpers
3. Update `Component.__call__()` to return descriptors
4. Add `Component.execute()` method
5. Add `descriptor` field to `Element`
6. Rewrite `RenderContext.render()` with reconcile-then-execute flow
7. Update reconciler to compare descriptors
8. Simplify `Stateful.__new__()`
9. Update tests

## Benefits

- **Performance**: Skip execution when props unchanged
- **Simpler state**: No `_rerender_target` heuristics
- **Cleaner mental model**: Describe vs Execute separation
- **Composable containers**: Nest arbitrarily, mount at leaves
- **Future-proof**: Foundation for async/concurrent rendering
