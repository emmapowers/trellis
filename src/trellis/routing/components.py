"""Router components for client-side routing."""

from dataclasses import dataclass

from trellis.core.components.composition import CompositionComponent, component
from trellis.core.rendering.child_ref import ChildRef
from trellis.core.state.stateful import Stateful
from trellis.html.links import A
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

    Only the first Route child that matches will render. Subsequent
    Route children are skipped even if they would match.

    Usage:
        ```python
        @component
        def App():
            with RouterState():
                with Routes():
                    Route(pattern="/", content=HomePage)
                    Route(pattern="/users", content=UsersPage)
                    Route(pattern="*", content=NotFoundPage)
        ```

    Route components must be used inside a Routes container.
    """
    state = router()

    with CurrentRouteContext():
        if not children:
            return

        matched_content: CompositionComponent | None = None

        # Iterate through Route children, find first match
        for child in children:
            # Call child() to keep Route elements in child_ids for re-renders
            # (Route.execute() is a no-op when inside Routes context)
            child()

            # Read pattern and content from Route element's props
            element = child.element
            if element is None:
                continue
            pattern = element.props.get("pattern")
            content = element.props.get("content")

            if pattern is None:
                # Not a Route element - skip
                continue

            # Only match if we haven't found a match yet
            if matched_content is None:
                matched, params = match_path(pattern, state.path)
                if matched:
                    state.set_params(params)
                    matched_content = content

        # Render the matched content (if any)
        if matched_content is not None:
            matched_content()


@component
def Route(*, pattern: str, content: CompositionComponent | None = None) -> None:
    """Define a route pattern and its content for use inside Routes.

    Route is a declarative component that defines a pattern and content.
    The actual matching logic is handled by the parent Routes container.

    Route must be used inside a Routes container. If used outside,
    a RuntimeError is raised.

    Args:
        pattern: Route pattern to match (e.g., "/users/:id", "*" for fallback)
        content: Component to render when matched

    Example:
        ```python
        @component
        def App():
            with RouterState():
                with Routes():
                    Route(pattern="/", content=HomePage)
                    Route(pattern="/users/:id", content=UserPage)
                    Route(pattern="*", content=NotFoundPage)
        ```
    """
    # Check if we're inside a Routes container
    ctx = CurrentRouteContext.from_context(default=None)
    if ctx is None:
        # Outside Routes - raise error
        raise RuntimeError(
            "Route must be used inside a Routes container. "
            "Use 'with Routes(): Route(pattern=..., content=...)' pattern."
        )
    # Inside Routes - no-op (Routes handles matching logic via props)


@component
def Link(*, to: str, text: str = "", children: list[ChildRef] | None = None) -> None:
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

    def handle_click(_event: object) -> None:
        # router() works in callbacks via callback_context
        # _event is the MouseEvent from the browser (unused)
        router().navigate(to)

    with A(text, href=to, onClick=handle_click):
        if children:
            for child in children:
                child()
