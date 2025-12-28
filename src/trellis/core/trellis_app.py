"""TrellisApp wrapper component for global application state.

Provides ClientState and other global context to the entire application.
"""

from __future__ import annotations

from collections.abc import Callable

from trellis.core.client_state import ClientState
from trellis.core.components.composition import component
from trellis.widgets.theme_provider import ThemeProvider


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

    Args:
        app: The root component to render (passed as a callable, executed inside)
        client_state: Optional pre-configured ClientState. If not provided,
            a default one is created with system theme from client config.

    Example:
        ```python
        @component
        def MyApp() -> None:
            # Access client state via context
            state = ClientState.from_context()
            if state.is_dark:
                w.Label(text="Dark mode!")

        @component
        def Main() -> None:
            TrellisApp(app=MyApp)
        ```
    """
    if client_state is None:
        client_state = ClientState()

    with client_state:  # Provide to descendants via context
        with ThemeProvider(
            mode=client_state.mode,
            resolved_theme=client_state.resolved_theme,
            on_system_theme_change=client_state.handle_system_theme_change,
            on_theme_mode_change=client_state.set_mode,
        ):
            app()  # Execute the app component
