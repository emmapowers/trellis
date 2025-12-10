"""Browser runtime for Trellis apps.

This module provides a lightweight runtime that replaces FastAPI/WebSocket
for running Trellis apps entirely in the browser via Pyodide.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering import IComponent, RenderContext

__all__ = ["BrowserRuntime"]


class BrowserRuntime:
    """Runs Trellis apps without FastAPI/WebSocket.

    This is a lightweight adapter that wraps RenderContext and provides
    a simple API for JavaScript to interact with.

    Example usage from JavaScript (via Pyodide):
        ```javascript
        const runtime = pyodide.runPython(`
            from trellis_playground import BrowserRuntime
            from my_app import App
            BrowserRuntime(App)
        `);

        // Get initial render
        const tree = runtime.render().toJs();
        renderTree(tree);

        // Handle user event
        const updatedTree = runtime.handle_event("cb_0", []).toJs();
        renderTree(updatedTree);
        ```

    Attributes:
        context: The underlying RenderContext
        root_component: The root component being rendered
    """

    context: RenderContext
    root_component: IComponent

    def __init__(self, root_component: IComponent) -> None:
        """Create a new browser runtime for a component.

        Args:
            root_component: The root Trellis component to render
        """
        self.root_component = root_component
        self.context = RenderContext(root_component)

    def render(self) -> dict[str, tp.Any]:
        """Render and return the serialized element tree.

        On first call, performs initial render. On subsequent calls,
        re-renders any dirty elements.

        Returns:
            Serialized element tree as a dict, suitable for JSON encoding.
            Callbacks are replaced with {"__callback__": "cb_N"} references.
        """
        return self.context.render()

    def handle_event(self, callback_id: str, args: list[tp.Any] | None = None) -> dict[str, tp.Any]:
        """Handle a user event by invoking a callback and re-rendering.

        Args:
            callback_id: The callback ID (e.g., "cb_0")
            args: Arguments to pass to the callback

        Returns:
            Updated serialized element tree

        Raises:
            KeyError: If callback_id is not found
        """
        if args is None:
            args = []

        callback = self.context.get_callback(callback_id)
        if callback is None:
            raise KeyError(f"Callback not found: {callback_id}")

        callback(*args)
        return self.render()
