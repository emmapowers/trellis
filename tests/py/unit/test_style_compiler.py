from __future__ import annotations

import pytest

from trellis import html as h
from trellis.html._style_compiler import compile_css_class, compile_style_props, merge_style_inputs


def test_merge_style_inputs_combines_flat_properties() -> None:
    merged = merge_style_inputs(
        h.Css(color="red", padding=16),
        h.Css(padding=24, gap=8),
    )

    assert merged is not None
    assert merged["color"] == "red"
    assert merged["padding"] == "24px"
    assert merged["gap"] == "8px"


def test_merge_style_inputs_overlay_wins() -> None:
    merged = merge_style_inputs(
        h.Css(color="red"),
        h.Css(color="green"),
    )

    assert merged is not None
    assert merged["color"] == "green"


def test_compile_css_class_keeps_unitless_line_height_numeric() -> None:
    cls = h.CssClass(
        "test-lh",
        line_height=1.5,
        hover=h.Css(line_height=1.1),
    )

    css = compile_css_class(cls)
    assert "line-height:1.5" in css
    assert "line-height:1.1" in css
    assert "line-height:1.1px" not in css


def test_compile_css_class_emits_selector_and_media_rules() -> None:
    cls = h.CssClass(
        "test-combo",
        color="red",
        hover=h.Css(color="blue"),
        media=[
            h.media(
                min_width=960,
                style=h.Css(padding=32),
            )
        ],
    )

    css = compile_css_class(cls)
    assert ".test-combo{" in css
    assert "color:red" in css
    assert ".test-combo:hover{" in css
    assert "color:blue" in css
    assert "@media (min-width: 960px)" in css
    assert "padding:32px" in css


def test_compile_css_class_serializes_full_media_rule_surface() -> None:
    cls = h.CssClass(
        "test-media",
        media=[
            h.media(
                style=h.Css(color="red"),
                min_width=720,
                display_mode="browser",
                any_hover="hover",
                color=8,
                aspect_ratio="16/9",
            )
        ],
    )

    css = compile_css_class(cls)
    assert "@media" in css
    assert "(min-width: 720px)" in css
    assert "(display-mode: browser)" in css
    assert "(any-hover: hover)" in css
    assert "(color: 8)" in css
    assert "(aspect-ratio: 16/9)" in css


def test_compile_css_class_rejects_empty_media_rules() -> None:
    with pytest.raises(ValueError, match="MediaRule must define"):
        compile_css_class(h.CssClass("test-empty", media=[h.MediaRule(style=h.Css())]))


def test_compile_css_class_is_deterministic() -> None:
    """Same CssClass input must always produce the same CSS output."""
    cls = h.CssClass(
        "test-deterministic",
        color="red",
        padding=16,
        line_height=1.5,
        hover=h.Css(color="blue", opacity=0.9),
        media=[
            h.media(min_width=768, style=h.Css(padding=32, gap=12)),
        ],
    )

    first = compile_css_class(cls)
    for _ in range(20):
        assert compile_css_class(cls) == first


def test_compile_style_props_compiles_inline_style() -> None:
    """compile_style_props converts a Css object to a flat CSS dict."""
    props = {"style": h.Css(color="red", padding=16)}
    result = compile_style_props(props)
    assert result["style"]["color"] == "red"
    assert result["style"]["padding"] == "16px"
