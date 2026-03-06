"""Trellis application entry point.

This module provides application and runtime theme-mode infrastructure.
"""

from trellis.app.app import App
from trellis.app.apploader import (
    AppLoader,
    find_app_path,
    get_app,
    get_app_root,
    get_apploader,
    get_config,
    get_dist_dir,
    get_workspace_dir,
    resolve_app_root,
    set_apploader,
)
from trellis.app.client_state import (
    ClientState,
    ThemeMode,
)
from trellis.app.config import Config
from trellis.app.theme_provider import ThemeProvider
from trellis.app.trellis_app import TrellisApp

__all__ = [
    "App",
    "AppLoader",
    "ClientState",
    "Config",
    "ThemeMode",
    "ThemeProvider",
    "TrellisApp",
    "find_app_path",
    "get_app",
    "get_app_root",
    "get_apploader",
    "get_config",
    "get_dist_dir",
    "get_workspace_dir",
    "resolve_app_root",
    "set_apploader",
]
