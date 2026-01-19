"""Browser platform - runs Python in browser via Pyodide.

This platform has two execution paths:
1. CLI mode (python app.py --browser): Build and serve static files
2. Pyodide mode (running inside browser): Use JS bridge for messaging

Usage:
    # From command line - builds and serves for testing
    python examples/demo.py --browser

    # Inside Pyodide - runs via JS bridge (handled automatically)
    # TrellisApp registers the bridge, then executes user code
"""

from pathlib import Path

from trellis.bundler import registry
from trellis.platforms.browser.handler import BrowserMessageHandler
from trellis.platforms.browser.platform import BrowserPlatform

_CLIENT_SRC = Path(__file__).parent / "client" / "src"

# Register the trellis-browser module
registry.register(
    "trellis-browser",
    static_files={"index.html": _CLIENT_SRC / "index.html"},
)

__all__ = ["BrowserMessageHandler", "BrowserPlatform"]
