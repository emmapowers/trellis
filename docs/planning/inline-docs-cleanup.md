# Inline Documentation Cleanup

## Problem

The inline documentation in `src/trellis/core/` has accumulated inconsistencies and outdated terminology that makes it more confusing than helpful:

1. **Outdated terminology**: "descriptor" (should be "Element"), "collection stack" (should be "frame stack")
2. **Inconsistent phase naming**: "Node Phase" vs "Placement Phase", "Render Phase" vs "Execution Phase"
3. **Method name confusion**: Docs reference `render()` but the actual method is `execute()`
4. **Stale attribute names**: `_nodes` referenced but actual attribute is `elements`

## Approach

Rather than patch inconsistent docs, we're removing outdated documentation and preserving only the accurate, well-written docs. This leaves room to write fresh documentation later with consistent terminology.

### Files with good docs (preserve/update)
- `state/stateful.py` - Accurate description of reactive state, dependency tracking, context API
- `state/tracked.py` - Thorough documentation of TrackedList/Dict/Set
- `rendering/frames.py` - Clear documentation of Frame/FrameStack

### Files with outdated docs (remove module docstrings)
- `rendering/element.py` - Incorrect mutability claims, outdated terminology
- `rendering/render.py` - Inconsistent phase naming, wrong method references
- `rendering/session.py` - Minor issues
- `rendering/reconcile.py` - "descriptor" terminology, wrong attribute names
- `components/base.py` - render() vs execute() confusion, "descriptor" terminology
- `components/composition.py` - "descriptor" terminology
- `components/react.py` - Minor issues
- `core/__init__.py` - Incorrect mutability claims
- `rendering/__init__.py` - Incorrect mutability claims

## Terminology Reference

When writing future docs, use these terms:

| Term | Meaning |
|------|---------|
| Element | Tree node representing a component invocation |
| ElementState | Mutable runtime state for an Element (local_state, context, etc.) |
| Component | Factory that creates Elements when called |
| Placement | When a component is called, creating/reusing an Element (`_place()`) |
| Execution | When a component's `execute()` method runs, producing children |
| Frame | Scope that collects child IDs during a `with` block |
| FrameStack | Stack of Frames for nested `with` blocks |

## Status

- [ ] Update good docs (stateful.py, tracked.py, frames.py)
- [ ] Remove outdated docs from rendering modules
- [ ] Remove outdated docs from component modules
- [ ] Remove outdated docs from __init__.py files
