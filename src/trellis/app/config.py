"""Configuration dataclass for Trellis applications."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for a Trellis application.

    Access via get_app().config after the app is loaded:

        from trellis.app import get_app

        config = get_app().config
        print(config.name, config.module)

    Attributes:
        name: Application name (used for window title, build artifacts, etc.)
        module: Python module path containing the entry point
    """

    name: str
    module: str
