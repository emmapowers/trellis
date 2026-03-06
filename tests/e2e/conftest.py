"""E2E test fixtures — starts a Trellis server and provides Playwright pages."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path

import pytest
from playwright.sync_api import Page

from trellis.app import AppLoader, set_apploader
from trellis.platforms.common import find_available_port

SHOWCASE_ROOT = Path(__file__).resolve().parents[2] / "examples" / "widget_showcase"


def _run_server(app_root: Path, host: str, port: int, ready: threading.Event) -> None:
    """Run a Trellis server in a background thread."""

    async def _serve() -> None:
        apploader = AppLoader(app_root)
        apploader.load_config()
        apploader.load_app()
        set_apploader(apploader)

        app = apploader.app
        assert app is not None

        def app_wrapper(_component: object, system_theme: str, theme_mode: str | None) -> object:
            return app.get_wrapped_top(system_theme, theme_mode)

        platform = apploader.platform

        from trellis.platforms.server.platform import ServerPlatform  # noqa: PLC0415

        assert isinstance(platform, ServerPlatform)

        # Signal that the server is about to start listening
        import uvicorn  # noqa: PLC0415
        from fastapi import FastAPI  # noqa: PLC0415
        from fastapi.staticfiles import StaticFiles  # noqa: PLC0415

        from trellis.platforms.server.handler import router as ws_router  # noqa: PLC0415
        from trellis.platforms.server.routes import (  # noqa: PLC0415
            create_static_dir,
            register_spa_fallback,
        )
        from trellis.platforms.server.routes import (  # noqa: PLC0415
            router as http_router,
        )

        fastapi_app = FastAPI()
        fastapi_app.include_router(http_router)
        fastapi_app.include_router(ws_router)
        fastapi_app.state.trellis_top_component = app.top
        fastapi_app.state.trellis_app_wrapper = app_wrapper
        fastapi_app.state.trellis_batch_delay = 1.0 / 30

        static = create_static_dir()
        if static.exists():
            fastapi_app.mount("/static", StaticFiles(directory=static), name="static")
        register_spa_fallback(fastapi_app)

        config = uvicorn.Config(
            fastapi_app, host=host, port=port, log_config=None, log_level="warning"
        )
        server = uvicorn.Server(config)

        # Mark ready once the server is started
        original_startup = server.startup

        async def startup_with_signal(*args: object, **kwargs: object) -> None:
            await original_startup(*args, **kwargs)
            ready.set()

        server.startup = startup_with_signal  # type: ignore[assignment]
        await server.serve()

    asyncio.run(_serve())


@pytest.fixture(scope="session")
def showcase_url() -> str:
    """Start the widget showcase server and yield its URL."""
    host = "127.0.0.1"
    port = find_available_port(host=host)
    ready = threading.Event()

    thread = threading.Thread(
        target=_run_server, args=(SHOWCASE_ROOT, host, port, ready), daemon=True
    )
    thread.start()

    if not ready.wait(timeout=30):
        raise RuntimeError("Showcase server did not start within 30 seconds")

    return f"http://{host}:{port}"


@pytest.fixture
def keyboard_page(page: Page, showcase_url: str) -> Page:
    """Navigate to the keyboard section of the showcase."""
    page.goto(f"{showcase_url}/keyboard")
    # Wait for the showcase to render the keyboard section
    page.wait_for_selector("text=Focus-scoped", timeout=10000)
    return page
