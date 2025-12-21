"""Root application component for widget showcase."""

from trellis import Margin, Padding, component
from trellis import widgets as w
from trellis.widgets import IconName

from .sections import (
    ActionsSection,
    ButtonsSection,
    ChartsSection,
    DataDisplaySection,
    FeedbackSection,
    FormInputsSection,
    IconsSection,
    LayoutSection,
    NavigationSection,
    ProgressSection,
    StatusSection,
    TableSection,
    TooltipSection,
    TypographySection,
)
from .state import ShowcaseState


# Tab definitions: (id, label, icon, component)
TABS = [
    ("layout", "Layout", IconName.LAYOUT_GRID, LayoutSection),
    ("buttons", "Buttons", IconName.MOUSE_POINTER, ButtonsSection),
    ("forms", "Forms", IconName.EDIT_2, FormInputsSection),
    ("status", "Status", IconName.CHECK_CIRCLE, StatusSection),
    ("tables", "Tables", IconName.TABLE, TableSection),
    ("progress", "Progress", IconName.LOADER, ProgressSection),
    ("tooltips", "Tooltips", IconName.MESSAGE_SQUARE, TooltipSection),
    ("typography", "Typography", IconName.TYPE, TypographySection),
    ("icons", "Icons", IconName.STAR, IconsSection),
    ("charts", "Charts", IconName.BAR_CHART, ChartsSection),
    ("data", "Data", IconName.ACTIVITY, DataDisplaySection),
    ("navigation", "Navigation", IconName.COMPASS, NavigationSection),
    ("feedback", "Feedback", IconName.BELL, FeedbackSection),
    ("actions", "Actions", IconName.MENU, ActionsSection),
]


@component
def App() -> None:
    """Main application component with tabbed navigation."""
    state = ShowcaseState()

    with state:
        with w.Column(gap=0, style={"height": "100vh"}):
            # Header
            with w.Row(
                align="center",
                gap=12,
                padding=Padding(x=24, y=16),
                style={
                    "borderBottom": "1px solid #e2e8f0",
                    "backgroundColor": "#ffffff",
                    "flexShrink": "0",
                },
            ):
                w.Icon(name=IconName.LAYOUT_DASHBOARD, size=24, color="#6366f1")
                w.Heading(text="Trellis Widget Showcase", level=2)

            # Main content with sidebar tabs
            with w.Row(gap=0, flex=1, style={"minHeight": "0", "alignItems": "stretch"}):
                # Sidebar
                with w.Column(
                    gap=2,
                    width=200,
                    padding=12,
                    style={
                        "borderRight": "1px solid #e2e8f0",
                        "backgroundColor": "#f8fafc",
                        "overflow": "auto",
                        "flexShrink": "0",
                    },
                ):
                    for tab_id, label, icon, _ in TABS:
                        is_active = state.active_tab == tab_id

                        def set_tab(tid: str=tab_id) -> None:
                            state.active_tab = tid

                        w.Button(
                            text=label,
                            variant="primary" if is_active else "ghost",
                            size="sm",
                            on_click=set_tab,
                            full_width=True,
                            style={"justifyContent": "flex-start"},
                        )

                # Content area
                with w.Column(
                    flex=1,
                    padding=24,
                    style={"overflow": "auto"},
                ):
                    # Find and render the active section
                    for tab_id, label, icon, SectionComponent in TABS:
                        if state.active_tab == tab_id:
                            # Section header
                            with w.Row(align="center", gap=8, margin=Margin(bottom=16)):
                                w.Icon(name=icon, size=20, color="#6366f1")
                                w.Heading(text=label, level=3)

                            # Section content in a card
                            with w.Card(padding=20):
                                SectionComponent()
                            break
