"""Register trellis-browser module with the bundler registry."""

from pathlib import Path

from trellis.bundler import registry

_CLIENT_SRC = Path(__file__).parent / "client" / "src"

# Register the trellis-browser module
# Browser platform includes a pyodide web worker
registry.register(
    "trellis-browser",
    files=["client/src/**/*.{ts,tsx,css}"],
    worker_entries={"pyodide": "client/src/pyodide.worker.ts"},
    static_files={"index.html": _CLIENT_SRC / "index.html"},
)
