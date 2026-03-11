"""Router state management."""

from dataclasses import dataclass, field
from urllib.parse import parse_qsl

from trellis.core.protocol import (
    MessageHandlerProtocol,
    MessageListener,
    get_message_handler,
    listen,
    send,
)
from trellis.core.rendering.session import get_active_session
from trellis.core.state.stateful import Stateful, Tracked
from trellis.routing.messages import HistoryBack, HistoryForward, HistoryPush, UrlChanged
from trellis.routing.path_matching import match_path


@dataclass(kw_only=True)
class RoutesContext(Stateful):
    """Marker context provided by Routes container.

    Used by Route to verify it's inside a Routes container.
    This is an implementation detail - not part of the public API.
    """

    pass


@dataclass(kw_only=True)
class CurrentRouteContext(Stateful):
    """Context storing the matched route pattern for param computation.

    Provided by Route component when it renders. Child components
    can use this to compute params on-demand via router().params.

    This is an implementation detail - not part of the public API.
    """

    pattern: str = ""


@dataclass()
class RouterState(Stateful, MessageListener):
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

    _path: Tracked[str] = field(default="/")
    _history: Tracked[list[str]] = field(default_factory=list)
    _history_index: Tracked[int] = field(default=0)

    def __init__(self, *, path: str | None = None) -> None:
        """Initialize with starting path.

        If no path is provided, uses the initial_path from the session
        (set from HelloMessage). Falls back to "/" if no session.
        """
        if path is None:
            # Try to get initial path from session
            session = get_active_session()
            if session is not None:
                path = session.initial_path
            else:
                path = "/"

        self._path = path
        self._history = [path]
        self._history_index = 0
        MessageListener.__init__(self)

    @property
    def path(self) -> str:
        """Current URL path."""
        return self._path

    @property
    def params(self) -> dict[str, str]:
        """Route parameters computed on-demand from path and matched pattern.

        Uses the pattern from CurrentRouteContext (set by Route) to extract
        parameters from the current path. Returns empty dict if outside
        a matched route context.
        """
        ctx = CurrentRouteContext.from_context(default=None)
        if ctx is None:
            raise RuntimeError("router().params called outside of a Route context")
        if not ctx.pattern:
            return {}
        # Strip query string before matching
        path = self._path.split("?", 1)[0] if "?" in self._path else self._path
        _, params = match_path(ctx.pattern, path)
        return params

    @property
    def query(self) -> dict[str, str]:
        """Query string parameters parsed on-demand from current path.

        Parses the query string portion of the path (after '?') and returns
        parameters as a dict. URL-encoded values are properly decoded.
        Returns empty dict if no query string present.
        """
        if "?" not in self._path:
            return {}
        query_string = self._path.split("?", 1)[1]
        return dict(parse_qsl(query_string))

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

    async def navigate(self, path: str) -> None:
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

        if get_message_handler() is not None:
            await send(HistoryPush(path=path))

    async def go_back(self) -> None:
        """Navigate back in history.

        Does nothing if already at the beginning of history.
        """
        if not self.can_go_back:
            return
        self._history_index -= 1
        self._path = self._history[self._history_index]

        if get_message_handler() is not None:
            await send(HistoryBack())

    async def go_forward(self) -> None:
        """Navigate forward in history.

        Does nothing if already at the end of history.
        """
        if not self.can_go_forward:
            return
        self._history_index += 1
        self._path = self._history[self._history_index]

        if get_message_handler() is not None:
            await send(HistoryForward())

    @listen(UrlChanged)
    async def on_url_changed(
        self,
        _message_handler: MessageHandlerProtocol,
        message: UrlChanged,
    ) -> None:
        """Update router state when the browser URL changes."""
        self._update_path_from_url(message.path)

    def on_mount(self) -> None:
        """Register session-scoped listeners after the router enters the tree."""
        self.register_message_listeners()

    def on_unmount(self) -> None:
        """Detach session-scoped listeners when the router leaves the tree."""
        self.unregister_message_listeners()

    def __enter__(self) -> "RouterState":
        """Provide router context and ensure its listeners are registered."""
        result = super().__enter__()
        self.register_message_listeners()
        return result

    def _update_path_from_url(self, path: str) -> None:
        """Update path from a browser-driven URL change.

        Used by the UrlChanged protocol listener. Does not enqueue history
        messages since the browser already owns the navigation.

        Args:
            path: The new path from browser URL
        """
        self._path = path


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
