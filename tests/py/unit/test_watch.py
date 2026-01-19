"""Unit tests for bundler watch functionality."""

from __future__ import annotations


class TestWatchAndRebuildSignature:
    """Tests for watch_and_rebuild function signature."""

    def test_accepts_steps_parameter(self) -> None:
        """watch_and_rebuild accepts a steps parameter."""
        import inspect

        from trellis.bundler.watch import watch_and_rebuild

        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "steps" in params

    def test_on_rebuild_signature(self) -> None:
        """watch_and_rebuild accepts an on_rebuild callback parameter."""
        import inspect

        from trellis.bundler.watch import watch_and_rebuild

        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "on_rebuild" in params

    def test_on_rebuild_default_is_none(self) -> None:
        """on_rebuild parameter defaults to None."""
        import inspect

        from trellis.bundler.watch import watch_and_rebuild

        sig = inspect.signature(watch_and_rebuild)
        param = sig.parameters["on_rebuild"]

        assert param.default is None
