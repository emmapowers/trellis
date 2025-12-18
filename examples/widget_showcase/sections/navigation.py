"""Navigation section of the widget showcase."""

from trellis import component
from trellis import widgets as w
from trellis.widgets import IconName

from ..state import ShowcaseState


@component
def NavigationSection() -> None:
    """Showcase navigation widgets."""
    state = ShowcaseState.from_context()

    with w.Column(gap=16):
        # Tabs
        w.Label(text="Tabs", font_size=12, color="#64748b", bold=True)
        with w.Tabs(
            selected=state.selected_tab,
            on_change=lambda t: setattr(state, "selected_tab", t),
            style={"marginTop": "8px"},
        ):
            with w.Tab(id="overview", label="Overview", icon=IconName.HOME):
                w.Label(text="Overview tab content goes here.")
            with w.Tab(id="analytics", label="Analytics", icon=IconName.BAR_CHART):
                w.Label(text="Analytics tab content goes here.")
            with w.Tab(id="settings", label="Settings", icon=IconName.SETTINGS):
                w.Label(text="Settings tab content goes here.")

        # Breadcrumb
        w.Label(text="Breadcrumb", font_size=12, color="#64748b", bold=True)
        w.Breadcrumb(
            items=[
                {"label": "Home"},
                {"label": "Products"},
                {"label": "Electronics"},
                {"label": "Phones"},
            ],
            style={"marginTop": "8px"},
        )

        # Tree
        w.Label(text="Tree", font_size=12, color="#64748b", bold=True)
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
            selected=state.selected_tree_node,
            on_select=lambda n: setattr(state, "selected_tree_node", n),
            style={"marginTop": "8px"},
        )
