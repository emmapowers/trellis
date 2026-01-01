"""Router state management."""

from dataclasses import dataclass, field

from trellis.core.state.stateful import Stateful


@dataclass(kw_only=True)
class RouterState(Stateful):
    """Reactive router state for client-side routing.

    Provides path-based routing with history navigation. Extends Stateful
    for reactive updates - components reading router state will re-render
    when the path changes.

    Usage:
        ```python
        @component
        def App():
            with RouterState():
                Route("/", HomePage)
                Route("/users/:id", UserPage)

        @component
        def UserPage():
            user_id = router().params["id"]
            Link("/", children=[Label(text="Home")])
        ```

    Attributes:
        path: Current URL path (read-only, use navigate() to change)
        params: Route parameters extracted from path (read-only)
        query: Query string parameters (read-only)
        history: List of visited paths (read-only)
        can_go_back: Whether back navigation is possible
        can_go_forward: Whether forward navigation is possible
    """

    # Private state fields (not exposed in __init__)
    _path: str = field(default="/", init=False)
    _params: dict[str, str] = field(default_factory=dict, init=False)
    _query: dict[str, str] = field(default_factory=dict, init=False)
    _history: list[str] = field(default_factory=list, init=False)
    _history_index: int = field(default=0, init=False)

    def __init__(self, *, path: str = "/") -> None:
        """Initialize with starting path."""
        self._path = path
        self._params = {}
        self._query = {}
        self._history = [path]
        self._history_index = 0

    @property
    def path(self) -> str:
        """Current URL path."""
        return self._path

    @property
    def params(self) -> dict[str, str]:
        """Route parameters extracted from path. Returns a copy."""
        return dict(self._params)

    @property
    def query(self) -> dict[str, str]:
        """Query string parameters. Returns a copy."""
        return dict(self._query)

    @property
    def history(self) -> list[str]:
        """List of visited paths. Returns a copy."""
        return list(self._history)

    @property
    def can_go_back(self) -> bool:
        """Whether back navigation is possible."""
        return self._history_index > 0

    @property
    def can_go_forward(self) -> bool:
        """Whether forward navigation is possible."""
        return self._history_index < len(self._history) - 1

    def _notify_path_change(self) -> None:
        """Mark nodes that read 'path' as dirty for re-render.

        Since _path is a private field, Stateful's automatic dirty marking
        doesn't trigger. We manually notify watchers of the 'path' property.
        """
        try:
            deps = object.__getattribute__(self, "_state_props")
        except AttributeError:
            return  # Not initialized yet

        if "path" in deps:
            state_info = deps["path"]
            for node in state_info.watchers:
                node_session = node._session_ref()
                if node_session is not None:
                    node_session.dirty.mark(node.id)

    def navigate(self, path: str) -> None:
        """Navigate to a new path.

        Adds the path to history and updates current path. If navigating
        after going back, forward history is discarded.

        Args:
            path: The path to navigate to
        """
        # Discard forward history if we're not at the end
        if self._history_index < len(self._history) - 1:
            self._history = self._history[: self._history_index + 1]

        self._history.append(path)
        self._history_index = len(self._history) - 1
        self._path = path
        self._notify_path_change()

    def go_back(self) -> None:
        """Navigate back in history.

        Does nothing if already at the beginning of history.
        """
        if not self.can_go_back:
            return
        self._history_index -= 1
        self._path = self._history[self._history_index]
        self._notify_path_change()

    def go_forward(self) -> None:
        """Navigate forward in history.

        Does nothing if already at the end of history.
        """
        if not self.can_go_forward:
            return
        self._history_index += 1
        self._path = self._history[self._history_index]
        self._notify_path_change()

    def set_params(self, params: dict[str, str]) -> None:
        """Set route parameters.

        Called internally by Route component when path matches.

        Args:
            params: The extracted route parameters
        """
        self._params = dict(params)

    def set_query(self, query: dict[str, str]) -> None:
        """Set query string parameters.

        Args:
            query: The query parameters
        """
        self._query = dict(query)


def router() -> RouterState:
    """Get the current RouterState from context.

    Must be called within a component that is a descendant of a RouterState
    context provider.

    Returns:
        The RouterState from the nearest ancestor

    Raises:
        RuntimeError: If called outside render context
        LookupError: If no RouterState is in the context
    """
    return RouterState.from_context()
