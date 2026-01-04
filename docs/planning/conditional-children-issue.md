# Conditional Children Issue

## The Problem

Conditional containers (like Route) don't work correctly with the `with` children pattern.

## Minimal Example

```python
@component
def ConditionalContainer(*, show: bool, children: list[Element] | None = None) -> None:
    """Only renders children when show=True."""
    if show and children:
        for child in children:
            child()

@component
def App() -> None:
    with ConditionalContainer(show=state.visible):
        ExpensiveChild()
```

## What Happens

### Render 1: `show=True`
1. `with ConditionalContainer(show=True):` - container created
2. `ExpensiveChild()` - child element created, added to container's collected children
3. ConditionalContainer.__exit__ → `child_ids = [ExpensiveChild_id]`
4. ConditionalContainer.execute() - show=True, calls `child()` on ExpensiveChild
5. Frame has ExpensiveChild → `node.child_ids = [ExpensiveChild_id]` ✓
6. ExpensiveChild executes ✓

### Render 2: `show=False`
1. ConditionalContainer.execute() - show=False, does NOT call `child()`
2. Frame is empty → **`node.child_ids = []`** ← children lost!
3. Reconciliation removes ExpensiveChild

### Render 3: `show=True` again
1. ConditionalContainer is dirty, re-renders
2. New node created with `child_ids = list(old_node.child_ids)`
3. But `old_node.child_ids = []` from render 2
4. **ConditionalContainer has no children!** ✗

## Root Cause

In `_execute_single_node` (render.py:207-209):
```python
new_child_ids = list(frame.child_ids)  # What was RENDERED
node.child_ids = new_child_ids          # Overwrites COLLECTED children
```

`child_ids` serves two purposes that conflict:
1. **Collected children** - what was inside the `with` block
2. **Rendered children** - what was actually output

When a container doesn't render its children, the collected children are lost.

## Why `content=` Pattern Works

```python
Route(pattern="/", content=HomePage)
```

- Route doesn't store children
- Route calls `content()` each execute, creating fresh children
- No state about children carried between renders

## Potential Fixes

1. **Separate collected vs rendered children** - store both
2. **Don't update child_ids for conditional containers** - needs a flag
3. **Re-execute parent when child container is dirty** - expensive
4. **Use callable pattern** - `content=` or `render=lambda: ...`

## Recommendation

For now, conditional containers should use the callable pattern (`content=`) rather than the `children` pattern. The `children` pattern works for containers that always render all children (like Div, Row, Column).
