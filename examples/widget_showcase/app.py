"""Root application component for widget showcase."""

from trellis import component
from trellis import widgets as w
from trellis.icons import IconName

from .state import ShowcaseState
from .sections import (
    ButtonsSection,
    FormInputsSection,
    StatusSection,
    TableSection,
    ProgressSection,
    TooltipSection,
    TypographySection,
    IconsSection,
    ChartsSection,
    DataDisplaySection,
    NavigationSection,
    FeedbackSection,
    ActionsSection,
)


# Tab definitions: (id, label, icon, component)
TABS = [
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
        with w.Column(
            gap=0,
            style={
                "minHeight": "100vh",
            },
        ):
            # Header
            with w.Row(
                align="center",
                gap=12,
                style={
                    "padding": "16px 24px",
                    "borderBottom": "1px solid #e2e8f0",
                    "backgroundColor": "#ffffff",
                },
            ):
                w.Icon(name=IconName.LAYOUT_DASHBOARD, size=24, color="#6366f1")
                w.Heading(text="Trellis Widget Showcase", level=2)

            # Main content with sidebar tabs
            with w.Row(gap=0, style={"flex": "1"}):
                # Sidebar
                with w.Column(
                    gap=2,
                    style={
                        "width": "200px",
                        "padding": "12px",
                        "borderRight": "1px solid #e2e8f0",
                        "backgroundColor": "#f8fafc",
                    },
                ):
                    for tab_id, label, icon, _ in TABS:
                        is_active = state.active_tab == tab_id
                        w.Button(
                            text=label,
                            variant="primary" if is_active else "ghost",
                            size="sm",
                            on_click=lambda t=tab_id: setattr(state, "active_tab", t),
                            style={
                                "width": "100%",
                                "justifyContent": "flex-start",
                            },
                        )

                # Content area
                with w.Column(
                    style={
                        "flex": "1",
                        "padding": "24px",
                        "overflow": "auto",
                    },
                ):
                    # Find and render the active section
                    for tab_id, label, icon, SectionComponent in TABS:
                        if state.active_tab == tab_id:
                            # Section header
                            with w.Row(align="center", gap=8, style={"marginBottom": "16px"}):
                                w.Icon(name=icon, size=20, color="#6366f1")
                                w.Heading(text=label, level=3)

                            # Section content in a card
                            with w.Card(padding=20):
                                SectionComponent()
                            break
