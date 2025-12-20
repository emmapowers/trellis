"""Icons section of the widget showcase."""

from trellis import component
from trellis import widgets as w
from trellis.widgets import IconName

from ..components import ExampleCard
from ..example import example


@example("Icons")
def Icons() -> None:
    """Icon variants, colors, and sizes."""
    with w.Column(gap=16):
        w.Label(text="Common Icons", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16):
            w.Icon(name=IconName.CHECK, size=20)
            w.Icon(name=IconName.X, size=20)
            w.Icon(name=IconName.PLUS, size=20)
            w.Icon(name=IconName.EDIT, size=20)
            w.Icon(name=IconName.TRASH, size=20)
            w.Icon(name=IconName.SEARCH, size=20)
            w.Icon(name=IconName.SETTINGS, size=20)
            w.Icon(name=IconName.HOME, size=20)

        w.Label(text="Status Icons", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16):
            w.Icon(name=IconName.INFO, size=20, color="#2563eb")
            w.Icon(name=IconName.CHECK_CIRCLE, size=20, color="#16a34a")
            w.Icon(name=IconName.ALERT_TRIANGLE, size=20, color="#d97706")
            w.Icon(name=IconName.ALERT_CIRCLE, size=20, color="#dc2626")

        w.Label(text="Chart Icons", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16):
            w.Icon(name=IconName.BAR_CHART, size=20)
            w.Icon(name=IconName.LINE_CHART, size=20)
            w.Icon(name=IconName.PIE_CHART, size=20)
            w.Icon(name=IconName.TRENDING_UP, size=20, color="#16a34a")
            w.Icon(name=IconName.TRENDING_DOWN, size=20, color="#dc2626")

        w.Label(text="Sizes", font_size=12, color="#64748b", bold=True)
        with w.Row(gap=16, align="center"):
            w.Icon(name=IconName.STAR, size=12)
            w.Icon(name=IconName.STAR, size=16)
            w.Icon(name=IconName.STAR, size=20)
            w.Icon(name=IconName.STAR, size=24)
            w.Icon(name=IconName.STAR, size=32)


@component
def IconsSection() -> None:
    """Showcase icon widget."""
    with w.Column(gap=16):
        ExampleCard(example=Icons)
