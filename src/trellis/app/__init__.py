"""Trellis application entry point.

This module provides the Trellis class for creating and running applications,
along with theming infrastructure (ClientState, ThemeProvider, TrellisApp).
"""

from trellis.app.app import App
from trellis.app.apploader import (
    AppLoader,
    find_app_path,
    get_app,
    get_app_root,
    get_apploader,
    get_config,
    resolve_app_root,
    set_apploader,
)
from trellis.app.client_state import (
    ClientState,
    ThemeMode,
    ThemeTokens,
    theme,
)
from trellis.app.config import Config
from trellis.app.entry import Trellis
from trellis.app.theme_provider import ThemeProvider
from trellis.app.trellis_app import TrellisApp

__all__ = [
    "App",
    "AppLoader",
    "ClientState",
    "Config",
    "ThemeMode",
    "ThemeProvider",
    "ThemeTokens",
    "Trellis",
    "TrellisApp",
    "find_app_path",
    "get_app",
    "get_app_root",
    "get_apploader",
    "get_config",
    "resolve_app_root",
    "set_apploader",
    "theme",
]
