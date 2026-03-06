"""Shadcn-backed design system assets."""

from __future__ import annotations

from pathlib import Path

from trellis.registry import ExportKind, registry
from trellis.widgets.dependencies import WIDGET_CLIENT_PACKAGES

THEME_CSS_SOURCE = Path(__file__).parent.resolve() / "client" / "index.css"
THEME_CSS_IMPORT = "@trellis/trellis-theme/theme.css"

registry.register(
    "trellis-theme",
    packages=WIDGET_CLIENT_PACKAGES,
    exports=[("styles", ExportKind.STYLESHEET, "theme.css")],
)

__all__ = ["THEME_CSS_IMPORT", "THEME_CSS_SOURCE"]
