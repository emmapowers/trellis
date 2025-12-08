"""Browser runtime for Trellis apps.

This module provides a lightweight runtime that replaces FastAPI/WebSocket
for running Trellis apps entirely in the browser via Pyodide.
"""

from __future__ import annotations

import typing as tp

from trellis.core.rendering import IComponent, RenderContext

__all__ = ["BrowserRuntime"]


def _serialize_value(
    value: tp.Any, callback_registry: dict[str, tp.Callable[..., tp.Any]]
) -> tp.Any:
    """Serialize a single value, handling special cases.

    Args:
        value: The value to serialize
        callback_registry: Dict to store callbacks in (will be mutated)

    Returns:
        A JSON-serializable version of the value
    """
    if callable(value):
        # Generate callback ID and register
        cb_id = f"cb_{len(callback_registry)}"
        callback_registry[cb_id] = value
        return {"__callback__": cb_id}
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v, callback_registry) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v, callback_registry) for k, v in value.items()}
    # For other types, convert to string
    return str(value)


def _serialize_element(
    element: tp.Any,  # Element type, but avoid import cycle
    callback_registry: dict[str, tp.Callable[..., tp.Any]],
) -> dict[str, tp.Any]:
    """Convert an Element tree to a serializable dict.

    Similar to trellis.core.serialization.serialize_element, but uses
    instance-local callback registry instead of global.

    Args:
        element: The Element to serialize
        callback_registry: Dict to store callbacks in (will be mutated)

    Returns:
        A dict suitable for JSON encoding
    """
    # Serialize props, excluding children (handled separately)
    props: dict[str, tp.Any] = {}
    for key, value in element.properties.items():
        if key == "children":
            continue  # Children are serialized separately
        props[key] = _serialize_value(value, callback_registry)

    return {
        "type": element.component.react_type,  # React component to use
        "name": element.component.name,  # Python component name for debugging
        "key": element.key or None,
        "props": props,
        "children": [_serialize_element(child, callback_registry) for child in element.children],
    }


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
        callback_registry: Maps callback IDs to Python callables
    """

    context: RenderContext
    root_component: IComponent
    callback_registry: dict[str, tp.Callable[..., tp.Any]]

    def __init__(self, root_component: IComponent) -> None:
        """Create a new browser runtime for a component.

        Args:
            root_component: The root Trellis component to render
        """
        self.root_component = root_component
        self.context = RenderContext(root_component)
        self.callback_registry = {}

    def render(self) -> dict[str, tp.Any]:
        """Render and return the serialized element tree.

        On first call, performs initial render. On subsequent calls,
        re-renders any dirty elements.

        Returns:
            Serialized element tree as a dict, suitable for JSON encoding.
            Callbacks are replaced with {"__callback__": "cb_N"} references.
        """
        # Clear old callbacks
        self.callback_registry.clear()

        # Render (initial or dirty)
        if self.context.root_element is None:
            self.context.render(from_element=None)
        else:
            self.context.render_dirty()

        # Serialize and return
        assert self.context.root_element is not None
        return _serialize_element(self.context.root_element, self.callback_registry)

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

        callback = self.callback_registry.get(callback_id)
        if callback is None:
            raise KeyError(f"Callback not found: {callback_id}")

        # Invoke the callback
        callback(*args)

        # Re-render and return updated tree
        return self.render()

    def get_callback_ids(self) -> list[str]:
        """Get all registered callback IDs.

        Useful for debugging.

        Returns:
            List of callback ID strings
        """
        return list(self.callback_registry.keys())
