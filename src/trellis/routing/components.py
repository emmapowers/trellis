"""Router components for client-side routing."""

from dataclasses import dataclass

from trellis.core.components.composition import component
from trellis.core.rendering.child_ref import ChildRef
from trellis.core.state.stateful import Stateful
from trellis.routing.path_matching import match_path
from trellis.routing.state import router


@dataclass(kw_only=True)
class CurrentRouteContext(Stateful):
    """Marker context indicating we're inside a Routes container.

    This is an implementation detail - not part of the public API.
    """

    def __init__(self) -> None:
        """Initialize marker context."""
        pass


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

    with CurrentRouteContext():
        if not children:
            return

        # Find first matching Route and execute only that one
        for child in children:
            element = child.element
            if element is None:
                continue

            pattern = element.props.get("pattern")
            if pattern is None:
                # Not a Route element - skip
                continue

            matched, params = match_path(pattern, state.path)
            if matched:
                state.set_params(params)
                child()  # Execute only the matched Route
                return  # Stop after first match


@component
def Route(*, pattern: str, children: list[ChildRef] | None = None) -> None:
    """Define a route pattern and its content for use inside Routes.

    Route is a container component that renders its children when matched.
    The matching logic is handled by the parent Routes container, which
    decides which Route to execute.

    Route must be used inside a Routes container. If used outside,
    a RuntimeError is raised.

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
    ctx = CurrentRouteContext.from_context(default=None)
    if ctx is None:
        # Outside Routes - raise error
        raise RuntimeError(
            "Route must be used inside a Routes container. "
            "Use 'with Routes(): with Route(pattern=...): ...' pattern."
        )

    # Render children - if we're executing, Routes determined we match
    if children:
        for child in children:
            child()
