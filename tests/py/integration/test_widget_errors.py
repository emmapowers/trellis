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
        """
        Verify that a Slider preserves a provided value below its minimum while keeping the specified minimum property.
        
        This test renders a Slider with value -10 and min 0 and asserts the rendered element's `value` equals -10 and `min` equals 0.
        """

        @component
        def App() -> None:
            """
            Builds a minimal component tree containing a Slider configured with value -10, min 0, and max 100.
            
            Used in tests to verify that a Slider accepts a value below its declared minimum without automatic clamping.
            """
            Slider(value=-10, min=0, max=100)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["value"] == -10
        assert slider.properties["min"] == 0

    def test_slider_value_above_max(self) -> None:
        """
        Verify that a Slider retains a provided value greater than its max in rendered element properties.
        
        Asserts that the rendered slider's `value` equals the provided value and `max` equals the provided max.
        """

        @component
        def App() -> None:
            """
            Create an app component containing a Slider whose value is set to 200 while its bounds are 0 and 100.
            
            This component is intended for testing edge-case behavior when a slider's value lies outside its configured min/max.
            """
            Slider(value=200, min=0, max=100)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["value"] == 200
        assert slider.properties["max"] == 100

    def test_slider_min_greater_than_max(self) -> None:
        """
        Ensure Slider preserves the provided `min` and `max` properties when `min` is greater than `max`.
        
        Asserts that the rendered Slider element contains the exact `min` and `max` values supplied (no server-side validation).
        """

        @component
        def App() -> None:
            """
            Builds a minimal component tree containing a Slider configured with value 50, min 100, and max 0.
            
            This component is used in tests to verify that a Slider accepts a value outside the specified min/max bounds (permissive client-side validation); it does not perform validation or raise errors.
            """
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
            """
            Create a minimal app that renders a Slider configured with value 50 and step 0.
            
            Used by tests to exercise Slider behavior when the step is zero.
            """
            Slider(value=50, step=0)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert slider.properties["step"] == 0

    def test_slider_negative_step(self) -> None:
        """
        Verifies the Slider preserves a negative step value when rendered.
        
        Asserts that the rendered slider element's "step" property equals the negative value provided (e.g., -5).
        """

        @component
        def App() -> None:
            """
            Create an application containing a Slider widget configured with a value of 50 and a negative step (-5) to exercise handling of negative step values.
            """
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
            """
            Create a minimal app that renders a NumberInput with value -10 and min 0 and max 100.
            
            This component is used to exercise permissive client-side validation by providing a value below the declared minimum.
            """
            NumberInput(value=-10, min=0, max=100)

        ctx = RenderSession(App)
        render(ctx)

        input_el = ctx.elements.get(ctx.root_element.child_ids[0])
        assert input_el.properties["value"] == -10
        assert input_el.properties["min"] == 0

    def test_number_input_value_above_max(self) -> None:
        """
        Preserves a provided value greater than the specified max for NumberInput and leaves the max property unchanged.
        
        Asserts that rendering a NumberInput with value=200 and max=100 results in an element whose `value` is 200 and whose `max` is 100.
        """

        @component
        def App() -> None:
            """
            Create a test App that renders a NumberInput initialized with value 200 while min is 0 and max is 100.
            
            Used by tests to verify that NumberInput accepts a value outside its defined min/max without clamping.
            """
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
            """
            Create a test app that renders a Select widget configured with an empty options list and an empty-string value.
            """
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
            """
            Construct an application component containing a Select whose `value` is not present in `options`.
            
            This App builds a Select with `value="not_in_list"` to exercise and document behavior when the selected value is not included in the provided options list.
            """
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
            """
            Render a Select component with an explicit None value.
            
            Used by tests to verify that a Select accepts `None` as its `value` prop while providing `options`.
            """
            Select(options=options, value=None)  # type: ignore[arg-type]

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.elements.get(ctx.root_element.child_ids[0])
        assert select.properties["value"] is None


class TestHeadingEdgeCases:
    """Tests for Heading widget with edge case values."""

    def test_heading_level_zero(self) -> None:
        """
        Verify that Heading accepts level=0 and that the rendered element preserves this value.
        
        Asserts that the rendered Heading element's "level" property is 0.
        """

        @component
        def App() -> None:
            """
            Create a minimal app containing a heading with text "Zero" at level 0.
            
            Used by tests to exercise rendering behavior when a Heading is given level=0.
            """
            Heading(text="Zero", level=0)

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.elements.get(ctx.root_element.child_ids[0])
        assert heading.properties["level"] == 0

    def test_heading_level_beyond_range(self) -> None:
        """Heading accepts level=7+ (invalid HTML, client handles it)."""

        @component
        def App() -> None:
            """
            Builds a minimal app containing a Heading with text "Seven" at level 7.
            
            This function constructs a Heading component with text "Seven" and level 7. It does not return a value.
            """
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
            """
            Create a component tree containing a Button whose `on_click` callback is explicitly set to None.
            
            This function is used by tests to render an app with a button that has no click handler.
            """
            Button(text="No callback", on_click=None)

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.elements.get(ctx.root_element.child_ids[0])
        assert button.properties["on_click"] is None

    def test_button_callback_exception_propagates(self) -> None:
        """Exceptions from button callbacks propagate when invoked."""

        def failing_callback() -> None:
            """
            Invoke a callback that always raises a ValueError.
            
            Raises:
                ValueError: Always raised with the message "Callback failed".
            """
            raise ValueError("Callback failed")

        @component
        def App() -> None:
            """
            Create an app component that renders a Button labeled "Fail" with its `on_click` set to `failing_callback`.
            
            This component is used in tests to exercise callback error propagation by invoking the Button's `on_click`, which raises an exception.
            """
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
            """
            Create a minimal app that renders a TextInput with the value "test" and no on_change handler.
            
            Used in tests to verify that a TextInput accepts None for its on_change callback and preserves the provided value.
            """
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
            """
            Create a minimal application component containing an empty Label.
            
            This helper constructs a component tree with a single Label whose text is the empty string and is intended for use in tests that render and inspect widget properties.
            """
            Label(text="")

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.elements.get(ctx.root_element.child_ids[0])
        assert label.properties["text"] == ""

    def test_label_no_text_argument(self) -> None:
        """Label without text argument omits text from properties."""

        @component
        def App() -> None:
            """
            Create a minimal App component that renders a Label without providing a `text` argument.
            
            Used by tests to verify rendering behavior when a Label is constructed with no text (expecting the rendered element to omit the text property or provide an empty default).
            """
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
            """
            Create an app that renders a Label with the text "Tiny?" and a negative font_size.
            
            This component is used to exercise how the system handles a Label whose `font_size` is less than zero.
            """
            Label(text="Tiny?", font_size=-10)

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.elements.get(ctx.root_element.child_ids[0])
        assert label.properties["font_size"] == -10