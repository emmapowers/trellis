"""Tests for server platform routes."""


class TestIndexHtmlTemplate:
    """Tests for index.html Jinja2 template."""

    def test_template_file_exists(self) -> None:
        """Template file exists at expected location."""
        from trellis.platforms.server.routes import _TEMPLATE_DIR

        template_path = _TEMPLATE_DIR / "index.html"
        assert template_path.exists(), f"Template not found at {template_path}"

    def test_template_is_valid_jinja2(self) -> None:
        """Template can be loaded by Jinja2 environment."""
        from trellis.platforms.server.routes import _jinja_env

        # Should not raise
        template = _jinja_env.get_template("index.html")
        assert template is not None


class TestGetIndexHtml:
    """Tests for get_index_html function."""

    def test_valid_html_structure(self) -> None:
        """Generated HTML has valid structure."""
        from trellis.platforms.server.routes import get_index_html

        result = get_index_html()

        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "</html>" in result
        assert 'id="root"' in result
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

    def test_custom_title(self) -> None:
        """Custom title is rendered in the page."""
        from trellis.platforms.server.routes import get_index_html

        result = get_index_html(title="My Custom App")

        assert "<title>My Custom App</title>" in result

    def test_default_title(self) -> None:
        """Default title is 'Trellis App'."""
        from trellis.platforms.server.routes import get_index_html

        result = get_index_html()

        assert "<title>Trellis App</title>" in result
