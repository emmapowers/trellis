"""Tests for data display widgets: Stat, Tag, and chart widgets."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.widgets import (
    AreaChart,
    BarChart,
    LineChart,
    PieChart,
    Sparkline,
    Stat,
    Tag,
    TimeSeriesChart,
)


class TestStatWidget:
    """Tests for Stat widget."""

    def test_stat_with_label_and_value(self) -> None:
        """Stat stores label and value props."""

        @component
        def App() -> None:
            """
            Render a Stat widget showing revenue and its value.
            
            Renders a Stat component with label "Revenue" and value "$12,345".
            """
            Stat(label="Revenue", value="$12,345")

        ctx = RenderSession(App)
        render(ctx)

        stat = ctx.elements.get(ctx.root_element.child_ids[0])
        assert stat.component.name == "Stat"
        assert stat.properties["label"] == "Revenue"
        assert stat.properties["value"] == "$12,345"

    def test_stat_with_delta(self) -> None:
        """Stat accepts delta and delta_type props."""

        @component
        def App() -> None:
            """
            Render a component that displays a Stat widget for user count with a delta indicator.
            
            Renders a Stat widget with label "Users", value "1,234", delta "+12%", and delta_type "increase".
            """
            Stat(label="Users", value="1,234", delta="+12%", delta_type="increase")

        ctx = RenderSession(App)
        render(ctx)

        stat = ctx.elements.get(ctx.root_element.child_ids[0])
        assert stat.properties["delta"] == "+12%"
        assert stat.properties["delta_type"] == "increase"

    def test_stat_with_size(self) -> None:
        """Stat accepts size prop."""

        @component
        def App() -> None:
            """
            Component that renders a Stat widget with label "Big", value "999", and size "lg".
            
            Used by tests as a minimal application component to verify Stat widget rendering and prop propagation.
            """
            Stat(label="Big", value="999", size="lg")

        ctx = RenderSession(App)
        render(ctx)

        stat = ctx.elements.get(ctx.root_element.child_ids[0])
        assert stat.properties["size"] == "lg"


class TestTagWidget:
    """Tests for Tag widget."""

    def test_tag_with_text(self) -> None:
        """Tag stores text prop."""

        @component
        def App() -> None:
            """
            Renders a simple test component that displays a Tag with the text "Python".
            """
            Tag(text="Python")

        ctx = RenderSession(App)
        render(ctx)

        tag = ctx.elements.get(ctx.root_element.child_ids[0])
        assert tag.component.name == "Tag"
        assert tag.properties["text"] == "Python"

    def test_tag_with_variant(self) -> None:
        """Tag accepts variant prop."""

        @component
        def App() -> None:
            """
            Renders a Tag component with text "Success" and variant "success" for testing.
            
            This component is used in tests to verify that a Tag with the given text and variant is created.
            """
            Tag(text="Success", variant="success")

        ctx = RenderSession(App)
        render(ctx)

        tag = ctx.elements.get(ctx.root_element.child_ids[0])
        assert tag.properties["variant"] == "success"

    def test_tag_removable_with_callback(self) -> None:
        """Tag captures on_remove callback when removable."""
        removed = []

        @component
        def App() -> None:
            """
            Render a removable Tag component labeled "Remove me" that triggers an on_remove callback when removed.
            
            The Tag is configured with removable=True and an on_remove callback that appends True to the enclosing `removed` list.
            """
            Tag(text="Remove me", removable=True, on_remove=lambda: removed.append(True))

        ctx = RenderSession(App)
        render(ctx)

        tag = ctx.elements.get(ctx.root_element.child_ids[0])
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
            """
            Render a TimeSeriesChart with a small sample dataset for testing.
            
            Renders a chart using two-row data (timestamps and corresponding values), a single series labeled "CPU" with stroke color "#6366f1", and a height of 300 pixels. This App exists solely to provide a predictable component instance for unit tests.
            """
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

        chart = ctx.elements.get(ctx.root_element.child_ids[0])
        assert chart.component.name == "TimeSeriesChart"
        assert len(chart.properties["data"]) == 2
        assert chart.properties["height"] == 300

    def test_line_chart_with_data(self) -> None:
        """LineChart stores data and configuration props."""

        @component
        def App() -> None:
            """
            Renders a LineChart component configured with two months of sample data, using "month" as the x-axis key and "value" as the data series key.
            """
            LineChart(
                data=[{"month": "Jan", "value": 100}, {"month": "Feb", "value": 120}],
                data_keys=["value"],
                x_key="month",
            )

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.elements.get(ctx.root_element.child_ids[0])
        assert chart.component.name == "LineChart"
        assert len(chart.properties["data"]) == 2
        assert chart.properties["x_key"] == "month"

    def test_bar_chart_with_data(self) -> None:
        """BarChart stores data and configuration props."""

        @component
        def App() -> None:
            """
            Render a minimal test app containing a stacked BarChart widget.
            
            Renders a BarChart with a single data point {"category": "A", "value": 100"} and `stacked=True` for use in unit tests.
            """
            BarChart(
                data=[{"category": "A", "value": 100}],
                stacked=True,
            )

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.elements.get(ctx.root_element.child_ids[0])
        assert chart.component.name == "BarChart"
        assert chart.properties["stacked"] is True

    def test_area_chart_with_data(self) -> None:
        """AreaChart stores data and configuration props."""

        @component
        def App() -> None:
            """
            Renders an AreaChart component configured with a single data point and a step curve.
            
            The component is created with data containing one entry for "Jan" with value 100 and with `curve_type` set to "step".
            """
            AreaChart(
                data=[{"name": "Jan", "value": 100}],
                curve_type="step",
            )

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.elements.get(ctx.root_element.child_ids[0])
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

        chart = ctx.elements.get(ctx.root_element.child_ids[0])
        assert chart.component.name == "PieChart"
        assert chart.properties["inner_radius"] == 50

    def test_sparkline_with_data(self) -> None:
        """
        Verify that a Sparkline component stores provided visual and data properties.
        
        Asserts that the rendered Sparkline element exposes the supplied `data`, `height`, and `color` properties.
        """

        @component
        def App() -> None:
            """
            Render an App component that displays a Sparkline chart with predefined data, height, and color.
            
            The Sparkline is configured with data [10, 20, 15, 25], a height of 30, and color "#22c55e".
            """
            Sparkline(data=[10, 20, 15, 25], height=30, color="#22c55e")

        ctx = RenderSession(App)
        render(ctx)

        chart = ctx.elements.get(ctx.root_element.child_ids[0])
        assert chart.component.name == "Sparkline"
        assert chart.properties["data"] == [10, 20, 15, 25]
        assert chart.properties["height"] == 30
        assert chart.properties["color"] == "#22c55e"