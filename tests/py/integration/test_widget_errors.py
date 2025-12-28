"""Tests for widget edge cases and error handling.

These tests document how widgets behave with edge case inputs like
invalid props, out-of-range values, and missing required data. The
current design philosophy is permissive - most invalid values are
passed to the React client without validation.
"""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.widgets import (
    Button,
    Heading,
    Label,
    NumberInput,
    Select,
    Slider,
    TextInput,
)


class TestSliderEdgeCases:
    """Tests for Slider widget with edge case values."""

    def test_slider_value_below_min(self) -> None:
        """Slider accepts value below min (validation is client-side)."""

        @component
        def App() -> None:
            Slider(value=-10, min=0, max=100)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["value"] == -10
        assert slider.properties["min"] == 0

    def test_slider_value_above_max(self) -> None:
        """Slider accepts value above max (validation is client-side)."""

        @component
        def App() -> None:
            Slider(value=200, min=0, max=100)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["value"] == 200
        assert slider.properties["max"] == 100

    def test_slider_min_greater_than_max(self) -> None:
        """Slider accepts min > max (validation is client-side)."""

        @component
        def App() -> None:
            Slider(value=50, min=100, max=0)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["min"] == 100
        assert slider.properties["max"] == 0

    def test_slider_zero_step(self) -> None:
        """Slider accepts step=0 (may cause client-side issues)."""

        @component
        def App() -> None:
            Slider(value=50, step=0)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["step"] == 0

    def test_slider_negative_step(self) -> None:
        """Slider accepts negative step (may cause client-side issues)."""

        @component
        def App() -> None:
            Slider(value=50, step=-5)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["step"] == -5


class TestNumberInputEdgeCases:
    """Tests for NumberInput widget with edge case values."""

    def test_number_input_value_below_min(self) -> None:
        """NumberInput accepts value below min (validation is client-side)."""

        @component
        def App() -> None:
            NumberInput(value=-10, min=0, max=100)

        ctx = RenderSession(App)
        render(ctx)

        input_el = ctx.elements.get(ctx.root_element.child_ids[0])
        assert input_el.properties["value"] == -10
        assert input_el.properties["min"] == 0

    def test_number_input_value_above_max(self) -> None:
        """NumberInput accepts value above max (validation is client-side)."""

        @component
        def App() -> None:
            NumberInput(value=200, min=0, max=100)

        ctx = RenderSession(App)
        render(ctx)

        input_el = ctx.elements.get(ctx.root_element.child_ids[0])
        assert input_el.properties["value"] == 200
        assert input_el.properties["max"] == 100


class TestSelectEdgeCases:
    """Tests for Select widget with edge case inputs."""

    def test_select_empty_options(self) -> None:
        """Select accepts empty options list."""

        @component
        def App() -> None:
            Select(options=[], value="")

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.elements.get(ctx.root_element.child_ids[0])
        assert select.properties["options"] == []

    def test_select_value_not_in_options(self) -> None:
        """Select accepts value not present in options (no validation)."""
        options = [
            {"value": "a", "label": "Option A"},
            {"value": "b", "label": "Option B"},
        ]

        @component
        def App() -> None:
            Select(options=options, value="not_in_list")

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.elements.get(ctx.root_element.child_ids[0])
        assert select.properties["value"] == "not_in_list"

    def test_select_none_value(self) -> None:
        """Select accepts None as value."""
        options = [
            {"value": "a", "label": "Option A"},
        ]

        @component
        def App() -> None:
            Select(options=options, value=None)  # type: ignore[arg-type]

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.elements.get(ctx.root_element.child_ids[0])
        assert select.properties["value"] is None


class TestHeadingEdgeCases:
    """Tests for Heading widget with edge case values."""

    def test_heading_level_zero(self) -> None:
        """Heading accepts level=0 (invalid HTML, client handles it)."""

        @component
        def App() -> None:
            Heading(text="Zero", level=0)

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.elements.get(ctx.root_element.child_ids[0])
        assert heading.properties["level"] == 0

    def test_heading_level_beyond_range(self) -> None:
        """Heading accepts level=7+ (invalid HTML, client handles it)."""

        @component
        def App() -> None:
            Heading(text="Seven", level=7)

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.elements.get(ctx.root_element.child_ids[0])
        assert heading.properties["level"] == 7


class TestButtonEdgeCases:
    """Tests for Button widget with edge case callbacks."""

    def test_button_with_none_callback(self) -> None:
        """Button accepts None callback."""

        @component
        def App() -> None:
            Button(text="No callback", on_click=None)

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.elements.get(ctx.root_element.child_ids[0])
        assert button.properties["on_click"] is None

    def test_button_callback_exception_propagates(self) -> None:
        """Exceptions from button callbacks propagate when invoked."""

        def failing_callback() -> None:
            raise ValueError("Callback failed")

        @component
        def App() -> None:
            Button(text="Fail", on_click=failing_callback)

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.elements.get(ctx.root_element.child_ids[0])

        import pytest

        with pytest.raises(ValueError, match="Callback failed"):
            button.properties["on_click"]()


class TestTextInputEdgeCases:
    """Tests for TextInput widget with edge case inputs."""

    def test_text_input_with_none_callback(self) -> None:
        """TextInput accepts None on_change callback."""

        @component
        def App() -> None:
            TextInput(value="test", on_change=None)

        ctx = RenderSession(App)
        render(ctx)

        input_el = ctx.elements.get(ctx.root_element.child_ids[0])
        assert input_el.properties["on_change"] is None


class TestLabelEdgeCases:
    """Tests for Label widget with edge case inputs."""

    def test_label_empty_text(self) -> None:
        """Label accepts empty string."""

        @component
        def App() -> None:
            Label(text="")

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.elements.get(ctx.root_element.child_ids[0])
        assert label.properties["text"] == ""

    def test_label_no_text_argument(self) -> None:
        """Label without text argument omits text from properties."""

        @component
        def App() -> None:
            Label()  # No text argument

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.elements.get(ctx.root_element.child_ids[0])
        # text prop is not included when using default empty string
        assert "text" not in label.properties or label.properties.get("text") == ""

    def test_label_negative_font_size(self) -> None:
        """Label accepts negative font_size (client handles it)."""

        @component
        def App() -> None:
            Label(text="Tiny?", font_size=-10)

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.elements.get(ctx.root_element.child_ids[0])
        assert label.properties["font_size"] == -10
