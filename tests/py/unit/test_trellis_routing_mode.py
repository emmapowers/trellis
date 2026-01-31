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

    def test_routing_mode_defaults_to_hash(self, mock_platform: Mock) -> None:
        """routing_mode defaults to HASH."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(top=dummy_component, ignore_cli=True)

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH


class TestRoutingModeExplicit:
    """Tests for explicitly setting routing_mode."""

    def test_routing_mode_can_be_set_hidden(self, mock_platform: Mock) -> None:
        """routing_mode=HIDDEN is passed to platform.run()."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    routing_mode=RoutingMode.HIDDEN,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HIDDEN

    def test_routing_mode_can_be_set_url(self, mock_platform: Mock) -> None:
        """routing_mode=URL is passed to platform.run()."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    routing_mode=RoutingMode.URL,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.URL

    def test_routing_mode_can_be_set_hash(self, mock_platform: Mock) -> None:
        """routing_mode=HASH is passed to platform.run()."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    routing_mode=RoutingMode.HASH,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH


class TestDesktopForcesHidden:
    """Tests for desktop platform always using hidden mode."""

    def test_desktop_forces_hidden(self, mock_platform: Mock) -> None:
        """Desktop platform forces HIDDEN even if user specifies different mode."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.DESKTOP,
                    routing_mode=RoutingMode.HASH,  # User tries to set HASH
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        # Desktop should force HIDDEN regardless of user input
        assert call_kwargs["routing_mode"] == RoutingMode.HIDDEN

    def test_desktop_hidden_when_not_specified(self, mock_platform: Mock) -> None:
        """Desktop platform uses HIDDEN when routing_mode not explicitly specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.DESKTOP,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HIDDEN


class TestBrowserRespectsRoutingMode:
    """Tests for browser platform respecting routing_mode param."""

    def test_browser_respects_hidden(self, mock_platform: Mock) -> None:
        """Browser platform uses HIDDEN when specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.BROWSER,
                    routing_mode=RoutingMode.HIDDEN,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HIDDEN

    def test_browser_respects_hash(self, mock_platform: Mock) -> None:
        """Browser platform uses HASH when specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.BROWSER,
                    routing_mode=RoutingMode.HASH,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH

    def test_browser_defaults_hash(self, mock_platform: Mock) -> None:
        """Browser platform defaults to HASH."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.BROWSER,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH


class TestServerRoutingMode:
    """Tests for server platform routing_mode behavior."""

    def test_server_defaults_hash(self, mock_platform: Mock) -> None:
        """Server platform defaults to HASH."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.SERVER,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["routing_mode"] == RoutingMode.HASH
