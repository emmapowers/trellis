"""Entry point for standalone packaged Trellis applications.

Invoked by the pytauri standalone binary via PythonScript::Module.
Reads the user's app module from TRELLIS_APP_MODULE environment variable,
discovers the App instance, and starts the desktop runtime.
"""

from __future__ import annotations

import asyncio
import importlib
import os
from typing import Any

from trellis.app.app import App
from trellis.platforms.desktop.standalone_platform import DesktopStandalonePlatform


def _find_app(module_name: str) -> App:
    """Import the user module and find the App instance."""
    mod = importlib.import_module(module_name)
    for name in dir(mod):
        obj = getattr(mod, name)
        if isinstance(obj, App):
            return obj
    raise RuntimeError(
        f"No App instance found in {module_name}. "
        "Your app module must define: app = App(RootComponent)"
    )


def main() -> None:
    module_name = os.environ.get("TRELLIS_APP_MODULE")
    if not module_name:
        raise RuntimeError(
            "TRELLIS_APP_MODULE environment variable not set. "
            "This entry point is meant to be called from a pytauri standalone binary."
        )

    app = _find_app(module_name)
    platform = DesktopStandalonePlatform()

    def app_wrapper(_component: Any, system_theme: str, theme_mode: str | None) -> Any:
        return app.get_wrapped_top(system_theme, theme_mode)

    asyncio.run(platform.run(app.top, app_wrapper))


main()
