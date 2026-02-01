"""Root application component for widget showcase."""

from trellis import Margin, Padding, Route, Routes, component, router
from trellis import widgets as w
from trellis.app import App, theme
from trellis.widgets import IconName, ThemeSwitcher

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
def WidgetShowcase() -> None:
    """Main application component with routed navigation."""
    # Get active tab from URL path (e.g., "/buttons" -> "buttons", "/" -> "layout")
    path = router().path
    active_tab = path.strip("/") or "layout"

    with w.Column(gap=0, style={"height": "100vh"}):
        # Header
        with w.Row(
            align="center",
            gap=12,
            padding=Padding(x=24, y=16),
            style={
                "borderBottom": f"1px solid {theme.border_default}",
                "backgroundColor": theme.bg_surface,
                "flexShrink": "0",
            },
        ):
            w.Icon(name=IconName.LAYOUT_DASHBOARD, size=24, color=theme.accent_primary)
            w.Heading(text="Trellis Widget Showcase", level=2, flex=1)
            ThemeSwitcher()

        # Main content with sidebar tabs
        with w.Row(gap=0, flex=1, style={"minHeight": "0", "alignItems": "stretch"}):
            # Sidebar
            with w.Column(
                gap=2,
                width=200,
                padding=12,
                style={
                    "borderRight": f"1px solid {theme.border_default}",
                    "backgroundColor": theme.bg_page,
                    "overflow": "auto",
                    "flexShrink": "0",
                },
            ):
                for tab_id, label, _icon, _ in TABS:
                    is_active = active_tab == tab_id
                    # Use href for client-side navigation
                    href = "/" if tab_id == "layout" else f"/{tab_id}"

                    w.Button(
                        text=label,
                        variant="primary" if is_active else "ghost",
                        size="sm",
                        href=href,
                        full_width=True,
                        style={"justifyContent": "flex-start"},
                    )

            # Content area
            with w.Column(
                flex=1,
                padding=24,
                style={"overflow": "auto"},
            ):
                with Routes():
                    # Default route shows Layout section
                    with Route(pattern="/"):
                        SectionContent(
                            label="Layout",
                            icon=IconName.LAYOUT_GRID,
                            section=LayoutSection,
                        )

                    # Generate routes for each tab
                    for tab_id, label, icon, SectionComponent in TABS:
                        if tab_id != "layout":  # Skip layout, it's the default
                            with Route(pattern=f"/{tab_id}"):
                                SectionContent(
                                    label=label,
                                    icon=icon,
                                    section=SectionComponent,
                                )


@component
def SectionContent(
    label: str,
    icon: IconName,
    section: type,
) -> None:
    """Render a section with header and content card."""
    # Section header
    with w.Row(align="center", gap=8, margin=Margin(bottom=16)):
        w.Icon(name=icon, size=20, color=theme.accent_primary)
        w.Heading(text=label, level=3)

    # Section content in a card
    with w.Card(padding=20):
        section()


app = App(WidgetShowcase)
