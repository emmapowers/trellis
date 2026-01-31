"""Routing enums."""

from enum import StrEnum, auto


class RoutingMode(StrEnum):
    """Routing mode for URL handling.

    Controls how the router handles browser history and URLs:
    - URL: Uses browser history API with pathname URLs (/path)
    - HASH: Uses hash-based URLs (#/path) for platforms without server routing
    - HIDDEN: Internal history only, no browser URL changes (e.g., desktop apps)
    """

    URL = auto()
    HASH = auto()
    HIDDEN = auto()
