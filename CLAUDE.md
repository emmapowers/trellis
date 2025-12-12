# Trellis

Reactive UI framework for Python with fine-grained state tracking.

## Architecture

`App()` starts a web server hosting static files, a WebSocket endpoint, and a `/` route. When `/` is hit, a render occurs and a page is sent with React and bundled components. The page connects via WebSocket for updates. User actions or server-side I/O trigger re-renders, sending diffs over WebSocket to update the UI.

## Tech Stack

**Python (3.14)**
- FastAPI — Async web framework with WebSocket support
- msgspec — Fast serialization/validation (Pydantic alternative)
- watchfiles — Hot reload during development
- pytest — Testing

**JavaScript/TypeScript**
- esbuild — Fast bundling (pip-installable)
- React — UI framework
- Blueprint — Desktop-first component library (Palantir)
- uPlot — High-performance time-series charts
- Recharts — General-purpose charts
- Vitest — Testing
- Playwright — E2E testing

## Project Structure

```
src/trellis/
├── core/
│   ├── rendering.py         # ElementNode, ElementState, RenderTree
│   ├── reconcile.py         # Tree reconciliation algorithm
│   ├── serialization.py     # ElementNode tree serialization
│   ├── base_component.py    # Component base class
│   ├── functional_component.py  # @component decorator
│   ├── react_component.py   # ReactComponent base for widgets
│   └── state.py             # Stateful base class, automatic dependency tracking
└── utils/
    └── lock_helper.py       # @with_lock decorator
```

## Key Concepts

- **ElementNode**: Immutable tree node representing a component invocation (component, props, key, children, id)
- **ElementState**: Mutable runtime state for an ElementNode, keyed by node.id (dirty flag, local_state, context)
- **RenderTree**: Manages the render lifecycle and node tree; tracks dirty nodes, handles re-rendering
- **Stateful**: Base class for reactive state; properties auto-track which nodes read them
- **FunctionalComponent**: Components created via `@component` decorator that use `with` syntax to collect children

## Commands

- `pixi run cleanup` - Format and lint with auto-fix
- `pixi run lint` - Check all linters (no fix)
- `pixi run test` - Run tests
- `pixi run ci` - Full CI checks
- `pixi run build-client` - Build the TypeScript/React client bundle

## Dependencies

- **pyproject.toml**: Runtime dependencies for trellis (shipped with pip package)
- **pixi.toml**: Dev-only tools (black, ruff, mypy, pytest, nodejs for esbuild)

Since trellis is installed in editable mode, pyproject.toml dependencies are also available in the pixi environment.

## Planning Docs

See `docs/planning/` for API design mockups:
- `api_example.py` - Target developer experience
- `component_tree.py` - Tree data structures
- `react_integration.py` - React/TSX integration concepts
