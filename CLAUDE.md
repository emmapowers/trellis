# Trellis

Reactive UI framework for Python with fine-grained state tracking.

## Project Structure

```
src/trellis/
├── core/
│   ├── rendering.py         # Element, RenderContext, Elements type
│   ├── base_component.py    # Component base class
│   ├── functional_component.py  # @component decorator
│   ├── block_component.py   # @blockComponent decorator (context manager)
│   └── state.py             # Stateful base class, automatic dependency tracking
└── util/
    └── lock_helper.py       # @with_lock decorator
```

## Key Concepts

- **Element**: Node in the component tree with component reference, properties, children, parent, depth
- **RenderContext**: Manages the element tree, tracks dirty elements, handles re-rendering
- **Stateful**: Base class for reactive state; properties auto-track which elements read them
- **BlockComponent**: Components that use `with` syntax to collect children

## Commands

- `pixi run cleanup` - Format and lint with auto-fix
- `pixi run lint` - Check all linters (no fix)
- `pixi run test` - Run tests
- `pixi run ci` - Full CI checks

## Planning Docs

See `docs/planning/` for API design mockups:
- `api_example.py` - Target developer experience
- `component_tree.py` - Tree data structures
- `react_integration.py` - React/TSX integration concepts
