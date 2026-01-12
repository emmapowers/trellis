"""Unit tests for Trellis routing_mode parameter."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from trellis.app.entry import Trellis
from trellis.platforms.common.base import Platform, PlatformType
from trellis.routing.enums import RoutingMode


@pytest.fixture
def mock_platform() -> Mock:
    """Mock Platform implementation for testing."""
    platform = Mock(spec=Platform)
    platform.name = "test"
    platform.bundle = Mock()
    platform.run = AsyncMock()
    return platform


def dummy_component() -> None:
    """Dummy component for testing."""
    pass


class TestRoutingModeDefault:
    """Tests for default routing_mode value."""

    def test_routing_mode_defaults_to_hash_url(self, mock_platform: Mock) -> None:
        """routing_mode defaults to HASH_URL."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(top=dummy_component, ignore_cli=True)

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH_URL


class TestRoutingModeExplicit:
    """Tests for explicitly setting routing_mode."""

    def test_routing_mode_can_be_set_embedded(self, mock_platform: Mock) -> None:
        """routing_mode=EMBEDDED is passed to platform.run()."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    routing_mode=RoutingMode.EMBEDDED,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.EMBEDDED

    def test_routing_mode_can_be_set_standard(self, mock_platform: Mock) -> None:
        """routing_mode=STANDARD is passed to platform.run()."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    routing_mode=RoutingMode.STANDARD,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.STANDARD

    def test_routing_mode_can_be_set_hash_url(self, mock_platform: Mock) -> None:
        """routing_mode=HASH_URL is passed to platform.run()."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    routing_mode=RoutingMode.HASH_URL,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH_URL


class TestDesktopForcesEmbedded:
    """Tests for desktop platform always using embedded mode."""

    def test_desktop_forces_embedded(self, mock_platform: Mock) -> None:
        """Desktop platform forces EMBEDDED even if user specifies different mode."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.DESKTOP,
                    routing_mode=RoutingMode.HASH_URL,  # User tries to set HASH_URL
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        # Desktop should force EMBEDDED regardless of user input
        assert call_kwargs["routing_mode"] == RoutingMode.EMBEDDED

    def test_desktop_embedded_when_not_specified(self, mock_platform: Mock) -> None:
        """Desktop platform uses EMBEDDED when routing_mode not explicitly specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.DESKTOP,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.EMBEDDED


class TestBrowserRespectsRoutingMode:
    """Tests for browser platform respecting routing_mode param."""

    def test_browser_respects_embedded(self, mock_platform: Mock) -> None:
        """Browser platform uses EMBEDDED when specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.BROWSER,
                    routing_mode=RoutingMode.EMBEDDED,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.EMBEDDED

    def test_browser_respects_hash_url(self, mock_platform: Mock) -> None:
        """Browser platform uses HASH_URL when specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.BROWSER,
                    routing_mode=RoutingMode.HASH_URL,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH_URL

    def test_browser_defaults_hash_url(self, mock_platform: Mock) -> None:
        """Browser platform defaults to HASH_URL."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.BROWSER,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH_URL


class TestServerRoutingMode:
    """Tests for server platform routing_mode behavior."""

    def test_server_defaults_hash_url(self, mock_platform: Mock) -> None:
        """Server platform defaults to HASH_URL."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.SERVER,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH_URL
