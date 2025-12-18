"""Tests for ergonomic style props."""

from trellis.core.composition_component import component
from trellis.core.react_component import _merge_style_props
from trellis.core.rendering import RenderTree
from trellis.core.style_props import Height, Margin, Padding, Width
from trellis.widgets import Button, Card, Column, Label, Row


class TestMargin:
    """Tests for Margin dataclass."""

    def test_margin_single_side(self) -> None:
        """Margin with single side."""
        m = Margin(top=8)
        assert m.to_style() == {"marginTop": "8px"}

    def test_margin_multiple_sides(self) -> None:
        """Margin with multiple sides."""
        m = Margin(top=8, bottom=16)
        assert m.to_style() == {"marginTop": "8px", "marginBottom": "16px"}

    def test_margin_x_shorthand(self) -> None:
        """Margin x shorthand sets left and right."""
        m = Margin(x=8)
        assert m.to_style() == {"marginLeft": "8px", "marginRight": "8px"}

    def test_margin_y_shorthand(self) -> None:
        """Margin y shorthand sets top and bottom."""
        m = Margin(y=16)
        assert m.to_style() == {"marginTop": "16px", "marginBottom": "16px"}

    def test_margin_specific_overrides_shorthand(self) -> None:
        """Specific sides override shorthands."""
        m = Margin(x=8, left=12)
        assert m.to_style() == {"marginLeft": "12px", "marginRight": "8px"}


class TestPadding:
    """Tests for Padding dataclass."""

    def test_padding_single_side(self) -> None:
        """Padding with single side."""
        p = Padding(top=8)
        assert p.to_style() == {"paddingTop": "8px"}

    def test_padding_xy_shorthands(self) -> None:
        """Padding with x and y shorthands."""
        p = Padding(x=8, y=16)
        assert p.to_style() == {
            "paddingLeft": "8px",
            "paddingRight": "8px",
            "paddingTop": "16px",
            "paddingBottom": "16px",
        }


class TestWidth:
    """Tests for Width dataclass."""

    def test_width_value_int(self) -> None:
        """Width with int value converts to px."""
        w = Width(value=100)
        assert w.to_style() == {"width": "100px"}

    def test_width_value_string(self) -> None:
        """Width with string value passes through."""
        w = Width(value="100%")
        assert w.to_style() == {"width": "100%"}

    def test_width_with_constraints(self) -> None:
        """Width with min and max constraints."""
        w = Width(value=200, min=100, max=400)
        assert w.to_style() == {
            "width": "200px",
            "minWidth": "100px",
            "maxWidth": "400px",
        }

    def test_width_min_max_only(self) -> None:
        """Width with only constraints, no value."""
        w = Width(min=100, max=400)
        assert w.to_style() == {"minWidth": "100px", "maxWidth": "400px"}


class TestHeight:
    """Tests for Height dataclass."""

    def test_height_value(self) -> None:
        """Height with value."""
        h = Height(value=300)
        assert h.to_style() == {"height": "300px"}

    def test_height_max_string(self) -> None:
        """Height with string max (e.g., viewport units)."""
        h = Height(max="60vh")
        assert h.to_style() == {"maxHeight": "60vh"}


