"""Data display section of the widget showcase."""

import asyncio

from trellis import component, load, mutable, state
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


METRICS = {
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
    """Deterministic local async loading with success, failure, and reload states."""
    metric = state("revenue")
    force_error = state(False)

    async def fetch_metric(name: str, should_fail: bool) -> dict[str, str]:
        delay = 0.45 if name == "revenue" else 0.2
        await asyncio.sleep(delay)
        if should_fail:
            raise RuntimeError(f"Could not load {name}")
        return METRICS[name]

    result = load(fetch_metric, metric.value, force_error.value)

    with w.Column(gap=12):
        with w.Row(gap=8, align="center"):
            w.Label(text="Metric:", width=80)
            w.Select(
                value=mutable(metric.value),
                options=[
                    {"value": "revenue", "label": "Revenue"},
                    {"value": "users", "label": "Users"},
                    {"value": "orders", "label": "Orders"},
                ],
                width=180,
            )
            w.Checkbox(
                checked=mutable(force_error.value),
                label="Force error",
            )
            w.Button(text="Reload", variant="outline", on_click=result.reload)

        if result.loading:
            with w.Callout(title="Loading", intent="info"):
                w.Label(text="Fetching local metrics...")
        elif isinstance(result, Failed):
            with w.Callout(title="Load Failed", intent="error"):
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
