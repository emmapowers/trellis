"""Router components for client-side routing."""

from trellis.core.components.composition import CompositionComponent, component
from trellis.core.rendering.element import Element
from trellis.html.links import A
from trellis.routing.path_matching import match_path
from trellis.routing.state import router


@component
def Route(*, pattern: str, content: CompositionComponent | None = None) -> None:
    """Conditionally render content when path matches pattern.

    Route checks the current path from RouterState and renders its content
    only when the pattern matches. Parameters extracted from the path are
    made available via router().params.

    Args:
        pattern: Route pattern to match (e.g., "/users/:id")
        content: Component to render when matched

    Example:
        ```python
        @component
        def App():
            with RouterState():
                Route(pattern="/", content=HomePage)
                Route(pattern="/users/:id", content=UserPage)
                Route(pattern="*", content=NotFoundPage)
        ```
    """
    state = router()
    matched, params = match_path(pattern, state.path)

    if matched:
        # Set extracted params on router state
        state.set_params(params)

        # Render the content component
        if content is not None:
            content()


@component
def Link(*, to: str, text: str = "", children: list[Element] | None = None) -> None:
    """Navigation link that uses client-side routing.

    Renders an anchor element that navigates without full page reload.
    Click handler calls router().navigate() to update RouterState.

    Args:
        to: Path to navigate to when clicked
        text: Text content for the link (optional)
        children: Child elements to render inside link (optional)

    Example:
        ```python
        Link(to="/", text="Home")
        Link(to="/users/123", text="User Profile")

        # With children
        with Link(to="/about"):
            h.Span("About Us")
        ```
    """

    # Capture router state at render time, not callback time
    router_state = router()

    def handle_click() -> None:
        router_state.navigate(to)

    with A(text, href=to, onClick=handle_click):
        if children:
            for child in children:
                child()
