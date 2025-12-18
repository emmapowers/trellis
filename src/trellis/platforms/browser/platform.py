"""Browser platform implementation for Pyodide.

This platform runs inside Pyodide in the browser, using a JS bridge for messaging.
For the CLI server that serves browser apps, see serve_platform.py.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from trellis.core.platform import Platform

__all__ = ["BrowserPlatform"]


class BrowserPlatform(Platform):
    """Browser platform running inside Pyodide.

    Uses the trellis_browser_bridge JS module (registered by TrellisApp)
    for communication between Python and JavaScript.
    """

    @property
    def name(self) -> str:
        return "browser"

    def bundle(
        self,
        force: bool = False,
        extra_packages: dict[str, str] | None = None,
    ) -> None:
        """No-op in Pyodide - bundling is done before loading.

        The bundle is already built and served by the time this platform runs.
        """
        pass

    async def run(
        self,
        root_component: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        """Run inside Pyodide using the JS bridge.

        The bridge is registered by TrellisApp before executing Python code.
        """
        # Import the bridge module (registered by JavaScript)
        import js  # type: ignore[import-not-found]
        import trellis_browser_bridge as bridge  # type: ignore[import-not-found]
        from pyodide.ffi import create_proxy, to_js  # type: ignore[import-not-found]

        from trellis.platforms.browser.handler import BrowserMessageHandler

        # Pyodide serializer: convert Python dict to JS object
        def pyodide_serializer(msg_dict: dict[str, Any]) -> Any:
            return to_js(msg_dict, dict_converter=js.Object.fromEntries)

        # Create handler and connect to bridge
        # root_component is typed as Callable but is actually IComponent at runtime
        handler = BrowserMessageHandler(root_component)  # type: ignore[arg-type]
        handler.set_send_callback(bridge.send_message, serializer=pyodide_serializer)

        # Create a persistent proxy for the handler so JavaScript can keep a reference
        # Without this, Pyodide would destroy the borrowed proxy after set_handler returns
        handler_proxy = create_proxy(handler)
        bridge.set_handler(handler_proxy)

        # Run the message loop
        await handler.run()
