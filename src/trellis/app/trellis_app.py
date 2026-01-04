"""TrellisApp wrapper component for global application state.

Provides ClientState and other global context to the entire application.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal, cast

from trellis.app.client_state import ClientState, ThemeMode
from trellis.app.theme_provider import ThemeProvider
from trellis.core.components.composition import component
from trellis.routing.state import RouterState


@component
def TrellisApp(
    app: Callable[[], None],
    *,
    client_state: ClientState | None = None,
) -> None:
    """Application wrapper providing global state (theme, device info, etc.).

    Wraps the app component with:
    - ClientState in context (accessible via ClientState.from_context())
    - ThemeProvider for CSS theming and OS theme detection

    Note: Trellis automatically wraps your app with TrellisApp, so you don't
    need to use this directly. Just use ClientState.from_context() in your
    components to access theme state.

    Args:
        app: The root component to render (passed as a callable, executed inside)
        client_state: Optional pre-configured ClientState. If not provided,
            a default one is created with system theme from client config.
    """
    if client_state is None:
        client_state = ClientState()

    # Bridge between string-based ThemeProvider callbacks and enum-based ClientState
    def handle_system_theme_change(new_theme: Literal["light", "dark"]) -> None:
        client_state.handle_system_theme_change(
            ThemeMode.DARK if new_theme == "dark" else ThemeMode.LIGHT
        )

    def handle_theme_mode_change(mode: Literal["system", "light", "dark"]) -> None:
        client_state.set_mode(ThemeMode(mode))

    # Type narrowing: StrEnum.value returns str, but we know it's one of the literal values
    theme_setting_str = cast("Literal['system', 'light', 'dark']", client_state.theme_setting.value)
    theme_str = cast("Literal['light', 'dark']", client_state.theme.value)

    with client_state, RouterState():  # Provide to descendants via context
        with ThemeProvider(
            theme_setting=theme_setting_str,
            theme=theme_str,
            on_system_theme_change=handle_system_theme_change,
            on_theme_mode_change=handle_theme_mode_change,
        ):
            app()  # Execute the app component
