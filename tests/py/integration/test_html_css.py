from __future__ import annotations

import pytest

from trellis import component
from trellis import html as h


def test_style_compiles_inline_css(rendered) -> None:
    @component
    def App() -> None:
        h.Div(
            style=h.Style(
                width=h.px(320),
                display="flex",
                opacity=0.5,
                color=h.rgb(12, 34, 56),
            )
        )

    result = rendered(App)
    div = result.tree["children"][0]

    assert div["props"]["style"] == {
        "width": "320px",
        "display": "flex",
        "opacity": 0.5,
        "color": "rgb(12 34 56)",
    }
    assert "_style_rules" not in div["props"]


def test_style_compiles_hover_media_and_selectors(rendered) -> None:
    @component
    def App() -> None:
        h.Div(
            style=h.Style(
                color=h.rgb(0, 0, 0),
                hover=h.Style(color=h.rgb(255, 0, 0)),
                media=[
                    h.media(min_width=h.px(768), style=h.Style(padding=h.px(24))),
                ],
                selectors={"& > *": h.Style(margin_bottom=h.px(8))},
            )
        )

    result = rendered(App)
    div = result.tree["children"][0]

    assert div["props"]["class_name"].startswith("tcss_")
    assert ":hover" in div["props"]["_style_rules"]
    assert "@media (min-width: 768px)" in div["props"]["_style_rules"]
    assert "> *" in div["props"]["_style_rules"]
    assert div["props"]["style"] == {"color": "rgb(0 0 0)"}


def test_style_accepts_dom_dict_escape_hatch(rendered) -> None:
    @component
    def App() -> None:
        h.Div(
            style={
                "border-radius": "8px",
                ":hover": {"color": "red"},
                "@media (min-width: 768px)": {"padding": "24px"},
            }
        )

    result = rendered(App)
    div = result.tree["children"][0]

    assert div["props"]["style"] == {"border-radius": "8px"}
    assert div["props"]["class_name"].startswith("tcss_")
    assert ":hover" in div["props"]["_style_rules"]
    assert "@media (min-width: 768px)" in div["props"]["_style_rules"]


def test_style_rejects_non_dom_dict_keys(rendered) -> None:
    @component
    def App() -> None:
        h.Div(
            style={
                "backgroundColor": "red",
                "border_radius": "8px",
            }
        )

    with pytest.raises(TypeError, match="DOM-style CSS names"):
        rendered(App)
