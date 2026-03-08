"""Data display section of the widget showcase."""

import asyncio

from trellis import component, load
from trellis import widgets as w
from trellis.state import Failed, Ready
from trellis.widgets import IconName

from ..components import ExampleCard
from ..example import example


@example("Stats")
def Stats() -> None:
    """Key metrics with delta indicators."""
    with w.Row(gap=16):
        w.Stat(
            label="Revenue",
            value="$12,450",
            delta="+12%",
            delta_type="increase",
            icon=IconName.TRENDING_UP,
        )
        w.Stat(
            label="Users",
            value="1,234",
            delta="-5%",
            delta_type="decrease",
            icon=IconName.USERS,
        )
        w.Stat(
            label="Orders",
            value="456",
            delta="0%",
            delta_type="neutral",
            icon=IconName.ACTIVITY,
        )


@example("Tags")
def Tags() -> None:
    """Categorization labels."""
    with w.Row(gap=8):
        w.Tag(text="Default")
        w.Tag(text="Primary", variant="primary")
        w.Tag(text="Success", variant="success")
        w.Tag(text="Warning", variant="warning")
        w.Tag(text="Error", variant="error")
        w.Tag(text="Removable", variant="primary", removable=True)


type MetricData = dict[str, str | IconName]


METRICS: dict[str, MetricData] = {
    "revenue": {
        "label": "Revenue",
        "value": "$12,450",
        "delta": "+12%",
        "delta_type": "increase",
        "icon": IconName.TRENDING_UP,
    },
    "users": {
        "label": "Users",
        "value": "1,234",
        "delta": "-5%",
        "delta_type": "decrease",
        "icon": IconName.USERS,
    },
    "orders": {
        "label": "Orders",
        "value": "456",
        "delta": "+3%",
        "delta_type": "increase",
        "icon": IconName.ACTIVITY,
    },
}


@example("Async Load", includes=["METRICS"])
def AsyncLoadExample() -> None:
    """Focused local async loading example with reload support."""

    async def fetch_metric() -> MetricData:
        await asyncio.sleep(0.35)
        return METRICS["revenue"]

    result = load(fetch_metric)

    with w.Column(gap=12):
        w.Button(text="Reload", variant="outline", on_click=result.reload)

        if result.loading:
            with w.Callout(title="Loading", intent="info"):
                w.Label(text="Fetching local metrics...")
        elif isinstance(result, Failed):
            with w.Callout(title="Error", intent="error"):
                w.Label(text=str(result.error))
        else:
            assert isinstance(result, Ready)
            metric_data = result.value
            w.Stat(
                label=metric_data["label"],
                value=metric_data["value"],
                delta=metric_data["delta"],
                delta_type=metric_data["delta_type"],
                icon=metric_data["icon"],
            )


@component
def DataDisplaySection() -> None:
    """Showcase data display widgets."""
    with w.Column(gap=16):
        ExampleCard(example=Stats)
        ExampleCard(example=Tags)
        ExampleCard(example=AsyncLoadExample)
