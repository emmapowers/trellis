"""Helper script to start a minimal Trellis server for e2e testing.

Usage: python _run_test_server.py <host> <port>
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path
from typing import Any

from trellis.app.app import App
from trellis.app.apploader import AppLoader, set_apploader
from trellis.app.config import Config
from trellis.core.components.composition import component
from trellis.platforms.server.platform import ServerPlatform
from trellis.widgets import Label


@component
def test_app() -> None:
    Label(text="Hello from SSR")


def main() -> None:
    host = sys.argv[1]
    port = int(sys.argv[2])

    # Use a temp directory as the app root so workspace/dist dirs can be created
    app_root = Path(tempfile.mkdtemp(prefix="trellis-e2e-"))

    config = Config(name="ssr-e2e-test", module="__main__")
    loader = AppLoader(path=app_root)
    loader.config = config
    set_apploader(loader)

    # Build the client bundle via the standard pipeline
    asyncio.run(loader.bundle())

    # Create app wrapper using the real App infrastructure
    app_instance = App(test_app)

    def app_wrapper(_component: Any, system_theme: str, theme_mode: str | None) -> Any:
        return app_instance.get_wrapped_top(system_theme, theme_mode)

    asyncio.run(
        ServerPlatform().run(
            test_app,
            app_wrapper,
            host=host,
            port=port,
            hot_reload=False,
            ssr=True,
        )
    )


if __name__ == "__main__":
    main()
