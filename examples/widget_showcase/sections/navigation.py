"""Navigation section of the widget showcase."""

from trellis import Stateful, component, mutable
from trellis import widgets as w
from trellis.widgets import IconName
from trellis.widgets import theme

from ..components import ExampleCard
from ..example import example


class TabsState(Stateful):
    """State for tabs example."""

    selected_tab: str = "overview"


@example("Tabs", includes=[TabsState])
def TabsExample() -> None:
    """Tabbed content navigation."""
    state = TabsState()
    with w.Tabs(
        selected=mutable(state.selected_tab),
    ):
        with w.Tab(id="overview", label="Overview", icon=IconName.HOME):
            w.Label(text="Overview tab content goes here.")
        with w.Tab(id="analytics", label="Analytics", icon=IconName.BAR_CHART):
            w.Label(text="Analytics tab content goes here.")
        with w.Tab(id="settings", label="Settings", icon=IconName.SETTINGS):
            w.Label(text="Settings tab content goes here.")


@example("Breadcrumb")
def BreadcrumbExample() -> None:
    """Hierarchical navigation path."""
    w.Breadcrumb(
        items=[
            {"label": "Home"},
            {"label": "Products"},
            {"label": "Electronics"},
            {"label": "Phones"},
        ],
    )


class TreeState(Stateful):
    """State for tree example."""

    selected_node: str | None = None


@example("Tree", includes=[TreeState])
def TreeExample() -> None:
    """Hierarchical data navigation."""
    state = TreeState()
    w.Tree(
        data=[
            {
                "id": "src",
                "label": "src",
                "children": [
                    {"id": "components", "label": "components"},
                    {"id": "utils", "label": "utils"},
                    {"id": "main.py", "label": "main.py"},
                ],
            },
            {
                "id": "tests",
                "label": "tests",
                "children": [
                    {"id": "test_main.py", "label": "test_main.py"},
                ],
            },
            {"id": "README.md", "label": "README.md"},
        ],
        selected=state.selected_node,
        on_select=lambda n: setattr(state, "selected_node", n),
    )


class CollapsibleState(Stateful):
    """State for collapsible example."""

    expanded: bool = False
    experimental_features: bool = False


@example("Collapsible", includes=[CollapsibleState])
def CollapsibleExample() -> None:
    """Expandable content section."""
    state = CollapsibleState()
    with w.Collapsible(
        title="Advanced Settings",
        expanded=mutable(state.expanded),
        icon=IconName.SETTINGS,
    ):
        with w.Column(gap=8):
            w.Label(text="This content can be collapsed.")
            w.Checkbox(
                checked=mutable(state.experimental_features),
                label="Enable experimental features",
            )


@component
def NavigationSection() -> None:
    """Showcase navigation widgets."""
    with w.Column(gap=16):
        ExampleCard(example=TabsExample)
        ExampleCard(example=BreadcrumbExample)
        ExampleCard(example=TreeExample)
        ExampleCard(example=CollapsibleExample)
