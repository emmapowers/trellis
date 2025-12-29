"""Trellis application entry point.

This module provides the Trellis class for creating and running applications,
along with theming infrastructure (ClientState, ThemeProvider, TrellisApp).
"""

from trellis.app.client_state import (
    Browser,
    ClientState,
    DeviceType,
    OperatingSystem,
    ThemeMode,
    ThemeTokens,
    theme,
)
from trellis.app.entry import Trellis
from trellis.app.theme_provider import ThemeProvider
from trellis.app.trellis_app import TrellisApp

__all__ = [
    "Browser",
    "ClientState",
    "DeviceType",
    "OperatingSystem",
    "ThemeMode",
    "ThemeProvider",
    "ThemeTokens",
    "Trellis",
    "TrellisApp",
    "theme",
]
