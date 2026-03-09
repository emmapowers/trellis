"""SSR rendered-HTML cache keyed by (route, theme).

Caches only the rendered HTML output from renderToString(), not the
full page template or dehydration data. Dehydration data (patches,
session ID) contains per-session element IDs and must be computed
fresh for every request.
"""

from __future__ import annotations

import threading

__all__ = ["SSRCache"]


_DEFAULT_MAX_ENTRIES = 100


class SSRCache:
    """Caches rendered SSR HTML per route and theme.

    The cached value is the HTML fragment produced by the Bun sidecar's
    renderToString(). This is purely structural and does not contain
    session-specific data, so it can be safely reused across requests.

    Bounded to max_entries to prevent unbounded growth from arbitrary
    request paths (404 probes, client-side route variants, etc.).
    """

    def __init__(self, max_entries: int = _DEFAULT_MAX_ENTRIES) -> None:
        self._cache: dict[tuple[str, str], str] = {}
        self._lock = threading.Lock()
        self._max_entries = max_entries

    def get(self, route: str, theme: str) -> str | None:
        """Get cached rendered HTML for a route+theme pair."""
        with self._lock:
            return self._cache.get((route, theme))

    def put(self, route: str, theme: str, ssr_html: str) -> None:
        """Cache rendered HTML for a route+theme pair."""
        with self._lock:
            if len(self._cache) >= self._max_entries and (route, theme) not in self._cache:
                # Evict oldest entry (first inserted)
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[(route, theme)] = ssr_html

    def invalidate(self) -> None:
        """Clear all cached entries. Called on hot reload / rebuild."""
        with self._lock:
            self._cache.clear()
