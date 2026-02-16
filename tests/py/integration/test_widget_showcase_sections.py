"""Integration tests for widget showcase sections."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest


def _import_showcase_module(module_name: str, monkeypatch: pytest.MonkeyPatch):
    app_root = Path(__file__).resolve().parents[3] / "examples" / "widget_showcase"
    monkeypatch.syspath_prepend(str(app_root))
    return importlib.import_module(module_name)


def _collect_label_texts(node: dict[str, Any]) -> list[str]:
    texts: list[str] = []

    def _visit(current: Any) -> None:
        if not isinstance(current, dict):
            return
        if current.get("name") == "Label":
            text = current.get("props", {}).get("text")
            if isinstance(text, str):
                texts.append(text)
        for child in current.get("children", []):
            _visit(child)

    _visit(node)
    return texts


class TestWidgetShowcaseSections:
    """Section-level behavior tests for widget showcase."""

    def test_form_inputs_section_excludes_desktop_dialogs(
        self, rendered, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        forms_module = _import_showcase_module("widget_showcase.sections.forms", monkeypatch)

        result = rendered(forms_module.FormInputsSection)
        label_texts = _collect_label_texts(result.tree)

        assert "Desktop File Dialogs" not in label_texts

