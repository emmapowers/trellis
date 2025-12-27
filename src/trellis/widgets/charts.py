"""Chart widgets for data visualization."""

from __future__ import annotations

import typing as tp

from trellis.core.components.react import react_component_base
from trellis.core.components.style_props import Margin
from trellis.core.rendering.element import ElementNode


@react_component_base("TimeSeriesChart")
def TimeSeriesChart(
    *,
    data: list[list[float]] | None = None,
    series: list[dict[str, tp.Any]] | None = None,
    width: int | None = None,
    height: int = 200,
    title: str | None = None,
    show_legend: bool = True,
    show_tooltip: bool = True,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """High-performance time-series chart using uPlot.

    Optimized for real-time data with high update frequencies.

    Args:
        data: Array of arrays where first array is timestamps (Unix seconds),
            and subsequent arrays are values for each series.
            Example: [[1700000000, 1700000001, ...], [10, 20, ...], [5, 15, ...]]
        series: List of series configuration dicts. Each can contain:
            - label: Series name for legend
            - stroke: Line color (CSS color string)
            - fill: Area fill color (optional)
            - width: Line width in pixels
        width: Chart width in pixels. Defaults to container width.
        height: Chart height in pixels. Defaults to 200.
        title: Optional chart title.
        show_legend: Whether to show the legend. Defaults to True.
        show_tooltip: Whether to show tooltip on hover. Defaults to True.
        margin: Margin around the chart (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the TimeSeriesChart component.

    Example:
        TimeSeriesChart(
            data=[
                [1700000000, 1700000001, 1700000002],  # timestamps
                [10, 20, 15],  # series 1
                [5, 8, 12],   # series 2
            ],
            series=[
                {"label": "CPU", "stroke": "#6366f1"},
                {"label": "Memory", "stroke": "#22c55e"},
            ],
            height=300,
        )
    """
    ...


@react_component_base("LineChart")
def LineChart(
    *,
    data: list[dict[str, tp.Any]] | None = None,
    data_keys: list[str] | None = None,
    x_key: str = "name",
    width: int | None = None,
    height: int = 200,
    show_grid: bool = True,
    show_legend: bool = True,
    show_tooltip: bool = True,
    colors: list[str] | None = None,
    curve_type: tp.Literal["linear", "monotone", "step"] = "monotone",
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Line chart using Recharts.

    General-purpose line chart for trend visualization.

    Args:
        data: List of data point dicts. Each dict should contain the x_key
            and values for each data_key.
            Example: [{"name": "Jan", "value": 100}, {"name": "Feb", "value": 120}]
        data_keys: List of keys to plot as lines. Defaults to ["value"].
        x_key: Key to use for the X axis. Defaults to "name".
        width: Chart width in pixels. Defaults to container width.
        height: Chart height in pixels. Defaults to 200.
        show_grid: Whether to show grid lines. Defaults to True.
        show_legend: Whether to show the legend. Defaults to True.
        show_tooltip: Whether to show tooltip on hover. Defaults to True.
        colors: List of colors for each data key. Defaults to theme palette.
        curve_type: Line interpolation type. Defaults to "monotone".
        margin: Margin around the chart (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the LineChart component.

    Example:
        LineChart(
            data=[
                {"month": "Jan", "sales": 100, "revenue": 200},
                {"month": "Feb", "sales": 120, "revenue": 250},
            ],
            data_keys=["sales", "revenue"],
            x_key="month",
        )
    """
    ...


@react_component_base("BarChart")
def BarChart(
    *,
    data: list[dict[str, tp.Any]] | None = None,
    data_keys: list[str] | None = None,
    x_key: str = "name",
    width: int | None = None,
    height: int = 200,
    show_grid: bool = True,
    show_legend: bool = True,
    show_tooltip: bool = True,
    colors: list[str] | None = None,
    stacked: bool = False,
    layout: tp.Literal["horizontal", "vertical"] = "horizontal",
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Bar chart using Recharts.

    Categorical data comparison with vertical or horizontal bars.

    Args:
        data: List of data point dicts.
        data_keys: List of keys to plot as bars. Defaults to ["value"].
        x_key: Key to use for the X axis. Defaults to "name".
        width: Chart width in pixels. Defaults to container width.
        height: Chart height in pixels. Defaults to 200.
        show_grid: Whether to show grid lines. Defaults to True.
        show_legend: Whether to show the legend. Defaults to True.
        show_tooltip: Whether to show tooltip on hover. Defaults to True.
        colors: List of colors for each data key. Defaults to theme palette.
        stacked: Whether to stack bars. Defaults to False.
        layout: Bar orientation. Defaults to "horizontal".
        margin: Margin around the chart (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the BarChart component.

    Example:
        BarChart(
            data=[
                {"category": "A", "value": 100},
                {"category": "B", "value": 200},
            ],
            data_keys=["value"],
            x_key="category",
        )
    """
    ...


@react_component_base("AreaChart")
def AreaChart(
    *,
    data: list[dict[str, tp.Any]] | None = None,
    data_keys: list[str] | None = None,
    x_key: str = "name",
    width: int | None = None,
    height: int = 200,
    show_grid: bool = True,
    show_legend: bool = True,
    show_tooltip: bool = True,
    colors: list[str] | None = None,
    stacked: bool = False,
    curve_type: tp.Literal["linear", "monotone", "step"] = "monotone",
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Area chart using Recharts.

    Line chart with filled area beneath, good for showing volume/magnitude.

    Args:
        data: List of data point dicts.
        data_keys: List of keys to plot as areas. Defaults to ["value"].
        x_key: Key to use for the X axis. Defaults to "name".
        width: Chart width in pixels. Defaults to container width.
        height: Chart height in pixels. Defaults to 200.
        show_grid: Whether to show grid lines. Defaults to True.
        show_legend: Whether to show the legend. Defaults to True.
        show_tooltip: Whether to show tooltip on hover. Defaults to True.
        colors: List of colors for each data key. Defaults to theme palette.
        stacked: Whether to stack areas. Defaults to False.
        curve_type: Line interpolation type. Defaults to "monotone".
        margin: Margin around the chart (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the AreaChart component.
    """
    ...


@react_component_base("PieChart")
def PieChart(
    *,
    data: list[dict[str, tp.Any]] | None = None,
    data_key: str = "value",
    name_key: str = "name",
    width: int | None = None,
    height: int = 200,
    inner_radius: int = 0,
    show_legend: bool = True,
    show_tooltip: bool = True,
    show_labels: bool = False,
    colors: list[str] | None = None,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Pie/donut chart using Recharts.

    Part-to-whole relationships. Set inner_radius > 0 for donut style.

    Args:
        data: List of data point dicts with name and value.
            Example: [{"name": "A", "value": 100}, {"name": "B", "value": 200}]
        data_key: Key for the numeric value. Defaults to "value".
        name_key: Key for the segment name. Defaults to "name".
        width: Chart width in pixels. Defaults to container width.
        height: Chart height in pixels. Defaults to 200.
        inner_radius: Inner radius for donut chart. 0 = pie, >0 = donut.
        show_legend: Whether to show the legend. Defaults to True.
        show_tooltip: Whether to show tooltip on hover. Defaults to True.
        show_labels: Whether to show labels on segments. Defaults to False.
        colors: List of colors for segments. Defaults to theme palette.
        margin: Margin around the chart (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the PieChart component.

    Example:
        PieChart(
            data=[
                {"name": "Desktop", "value": 60},
                {"name": "Mobile", "value": 30},
                {"name": "Tablet", "value": 10},
            ],
            inner_radius=50,  # Donut style
        )
    """
    ...


@react_component_base("Sparkline")
def Sparkline(
    *,
    data: list[float] | None = None,
    width: int = 80,
    height: int = 24,
    color: str | None = None,
    show_area: bool = False,
    margin: Margin | None = None,
    flex: int | None = None,
    class_name: str | None = None,
    style: dict[str, tp.Any] | None = None,
    key: str | None = None,
) -> ElementNode:
    """Inline mini-chart for compact data visualization.

    Ideal for use in tables, cards, or alongside metrics.

    Args:
        data: List of numeric values to plot.
        width: Chart width in pixels. Defaults to 80.
        height: Chart height in pixels. Defaults to 24.
        color: Line/area color. Defaults to theme accent color.
        show_area: Whether to fill area under the line. Defaults to False.
        margin: Margin around the sparkline (Margin dataclass).
        flex: Flex grow/shrink value.
        class_name: CSS class name(s) to apply.
        style: Additional inline styles to apply.
        key: Optional key for reconciliation.

    Returns:
        An ElementNode for the Sparkline component.

    Example:
        Sparkline(data=[10, 20, 15, 25, 30, 28], color="#22c55e")
    """
    ...
