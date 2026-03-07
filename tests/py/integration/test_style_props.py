from __future__ import annotations

from tests.conftest import find_element_by_type
from trellis import component
from trellis import html as h
from trellis import widgets as w


def test_widget_style_sugar_merges_into_typed_style(rendered) -> None:
    @component
    def App() -> None:
        w.Label(
            text="Test",
            margin=8,
            width=100,
            flex=1,
            style=h.Style(color="blue"),
        )

    result = rendered(App)
    label = find_element_by_type(result.tree, "Label")

    assert label is not None
    assert label["props"]["style"] == {
        "color": "blue",
        "margin": "8px",
        "width": "100px",
        "flex": 1,
    }


def test_widget_style_accepts_dom_dict_escape_hatch(rendered) -> None:
    @component
    def App() -> None:
        w.Slider(
            width=240,
            style={
                "border-radius": "8px",
                ":hover": {"color": "red"},
            },
        )

    result = rendered(App)
    slider = find_element_by_type(result.tree, "Slider")

    assert slider is not None
    assert slider["props"]["style"] == {
        "border-radius": "8px",
        "width": "240px",
    }
    assert slider["props"]["class_name"].startswith("tcss_")
    assert ":hover" in slider["props"]["_style_rules"]


def test_table_uses_shared_widget_style_normalization(rendered) -> None:
    @component
    def App() -> None:
        w.Table(
            columns=["name"],
            data=[{"name": "Item"}],
            margin=8,
            width=320,
            height=240,
            style=h.Style(border=h.border(1, "solid", "red")),
        )

    result = rendered(App)
    table = find_element_by_type(result.tree, "TableInner")

    assert table is not None
    assert table["props"]["style"] == {
        "border": "1px solid red",
        "margin": "8px",
        "width": "320px",
        "height": "240px",
    }


def test_breadcrumb_uses_typed_html_styles(rendered) -> None:
    @component
    def App() -> None:
        w.Breadcrumb(
            items=[{"label": "Home", "href": "/"}, {"label": "Current"}],
            margin=8,
            style=h.Style(color="purple"),
        )

    result = rendered(App)
    nav = find_element_by_type(result.tree, "nav")

    assert nav is not None
    assert nav["props"]["style"] == {
        "display": "flex",
        "align-items": "center",
        "font-family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font-size": "0.875rem",
        "line-height": "1.5",
        "margin": "8px",
        "color": "purple",
    }
