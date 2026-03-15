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


def test_css_class_compiles_hover_media_and_selectors() -> None:
    """CssClass compiles pseudo-selectors and media rules to CSS text."""
    cls = h.CssClass(
        "test-cls",
        color="black",
        hover=h.Css(color="red"),
        media=[
            h.media(min_width=768, style=h.Css(padding=24)),
        ],
    )

    css = str(cls)
    assert ".test-cls{" in css
    assert "color:black" in css
    assert ".test-cls:hover{" in css
    assert "color:red" in css
    assert "@media (min-width: 768px)" in css
    assert "padding:24px" in css


def test_style_preserves_raw_dict_keys(rendered) -> None:
    """Raw dict style is the escape hatch — keys pass through verbatim."""

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

    assert div["props"]["style"] == {"backgroundColor": "red", "border_radius": "8px"}


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


def test_css_class_compiles_permissive_kwargs_and_nested_raw_mappings() -> None:
    """CssClass handles selectors and media with nested raw mappings."""
    cls = h.CssClass(
        "test-permissive",
        backgroundColor="red",
        border_radius=8,
        vars={"--accent": h.rgb(10, 20, 30)},
        selectors={
            "& > span": h.Css(margin_top=4),
            "&:focus-visible": {"outlineWidth": 3},
        },
        media=[
            h.media(
                min_width=640,
                style=h.Css(padding_inline=h.rem(2)),
            ),
        ],
    )

    css = str(cls)
    assert ".test-permissive{" in css
    assert "background-color:red" in css
    assert "border-radius:8px" in css
    assert "--accent:rgb(10 20 30)" in css
    assert "> span" in css
    assert "margin-top:4px" in css
    assert ":focus-visible" in css
    assert "@media (min-width: 640px)" in css
    assert "padding-inline:2rem" in css
