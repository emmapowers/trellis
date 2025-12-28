"""Tests for trellis.utils module."""

from __future__ import annotations

import asyncio
import logging
import subprocess
import sys
import textwrap

import pytest


class TestAsyncMain:
    def test_runs_when_main(self) -> None:
        """@async_main runs the function when module is __main__."""
        code = textwrap.dedent(
            """
            from trellis.utils import async_main

            @async_main
            async def main() -> None:
                print("executed")
        """
        )

        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "executed" in result.stdout

    def test_does_not_run_when_imported(self) -> None:
        """@async_main does not run when module is imported."""
        # When imported (not as __main__), the decorator should not run the function
        from trellis.utils import async_main

        ran = False

        @async_main
        async def main() -> None:
            nonlocal ran
            ran = True

        # The function should not have been executed
        assert not ran

    def test_returns_callable(self) -> None:
        """@async_main returns the original function."""
        from trellis.utils import async_main

        @async_main
        async def main() -> None:
            pass

        # Should still be callable
        assert callable(main)
        # Should be a coroutine function
        assert asyncio.iscoroutinefunction(main)


class TestSetupLogging:
    def test_setup_logging_configures_root_logger(self) -> None:
        """setup_logging configures the root logger."""
        from trellis.utils import setup_logging

        # Clear any existing handlers
        root = logging.getLogger()
        original_handlers = root.handlers.copy()
        root.handlers.clear()

        try:
            setup_logging(level=logging.DEBUG)

            assert len(root.handlers) > 0
            assert root.level == logging.DEBUG
        finally:
            # Restore original handlers
            root.handlers = original_handlers

    def test_setup_logging_defaults_to_info(self) -> None:
        """setup_logging defaults to INFO level."""
        from trellis.utils import setup_logging

        root = logging.getLogger()
        original_handlers = root.handlers.copy()
        original_level = root.level
        root.handlers.clear()

        try:
            setup_logging()
            assert root.level == logging.INFO
        finally:
            root.handlers = original_handlers
            root.level = original_level


class TestLogger:
    def test_logger_returns_logger_for_caller(self) -> None:
        """logger import returns a logger named for the importing module."""
        from trellis.utils.logger import logger

        # Should return a logger for this test module
        assert isinstance(logger, logging.Logger)
        assert logger.name == __name__

    def test_logger_different_per_module(self) -> None:
        """Different modules get different logger names."""
        # Import from a subprocess to test different module context
        code = textwrap.dedent(
            """
            from trellis.utils.logger import logger
            print(logger.name)
        """
        )

        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "__main__" in result.stdout

    def test_logger_raises_for_unknown_attr(self) -> None:
        """Accessing unknown attributes raises AttributeError."""
        import trellis.utils.logger as logger_module

        with pytest.raises(AttributeError, match="unknown_attr"):
            _ = logger_module.unknown_attr  # type: ignore[attr-defined]
