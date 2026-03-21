"""Tests for SSR HTML cache."""

from __future__ import annotations

from trellis.platforms.server.ssr_cache import SSRCache


class TestSSRCache:
    def test_cache_miss_returns_none(self) -> None:
        cache = SSRCache()
        assert cache.get("/") is None

    def test_cache_hit_returns_html(self) -> None:
        cache = SSRCache()
        cache.put("/", "<html>cached</html>")
        assert cache.get("/") == "<html>cached</html>"

    def test_invalidation_clears_cache(self) -> None:
        cache = SSRCache()
        cache.put("/", "<html>cached</html>")
        cache.invalidate()
        assert cache.get("/") is None

    def test_different_routes_cached_separately(self) -> None:
        cache = SSRCache()
        cache.put("/", "<html>home</html>")
        cache.put("/about", "<html>about</html>")
        assert cache.get("/") == "<html>home</html>"
        assert cache.get("/about") == "<html>about</html>"

    def test_put_overwrites_existing(self) -> None:
        cache = SSRCache()
        cache.put("/", "<html>old</html>")
        cache.put("/", "<html>new</html>")
        assert cache.get("/") == "<html>new</html>"
