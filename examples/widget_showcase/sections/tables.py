"""Table section of the widget showcase."""

from trellis import component
from trellis import widgets as w

from ..components import ExampleCard
from ..example import example


@example("Basic Table")
def BasicTable() -> None:
    """Table with columns and striped rows."""
    w.Table(
        columns=[
            {"key": "name", "label": "Name", "width": "150px"},
            {"key": "status", "label": "Status", "align": "center"},
            {"key": "value", "label": "Value", "align": "right"},
            {"key": "change", "label": "Change", "align": "right"},
        ],
        data=[
            {"name": "Revenue", "status": "Active", "value": "$12,450", "change": "+12%"},
            {"name": "Users", "status": "Active", "value": "1,234", "change": "+5%"},
            {"name": "Orders", "status": "Pending", "value": "456", "change": "-2%"},
            {"name": "Conversion", "status": "Active", "value": "3.2%", "change": "+0.5%"},
        ],
        striped=True,
    )


@component
def TableSection() -> None:
    """Showcase table widget."""
    with w.Column(gap=16):
        ExampleCard(example=BasicTable)
