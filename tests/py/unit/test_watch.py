"""Unit tests for bundler watch functionality."""

from __future__ import annotations

import inspect

from trellis.bundler.watch import watch_and_rebuild


class TestWatchAndRebuildSignature:
    """Tests for watch_and_rebuild function signature."""

    def test_accepts_workspace_parameter(self) -> None:
        """watch_and_rebuild accepts a workspace parameter."""
        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "workspace" in params

    def test_accepts_rebuild_parameter(self) -> None:
        """watch_and_rebuild accepts a rebuild callback parameter."""
        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "rebuild" in params

    def test_on_rebuild_signature(self) -> None:
        """watch_and_rebuild accepts an on_rebuild callback parameter."""
        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "on_rebuild" in params

    def test_on_rebuild_default_is_none(self) -> None:
        """on_rebuild parameter defaults to None."""
        sig = inspect.signature(watch_and_rebuild)
        param = sig.parameters["on_rebuild"]

        assert param.default is None

    def test_does_not_accept_registry_parameter(self) -> None:
        """watch_and_rebuild no longer accepts registry parameter (simplified API)."""
        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "registry" not in params

    def test_does_not_accept_entry_point_parameter(self) -> None:
        """watch_and_rebuild no longer accepts entry_point parameter (simplified API)."""
        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "entry_point" not in params

    def test_does_not_accept_steps_parameter(self) -> None:
        """watch_and_rebuild no longer accepts steps parameter (simplified API)."""
        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "steps" not in params

    def test_does_not_accept_output_dir_parameter(self) -> None:
        """watch_and_rebuild no longer accepts output_dir parameter (simplified API)."""
        sig = inspect.signature(watch_and_rebuild)
        params = list(sig.parameters.keys())

        assert "output_dir" not in params
