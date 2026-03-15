"""Tests for widget showcase example source capture."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest


class TestNavigationExamples:
    def test_tree_example_source_is_self_contained(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.syspath_prepend(str(Path("examples/widget_showcase").resolve()))

        from widget_showcase.sections.navigation import TreeExample  # noqa: PLC0415

        assert "cast(" not in TreeExample.source

    def test_config_accepts_string_icon_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.syspath_prepend(str(Path("examples/widget_showcase").resolve()))

        from trellis.app.config import Config  # noqa: PLC0415

        trellis_config = importlib.import_module("trellis_config")

        assert isinstance(trellis_config.config, Config)
        assert trellis_config.config.icon == Path("assets/icon.png")
