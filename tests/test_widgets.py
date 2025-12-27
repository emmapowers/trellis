"""Tests for built-in widgets."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.serialization import serialize_node
from trellis.core.rendering.session import RenderSession
from trellis.widgets import (
    AreaChart,
    Badge,
    BarChart,
    Breadcrumb,
    Button,
    Callout,
    Card,
    Checkbox,
    Collapsible,
    Column,
    Divider,
    Heading,
    Icon,
    Label,
    LineChart,
    Menu,
    MenuDivider,
    MenuItem,
    NumberInput,
    PieChart,
    ProgressBar,
    Row,
    Select,
    Slider,
    Sparkline,
    Stat,
    StatusIndicator,
    Tab,
    Table,
    TableColumn,
    Tabs,
    Tag,
    TextInput,
    TimeSeriesChart,
    Toolbar,
    Tooltip,
    Tree,
)


class TestLayoutWidgets:
    """Tests for Column and Row layout widgets."""

    def test_column_renders_children(self) -> None:
        """Column component renders its children."""

        @component
        def App() -> None:
            with Column():
                Label(text="A")
                Label(text="B")

        ctx = RenderSession(App)
        render(ctx)

        # App has Column as child
        column = ctx.get_node(ctx.root_node.child_ids[0])
        assert column.component.name == "Column"
        assert len(column.child_ids) == 2
        assert ctx.get_node(column.child_ids[0]).component.name == "Label"
        assert ctx.get_node(column.child_ids[1]).component.name == "Label"

    def test_row_renders_children(self) -> None:
        """Row component renders its children."""

        @component
        def App() -> None:
            with Row():
                Button(text="Left")
                Button(text="Right")

        ctx = RenderSession(App)
        render(ctx)

        row = ctx.get_node(ctx.root_node.child_ids[0])
        assert row.component.name == "Row"
        assert len(row.child_ids) == 2

    def test_column_with_props(self) -> None:
        """Column accepts gap and padding props."""

        @component
        def App() -> None:
            with Column(gap=16, padding=8):
                Label(text="Test")

        ctx = RenderSession(App)
        render(ctx)

        column = ctx.get_node(ctx.root_node.child_ids[0])
        assert column.properties["gap"] == 16
        assert column.properties["padding"] == 8

    def test_nested_layout(self) -> None:
        """Layouts can be nested."""

        @component
        def App() -> None:
            with Column():
                with Row():
                    Label(text="A")
                    Label(text="B")
                with Row():
                    Label(text="C")
                    Label(text="D")

        ctx = RenderSession(App)
        render(ctx)

        column = ctx.get_node(ctx.root_node.child_ids[0])
        assert len(column.child_ids) == 2

        row1 = ctx.get_node(column.child_ids[0])
        row2 = ctx.get_node(column.child_ids[1])

        assert row1.component.name == "Row"
        assert row2.component.name == "Row"
        assert len(row1.child_ids) == 2
        assert len(row2.child_ids) == 2


class TestBasicWidgets:
    """Tests for Label and Button widgets."""

    def test_label_with_text(self) -> None:
        """Label stores text prop."""

        @component
        def App() -> None:
            Label(text="Hello World")

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.get_node(ctx.root_node.child_ids[0])
        assert label.component.name == "Label"
        assert label.properties["text"] == "Hello World"

    def test_label_with_styling(self) -> None:
        """Label accepts font_size and color props."""

        @component
        def App() -> None:
            Label(text="Styled", font_size=24, color="red")

        ctx = RenderSession(App)
        render(ctx)

        label = ctx.get_node(ctx.root_node.child_ids[0])
        assert label.properties["font_size"] == 24
        assert label.properties["color"] == "red"

    def test_button_with_text(self) -> None:
        """Button stores text prop."""

        @component
        def App() -> None:
            Button(text="Click Me")

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.get_node(ctx.root_node.child_ids[0])
        assert button.component.name == "Button"
        assert button.properties["text"] == "Click Me"

    def test_button_with_callback(self) -> None:
        """Button captures on_click callback."""
        clicked = []

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: clicked.append(True))

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.get_node(ctx.root_node.child_ids[0])
        assert callable(button.properties["on_click"])

        # Invoke the callback
        button.properties["on_click"]()
        assert clicked == [True]

    def test_button_disabled(self) -> None:
        """Button accepts disabled prop."""

        @component
        def App() -> None:
            Button(text="Disabled", disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        button = ctx.get_node(ctx.root_node.child_ids[0])
        assert button.properties["disabled"] is True

    def test_slider_with_value(self) -> None:
        """Slider stores value and range props."""

        @component
        def App() -> None:
            Slider(value=50, min=0, max=100, step=1)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.get_node(ctx.root_node.child_ids[0])
        assert slider.component.name == "Slider"
        assert slider.properties["value"] == 50
        assert slider.properties["min"] == 0
        assert slider.properties["max"] == 100
        assert slider.properties["step"] == 1

    def test_slider_with_callback(self) -> None:
        """Slider captures on_change callback."""
        values: list[float] = []

        @component
        def App() -> None:
            Slider(value=25, on_change=lambda v: values.append(v))

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.get_node(ctx.root_node.child_ids[0])
        assert callable(slider.properties["on_change"])

        # Invoke the callback
        slider.properties["on_change"](75.0)
        assert values == [75.0]

    def test_slider_default_values(self) -> None:
        """Slider with no explicit props has empty properties.

        Default values (value=50, min=0, max=100, step=1) are defined in the
        function signature for documentation but applied by the React client.
        Only explicitly passed props appear in properties.
        """

        @component
        def App() -> None:
            Slider()

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.get_node(ctx.root_node.child_ids[0])
        # No explicit props passed, so properties should be empty
        # (React client applies defaults)
        assert "value" not in slider.properties
        assert "min" not in slider.properties
        assert "max" not in slider.properties
        assert "step" not in slider.properties

    def test_slider_disabled(self) -> None:
        """Slider accepts disabled prop."""

        @component
        def App() -> None:
            Slider(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.get_node(ctx.root_node.child_ids[0])
        assert slider.properties["disabled"] is True

    def test_slider_custom_range(self) -> None:
        """Slider can have custom min/max/step."""

        @component
        def App() -> None:
            Slider(value=5.5, min=-10, max=10, step=0.5)

        ctx = RenderSession(App)
        render(ctx)

        slider = ctx.get_node(ctx.root_node.child_ids[0])
        assert slider.properties["value"] == 5.5
        assert slider.properties["min"] == -10
        assert slider.properties["max"] == 10
        assert slider.properties["step"] == 0.5


class TestWidgetSerialization:
    """Tests for serializing widgets."""

    def test_serialize_label(self) -> None:
        """Label serializes correctly."""

        @component
        def App() -> None:
            Label(text="Test")

        ctx = RenderSession(App)
        render(ctx)

        result = serialize_node(ctx.root_node, ctx)

        label_data = result["children"][0]
        assert label_data["type"] == "Label"
        assert label_data["props"]["text"] == "Test"

    def test_serialize_button_with_callback(self) -> None:
        """Button callback serializes as reference."""

        @component
        def App() -> None:
            Button(text="Click", on_click=lambda: None)

        ctx = RenderSession(App)
        render(ctx)

        result = serialize_node(ctx.root_node, ctx)

        button_data = result["children"][0]
        assert button_data["type"] == "Button"
        assert "__callback__" in button_data["props"]["on_click"]

    def test_serialize_nested_layout(self) -> None:
        """Nested layout serializes with structure."""

        @component
        def App() -> None:
            with Column(gap=16):
                Label(text="Header")
                with Row():
                    Button(text="OK")
                    Button(text="Cancel")

        ctx = RenderSession(App)
        render(ctx)

        result = serialize_node(ctx.root_node, ctx)

        column_data = result["children"][0]
        assert column_data["type"] == "Column"
        assert column_data["props"]["gap"] == 16
        assert len(column_data["children"]) == 2

        label_data = column_data["children"][0]
        row_data = column_data["children"][1]

        assert label_data["type"] == "Label"
        assert row_data["type"] == "Row"
        assert len(row_data["children"]) == 2


class TestInputWidgets:
    """Tests for TextInput, NumberInput, Checkbox, and Select widgets."""

    def test_text_input_with_value(self) -> None:
        """TextInput stores value and placeholder props."""

        @component
        def App() -> None:
            TextInput(value="hello", placeholder="Enter text...")

        ctx = RenderSession(App)
        render(ctx)

        text_input = ctx.get_node(ctx.root_node.child_ids[0])
        assert text_input.component.name == "TextInput"
        assert text_input.properties["value"] == "hello"
        assert text_input.properties["placeholder"] == "Enter text..."

    def test_text_input_with_callback(self) -> None:
        """TextInput captures on_change callback."""
        values: list[str] = []

        @component
        def App() -> None:
            TextInput(value="test", on_change=lambda v: values.append(v))

        ctx = RenderSession(App)
        render(ctx)

        text_input = ctx.get_node(ctx.root_node.child_ids[0])
        assert callable(text_input.properties["on_change"])

        text_input.properties["on_change"]("new value")
        assert values == ["new value"]

    def test_text_input_disabled(self) -> None:
        """TextInput accepts disabled prop."""

        @component
        def App() -> None:
            TextInput(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        text_input = ctx.get_node(ctx.root_node.child_ids[0])
        assert text_input.properties["disabled"] is True

    def test_number_input_with_value(self) -> None:
        """NumberInput stores value and range props."""

        @component
        def App() -> None:
            NumberInput(value=42, min=0, max=100, step=1)

        ctx = RenderSession(App)
        render(ctx)

        number_input = ctx.get_node(ctx.root_node.child_ids[0])
        assert number_input.component.name == "NumberInput"
        assert number_input.properties["value"] == 42
        assert number_input.properties["min"] == 0
        assert number_input.properties["max"] == 100
        assert number_input.properties["step"] == 1

    def test_number_input_with_callback(self) -> None:
        """NumberInput captures on_change callback."""
        values: list[float] = []

        @component
        def App() -> None:
            NumberInput(value=10, on_change=lambda v: values.append(v))

        ctx = RenderSession(App)
        render(ctx)

        number_input = ctx.get_node(ctx.root_node.child_ids[0])
        assert callable(number_input.properties["on_change"])

        number_input.properties["on_change"](25.5)
        assert values == [25.5]

    def test_number_input_disabled(self) -> None:
        """NumberInput accepts disabled prop."""

        @component
        def App() -> None:
            NumberInput(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        number_input = ctx.get_node(ctx.root_node.child_ids[0])
        assert number_input.properties["disabled"] is True

    def test_checkbox_with_checked(self) -> None:
        """Checkbox stores checked and label props."""

        @component
        def App() -> None:
            Checkbox(checked=True, label="Enable feature")

        ctx = RenderSession(App)
        render(ctx)

        checkbox = ctx.get_node(ctx.root_node.child_ids[0])
        assert checkbox.component.name == "Checkbox"
        assert checkbox.properties["checked"] is True
        assert checkbox.properties["label"] == "Enable feature"

    def test_checkbox_with_callback(self) -> None:
        """Checkbox captures on_change callback."""
        states: list[bool] = []

        @component
        def App() -> None:
            Checkbox(checked=False, on_change=lambda v: states.append(v))

        ctx = RenderSession(App)
        render(ctx)

        checkbox = ctx.get_node(ctx.root_node.child_ids[0])
        assert callable(checkbox.properties["on_change"])

        checkbox.properties["on_change"](True)
        assert states == [True]

    def test_checkbox_disabled(self) -> None:
        """Checkbox accepts disabled prop."""

        @component
        def App() -> None:
            Checkbox(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        checkbox = ctx.get_node(ctx.root_node.child_ids[0])
        assert checkbox.properties["disabled"] is True

    def test_select_with_options(self) -> None:
        """Select stores value and options props."""

        @component
        def App() -> None:
            Select(
                value="opt1",
                options=[
                    {"value": "opt1", "label": "Option 1"},
                    {"value": "opt2", "label": "Option 2"},
                ],
                placeholder="Choose...",
            )

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.get_node(ctx.root_node.child_ids[0])
        assert select.component.name == "Select"
        assert select.properties["value"] == "opt1"
        assert len(select.properties["options"]) == 2
        assert select.properties["placeholder"] == "Choose..."

    def test_select_with_callback(self) -> None:
        """Select captures on_change callback."""
        selections: list[str] = []

        @component
        def App() -> None:
            Select(
                value="opt1",
                options=[{"value": "opt1", "label": "Option 1"}],
                on_change=lambda v: selections.append(v),
            )

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.get_node(ctx.root_node.child_ids[0])
        assert callable(select.properties["on_change"])

        select.properties["on_change"]("opt2")
        assert selections == ["opt2"]

    def test_select_disabled(self) -> None:
        """Select accepts disabled prop."""

        @component
        def App() -> None:
            Select(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        select = ctx.get_node(ctx.root_node.child_ids[0])
        assert select.properties["disabled"] is True


class TestCardAndDivider:
    """Tests for Card and Divider widgets."""

    def test_card_renders_children(self) -> None:
        """Card component renders its children."""

        @component
        def App() -> None:
            with Card():
                Label(text="Inside card")

        ctx = RenderSession(App)
        render(ctx)

        card = ctx.get_node(ctx.root_node.child_ids[0])
        assert card.component.name == "Card"
        assert len(card.child_ids) == 1
        assert ctx.get_node(card.child_ids[0]).component.name == "Label"

    def test_card_with_padding(self) -> None:
        """Card accepts padding prop."""

        @component
        def App() -> None:
            with Card(padding=32):
                Label(text="Content")

        ctx = RenderSession(App)
        render(ctx)

        card = ctx.get_node(ctx.root_node.child_ids[0])
        assert card.properties["padding"] == 32

    def test_card_nested_in_layout(self) -> None:
        """Card can be nested inside layout widgets."""

        @component
        def App() -> None:
            with Column():
                with Card():
                    Label(text="Card 1")
                with Card():
                    Label(text="Card 2")

        ctx = RenderSession(App)
        render(ctx)

        column = ctx.get_node(ctx.root_node.child_ids[0])
        assert len(column.child_ids) == 2
        assert ctx.get_node(column.child_ids[0]).component.name == "Card"
        assert ctx.get_node(column.child_ids[1]).component.name == "Card"

    def test_divider_renders(self) -> None:
        """Divider component renders."""

        @component
        def App() -> None:
            Divider()

        ctx = RenderSession(App)
        render(ctx)

        divider = ctx.get_node(ctx.root_node.child_ids[0])
        assert divider.component.name == "Divider"

    def test_divider_with_props(self) -> None:
        """Divider accepts margin and color props."""

        @component
        def App() -> None:
            Divider(margin=24, color="#6366f1")

        ctx = RenderSession(App)
        render(ctx)

        divider = ctx.get_node(ctx.root_node.child_ids[0])
        assert divider.properties["margin"] == 24
        assert divider.properties["color"] == "#6366f1"

    def test_divider_vertical_orientation(self) -> None:
        """Divider accepts orientation prop."""

        @component
        def App() -> None:
            Divider(orientation="vertical")

        ctx = RenderSession(App)
        render(ctx)

        divider = ctx.get_node(ctx.root_node.child_ids[0])
        assert divider.properties["orientation"] == "vertical"

    def test_divider_in_layout(self) -> None:
        """Divider can separate content in a layout."""

        @component
        def App() -> None:
            with Column():
                Label(text="Above")
                Divider()
                Label(text="Below")

        ctx = RenderSession(App)
        render(ctx)

        column = ctx.get_node(ctx.root_node.child_ids[0])
        assert len(column.child_ids) == 3
        assert ctx.get_node(column.child_ids[0]).component.name == "Label"
        assert ctx.get_node(column.child_ids[1]).component.name == "Divider"
        assert ctx.get_node(column.child_ids[2]).component.name == "Label"


class TestHeadingWidget:
    """Tests for Heading widget."""

    def test_heading_with_text(self) -> None:
        """Heading stores text prop."""

        @component
        def App() -> None:
            Heading(text="Welcome")

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.get_node(ctx.root_node.child_ids[0])
        assert heading.component.name == "Heading"
        assert heading.properties["text"] == "Welcome"

    def test_heading_with_level(self) -> None:
        """Heading accepts level prop for h1-h6."""

        @component
        def App() -> None:
            Heading(text="Section", level=2)

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.get_node(ctx.root_node.child_ids[0])
        assert heading.properties["level"] == 2

    def test_heading_with_color(self) -> None:
        """Heading accepts color prop."""

        @component
        def App() -> None:
            Heading(text="Colored", color="#333")

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.get_node(ctx.root_node.child_ids[0])
        assert heading.properties["color"] == "#333"

    def test_heading_with_style(self) -> None:
        """Heading accepts style dict."""

        @component
        def App() -> None:
            Heading(text="Styled", style={"marginBottom": "16px"})

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.get_node(ctx.root_node.child_ids[0])
        assert heading.properties["style"] == {"marginBottom": "16px"}

    def test_heading_default_level(self) -> None:
        """Heading without explicit level has no level in properties."""

        @component
        def App() -> None:
            Heading(text="Default")

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.get_node(ctx.root_node.child_ids[0])
        # Default values are applied by React client, not stored in properties
        assert "level" not in heading.properties


class TestProgressBarWidget:
    """Tests for ProgressBar widget."""

    def test_progress_bar_with_value(self) -> None:
        """ProgressBar stores value, min, max props."""

        @component
        def App() -> None:
            ProgressBar(value=50, min=0, max=100)

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.get_node(ctx.root_node.child_ids[0])
        assert progress.component.name == "ProgressBar"
        assert progress.properties["value"] == 50
        assert progress.properties["min"] == 0
        assert progress.properties["max"] == 100

    def test_progress_bar_loading(self) -> None:
        """ProgressBar accepts loading prop."""

        @component
        def App() -> None:
            ProgressBar(loading=True)

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.get_node(ctx.root_node.child_ids[0])
        assert progress.properties["loading"] is True

    def test_progress_bar_disabled(self) -> None:
        """ProgressBar accepts disabled prop."""

        @component
        def App() -> None:
            ProgressBar(disabled=True)

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.get_node(ctx.root_node.child_ids[0])
        assert progress.properties["disabled"] is True

    def test_progress_bar_with_color(self) -> None:
        """ProgressBar accepts color prop."""

        @component
        def App() -> None:
            ProgressBar(value=75, color="#22c55e")

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.get_node(ctx.root_node.child_ids[0])
        assert progress.properties["color"] == "#22c55e"

    def test_progress_bar_with_height(self) -> None:
        """ProgressBar accepts height prop."""

        @component
        def App() -> None:
            ProgressBar(value=25, height=12)

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.get_node(ctx.root_node.child_ids[0])
        assert progress.properties["height"] == 12

    def test_progress_bar_with_style(self) -> None:
        """ProgressBar accepts style dict."""

        @component
        def App() -> None:
            ProgressBar(value=50, style={"marginBottom": "24px"})

        ctx = RenderSession(App)
        render(ctx)

        progress = ctx.get_node(ctx.root_node.child_ids[0])
        assert progress.properties["style"] == {"marginBottom": "24px"}


class TestStatusIndicatorWidget:
    """Tests for StatusIndicator widget."""

    def test_status_indicator_with_status(self) -> None:
        """StatusIndicator stores status prop."""

        @component
        def App() -> None:
            StatusIndicator(status="success")

        ctx = RenderSession(App)
        render(ctx)

        indicator = ctx.get_node(ctx.root_node.child_ids[0])
        assert indicator.component.name == "StatusIndicator"
        assert indicator.properties["status"] == "success"

    def test_status_indicator_with_label(self) -> None:
        """StatusIndicator stores label prop."""

        @component
        def App() -> None:
            StatusIndicator(status="error", label="Failed")

        ctx = RenderSession(App)
        render(ctx)

        indicator = ctx.get_node(ctx.root_node.child_ids[0])
        assert indicator.properties["status"] == "error"
        assert indicator.properties["label"] == "Failed"

    def test_status_indicator_hide_icon(self) -> None:
        """StatusIndicator accepts show_icon prop."""

        @component
        def App() -> None:
            StatusIndicator(status="warning", show_icon=False)

        ctx = RenderSession(App)
        render(ctx)

        indicator = ctx.get_node(ctx.root_node.child_ids[0])
        assert indicator.properties["show_icon"] is False


class TestBadgeWidget:
    """Tests for Badge widget."""

    def test_badge_with_text(self) -> None:
        """Badge stores text prop."""

        @component
        def App() -> None:
            Badge(text="New")

        ctx = RenderSession(App)
        render(ctx)

        badge = ctx.get_node(ctx.root_node.child_ids[0])
        assert badge.component.name == "Badge"
        assert badge.properties["text"] == "New"

    def test_badge_with_variant(self) -> None:
        """Badge accepts variant prop."""

        @component
        def App() -> None:
            Badge(text="Error", variant="error")

        ctx = RenderSession(App)
        render(ctx)

        badge = ctx.get_node(ctx.root_node.child_ids[0])
        assert badge.properties["variant"] == "error"

    def test_badge_with_size(self) -> None:
        """Badge accepts size prop."""

        @component
        def App() -> None:
            Badge(text="Large", size="md")

        ctx = RenderSession(App)
        render(ctx)

        badge = ctx.get_node(ctx.root_node.child_ids[0])
        assert badge.properties["size"] == "md"


class TestTooltipWidget:
    """Tests for Tooltip widget."""

    def test_tooltip_with_content(self) -> None:
        """Tooltip stores content prop."""

        @component
        def App() -> None:
            with Tooltip(content="Helpful hint"):
                Label(text="Hover me")

        ctx = RenderSession(App)
        render(ctx)

        tooltip = ctx.get_node(ctx.root_node.child_ids[0])
        assert tooltip.component.name == "Tooltip"
        assert tooltip.properties["content"] == "Helpful hint"
        assert len(tooltip.child_ids) == 1

    def test_tooltip_with_position(self) -> None:
        """Tooltip accepts position prop."""

        @component
        def App() -> None:
            with Tooltip(content="Below", position="bottom"):
                Button(text="Click")

        ctx = RenderSession(App)
        render(ctx)

        tooltip = ctx.get_node(ctx.root_node.child_ids[0])
        assert tooltip.properties["position"] == "bottom"

    def test_tooltip_with_delay(self) -> None:
        """Tooltip accepts delay prop."""

        @component
        def App() -> None:
            with Tooltip(content="Slow", delay=500):
                Label(text="Wait")

        ctx = RenderSession(App)
        render(ctx)

        tooltip = ctx.get_node(ctx.root_node.child_ids[0])
        assert tooltip.properties["delay"] == 500


class TestTableWidget:
    """Tests for Table widget."""

    def test_table_with_columns_and_data(self) -> None:
        """Table stores columns and data props."""

        @component
        def App() -> None:
            Table(
                columns=["name", "value"],
                data=[
                    {"name": "Item 1", "value": 100},
                    {"name": "Item 2", "value": 200},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        # Table is a CompositionComponent that wraps _TableInner
        table_comp = ctx.get_node(ctx.root_node.child_ids[0])
        assert table_comp.component.name == "Table"
        # The actual TableInner is a child
        table_inner = ctx.get_node(table_comp.child_ids[0])
        assert table_inner.component.element_name == "TableInner"
        assert len(table_inner.properties["columns"]) == 2
        assert len(table_inner.properties["data"]) == 2

    def test_table_with_styling_options(self) -> None:
        """Table accepts striped, compact, bordered props."""

        @component
        def App() -> None:
            Table(striped=True, compact=False, bordered=True)

        ctx = RenderSession(App)
        render(ctx)

        table = ctx.get_node(ctx.root_node.child_ids[0])
        assert table.properties["striped"] is True
        assert table.properties["compact"] is False
        assert table.properties["bordered"] is True

    def test_table_with_custom_cell_render(self) -> None:
        """Table with custom cell rendering creates CellSlot children."""
        render_calls: list[dict] = []

        def CustomCell(*, row: dict) -> None:
            render_calls.append(row)
            Label(text=f"Custom: {row['name']}")

        @component
        def App() -> None:
            Table(
                columns=[
                    TableColumn(name="name", label="Name"),
                    TableColumn(name="value", label="Value", render=CustomCell),
                ],
                data=[
                    {"_key": "row1", "name": "Item 1", "value": 100},
                    {"_key": "row2", "name": "Item 2", "value": 200},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        # Verify render function was called for each row
        assert len(render_calls) == 2
        assert render_calls[0]["name"] == "Item 1"
        assert render_calls[1]["name"] == "Item 2"

        # Verify CellSlot children were created
        table_comp = ctx.get_node(ctx.root_node.child_ids[0])
        table_inner = ctx.get_node(table_comp.child_ids[0])
        assert table_inner.component.element_name == "TableInner"

        # CellSlots are children of TableInner
        cell_slots = [ctx.get_node(cid) for cid in table_inner.child_ids if ctx.get_node(cid).component.element_name == "CellSlot"]
        assert len(cell_slots) == 2  # One per row (only 'value' column has render)

        # Verify slot IDs follow "rowKey:columnName" format
        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "row1:value" in slot_ids
        assert "row2:value" in slot_ids

    def test_table_row_key_from_column(self) -> None:
        """Table uses column with row_key=True for slot keys."""

        @component
        def CustomCell(*, row: dict) -> None:
            Label(text=row["name"])

        @component
        def App() -> None:
            Table(
                columns=[
                    TableColumn(name="id", label="ID", row_key=True),
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"id": "abc123", "name": "Item 1"},
                    {"id": "def456", "name": "Item 2"},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        table_comp = ctx.get_node(ctx.root_node.child_ids[0])
        table_inner = ctx.get_node(table_comp.child_ids[0])
        cell_slots = [ctx.get_node(cid) for cid in table_inner.child_ids if ctx.get_node(cid).component.element_name == "CellSlot"]

        # Slot keys should use the row_key column value
        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "abc123:name" in slot_ids
        assert "def456:name" in slot_ids

    def test_table_row_key_from_key_field(self) -> None:
        """Table falls back to _key field for slot keys."""

        @component
        def CustomCell(*, row: dict) -> None:
            Label(text=row["name"])

        @component
        def App() -> None:
            Table(
                columns=[
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"_key": "custom1", "name": "Item 1"},
                    {"_key": "custom2", "name": "Item 2"},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        table_comp = ctx.get_node(ctx.root_node.child_ids[0])
        table_inner = ctx.get_node(table_comp.child_ids[0])
        cell_slots = [ctx.get_node(cid) for cid in table_inner.child_ids if ctx.get_node(cid).component.element_name == "CellSlot"]

        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "custom1:name" in slot_ids
        assert "custom2:name" in slot_ids

    def test_table_row_key_from_index(self) -> None:
        """Table falls back to row index for slot keys."""

        @component
        def CustomCell(*, row: dict) -> None:
            Label(text=row["name"])

        @component
        def App() -> None:
            Table(
                columns=[
                    TableColumn(name="name", label="Name", render=CustomCell),
                ],
                data=[
                    {"name": "Item 1"},  # No _key or row_key column
                    {"name": "Item 2"},
                ],
            )

        ctx = RenderSession(App)
        render(ctx)

        table_comp = ctx.get_node(ctx.root_node.child_ids[0])
        table_inner = ctx.get_node(table_comp.child_ids[0])
        cell_slots = [ctx.get_node(cid) for cid in table_inner.child_ids if ctx.get_node(cid).component.element_name == "CellSlot"]

        slot_ids = [slot.properties["slot"] for slot in cell_slots]
        assert "0:name" in slot_ids
        assert "1:name" in slot_ids


class TestStatWidget:
    """Tests for Stat widget."""

    def test_stat_with_label_and_value(self) -> None:
        """Stat stores label and value props."""

        @component
        def App() -> None:
            Stat(label="Revenue", value="$12,345")

        ctx = RenderSession(App)
        render(ctx)

        stat = ctx.get_node(ctx.root_node.child_ids[0])
        assert stat.component.name == "Stat"
        assert stat.properties["label"] == "Revenue"
        assert stat.properties["value"] == "$12,345"

    def test_stat_with_delta(self) -> None:
        """Stat accepts delta and delta_type props."""

        @component
        def App() -> None:
            Stat(label="Users", value="1,234", delta="+12%", delta_type="increase")

        ctx = RenderSession(App)
        render(ctx)

        stat = ctx.get_node(ctx.root_node.child_ids[0])
        assert stat.properties["delta"] == "+12%"
        assert stat.properties["delta_type"] == "increase"

    def test_stat_with_size(self) -> None:
        """Stat accepts size prop."""

        @component
        def App() -> None:
            Stat(label="Big", value="999", size="lg")

        ctx = RenderSession(App)
        render(ctx)

        stat = ctx.get_node(ctx.root_node.child_ids[0])
        assert stat.properties["size"] == "lg"


class TestTagWidget:
    """Tests for Tag widget."""

    def test_tag_with_text(self) -> None:
        """Tag stores text prop."""

        @component
        def App() -> None:
            Tag(text="Python")

        ctx = RenderSession(App)
        render(ctx)

        tag = ctx.get_node(ctx.root_node.child_ids[0])
        assert tag.component.name == "Tag"
        assert tag.properties["text"] == "Python"

    def test_tag_with_variant(self) -> None:
        """Tag accepts variant prop."""

        @component
        def App() -> None:
            Tag(text="Success", variant="success")

        ctx = RenderSession(App)
        render(ctx)

        tag = ctx.get_node(ctx.root_node.child_ids[0])
        assert tag.properties["variant"] == "success"

    def test_tag_removable_with_callback(self) -> None:
        """Tag captures on_remove callback when removable."""
        removed = []

        @component
        def App() -> None:
            Tag(text="Remove me", removable=True, on_remove=lambda: removed.append(True))

        ctx = RenderSession(App)
        render(ctx)

        tag = ctx.get_node(ctx.root_node.child_ids[0])
        assert tag.properties["removable"] is True
        assert callable(tag.properties["on_remove"])

        tag.properties["on_remove"]()
        assert removed == [True]


class TestChartWidgets:
    """Tests for chart widgets."""

    def test_time_series_chart_with_data(self) -> None:
        """TimeSeriesChart stores data and series props."""

        @component
        def App() -> None:
            TimeSeriesChart(
                data=[
                    [1700000000, 1700000001, 1700000002],
                    [10, 20, 15],
                ],
                series=[{"label": "CPU", "stroke": "#6366f1"}],
                height=300,
            )

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.get_node(ctx.root_node.child_ids[0])
        assert chart.component.name == "TimeSeriesChart"
        assert len(chart.properties["data"]) == 2
        assert chart.properties["height"] == 300

    def test_line_chart_with_data(self) -> None:
        """LineChart stores data and configuration props."""

        @component
        def App() -> None:
            LineChart(
                data=[{"month": "Jan", "value": 100}, {"month": "Feb", "value": 120}],
                data_keys=["value"],
                x_key="month",
            )

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.get_node(ctx.root_node.child_ids[0])
        assert chart.component.name == "LineChart"
        assert len(chart.properties["data"]) == 2
        assert chart.properties["x_key"] == "month"

    def test_bar_chart_with_data(self) -> None:
        """BarChart stores data and configuration props."""

        @component
        def App() -> None:
            BarChart(
                data=[{"category": "A", "value": 100}],
                stacked=True,
            )

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.get_node(ctx.root_node.child_ids[0])
        assert chart.component.name == "BarChart"
        assert chart.properties["stacked"] is True

    def test_area_chart_with_data(self) -> None:
        """AreaChart stores data and configuration props."""

        @component
        def App() -> None:
            AreaChart(
                data=[{"name": "Jan", "value": 100}],
                curve_type="step",
            )

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.get_node(ctx.root_node.child_ids[0])
        assert chart.component.name == "AreaChart"
        assert chart.properties["curve_type"] == "step"

    def test_pie_chart_with_data(self) -> None:
        """PieChart stores data and configuration props."""

        @component
        def App() -> None:
            PieChart(
                data=[{"name": "A", "value": 60}, {"name": "B", "value": 40}],
                inner_radius=50,
            )

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.get_node(ctx.root_node.child_ids[0])
        assert chart.component.name == "PieChart"
        assert chart.properties["inner_radius"] == 50

    def test_sparkline_with_data(self) -> None:
        """Sparkline stores data props."""

        @component
        def App() -> None:
            Sparkline(data=[10, 20, 15, 25], height=30, color="#22c55e")

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.get_node(ctx.root_node.child_ids[0])
        assert chart.component.name == "Sparkline"
        assert chart.properties["data"] == [10, 20, 15, 25]
        assert chart.properties["height"] == 30
        assert chart.properties["color"] == "#22c55e"


class TestIconWidget:
    """Tests for Icon widget."""

    def test_icon_with_name(self) -> None:
        """Icon stores name prop."""

        @component
        def App() -> None:
            Icon(name="check")

        ctx = RenderSession(App)
        render(ctx)

        icon = ctx.get_node(ctx.root_node.child_ids[0])
        assert icon.component.name == "Icon"
        assert icon.properties["name"] == "check"

    def test_icon_with_size_and_color(self) -> None:
        """Icon accepts size and color props."""

        @component
        def App() -> None:
            Icon(name="alert-triangle", size=24, color="#d97706")

        ctx = RenderSession(App)
        render(ctx)

        icon = ctx.get_node(ctx.root_node.child_ids[0])
        assert icon.properties["size"] == 24
        assert icon.properties["color"] == "#d97706"

    def test_icon_with_stroke_width(self) -> None:
        """Icon accepts stroke_width prop."""

        @component
        def App() -> None:
            Icon(name="circle", stroke_width=3)

        ctx = RenderSession(App)
        render(ctx)

        icon = ctx.get_node(ctx.root_node.child_ids[0])
        assert icon.properties["stroke_width"] == 3


class TestNavigationWidgets:
    """Tests for navigation widgets."""

    def test_tabs_with_children(self) -> None:
        """Tabs renders children and stores props."""

        @component
        def App() -> None:
            with Tabs(selected="tab1", variant="enclosed"):
                with Tab(id="tab1", label="First"):
                    Label(text="Content 1")
                with Tab(id="tab2", label="Second"):
                    Label(text="Content 2")

        ctx = RenderSession(App)
        render(ctx)

        tabs = ctx.get_node(ctx.root_node.child_ids[0])
        assert tabs.component.name == "Tabs"
        assert tabs.properties["selected"] == "tab1"
        assert tabs.properties["variant"] == "enclosed"
        assert len(tabs.child_ids) == 2

    def test_tabs_with_callback(self) -> None:
        """Tabs captures on_change callback."""
        selections: list[str] = []

        @component
        def App() -> None:
            with Tabs(on_change=lambda v: selections.append(v)):
                with Tab(id="t1", label="Tab 1"):
                    Label(text="Content")

        ctx = RenderSession(App)
        render(ctx)

        tabs = ctx.get_node(ctx.root_node.child_ids[0])
        assert callable(tabs.properties["on_change"])

        tabs.properties["on_change"]("t2")
        assert selections == ["t2"]

    def test_tab_with_props(self) -> None:
        """Tab stores id, label, and other props."""

        @component
        def App() -> None:
            with Tabs():
                with Tab(id="disabled-tab", label="Disabled", disabled=True, icon="lock"):
                    Label(text="Content")

        ctx = RenderSession(App)
        render(ctx)

        tabs = ctx.get_node(ctx.root_node.child_ids[0])
        tab = ctx.get_node(tabs.child_ids[0])
        assert tab.component.name == "Tab"
        assert tab.properties["id"] == "disabled-tab"
        assert tab.properties["label"] == "Disabled"
        assert tab.properties["disabled"] is True
        assert tab.properties["icon"] == "lock"

    def test_tree_with_data(self) -> None:
        """Tree stores data and selection props."""

        @component
        def App() -> None:
            Tree(
                data=[
                    {"id": "1", "label": "Root", "children": [{"id": "1.1", "label": "Child"}]}
                ],
                selected="1",
                expanded=["1"],
            )

        ctx = RenderSession(App)
        render(ctx)

        tree = ctx.get_node(ctx.root_node.child_ids[0])
        assert tree.component.name == "Tree"
        assert tree.properties["selected"] == "1"
        assert tree.properties["expanded"] == ["1"]

    def test_tree_with_callbacks(self) -> None:
        """Tree captures on_select and on_expand callbacks."""
        selections: list[str] = []
        expansions: list[tuple[str, bool]] = []

        @component
        def App() -> None:
            Tree(
                data=[{"id": "1", "label": "Root"}],
                on_select=lambda v: selections.append(v),
                on_expand=lambda id, exp: expansions.append((id, exp)),
            )

        ctx = RenderSession(App)
        render(ctx)

        tree = ctx.get_node(ctx.root_node.child_ids[0])
        tree.properties["on_select"]("1")
        tree.properties["on_expand"]("1", True)

        assert selections == ["1"]
        assert expansions == [("1", True)]

    def test_breadcrumb_with_items(self) -> None:
        """Breadcrumb stores items and separator props."""

        @component
        def App() -> None:
            Breadcrumb(
                items=[{"label": "Home"}, {"label": "Products"}, {"label": "Details"}],
                separator=">",
            )

        ctx = RenderSession(App)
        render(ctx)

        breadcrumb = ctx.get_node(ctx.root_node.child_ids[0])
        assert breadcrumb.component.name == "Breadcrumb"
        assert len(breadcrumb.properties["items"]) == 3
        assert breadcrumb.properties["separator"] == ">"

    def test_breadcrumb_with_callback(self) -> None:
        """Breadcrumb captures on_click callback."""
        clicks: list[int] = []

        @component
        def App() -> None:
            Breadcrumb(
                items=[{"label": "Home"}, {"label": "Page"}],
                on_click=lambda idx: clicks.append(idx),
            )

        ctx = RenderSession(App)
        render(ctx)

        breadcrumb = ctx.get_node(ctx.root_node.child_ids[0])
        breadcrumb.properties["on_click"](0)
        assert clicks == [0]


class TestFeedbackWidgets:
    """Tests for feedback widgets."""

    def test_callout_with_title_and_intent(self) -> None:
        """Callout stores title and intent props."""

        @component
        def App() -> None:
            with Callout(title="Warning", intent="warning"):
                Label(text="Be careful!")

        ctx = RenderSession(App)
        render(ctx)

        callout = ctx.get_node(ctx.root_node.child_ids[0])
        assert callout.component.name == "Callout"
        assert callout.properties["title"] == "Warning"
        assert callout.properties["intent"] == "warning"
        assert len(callout.child_ids) == 1

    def test_callout_dismissible_with_callback(self) -> None:
        """Callout captures on_dismiss callback when dismissible."""
        dismissed = []

        @component
        def App() -> None:
            with Callout(dismissible=True, on_dismiss=lambda: dismissed.append(True)):
                Label(text="Dismissable")

        ctx = RenderSession(App)
        render(ctx)

        callout = ctx.get_node(ctx.root_node.child_ids[0])
        assert callout.properties["dismissible"] is True
        callout.properties["on_dismiss"]()
        assert dismissed == [True]

    def test_collapsible_with_title(self) -> None:
        """Collapsible stores title and expanded props."""

        @component
        def App() -> None:
            with Collapsible(title="Details", expanded=False):
                Label(text="Hidden content")

        ctx = RenderSession(App)
        render(ctx)

        collapsible = ctx.get_node(ctx.root_node.child_ids[0])
        assert collapsible.component.name == "Collapsible"
        assert collapsible.properties["title"] == "Details"
        assert collapsible.properties["expanded"] is False

    def test_collapsible_with_callback(self) -> None:
        """Collapsible captures on_toggle callback."""
        toggles: list[bool] = []

        @component
        def App() -> None:
            with Collapsible(title="Toggle", on_toggle=lambda v: toggles.append(v)):
                Label(text="Content")

        ctx = RenderSession(App)
        render(ctx)

        collapsible = ctx.get_node(ctx.root_node.child_ids[0])
        collapsible.properties["on_toggle"](True)
        assert toggles == [True]


class TestActionWidgets:
    """Tests for action widgets."""

    def test_menu_with_items(self) -> None:
        """Menu renders children."""

        @component
        def App() -> None:
            with Menu():
                MenuItem(text="Open")
                MenuItem(text="Save")
                MenuDivider()
                MenuItem(text="Exit")

        ctx = RenderSession(App)
        render(ctx)

        menu = ctx.get_node(ctx.root_node.child_ids[0])
        assert menu.component.name == "Menu"
        assert len(menu.child_ids) == 4

    def test_menu_item_with_props(self) -> None:
        """MenuItem stores text, icon, and other props."""

        @component
        def App() -> None:
            with Menu():
                MenuItem(text="Delete", icon="trash", disabled=True, shortcut="Ctrl+D")

        ctx = RenderSession(App)
        render(ctx)

        menu = ctx.get_node(ctx.root_node.child_ids[0])
        item = ctx.get_node(menu.child_ids[0])
        assert item.component.name == "MenuItem"
        assert item.properties["text"] == "Delete"
        assert item.properties["icon"] == "trash"
        assert item.properties["disabled"] is True
        assert item.properties["shortcut"] == "Ctrl+D"

    def test_menu_item_with_callback(self) -> None:
        """MenuItem captures on_click callback."""
        clicks = []

        @component
        def App() -> None:
            with Menu():
                MenuItem(text="Click me", on_click=lambda: clicks.append(True))

        ctx = RenderSession(App)
        render(ctx)

        menu = ctx.get_node(ctx.root_node.child_ids[0])
        item = ctx.get_node(menu.child_ids[0])
        item.properties["on_click"]()
        assert clicks == [True]

    def test_menu_divider_renders(self) -> None:
        """MenuDivider component renders."""

        @component
        def App() -> None:
            with Menu():
                MenuDivider()

        ctx = RenderSession(App)
        render(ctx)

        menu = ctx.get_node(ctx.root_node.child_ids[0])
        divider = ctx.get_node(menu.child_ids[0])
        assert divider.component.name == "MenuDivider"

    def test_toolbar_with_children(self) -> None:
        """Toolbar renders children and stores props."""

        @component
        def App() -> None:
            with Toolbar(variant="minimal", orientation="vertical"):
                Button(text="Bold")
                Button(text="Italic")

        ctx = RenderSession(App)
        render(ctx)

        toolbar = ctx.get_node(ctx.root_node.child_ids[0])
        assert toolbar.component.name == "Toolbar"
        assert toolbar.properties["variant"] == "minimal"
        assert toolbar.properties["orientation"] == "vertical"
        assert len(toolbar.child_ids) == 2
