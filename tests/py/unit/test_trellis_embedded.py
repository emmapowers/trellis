"""Unit tests for Trellis embedded mode parameter."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from trellis.app.entry import Trellis
from trellis.platforms.common.base import Platform, PlatformType


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


class TestEmbeddedDefault:
    """Tests for default embedded value."""

    def test_embedded_defaults_to_false(self, mock_platform: Mock) -> None:
        """embedded param defaults to False."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(top=dummy_component, ignore_cli=True)

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["embedded"] is False


class TestEmbeddedExplicit:
    """Tests for explicitly setting embedded."""

    def test_embedded_can_be_set_true(self, mock_platform: Mock) -> None:
        """embedded=True is passed to platform.run()."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(top=dummy_component, ignore_cli=True, embedded=True)

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["embedded"] is True

    def test_embedded_can_be_set_false(self, mock_platform: Mock) -> None:
        """embedded=False is passed to platform.run()."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(top=dummy_component, ignore_cli=True, embedded=False)

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["embedded"] is False


class TestDesktopForcesEmbedded:
    """Tests for desktop platform always using embedded mode."""

    def test_desktop_forces_embedded_true(self, mock_platform: Mock) -> None:
        """Desktop platform forces embedded=True even if user specifies False."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.DESKTOP,
                    embedded=False,  # User tries to set False
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        # Desktop should force embedded=True regardless of user input
        assert call_kwargs["embedded"] is True

    def test_desktop_embedded_true_when_not_specified(self, mock_platform: Mock) -> None:
        """Desktop platform uses embedded=True when not explicitly specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.DESKTOP,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["embedded"] is True


class TestBrowserRespectsEmbedded:
    """Tests for browser platform respecting embedded param."""

    def test_browser_respects_embedded_true(self, mock_platform: Mock) -> None:
        """Browser platform uses embedded=True when specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.BROWSER,
                    embedded=True,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["embedded"] is True

    def test_browser_respects_embedded_false(self, mock_platform: Mock) -> None:
        """Browser platform uses embedded=False when specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.BROWSER,
                    embedded=False,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["embedded"] is False

    def test_browser_defaults_embedded_false(self, mock_platform: Mock) -> None:
        """Browser platform defaults to embedded=False."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.BROWSER,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["embedded"] is False


class TestServerEmbedded:
    """Tests for server platform embedded behavior."""

    def test_server_defaults_embedded_false(self, mock_platform: Mock) -> None:
        """Server platform defaults to embedded=False."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    platform=PlatformType.SERVER,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["embedded"] is False