class TestMergeStyleProps:
    """Tests for _merge_style_props function."""

    def test_margin_dataclass_converted(self) -> None:
        """Margin dataclass is converted to style dict."""
        props = {"margin": Margin(top=8)}
        result = _merge_style_props(props)
        assert "margin" not in result
        assert result["style"] == {"marginTop": "8px"}

    def test_margin_int_passed_through(self) -> None:
        """Margin int value is passed through (widget-specific)."""
        props = {"margin": 8}
        result = _merge_style_props(props)
        assert result["margin"] == 8
        assert "style" not in result

    def test_padding_dataclass_converted(self) -> None:
        """Padding dataclass is converted to style dict."""
        props = {"padding": Padding(x=16)}
        result = _merge_style_props(props)
        assert "padding" not in result
        assert result["style"] == {"paddingLeft": "16px", "paddingRight": "16px"}

    def test_padding_int_passed_through(self) -> None:
        """Padding int value is passed through (widget-specific)."""
        props = {"padding": 16}
        result = _merge_style_props(props)
        assert result["padding"] == 16
        assert "style" not in result

    def test_width_int_converted(self) -> None:
        """Width int is converted to style (generic)."""
        props = {"width": 200}
        result = _merge_style_props(props)
        assert "width" not in result
        assert result["style"] == {"width": "200px"}

    def test_width_string_converted(self) -> None:
        """Width string is converted to style."""
        props = {"width": "100%"}
        result = _merge_style_props(props)
        assert result["style"] == {"width": "100%"}

    def test_width_dataclass_converted(self) -> None:
        """Width dataclass is converted to style."""
        props = {"width": Width(value=200, max=400)}
        result = _merge_style_props(props)
        assert result["style"] == {"width": "200px", "maxWidth": "400px"}

    def test_height_dataclass_converted(self) -> None:
        """Height dataclass is converted to style."""
        props = {"height": Height(value=300)}
        result = _merge_style_props(props)
        assert result["style"] == {"height": "300px"}

    def test_height_int_passed_through(self) -> None:
        """Height int value is passed through (widget-specific, e.g., ProgressBar)."""
        props = {"height": 12}
        result = _merge_style_props(props)
        assert result["height"] == 12
        assert "style" not in result

    def test_flex_converted(self) -> None:
        """Flex is converted to style."""
        props = {"flex": 1}
        result = _merge_style_props(props)
        assert result["style"] == {"flex": 1}

    def test_existing_style_preserved(self) -> None:
        """Existing style dict is preserved and extended."""
        props = {"style": {"color": "red"}, "width": 200, "flex": 1}
        result = _merge_style_props(props)
        assert result["style"] == {"color": "red", "width": "200px", "flex": 1}

    def test_multiple_props_combined(self) -> None:
        """Multiple style props are combined."""
        props = {
            "margin": Margin(top=8),
            "padding": Padding(x=16),
            "width": 200,
            "flex": 1,
        }
        result = _merge_style_props(props)
        assert result["style"] == {
            "marginTop": "8px",
            "paddingLeft": "16px",
            "paddingRight": "16px",
            "width": "200px",
            "flex": 1,
        }


class TestWidgetIntegration:
    """Integration tests for style props with widgets."""

    def test_label_with_margin(self) -> None:
        """Label accepts Margin dataclass."""

        @component
        def App() -> None:
            Label(text="Test", margin=Margin(bottom=16))

        ctx = RenderTree(App)
        ctx.render()

        label = ctx.root_node.children[0]
        assert label.properties["style"] == {"marginBottom": "16px"}

    def test_label_with_width(self) -> None:
        """Label accepts width prop."""

        @component
        def App() -> None:
            Label(text="Test", width=100)

        ctx = RenderTree(App)
        ctx.render()

        label = ctx.root_node.children[0]
        assert label.properties["style"] == {"width": "100px"}

    def test_label_with_flex(self) -> None:
        """Label accepts flex prop."""

        @component
        def App() -> None:
            Label(text="Test", flex=1)

        ctx = RenderTree(App)
        ctx.render()

        label = ctx.root_node.children[0]
        assert label.properties["style"] == {"flex": 1}

    def test_column_with_padding_dataclass(self) -> None:
        """Column accepts Padding dataclass."""

        @component
        def App() -> None:
            with Column(padding=Padding(x=24, y=16)):
                Label(text="Test")

        ctx = RenderTree(App)
        ctx.render()

        column = ctx.root_node.children[0]
        assert column.properties["style"] == {
            "paddingLeft": "24px",
            "paddingRight": "24px",
            "paddingTop": "16px",
            "paddingBottom": "16px",
        }

    def test_column_with_padding_int(self) -> None:
        """Column accepts padding int (passed to React)."""

        @component
        def App() -> None:
            with Column(padding=24):
                Label(text="Test")

        ctx = RenderTree(App)
        ctx.render()

        column = ctx.root_node.children[0]
        assert column.properties["padding"] == 24

    def test_card_with_width(self) -> None:
        """Card accepts width prop."""

        @component
        def App() -> None:
            with Card(width=320):
                Label(text="Test")

        ctx = RenderTree(App)
        ctx.render()

        card = ctx.root_node.children[0]
        assert card.properties["style"] == {"width": "320px"}

    def test_button_with_width_string(self) -> None:
        """Button accepts width string."""

        @component
        def App() -> None:
            Button(text="Test", width="100%")

        ctx = RenderTree(App)
        ctx.render()

        button = ctx.root_node.children[0]
        assert button.properties["style"] == {"width": "100%"}

    def test_style_props_merge_with_existing_style(self) -> None:
        """Style props merge with existing style dict."""

        @component
        def App() -> None:
            Label(
                text="Test",
                margin=Margin(bottom=8),
                width=100,
                style={"color": "blue", "fontWeight": "bold"},
            )

        ctx = RenderTree(App)
        ctx.render()

        label = ctx.root_node.children[0]
        assert label.properties["style"] == {
            "color": "blue",
            "fontWeight": "bold",
            "marginBottom": "8px",
            "width": "100px",
        }
