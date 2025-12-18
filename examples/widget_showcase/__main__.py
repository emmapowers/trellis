"""Entry point for the widget showcase.

Run with: pixi run -- python -m examples.widget_showcase
Or: pixi run -- python examples/widget_showcase
"""

from trellis import Trellis, async_main

from .app import App


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App)
    await app.serve()
