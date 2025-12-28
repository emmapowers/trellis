"""Unit tests for Trellis.serve() method."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from trellis.app.entry import Trellis
from trellis.platforms.common.base import Platform


@pytest.fixture
def mock_platform() -> Mock:
    """
    Create a Mock implementing the Platform interface, preconfigured for serve() tests.
    
    The returned Mock has:
    - spec set to `Platform`
    - `name` set to `"test"`
    - `bundle` as a `unittest.mock.Mock`
    - `run` as an `AsyncMock`
    
    Returns:
        platform (Mock): A Mock object representing a platform suitable for unit tests of Trellis.serve().
    """
    platform = Mock(spec=Platform)
    platform.name = "test"
    platform.bundle = Mock()
    platform.run = AsyncMock()
    return platform


@pytest.fixture
def trellis_with_mock_platform(mock_platform: Mock) -> Trellis:
    """
    Create a Trellis instance configured to use the provided mock platform.
    
    Parameters:
        mock_platform (Mock): Mock object that will be returned by the module's platform lookup to simulate a Platform.
    
    Returns:
        Trellis: A Trellis instance whose top is a minimal dummy component and which is configured to ignore CLI arguments.
    """

    def dummy_component() -> None:
        """
        Create a minimal placeholder component used as a Trellis top component in tests.
        
        This component has no behavior and exists only to supply a non-None top value for test cases.
        """
        pass

    with patch("trellis.app.entry._get_platform", return_value=mock_platform):
        with patch("sys.argv", ["app"]):
            app = Trellis(top=dummy_component, ignore_cli=True)
    return app


class TestServeValidation:
    """Tests for serve() input validation."""

    def test_serve_raises_when_top_is_none(self, mock_platform: Mock) -> None:
        """serve() raises ValueError when no top component specified."""
        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(top=None, ignore_cli=True)

        with pytest.raises(ValueError, match="No top component specified"):
            asyncio.run(app.serve())

        # Ensure bundle and run were never called
        mock_platform.bundle.assert_not_called()
        mock_platform.run.assert_not_called()


class TestServeBundling:
    """Tests for serve() bundle building."""

    def test_serve_calls_bundle_with_default_force(
        self, trellis_with_mock_platform: Trellis, mock_platform: Mock
    ) -> None:
        """serve() calls platform.bundle() with force=False by default."""
        trellis_with_mock_platform._platform = mock_platform
        asyncio.run(trellis_with_mock_platform.serve())

        mock_platform.bundle.assert_called_once_with(force=False)

    def test_serve_calls_bundle_with_force_true(self, mock_platform: Mock) -> None:
        """serve() calls platform.bundle() with force=True when build_bundle=True."""

        def dummy_component() -> None:
            """
            A no-op placeholder component used as the Trellis top component in tests.
            
            Intended solely as a minimal stand-in for a real component; it performs no actions.
            """
            pass

        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(top=dummy_component, ignore_cli=True, build_bundle=True)

        asyncio.run(app.serve())

        mock_platform.bundle.assert_called_once_with(force=True)

    def test_serve_calls_bundle_with_cli_build_bundle(self, mock_platform: Mock) -> None:
        """serve() respects --build-bundle CLI flag."""

        def dummy_component() -> None:
            """
            A no-op placeholder component used as the Trellis top component in tests.
            
            Intended solely as a minimal stand-in for a real component; it performs no actions.
            """
            pass

        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app", "--build-bundle"]):
                app = Trellis(top=dummy_component)

        asyncio.run(app.serve())

        mock_platform.bundle.assert_called_once_with(force=True)


class TestServePlatformRun:
    """Tests for serve() platform.run() invocation."""

    def test_serve_awaits_platform_run(
        self, trellis_with_mock_platform: Trellis, mock_platform: Mock
    ) -> None:
        """serve() awaits platform.run()."""
        trellis_with_mock_platform._platform = mock_platform
        asyncio.run(trellis_with_mock_platform.serve())

        mock_platform.run.assert_awaited_once()

    def test_serve_passes_root_component_to_run(self, mock_platform: Mock) -> None:
        """serve() passes root_component to platform.run()."""

        def my_component() -> None:
            """
            Dummy top-level component used as a placeholder.
            
            Serves as a no-op root component when constructing Trellis instances for testing.
            """
            pass

        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(top=my_component, ignore_cli=True)

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["root_component"] is my_component

    def test_serve_passes_default_args_to_run(
        self, trellis_with_mock_platform: Trellis, mock_platform: Mock
    ) -> None:
        """serve() passes default configuration args to platform.run()."""
        trellis_with_mock_platform._platform = mock_platform
        asyncio.run(trellis_with_mock_platform.serve())

        call_kwargs = mock_platform.run.call_args.kwargs

        # Check default values are passed
        assert call_kwargs["host"] == "127.0.0.1"
        assert call_kwargs["port"] is None
        assert call_kwargs["batch_delay"] == pytest.approx(1.0 / 30)
        assert call_kwargs["build_bundle"] is False

    def test_serve_passes_custom_host_port_to_run(self, mock_platform: Mock) -> None:
        """serve() passes custom host/port to platform.run()."""

        def dummy_component() -> None:
            """
            A no-op placeholder component used as the Trellis top component in tests.
            
            Intended solely as a minimal stand-in for a real component; it performs no actions.
            """
            pass

        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    host="0.0.0.0",
                    port=8080,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["host"] == "0.0.0.0"
        assert call_kwargs["port"] == 8080

    def test_serve_passes_custom_batch_delay_to_run(self, mock_platform: Mock) -> None:
        """serve() passes custom batch_delay to platform.run()."""

        def dummy_component() -> None:
            """
            A no-op placeholder component used as the Trellis top component in tests.
            
            Intended solely as a minimal stand-in for a real component; it performs no actions.
            """
            pass

        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(
                    top=dummy_component,
                    ignore_cli=True,
                    batch_delay=0.1,
                )

        asyncio.run(app.serve())

        call_kwargs = mock_platform.run.call_args.kwargs
        assert call_kwargs["batch_delay"] == pytest.approx(0.1)


class TestServeOrdering:
    """Tests for serve() operation ordering."""

    def test_serve_bundles_before_run(self, mock_platform: Mock) -> None:
        """serve() calls bundle() before run()."""
        call_order: list[str] = []

        def record_bundle(*args, **kwargs) -> None:
            """
            Record that a bundle operation occurred by appending "bundle" to the shared `call_order` list.
            
            Appends the string "bundle" to the module-level list `call_order`; any positional or keyword arguments are ignored.
            """
            call_order.append("bundle")

        async def record_run(*args, **kwargs) -> None:
            """
            Record that a platform run occurred by appending "run" to the shared call_order list.
            
            Appends the string "run" to the module-level `call_order` list. Any positional or keyword
            arguments are ignored.
            """
            call_order.append("run")

        mock_platform.bundle.side_effect = record_bundle
        mock_platform.run.side_effect = record_run

        def dummy_component() -> None:
            """
            A no-op placeholder component used as the Trellis top component in tests.
            
            Intended solely as a minimal stand-in for a real component; it performs no actions.
            """
            pass

        with patch("trellis.app.entry._get_platform", return_value=mock_platform):
            with patch("sys.argv", ["app"]):
                app = Trellis(top=dummy_component, ignore_cli=True)

        asyncio.run(app.serve())

        assert call_order == ["bundle", "run"]