"""Simple example of starting a Trellis server."""

from trellis import App
from trellis.utils import async_main, setup_logging


@async_main
async def main() -> None:
    setup_logging()
    app = App(port=8080)
    await app.serve()
