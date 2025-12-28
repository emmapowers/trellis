"""Tests for server platform routes."""


class TestGetIndexHtml:
    """Tests for get_index_html function."""

    def test_valid_html_structure(self) -> None:
        """Generated HTML has valid structure."""
        from trellis.platforms.server.routes import get_index_html

        result = get_index_html()

        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "</html>" in result
        assert '<div id="root"></div>' in result
        assert "bundle.js" in result
        assert "bundle.css" in result

    def test_uses_static_path(self) -> None:
        """Static path is used for bundle URLs."""
        from trellis.platforms.server.routes import get_index_html

        result = get_index_html(static_path="/assets")

        assert "/assets/bundle.js" in result
        assert "/assets/bundle.css" in result

    def test_default_static_path(self) -> None:
        """Default static path is /static."""
        from trellis.platforms.server.routes import get_index_html

        result = get_index_html()

        assert "/static/bundle.js" in result
        assert "/static/bundle.css" in result
