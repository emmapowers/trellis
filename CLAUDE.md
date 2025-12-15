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

## Import Style

Canonical import style for Trellis applications:

```python
from trellis import Trellis, async_main, component, Stateful
from trellis import widgets as w
from trellis import html as h
```

- `trellis` exports core primitives (`component`, `Stateful`, `RenderTree`, etc.) plus `async_main` and `Trellis`
- Widgets are accessed via `w.Button`, `w.Label`, `w.Column`, etc.
- HTML elements are accessed via `h.Div`, `h.Span`, `h.P`, etc.

## Commands

- `pixi run cleanup` - Format and lint with auto-fix
- `pixi run lint` - Check all linters (no fix)
- `pixi run mypy` - Check for type errors
- `pixi run test` - Run tests
- `pixi run ci` - Full CI checks
- to build the client bundle run example/demo.py - Trellis builds the bundle on startup. If the demo comes up the bundle built.

## Dependencies

- **pyproject.toml**: Runtime dependencies for trellis (shipped with pip package)
- **pixi.toml**: Dev-only tools (black, ruff, mypy, pytest, nodejs for esbuild)

Since trellis is installed in editable mode, pyproject.toml dependencies are also available in the pixi environment.

## Documentation and Usage

- **docs/docs/** for usage and design docs
- **examples/** for examples

## UI Testing with Playwright MCP

Use Playwright MCP to test demos and iterate on UI designs.

**Workflow:**
1. Start the demo server in background: `pixi run demo`
2. Navigate: `browser_navigate` to `http://127.0.0.1:8004`
3. Inspect: `browser_snapshot` for element tree with refs for interaction
4. Interact: `browser_click`, `browser_type` etc. using element refs
5. Screenshot: `browser_take_screenshot` saves to `.playwright-mcp/`
6. View: `open .playwright-mcp/<filename>.png` to open in Preview

**When working on designs:** Use `browser_take_screenshot` to see what users see visually, not just accessibility snapshots. Screenshots capture styling, layout, and visual hierarchy that snapshots miss.

## Frontend-Backend Communication

When implementing communication between frontend (TypeScript/JavaScript) and backend (Python):
- **Always use the existing message passing framework** with serialized Message objects
- **Never use direct function calls** (e.g., individual pyInvoke calls per action)
- The client should construct the same message types used by other platforms
- New platforms implement transport, not new message protocols
