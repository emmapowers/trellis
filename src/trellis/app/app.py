"""User-facing application definition."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from trellis.app.client_state import ClientState, ThemeMode
from trellis.app.trellis_app import TrellisApp
from trellis.core.components.composition import CompositionComponent

if TYPE_CHECKING:
    from trellis.core.components.base import Component
    from trellis.core.rendering.element import Element


class App:
    """User-facing application definition.

    Specifies the root component to render. Created in user's module
    and discovered by AppLoader.

    Example:
        from trellis import App
        from myapp.components import Root

        app = App(Root)
    """

    def __init__(self, top: Callable[[], Element]) -> None:
        """Initialize an App with a root component.

        Args:
            top: The root component to render (a callable that returns Element)
        """
        self.top = top

    def get_wrapped_top(
        self,
        system_theme: str,
        theme_mode: str | None,
    ) -> Component:
        """Return top wrapped with TrellisApp for rendering.

        Args:
            system_theme: "light" or "dark" from client
            theme_mode: "system", "light", "dark", or None (defaults to "system")

        Returns:
            Component wrapped with TrellisApp and ClientState
        """
        # Convert strings to enums
        sys_theme = ThemeMode.DARK if system_theme == "dark" else ThemeMode.LIGHT
        mode = ThemeMode(theme_mode) if theme_mode else ThemeMode.SYSTEM

        client_state = ClientState(theme_setting=mode, system_theme=sys_theme)

        def wrapped_app() -> None:
            TrellisApp(app=self.top, client_state=client_state)

        return CompositionComponent(name="TrellisRoot", render_func=wrapped_app)
