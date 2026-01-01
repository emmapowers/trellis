"""Router components for client-side routing."""

from trellis.core.components.composition import CompositionComponent, component
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
