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
- code comments should document the code that as it is. Do not leave comments saying what has changed. Make sure existing comments are updated when code associated with them changes.
- prefer normal attribute access over `object.__getattribute__`/`object.__setattr__`. If a class owns an attribute, declare it on the class and initialize it in the constructor. Only use `object.__getattribute__`/`object.__setattr__` when working around framework limitations (e.g. `@dataclass` not calling `super().__init__`) or truly dynamic attribute access.
- Declare all owned instance attributes in the class body with type annotations.
- Initialize instance state in `__init__`, unless the class is intentionally using `@dataclass`.
- Use `ClassVar[...]` only for true class-level data, not per-instance defaults.
- Avoid class-body mutable instance defaults in plain classes.
- Use `state_var()` for simple component-local state such as 1-2 independent values. Keep `Stateful` classes for structured, multi-field, shared, or behavior-heavy state.

### Import Style

Canonical import style for Trellis applications:

```python
from trellis import App, component, Stateful
from trellis import widgets as w
from trellis import html as h
```

- `trellis` exports core primitives (`component`, `Stateful`, `RenderSession`, etc.) plus `App`
- Import state helpers like `state_var`, `on_mount`, and `load` directly from `trellis` when needed
- Widgets are accessed via `w.Button`, `w.Label`, `w.Column`, etc.
- HTML elements are accessed via `h.Div`, `h.Span`, `h.P`, etc.

## Commands

Run project tools through `uv run` unless you have confirmed the binary is already on PATH. Prefer `uv run just ci`, `uv run trellis ...`, `uv run ruff ...`, etc.

- `just cleanup` - Format and lint with auto-fix
- `just lint` - Check all linters (no fix)
- `just typecheck` - Check for type errors
- `just test` - Run tests
- `just ci` - Full CI checks
- `just showcase` - Run widget showcase
- `trellis bundle` - Build platform bundles (server + desktop)
- `trellis bundle --force-build` - Force rebuild even if sources unchanged
- `trellis bundle --platform server` - Build only server bundle

## Git Workflow

Run `just ci` before committing to catch formatting, lint, and type errors.

## Dependencies

- **pyproject.toml**: Runtime dependencies (shipped with pip package) and dev dependency groups
- **justfile**: Task runner recipes (uses `uv run` to invoke dev tools)

`uv sync --dev` installs everything needed for development, including desktop dependencies (pytauri, pyinstaller).

## UI Testing with Playwright MCP

Use Playwright MCP to test demos and iterate on UI designs.
