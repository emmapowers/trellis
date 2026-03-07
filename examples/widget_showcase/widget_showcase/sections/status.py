"""Status indicators and badges section of the widget showcase."""

import asyncio
from contextlib import suppress
import typing as tp

from trellis import component, mount, state
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Status Indicators")
def StatusIndicators() -> None:
    """Visual indicators for different states."""
    with w.Row(gap=16):
        w.StatusIndicator(status="success", label="Success")
        w.StatusIndicator(status="error", label="Error")
        w.StatusIndicator(status="warning", label="Warning")
        w.StatusIndicator(status="pending", label="Pending")
        w.StatusIndicator(status="info", label="Info")


@example("Badges")
def BadgeVariants() -> None:
    """Small labels for categorization."""
    with w.Row(gap=8):
        w.Badge(text="Default")
        w.Badge(text="Success", variant="success")
        w.Badge(text="Error", variant="error")
        w.Badge(text="Warning", variant="warning")
        w.Badge(text="Info", variant="info")


@example("Mount Lifecycle")
def MountLifecycle() -> None:
    """Show a mount-managed pulse task that restarts on remount."""
    pulse_count = state(0)
    active = state(False)

    async def heartbeat() -> tp.AsyncGenerator[None, None]:
        active.set(True)

        async def tick() -> None:
            while True:
                await asyncio.sleep(0.5)
                pulse_count.update(lambda value: value + 1)

        task = asyncio.create_task(tick())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    mount(heartbeat)

    with w.Column(gap=8):
        w.StatusIndicator(
            status="success" if active.value else "pending",
            label="Pulse task active" if active.value else "Waiting for mount",
        )
        w.Badge(text=f"Pulse {pulse_count.value}", variant="info")
        w.Label(text="Navigate away and back to confirm the pulse restarts cleanly.")


@component
def StatusSection() -> None:
    """Showcase status indicators and badges."""
    with w.Column(gap=16):
        ExampleCard(example=StatusIndicators)
        ExampleCard(example=BadgeVariants)
        ExampleCard(example=MountLifecycle)
