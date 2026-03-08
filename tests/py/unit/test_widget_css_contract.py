from __future__ import annotations

import importlib
import typing as tp

import pytest

import trellis
from trellis import widgets as w
from trellis.html._style_runtime import SpacingInput, StyleInput, WidthInput
from trellis.widgets.icons import Icon


def test_widget_signatures_use_shared_css_types() -> None:
    label_hints = tp.get_type_hints(w.Label, include_extras=True)

    assert label_hints["margin"] == SpacingInput | None
    assert label_hints["width"] == WidthInput | None
    assert label_hints["style"] == StyleInput | None


def test_legacy_style_dataclasses_are_removed() -> None:
    assert not hasattr(trellis, "Margin")
    assert not hasattr(trellis, "Padding")
    assert not hasattr(trellis, "Width")
    assert not hasattr(trellis, "Height")

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("trellis.core.components.style_props")

    core_module = importlib.import_module("trellis.core")

    def read_margin() -> object:
        return core_module.Margin

    with pytest.raises(AttributeError):
        read_margin()


def test_icon_has_single_widget_style_wrapper() -> None:
    wrapped_layers_with_component = 0
    current = Icon

    while True:
        if hasattr(current, "_component"):
            wrapped_layers_with_component += 1
        if not hasattr(current, "__wrapped__"):
            break
        current = current.__wrapped__  # type: ignore[attr-defined]

    assert wrapped_layers_with_component == 2
