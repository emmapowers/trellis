# Trellis

Reactive UI framework for Python with fine-grained state tracking.

## Architecture

`App()` starts a web server hosting static files, a WebSocket endpoint, and a `/` route. When `/` is hit, a render occurs and a page is sent with React and bundled components. The page connects via WebSocket for updates. User actions or server-side I/O trigger re-renders, sending diffs over WebSocket to update the UI.

### Tech Stack

**Python (3.13)**
- FastAPI — Async web framework with WebSocket support
- pytest — Testing

**JavaScript/TypeScript**
- bun - javascript runtime, package installation
- esbuild — Fast bundling
- React — UI framework
- Vitest — Testing
- Playwright — E2E testing

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

## Key Concepts

- **Element**: Tree node representing a component invocation (component, props, key, children, id)
- **ElementState**: Mutable runtime state for an Element, keyed by element.id (dirty flag, local_state, context)
- **RenderSession**: Manages the render lifecycle and element tree; tracks dirty elements, handles re-rendering
- **Stateful**: Base class for reactive state; properties auto-track which elements read them

## Style

- this project is in early development. All are backwards incompatible breaking changes unless specifically requested by the user. No shims, aliases, or compatability code.
- snake_case variables, functions, modules, variables, etc...
- PascalCase objects
- MyEnum.UPPER_CASE enums
- use absolute imports
- place imports at the top of the file unless there is a compelling reason not to. Imports mid file add complexity, so avoid them unless they are really needed, and add a comment to explain why.
- When writing tests, use pytest style instead of xunit. Organizing related tests into classes is fine, but use fixtures for shared code instead of class members and inheritance. Look for oportunities to re-factor common test code into fixtures. Check relevant conftest.py to see if there are useful fixtures already.

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

## Dependencies

- **pyproject.toml**: Runtime dependencies for trellis (shipped with pip package)
- **pixi.toml**: Dev-only tools (black, ruff, mypy, pytest, nodejs for esbuild)

Since trellis is installed in editable mode, pyproject.toml dependencies are also available in the pixi environment.

## Documentation and Usage

- **docs/reference/** for API and best practice reference
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
