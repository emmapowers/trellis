"""Tests for SSR HTML cache."""

from __future__ import annotations

from trellis.platforms.server.ssr_cache import SSRCache


class TestSSRCache:
    def test_cache_miss_returns_none(self) -> None:
        cache = SSRCache()
        assert cache.get("/", "light") is None

    def test_cache_hit_returns_html(self) -> None:
        cache = SSRCache()
        cache.put("/", "light", "<html>cached</html>")
        assert cache.get("/", "light") == "<html>cached</html>"

    def test_invalidation_clears_cache(self) -> None:
        cache = SSRCache()
        cache.put("/", "light", "<html>cached</html>")
        cache.invalidate()
        assert cache.get("/", "light") is None

    def test_different_routes_cached_separately(self) -> None:
        cache = SSRCache()
        cache.put("/", "light", "<html>home</html>")
        cache.put("/about", "light", "<html>about</html>")
        assert cache.get("/", "light") == "<html>home</html>"
        assert cache.get("/about", "light") == "<html>about</html>"

    def test_different_themes_cached_separately(self) -> None:
        cache = SSRCache()
        cache.put("/", "light", "<html>light</html>")
        cache.put("/", "dark", "<html>dark</html>")
        assert cache.get("/", "light") == "<html>light</html>"
        assert cache.get("/", "dark") == "<html>dark</html>"

    def test_put_overwrites_existing(self) -> None:
        cache = SSRCache()
        cache.put("/", "light", "<html>old</html>")
        cache.put("/", "light", "<html>new</html>")
        assert cache.get("/", "light") == "<html>new</html>"
