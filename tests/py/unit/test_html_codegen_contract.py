"""Contract tests for codegen-aligned HTML API conventions."""

from __future__ import annotations

import importlib

import pytest

from trellis import html as h
from trellis.html._generated_runtime import _A
from trellis.html._generated_runtime import Button as RawButton
from trellis.html._generated_runtime import Label as RawLabel


def test_generated_runtime_keeps_internal_anchor_binding_private() -> None:
    assert _A.__name__ == "_A"
    assert not hasattr(h, "_A")


def test_public_html_uses_generated_button_and_label_names() -> None:
    """Public HTML exports should use generated Button/Label names directly."""
    assert h.Button is RawButton
    assert h.Label is RawLabel
    assert not hasattr(h, "HtmlButton")
    assert not hasattr(h, "HtmlLabel")


@pytest.mark.parametrize(
    "module_name",
    [
        "trellis.html.forms",
        "trellis.html.layout",
        "trellis.html.lists",
        "trellis.html.media",
        "trellis.html.tables",
        "trellis.html.events",
    ],
)
def test_public_html_category_modules_are_removed(module_name: str) -> None:
    """HTML category modules are internal-only and no longer importable."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(module_name)


def test_public_html_still_exports_generated_event_types() -> None:
    """Event types remain publicly available from trellis.html."""
    assert h.MouseEvent.__name__ == "MouseEvent"
    assert "Callable" in repr(h.EventHandler)
    assert "Event" in repr(h.EventHandler)


def test_public_html_exports_full_generated_surface() -> None:
    for name in ("Area", "Canvas", "Map", "Picture", "Track", "Wbr"):
        assert hasattr(h, name)


def test_public_html_exports_style_input() -> None:
    """The HTML namespace should expose the public style input alias."""
    assert hasattr(h, "StyleInput")


def test_base_module_no_longer_exports_legacy_style_alias() -> None:
    """The old dict Style alias should not remain in html.base."""
    base = importlib.import_module("trellis.html.base")

    assert "Style" not in base.__all__
    assert not hasattr(base, "Style")
