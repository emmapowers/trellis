"""Platform implementations for Trellis.

Each platform provides a transport layer for Trellis applications:

- server: FastAPI + WebSocket (default)
- desktop: PyTorii IPC
- browser: Pyodide function calls

Platforms are selected via the Trellis class or CLI arguments.
"""

# Platform modules are imported on demand in trellis.app.entry._get_platform()
# to avoid loading unnecessary dependencies

__all__: list[str] = []
