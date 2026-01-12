"""Routing enums."""

from enum import StrEnum, auto


class RoutingMode(StrEnum):
    """Routing mode for URL handling.

    Controls how the router handles browser history and URLs:
    - STANDARD: Uses browser history API with pathname URLs (/path)
    - HASH_URL: Uses hash-based URLs (#/path) for platforms without server routing
    - EMBEDDED: Internal history only, no browser URL changes (e.g., desktop apps)
    """

    STANDARD = auto()
    HASH_URL = auto()
    EMBEDDED = auto()
