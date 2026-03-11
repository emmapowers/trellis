"""Navigation section of the widget showcase."""

from trellis import component, mutable, state_var
from trellis import widgets as w
from trellis.widgets import IconName

from ..components import ExampleCard
from ..example import example


@example("Tabs")
def TabsExample() -> None:
    """Tabbed content navigation."""
    selected_tab = state_var("overview")
    with w.Tabs(
        selected=mutable(selected_tab.value),
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


@example("Tree")
def TreeExample() -> None:
    """Hierarchical data navigation."""

    def initial_selection() -> str | None:
        return None

    selected_node = state_var(factory=initial_selection)
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
        selected=selected_node.value,
        on_select=selected_node.set,
    )


@example("Collapsible")
def CollapsibleExample() -> None:
    """Expandable content section."""
    expanded = state_var(False)
    experimental_features = state_var(False)
    with w.Collapsible(
        title="Advanced Settings",
        expanded=mutable(expanded.value),
        icon=IconName.SETTINGS,
    ):
        with w.Column(gap=8):
            w.Label(text="This content can be collapsed.")
            w.Checkbox(
                checked=mutable(experimental_features.value),
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
