from __future__ import annotations

import inspect

from trellis import html as h
from trellis.widgets._style_props import widget_style_props


def test_widget_style_props_preserves_signature_and_component_attr() -> None:
    component_marker = object()

    def base(
        *,
        margin: h.SpacingInput | None = None,
        style: h.StyleInput | None = None,
    ) -> dict[str, object | None]:
        return {"margin": margin, "style": style}

    base._component = component_marker  # type: ignore[attr-defined]
    wrapped = widget_style_props("margin")(base)

    assert inspect.signature(wrapped) == inspect.signature(base)
    assert wrapped._component is component_marker  # type: ignore[attr-defined]


def test_widget_style_props_merges_declared_style_sugar() -> None:
    def base(
        *,
        margin: h.SpacingInput | None = None,
        width: h.WidthInput | None = None,
        style: h.StyleInput | None = None,
    ) -> dict[str, object | None]:
        return {"margin": margin, "width": width, "style": style}

    wrapped = widget_style_props("margin", "width")(base)

    result = wrapped(
        margin=8,
        width=240,
        style=h.Css(color="red"),
    )

    assert result == {
        "margin": None,
        "width": None,
        "style": {
            "margin": "8px",
            "width": "240px",
            "color": "red",
        },
    }
