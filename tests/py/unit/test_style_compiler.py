from __future__ import annotations

from trellis import html as h
from trellis.html._style_compiler import compile_style, merge_style_inputs


def test_merge_style_inputs_deep_merges_nested_selectors_and_media() -> None:
    merged = merge_style_inputs(
        h.Style(
            color="red",
            hover=h.Style(color="blue", background_color="white"),
            media=[h.media(min_width=768, style=h.Style(padding=16, gap=8))],
        ),
        {
            ":hover": {"border-color": "black"},
            "@media (min-width: 768px)": {"gap": "12px", "margin": "4px"},
        },
    )

    assert merged == {
        "color": "red",
        ":hover": {
            "color": "blue",
            "background-color": "white",
            "border-color": "black",
        },
        "@media (min-width: 768px)": {
            "padding": "16px",
            "gap": "12px",
            "margin": "4px",
        },
    }


def test_merge_style_inputs_overlay_wins_at_leaf_level() -> None:
    merged = merge_style_inputs(
        {":hover": {"color": "blue"}},
        {":hover": {"color": "green"}},
    )

    assert merged == {
        ":hover": {
            "color": "green",
        }
    }


def test_compile_style_keeps_unitless_line_height_numeric() -> None:
    inline, class_name, style_rules = compile_style(
        h.Style(
            line_height=1.5,
            hover=h.Style(line_height=1.1),
        )
    )

    assert inline["line-height"] == 1.5
    assert class_name is not None
    assert style_rules is not None
    assert "line-height:1.1;" in style_rules
    assert "line-height:1.1px;" not in style_rules


def test_compile_style_omits_empty_selector_blocks_inside_media_rules() -> None:
    inline, class_name, style_rules = compile_style(
        h.Style(
            selectors={"& > * + *": h.Style(margin_top=24)},
            media=[
                h.media(
                    min_width=960,
                    style=h.Style(
                        selectors={"& > * + *": h.Style(margin_top=32)},
                    ),
                )
            ],
        )
    )

    assert inline == {}
    assert class_name is not None
    assert style_rules is not None
    assert f"{class_name}{{}}" not in style_rules
    assert ">{}" not in style_rules
    assert "@media (min-width: 960px)" in style_rules
    assert "> * + *{margin-top:32px;}" in style_rules
