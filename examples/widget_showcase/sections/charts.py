"""Charts section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Line & Area Charts")
def LineAndAreaCharts() -> None:
    """Time series data visualization."""
    with w.Row(gap=16):
        with w.Column(flex=1):
            w.LineChart(
                data=[
                    {"name": "Jan", "value": 100, "value2": 80},
                    {"name": "Feb", "value": 120, "value2": 90},
                    {"name": "Mar", "value": 90, "value2": 110},
                    {"name": "Apr", "value": 150, "value2": 100},
                    {"name": "May", "value": 130, "value2": 120},
                ],
                data_keys=["value", "value2"],
                height=150,
            )
        with w.Column(flex=1):
            w.AreaChart(
                data=[
                    {"name": "Jan", "value": 100},
                    {"name": "Feb", "value": 120},
                    {"name": "Mar", "value": 90},
                    {"name": "Apr", "value": 150},
                    {"name": "May", "value": 130},
                ],
                data_keys=["value"],
                height=150,
            )


@example("Bar & Pie Charts")
def BarAndPieCharts() -> None:
    """Categorical data visualization."""
    with w.Row(gap=16):
        with w.Column(flex=1):
            w.BarChart(
                data=[
                    {"name": "A", "value": 40},
                    {"name": "B", "value": 30},
                    {"name": "C", "value": 50},
                    {"name": "D", "value": 25},
                ],
                data_keys=["value"],
                height=150,
            )
        with w.Column(flex=1):
            w.PieChart(
                data=[
                    {"name": "Desktop", "value": 60},
                    {"name": "Mobile", "value": 30},
                    {"name": "Tablet", "value": 10},
                ],
                height=150,
            )


@example("Sparklines")
def Sparklines() -> None:
    """Compact inline charts."""
    with w.Row(gap=24, align="center"):
        w.Sparkline(data=[10, 20, 15, 30, 25, 35, 30], width=100, height=30)
        w.Sparkline(
            data=[30, 25, 35, 20, 30, 15, 25],
            width=100,
            height=30,
            show_area=True,
        )
        w.Sparkline(
            data=[5, 10, 8, 15, 12, 20, 18],
            width=100,
            height=30,
            color=w.theme.success,
        )


@component
def ChartsSection() -> None:
    """Showcase chart widgets."""
    with w.Column(gap=16):
        ExampleCard(example=LineAndAreaCharts)
        ExampleCard(example=BarAndPieCharts)
        ExampleCard(example=Sparklines)
