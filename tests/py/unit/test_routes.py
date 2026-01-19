"""Tests for server platform routes."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from trellis.platforms.server.routes import (
    _TEMPLATE_DIR,
    _jinja_env,
    get_index_html,
    register_spa_fallback,
    router,
)


class TestSpaRoutes:
    """Tests for SPA fallback routing via 404 exception handler."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client with routes and SPA fallback handler."""
        app = FastAPI()
        app.include_router(router)
        register_spa_fallback(app)
        return TestClient(app)

    def test_root_serves_index_html(self, client: TestClient) -> None:
        """Root path serves index HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert 'id="root"' in response.text

    def test_spa_route_serves_index_html(self, client: TestClient) -> None:
        """Non-root paths serve the same index HTML for client-side routing."""
        response = client.get("/about")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert 'id="root"' in response.text

    def test_nested_spa_route_serves_index_html(self, client: TestClient) -> None:
        """Nested paths serve index HTML for client-side routing."""
        response = client.get("/users/123")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text
        assert 'id="root"' in response.text


class TestIndexHtmlTemplate:
    """Tests for index.html.j2 Jinja2 template."""

    def test_template_file_exists(self) -> None:
        """Template file exists at expected location."""
        template_path = _TEMPLATE_DIR / "index.html.j2"
        assert template_path.exists(), f"Template not found at {template_path}"

    def test_template_is_valid_jinja2(self) -> None:
        """Template can be loaded by Jinja2 environment."""
        # Should not raise
        template = _jinja_env.get_template("index.html.j2")
        assert template is not None


class TestGetIndexHtml:
    """Tests for get_index_html function."""

    def test_valid_html_structure(self) -> None:
        """Generated HTML has valid structure."""
        result = get_index_html()

        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "</html>" in result
        assert 'id="root"' in result
        assert "bundle.js" in result
        assert "bundle.css" in result

    def test_uses_static_path(self) -> None:
        """Static path is used for bundle URLs."""
        result = get_index_html(static_path="/assets")

        assert "/assets/bundle.js" in result
        assert "/assets/bundle.css" in result

    def test_default_static_path(self) -> None:
        """Default static path is /static."""
        result = get_index_html()

        assert "/static/bundle.js" in result
        assert "/static/bundle.css" in result

    def test_custom_title(self) -> None:
        """Custom title is rendered in the page."""
        result = get_index_html(title="My Custom App")

        assert "<title>My Custom App</title>" in result

    def test_default_title(self) -> None:
        """Default title is 'Trellis App'."""
        result = get_index_html()

        assert "<title>Trellis App</title>" in result
