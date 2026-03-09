"""SSR HTML cache keyed by (route, theme)."""

from __future__ import annotations

import threading

__all__ = ["SSRCache"]


class SSRCache:
    """Caches SSR HTML templates per route and theme.

    The cached HTML contains a SESSION_ID_PLACEHOLDER that is replaced
    with a fresh session ID on each request. This allows the HTML structure
    to be reused while creating unique sessions.
    """

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], str] = {}
        self._lock = threading.Lock()

    def get(self, route: str, theme: str) -> str | None:
        """Get cached HTML for a route+theme pair."""
        with self._lock:
            return self._cache.get((route, theme))

    def put(self, route: str, theme: str, html_template: str) -> None:
        """Cache HTML for a route+theme pair."""
        with self._lock:
            self._cache[(route, theme)] = html_template

    def invalidate(self) -> None:
        """Clear all cached entries. Called on hot reload / rebuild."""
        with self._lock:
            self._cache.clear()
