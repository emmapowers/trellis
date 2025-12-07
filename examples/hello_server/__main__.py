"""Simple example of starting a Trellis server."""

from trellis import Trellis
from trellis.utils import async_main, setup_logging


@async_main
async def main() -> None:
    setup_logging()
    app = Trellis()
    await app.serve()
