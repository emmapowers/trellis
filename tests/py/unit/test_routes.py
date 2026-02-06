"""Tests for server platform routes."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from trellis.platforms.server.routes import (
    get_index_html,
    register_spa_fallback,
    router,
)


class TestSpaRoutes:
    """Tests for SPA fallback routing via 404 exception handler."""

    @pytest.fixture(autouse=True)
    def setup_mock_dist(self, tmp_path: Path) -> Generator[None]:
        """Create a mock dist directory and patch get_dist_dir for all tests."""
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        index_html = dist_dir / "index.html"
        index_html.write_text(
            "<!DOCTYPE html><html><head><title>Trellis App</title></head>"
            '<body><div id="root"></div>'
            '<script src="/static/bundle.js"></script>'
            '<link rel="stylesheet" href="/static/bundle.css">'
            "</body></html>"
        )
        with patch("trellis.platforms.server.routes.get_dist_dir", return_value=dist_dir):
            yield

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


class TestGetIndexHtml:
    """Tests for get_index_html function."""

    @pytest.fixture(autouse=True)
    def setup_mock_dist(self, tmp_path: Path) -> Generator[None]:
        """Create a mock dist directory and patch get_dist_dir for all tests."""
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        index_html = dist_dir / "index.html"
        index_html.write_text(
            "<!DOCTYPE html><html><head><title>Trellis App</title></head>"
            '<body><div id="root"></div>'
            '<script src="/static/bundle.js"></script>'
            '<link rel="stylesheet" href="/static/bundle.css">'
            "</body></html>"
        )
        with patch("trellis.platforms.server.routes.get_dist_dir", return_value=dist_dir):
            yield

    def test_valid_html_structure(self) -> None:
        """Generated HTML has valid structure."""
        result = get_index_html()

        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "</html>" in result
        assert 'id="root"' in result
        assert "bundle.js" in result
        assert "bundle.css" in result

    def test_static_path(self) -> None:
        """Static path /static is used for bundle URLs."""
        result = get_index_html()

        assert "/static/bundle.js" in result
        assert "/static/bundle.css" in result

    def test_default_title(self) -> None:
        """Default title is 'Trellis App'."""
        result = get_index_html()

        assert "<title>Trellis App</title>" in result
