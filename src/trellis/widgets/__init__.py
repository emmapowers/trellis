"""Shadcn-backed Trellis widgets."""

from __future__ import annotations

from pathlib import Path

import trellis.theme  # noqa: F401
from trellis.registry import registry
from trellis.widgets.button import Button
from trellis.widgets.dependencies import WIDGET_CLIENT_PACKAGES

registry.register(
    "trellis-widgets",
    packages=WIDGET_CLIENT_PACKAGES,
    base_path=Path(__file__).parent.resolve() / "client",
)

__all__ = ["Button"]
