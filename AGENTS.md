# Trellis

Reactive UI framework for Python with fine-grained state tracking.

## How Trellis Works

Trellis is a fine-grained reactive framework: **Stateful** objects auto-track which components read their properties and trigger re-renders on change. Components build an **Element** tree (each Element represents a component invocation), while **ElementState** holds mutable runtime state per element. **RenderSession** coordinates renders and emits patches to the frontend.

**Render flow:**
1. User action or server I/O marks elements dirty via `session.dirty.mark(element_id)`
2. RenderSession pops dirty elements, re-executes them depth-first
3. Reconciliation compares old/new children, emits Add/Update/Remove patches
4. Patches sent to frontend (React) via WebSocket

**Reactivity:**
- Reading `state.property` during render registers the current element as a watcher
- Writing `state.property` (outside render) marks all watchers dirty → next render re-executes them
- WeakSets auto-cleanup dead element references

**Component model:**
- `@component` decorator wraps a render function as a `CompositionComponent`
- Container components use `with` blocks to collect children
- State is cached per-element via `ElementState.local_state` (like React hooks)

## Project Structure

```
src/trellis/
├── core/           # Rendering engine, state tracking, component system
├── app/            # Application entry point, theme provider
├── bundler/        # esbuild bundling, package management, workspace generation
├── html/           # HTML element components (Div, Span, etc.)
├── widgets/        # UI components (Button, Table, Charts, etc.)
├── routing/        # Client-side routing
├── platforms/      # Platform implementations
│   ├── common/     # Shared message handling, client TypeScript
│   ├── server/     # FastAPI WebSocket server
│   ├── browser/    # Pyodide/WebAssembly runtime
│   └── desktop/    # Tauri desktop app
└── utils/          # Logging, hot reload, helpers
```

## Style

- this project is in early development. All are backwards incompatible breaking changes unless specifically requested by the user. No shims, aliases, or compatability code.
- snake_case variables, functions, modules, variables, etc...
- PascalCase objects
- MyEnum.UPPER_CASE enums
- use absolute imports
- place imports at the top of the file unless there is a compelling reason not to. Imports mid file add complexity, so avoid them unless they are really needed, and add a comment to explain why.
- When writing tests, use pytest style instead of xunit. Organizing related tests into classes is fine, but use fixtures for shared code instead of class members and inheritance. Look for opportunities to re-factor common test code into fixtures. Check relevant conftest.py to see if there are useful fixtures already.
 You may use test classes to group related tests, but they are not required and should only be used when they make large test files more readable.
- use the test-driven development skill when making changes

### Import Style

Canonical import style for Trellis applications:

```python
from trellis import Trellis, async_main, component, Stateful
from trellis import widgets as w
from trellis import html as h
```

- `trellis` exports core primitives (`component`, `Stateful`, `RenderSession`, etc.) plus `async_main` and `Trellis`
- Widgets are accessed via `w.Button`, `w.Label`, `w.Column`, etc.
- HTML elements are accessed via `h.Div`, `h.Span`, `h.P`, etc.

## Commands

- `pixi run cleanup` - Format and lint with auto-fix
- `pixi run lint` - Check all linters (no fix)
- `pixi run mypy` - Check for type errors
- `pixi run test` - Run tests
- `pixi run ci` - Full CI checks
- `pixi run showcase` - Run widget showcase
- `trellis bundle build` - Build platform bundles (server + desktop)
- `trellis bundle build --force` - Force rebuild even if sources unchanged
- `trellis bundle build --platform server` - Build only server bundle

## Git Workflow

Run `pixi run ci` before committing to catch formatting, lint, and type errors.

## Dependencies

- **pyproject.toml**: Runtime dependencies for trellis (shipped with pip package)
- **pixi.toml**: Dev-only tools (black, ruff, mypy, pytest, nodejs for esbuild)

Since trellis is installed in editable mode, pyproject.toml dependencies are also available in the pixi environment.

## UI Testing with Playwright MCP

Use Playwright MCP to test demos and iterate on UI designs.
