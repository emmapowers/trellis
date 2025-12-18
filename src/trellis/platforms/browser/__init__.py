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

from trellis.platforms.browser.handler import BrowserMessageHandler
from trellis.platforms.browser.platform import BrowserPlatform

__all__ = ["BrowserMessageHandler", "BrowserPlatform"]
