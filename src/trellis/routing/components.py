"""Router components for client-side routing."""

from trellis.core.components.composition import component
from trellis.core.rendering.child_ref import ChildRef
from trellis.routing.path_matching import match_path
from trellis.routing.state import CurrentRouteContext, RoutesContext, router


@component
def Routes(*, children: list[ChildRef] | None = None) -> None:
    """Container for exclusive route matching.

    Only the first Route child that matches will be executed. Subsequent
    Route children are skipped even if they would match.

    Usage:
        ```python
        @component
        def App():
            with RouterState():
                with Routes():
                    with Route(pattern="/"):
                        HomePage()
                    with Route(pattern="/users"):
                        UsersPage()
                    with Route(pattern="*"):
                        NotFoundPage()
        ```

    Route components must be used inside a Routes container.
    """
    state = router()

    if not children:
        return

    # Strip query string for route matching (query is handled separately)
    path = state.path.split("?", 1)[0] if "?" in state.path else state.path

    # Provide marker context so Route can verify it's inside Routes
    with RoutesContext():
        # Find first matching Route and execute only that one
        for child in children:
            element = child.element
            if element is None:
                continue

            # Validate that children are Route components
            if element.component is not Route:
                comp_name = element.component.name
                raise TypeError(
                    f"Routes children must be Route components, got {comp_name}. "
                    "Use 'with Route(pattern=...): ...' for each route."
                )

            pattern = element.props.get("pattern", "")
            assert isinstance(pattern, str), "Route pattern must be a string"
            matched, _ = match_path(pattern, path)
            if matched:
                child()  # Execute the matched Route (it provides its own context)
                return  # Stop after first match


@component
def Route(*, pattern: str, children: list[ChildRef] | None = None) -> None:
    """Define a route pattern and its content for use inside Routes.

    Route is a container component that renders its children when matched.
    The matching logic is handled by the parent Routes container, which
    decides which Route to execute.

    Route must be used inside a Routes container. If used outside,
    a RuntimeError is raised.

    Each Route provides its own CurrentRouteContext with its pattern,
    enabling router().params to compute parameters correctly. This context
    is cached per-Route element, so switching routes uses the correct pattern.

    Args:
        pattern: Route pattern to match (e.g., "/users/:id", "*" for fallback)
        children: Child elements to render when this route matches

    Example:
        ```python
        @component
        def App():
            with RouterState():
                with Routes():
                    with Route(pattern="/"):
                        HomePage()
                    with Route(pattern="/users/:id"):
                        UserPage()
                    with Route(pattern="*"):
                        NotFoundPage()
        ```
    """
    # Check if we're inside a Routes container
    if RoutesContext.from_context(default=None) is None:
        raise RuntimeError(
            "Route must be used inside a Routes container. "
            "Use 'with Routes(): with Route(pattern=...): ...' pattern."
        )

    # Provide context for on-demand param computation
    # Each Route has its own cached context, so pattern is always correct
    with CurrentRouteContext(pattern=pattern):
        if children:
            for child in children:
                child()
