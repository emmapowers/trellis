"""Trellis configuration for widget showcase."""

from pathlib import Path

from trellis.app.config import Config

config = Config(
    name="Widget Showcase",
    module="widget_showcase.app",
    icon=Path("assets/icon.png"),
)
