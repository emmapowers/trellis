"""Button widget backed by a shadcn adapter."""

from __future__ import annotations

from typing import Literal

from trellis.core.components.react import react
from trellis.widgets.dependencies import WIDGET_CLIENT_PACKAGES


@react(
    "client/components/Button.tsx",
    packages=WIDGET_CLIENT_PACKAGES,
)
def Button(
    *,
    text: str,
    disabled: bool = False,
    variant: Literal["default", "outline", "secondary", "ghost", "destructive", "link"] = "default",
    size: Literal["default", "xs", "sm", "lg"] = "default",
    key: str | None = None,
) -> None:
    """Render a button using the new shadcn-backed widget stack."""
    pass
