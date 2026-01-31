"""Browser platform implementation for Pyodide.

This platform runs inside Pyodide in the browser, using a JS bridge for messaging.
For the CLI server that serves browser apps, see serve_platform.py.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from trellis.core.rendering.element import Element
    from trellis.platforms.common.handler import AppWrapper

from trellis.platforms.browser.handler import BrowserMessageHandler
from trellis.platforms.common.base import Platform

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
        dest: Path | None = None,
        library: bool = False,
        assets_dir: Path | None = None,
    ) -> Path:
        """No-op in Pyodide - bundling is done before loading.

        The bundle is already built and served by the time this platform runs.
        Returns a placeholder path since no actual workspace is used.
        """
        return Path(".")

    async def run(
        self,
        root_component: Callable[[], Element],
        app_wrapper: AppWrapper,
        *,
        batch_delay: float = 1.0 / 30,
        **kwargs: Any,
    ) -> None:
        """Run inside Pyodide using the JS bridge.

        The bridge is registered by TrellisApp before executing Python code.

        Args:
            root_component: The root Trellis component to render
            app_wrapper: Callback to wrap component with TrellisApp
            batch_delay: Time between render frames in seconds (default ~33ms for 30fps)
        """
        # Pyodide-only imports - these modules only exist inside the Pyodide runtime
        import js  # type: ignore[import-not-found]  # noqa: PLC0415
        import trellis_browser_bridge as bridge  # type: ignore[import-not-found]  # noqa: PLC0415
        from pyodide.ffi import (  # type: ignore[import-not-found]  # noqa: PLC0415
            create_proxy,
            to_js,
        )

        # Pyodide serializer: convert Python dict to JS object
        def pyodide_serializer(msg_dict: dict[str, Any]) -> Any:
            return to_js(msg_dict, dict_converter=js.Object.fromEntries)

        # Create handler and connect to bridge
        # root_component is typed as Callable but is actually Component at runtime
        handler = BrowserMessageHandler(root_component, app_wrapper, batch_delay=batch_delay)  # type: ignore[arg-type]
        handler.set_send_callback(bridge.send_message, serializer=pyodide_serializer)

        # Create a persistent proxy for the handler so JavaScript can keep a reference
        # Without this, Pyodide would destroy the borrowed proxy after set_handler returns
        handler_proxy = create_proxy(handler)
        bridge.set_handler(handler_proxy)

        # Run the message loop
        await handler.run()
