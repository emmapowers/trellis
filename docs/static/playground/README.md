# Trellis Playground

A browser-based playground for experimenting with Trellis UI components using Pyodide.

## Running Locally

```bash
# 1. Build the wheel
pixi run build

# 2. Start the server
pixi run playground
```

Then open http://localhost:8000/playground/ in your browser.

## How It Works

1. **Pyodide 0.29** runs Python 3.13 in WebAssembly
2. **Monaco Editor** provides VS Code-like editing experience
3. **React** renders the Trellis component tree
4. Trellis is installed from a wheel via micropip

## Limitations

- **Python 3.13**: Pyodide 0.29 uses Python 3.13. Trellis targets Python 3.14, but most features work.
- **No hot reload**: After editing code, click "Run" (or Ctrl/Cmd+Enter) to re-render.

## Known Issues

- First load takes a few seconds while Pyodide and dependencies are downloaded (~15MB)
