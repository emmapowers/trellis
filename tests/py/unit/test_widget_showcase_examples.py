"""Tests for widget showcase example source capture."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestNavigationExamples:
    def test_tree_example_source_is_self_contained(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.syspath_prepend(str(Path("examples/widget_showcase").resolve()))

        from widget_showcase.sections.navigation import TreeExample  # noqa: PLC0415

        assert "cast(" not in TreeExample.source
