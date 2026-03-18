"""SSR rendered-HTML cache keyed by route.

Caches only the rendered HTML output from renderToString(), not the
full page template or dehydration data. Dehydration data (patches,
session ID) contains per-session element IDs and must be computed
fresh for every request.

Theme is not a cache dimension — all rendered HTML uses CSS variables,
so light and dark themes produce identical markup.
"""

from __future__ import annotations

import threading

__all__ = ["SSRCache"]


_DEFAULT_MAX_ENTRIES = 100


class SSRCache:
    """Caches rendered SSR HTML per route.

    The cached value is the HTML fragment produced by the Bun sidecar's
    renderToString(). This is purely structural and does not contain
    session-specific data, so it can be safely reused across requests.

    Bounded to max_entries to prevent unbounded growth from arbitrary
    request paths (404 probes, client-side route variants, etc.).
    """

    def __init__(self, max_entries: int = _DEFAULT_MAX_ENTRIES) -> None:
        self._cache: dict[str, str] = {}
        self._lock = threading.Lock()
        self._max_entries = max_entries

    def get(self, route: str) -> str | None:
        """Get cached rendered HTML for a route."""
        with self._lock:
            return self._cache.get(route)

    def put(self, route: str, ssr_html: str) -> None:
        """Cache rendered HTML for a route."""
        with self._lock:
            if len(self._cache) >= self._max_entries and route not in self._cache:
                # Evict oldest entry (first inserted)
                oldest = next(iter(self._cache))
                del self._cache[oldest]
            self._cache[route] = ssr_html

    def invalidate(self) -> None:
        """Clear all cached entries. Called on hot reload / rebuild."""
        with self._lock:
            self._cache.clear()
