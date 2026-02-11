"""Unit tests for trellis.platforms.browser.serve_platform module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.routing import Mount

from trellis.platforms.browser.serve_platform import BrowserServePlatform


class TestBrowserServePlatformRun:
    """Tests for BrowserServePlatform.run() method."""

    @pytest.fixture
    def platform(self) -> BrowserServePlatform:
        """Create a BrowserServePlatform instance."""
        return BrowserServePlatform()

    @pytest.fixture
    def mock_component(self) -> MagicMock:
        """Create a mock root component."""
        return MagicMock()

    @pytest.fixture
    def mock_wrapper(self) -> MagicMock:
        """Create a mock app wrapper."""
        return MagicMock()

    @pytest.mark.anyio
    async def test_serves_directly_from_dist(
        self,
        platform: BrowserServePlatform,
        mock_component: MagicMock,
        mock_wrapper: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Serves the pre-built bundle directly from dist directory (no temp copy)."""
        # Create a mock dist directory with index.html
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        (dist_dir / "index.html").write_text("<html>test</html>")
        (dist_dir / "bundle.js").write_text("// bundle")

        captured_app = None

        def capture_starlette(*args: object, **kwargs: object) -> MagicMock:
            nonlocal captured_app
            captured_app = MagicMock()
            return captured_app

        with (
            patch("trellis.platforms.browser.serve_platform.get_dist_dir") as mock_dist,
            patch("trellis.platforms.browser.serve_platform.uvicorn") as mock_uvicorn,
            patch(
                "trellis.platforms.browser.serve_platform.find_available_port", return_value=8000
            ),
            patch("trellis.platforms.browser.serve_platform._print_startup_banner"),
            patch(
                "trellis.platforms.browser.serve_platform.Starlette", side_effect=capture_starlette
            ) as mock_starlette,
        ):
            mock_dist.return_value = dist_dir

            # Make server.serve() complete immediately
            mock_server = AsyncMock()
            mock_uvicorn.Config.return_value = MagicMock()
            mock_uvicorn.Server.return_value = mock_server

            await platform.run(mock_component, mock_wrapper)

            # Verify Starlette was called
            mock_starlette.assert_called_once()
            call_kwargs = mock_starlette.call_args[1]

            # The static files should point to dist_dir (not a temp directory)
            routes = call_kwargs["routes"]
            # Find the Mount route for static files (the second route with path="/")
            # Route objects: [Route("/", index), Mount("/", StaticFiles(...))]
            mount_route = next(r for r in routes if isinstance(r, Mount))
            assert "dist" in str(mount_route.app.directory)

            # Verify uvicorn was started
            mock_uvicorn.Config.assert_called_once()
            mock_server.serve.assert_called_once()
