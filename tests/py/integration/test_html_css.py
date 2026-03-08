from __future__ import annotations

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
                color="rebeccapurple",
                background_color="#f0f0f0",
            )
        )

    result = rendered(App)
    div = result.tree["children"][0]

    assert div["props"]["style"] == {
        "width": "320px",
        "display": "flex",
        "opacity": 0.5,
        "color": "rebeccapurple",
        "background-color": "#f0f0f0",
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


def test_style_accepts_unvalidated_raw_dict_keys(rendered) -> None:
    @component
    def App() -> None:
        h.Div(
            style={
                "backgroundColor": "red",
                "border_radius": "8px",
            }
        )

    result = rendered(App)
    div = result.tree["children"][0]

    assert div["props"]["style"] == {
        "backgroundColor": "red",
        "border_radius": "8px",
    }


def test_style_serializes_modern_color_helpers(rendered) -> None:
    @component
    def App() -> None:
        h.Div(
            style=h.Style(
                background_color=h.hwb(210, 15, 10),
                border_color=h.lab(55.5, 18, -12),
                outline_color=h.lch(62, 34, 270),
                color=h.oklch(0.72, 0.18, 245, alpha=0.8),
                text_decoration_color=h.oklab(0.68, 0.08, -0.14),
                accent_color=h.color_space("display-p3", 0.2, 0.5, 0.7, alpha=0.9),
            )
        )

    result = rendered(App)
    div = result.tree["children"][0]

    assert div["props"]["style"] == {
        "background-color": "hwb(210 15% 10%)",
        "border-color": "lab(55.5% 18 -12)",
        "outline-color": "lch(62% 34 270)",
        "color": "oklch(72% 0.18 245 / 0.8)",
        "text-decoration-color": "oklab(68% 0.08 -0.14)",
        "accent-color": "color(display-p3 0.2 0.5 0.7 / 0.9)",
    }


def test_style_serializes_shadow_helper_lengths_with_units(rendered) -> None:
    @component
    def App() -> None:
        h.Div(style=h.Style(box_shadow=h.shadow(0, 18, 40, h.rgba(8, 15, 30, 0.16))))

    result = rendered(App)
    div = result.tree["children"][0]

    assert div["props"]["style"]["box-shadow"] == "0px 18px 40px rgb(8 15 30 / 0.16)"
