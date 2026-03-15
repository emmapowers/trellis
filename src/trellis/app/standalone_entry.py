"""Entry point for standalone packaged Trellis applications.

Invoked by the pytauri standalone binary via PythonScript::Module.
Uses AppLoader to discover trellis_config.py (via TRELLIS_APP_ROOT)
and load the app with full configuration support.
"""

from __future__ import annotations

import asyncio
from typing import Any

from trellis.app.apploader import AppLoader, resolve_app_root, set_apploader
from trellis.platforms.common.base import PlatformType


def main() -> None:
    app_root = resolve_app_root()
    apploader = AppLoader(app_root)
    apploader.load_config()
    set_apploader(apploader)

    config = apploader.config
    assert config is not None

    # The packaged binary is always a desktop app regardless of what
    # trellis_config.py says (the user may have packaged with --platform desktop
    # while the config defaults to server).
    config.platform = PlatformType.DESKTOP

    apploader.load_app()

    app = apploader.app
    assert app is not None

    run_kwargs: dict[str, Any] = {
        "batch_delay": config.batch_delay,
        "hot_reload": False,
        "window_title": config.title,
    }
    if config.window_size != "maximized":
        parts = config.window_size.split("x")
        run_kwargs["window_width"] = int(parts[0])
        run_kwargs["window_height"] = int(parts[1])

    def app_wrapper(_component: Any, system_theme: str, theme_mode: str | None) -> Any:
        return app.get_wrapped_top(system_theme, theme_mode)

    asyncio.run(apploader.platform.run(app.top, app_wrapper, **run_kwargs))


main()
