# Trellis Known Issues

## Context changes don't trigger re-renders of consuming components

**Symptom:** A parent provides a `Stateful` via `with state:` and later provides a *different*
instance (e.g. after switching which item is selected). Child components that called
`from_context()` continue rendering stale data.

**Root cause:** Two things combine:

1. **`from_context()` doesn't register reactive subscriptions.** It walks the parent chain and
   returns the value but never adds the consuming element to any watcher set. When the provided
   instance changes, no downstream consumer is marked dirty.

2. **The `_place()` reuse optimization skips re-execution.** When a parent re-renders and places
   a child with identical props, `_place()` returns the old element object. `_execute_tree` then
   sees `element is old_element` and skips the child entirely. Since the child never re-executes,
   it never calls `from_context()` again.

**Workaround:** Pass the context value (or a lightweight key like an ID) as a prop so the reuse
check fails when the context changes:

```python
# Broken — Child is reused and never sees the new state:
with new_state:
    Child()

# Works — prop change forces re-execution:
with new_state:
    Child(state=new_state)
```
