from __future__ import annotations

from trellis import html as h
from trellis.html._style_compiler import merge_style_inputs


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
