"""Tests for data display widgets: Stat, Tag, and chart widgets."""

from trellis.core.components.composition import component
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

    def test_stat_with_label_and_value(self, rendered) -> None:
        """Stat stores label and value props."""

        @component
        def App() -> None:
            Stat(label="Revenue", value="$12,345")

        result = rendered(App)

        stat = result.session.elements.get(result.root_element.child_ids[0])
        assert stat.component.name == "Stat"
        assert stat.properties["label"] == "Revenue"
        assert stat.properties["value"] == "$12,345"

    def test_stat_with_delta(self, rendered) -> None:
        """Stat accepts delta and delta_type props."""

        @component
        def App() -> None:
            Stat(label="Users", value="1,234", delta="+12%", delta_type="increase")

        result = rendered(App)

        stat = result.session.elements.get(result.root_element.child_ids[0])
        assert stat.properties["delta"] == "+12%"
        assert stat.properties["delta_type"] == "increase"

    def test_stat_with_size(self, rendered) -> None:
        """Stat accepts size prop."""

        @component
        def App() -> None:
            Stat(label="Big", value="999", size="lg")

        result = rendered(App)

        stat = result.session.elements.get(result.root_element.child_ids[0])
        assert stat.properties["size"] == "lg"


class TestTagWidget:
    """Tests for Tag widget."""

    def test_tag_with_text(self, rendered) -> None:
        """Tag stores text prop."""

        @component
        def App() -> None:
            Tag(text="Python")

        result = rendered(App)

        tag = result.session.elements.get(result.root_element.child_ids[0])
        assert tag.component.name == "Tag"
        assert tag.properties["text"] == "Python"

    def test_tag_with_variant(self, rendered) -> None:
        """Tag accepts variant prop."""

        @component
        def App() -> None:
            Tag(text="Success", variant="success")

        result = rendered(App)

        tag = result.session.elements.get(result.root_element.child_ids[0])
        assert tag.properties["variant"] == "success"

    def test_tag_removable_with_callback(self, rendered) -> None:
        """Tag captures on_remove callback when removable."""
        removed = []

        @component
        def App() -> None:
            Tag(text="Remove me", removable=True, on_remove=lambda: removed.append(True))

        result = rendered(App)

        tag = result.session.elements.get(result.root_element.child_ids[0])
        assert tag.properties["removable"] is True
        assert callable(tag.properties["on_remove"])

        tag.properties["on_remove"]()
        assert removed == [True]


class TestChartWidgets:
    """Tests for chart widgets."""

    def test_time_series_chart_with_data(self, rendered) -> None:
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

        result = rendered(App)

        chart = result.session.elements.get(result.root_element.child_ids[0])
        assert chart.component.name == "TimeSeriesChart"
        assert len(chart.properties["data"]) == 2
        assert chart.properties["height"] == 300

    def test_line_chart_with_data(self, rendered) -> None:
        """LineChart stores data and configuration props."""

        @component
        def App() -> None:
            LineChart(
                data=[{"month": "Jan", "value": 100}, {"month": "Feb", "value": 120}],
                data_keys=["value"],
                x_key="month",
            )

        result = rendered(App)

        chart = result.session.elements.get(result.root_element.child_ids[0])
        assert chart.component.name == "LineChart"
        assert len(chart.properties["data"]) == 2
        assert chart.properties["x_key"] == "month"

    def test_bar_chart_with_data(self, rendered) -> None:
        """BarChart stores data and configuration props."""

        @component
        def App() -> None:
            BarChart(
                data=[{"category": "A", "value": 100}],
                stacked=True,
            )

        result = rendered(App)

        chart = result.session.elements.get(result.root_element.child_ids[0])
        assert chart.component.name == "BarChart"
        assert chart.properties["stacked"] is True

    def test_area_chart_with_data(self, rendered) -> None:
        """AreaChart stores data and configuration props."""

        @component
        def App() -> None:
            AreaChart(
                data=[{"name": "Jan", "value": 100}],
                curve_type="step",
            )

        result = rendered(App)

        chart = result.session.elements.get(result.root_element.child_ids[0])
        assert chart.component.name == "AreaChart"
        assert chart.properties["curve_type"] == "step"

    def test_pie_chart_with_data(self, rendered) -> None:
        """PieChart stores data and configuration props."""

        @component
        def App() -> None:
            PieChart(
                data=[{"name": "A", "value": 60}, {"name": "B", "value": 40}],
                inner_radius=50,
            )

        result = rendered(App)

        chart = result.session.elements.get(result.root_element.child_ids[0])
        assert chart.component.name == "PieChart"
        assert chart.properties["inner_radius"] == 50

    def test_sparkline_with_data(self, rendered) -> None:
        """Sparkline stores data props."""

        @component
        def App() -> None:
            Sparkline(data=[10, 20, 15, 25], height=30, color="#22c55e")

        result = rendered(App)

        chart = result.session.elements.get(result.root_element.child_ids[0])
        assert chart.component.name == "Sparkline"
        assert chart.properties["data"] == [10, 20, 15, 25]
        assert chart.properties["height"] == 30
        assert chart.properties["color"] == "#22c55e"
