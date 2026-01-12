"""Entry point for the router demo."""

from trellis import Trellis, async_main

from .app import App


@async_main
async def main() -> None:
    """Start the Trellis server."""
    app = Trellis(top=App)
    await app.serve()
