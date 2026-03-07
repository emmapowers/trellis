"""Root application component for widget showcase."""

import sys
from dataclasses import dataclass

from trellis import HotKey, Margin, Padding, Route, Routes, Stateful, component, router, sequence
from trellis import html as h
from trellis import widgets as w
from trellis.app import App, get_config, theme
from trellis.core.components.composition import CompositionComponent
from trellis.core.hotkey_types import Hotkey
from trellis.platforms.common.base import PlatformType
from trellis.widgets import IconName, ThemeSwitcher

from .components import Kbd
from .sections.actions import ActionsSection
from .sections.buttons import ButtonsSection
from .sections.charts import ChartsSection
from .sections.data import DataDisplaySection
from .sections.feedback import FeedbackSection
from .sections.forms import FormInputsSection
from .sections.icons import IconsSection
from .sections.keyboard import KeyboardSection
from .sections.layout import LayoutSection
from .sections.navigation import NavigationSection
from .sections.progress import ProgressSection
from .sections.status import StatusSection
from .sections.tables import TableSection
from .sections.tooltips import TooltipSection
from .sections.typography import TypographySection

type ShowcaseTab = tuple[str, str, IconName, CompositionComponent]


_BASE_TABS: list[ShowcaseTab] = [
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
    ("keyboard", "Keyboard", IconName.HASH, KeyboardSection),
]

# Map a single letter to each section for Mod+K → <letter> shortcuts.
# Uses first unused letter from the section name, like menu accelerators.
_SECTION_KEYS: dict[Hotkey, str] = {
    "L": "layout",
    "B": "buttons",
    "F": "forms",
    "S": "status",
    "T": "tables",
    "P": "progress",
    "O": "tooltips",  # t-O-oltips (T taken)
    "Y": "typography",  # t-Y-pography (T taken)
    "I": "icons",
    "C": "charts",
    "D": "data",
    "N": "navigation",
    "E": "feedback",  # f-E-edback (F taken)
    "A": "actions",
    "K": "keyboard",
    "X": "desktop",  # des-X-top (all other letters taken)
}


def _resolve_desktop_tab() -> ShowcaseTab:
    # Desktop section imports desktop-only APIs; keep import local to desktop platform.
    from .sections.desktop import DesktopSection  # noqa: PLC0415

    return ("desktop", "Desktop", IconName.MONITOR, DesktopSection)


def _resolve_platform() -> PlatformType:
    try:
        config = get_config()
    except RuntimeError:
        return PlatformType.SERVER

    if config is None:
        return PlatformType.SERVER

    return config.platform


def resolve_tabs(platform: PlatformType | None = None) -> list[ShowcaseTab]:
    tabs = list(_BASE_TABS)
    active_platform = platform if platform is not None else _resolve_platform()
    if active_platform != PlatformType.DESKTOP:
        return tabs

    forms_index = next(
        (index for index, (tab_id, *_rest) in enumerate(tabs) if tab_id == "forms"), -1
    )
    if forms_index == -1:
        tabs.append(_resolve_desktop_tab())
        return tabs

    tabs.insert(forms_index + 1, _resolve_desktop_tab())
    return tabs


def _tab_path(tab_id: str) -> str:
    return "/" if tab_id == "layout" else f"/{tab_id}"


def _active_tab_from_path(path: str) -> str:
    return path.strip("/") or "layout"


@dataclass
class HelpPanelState(Stateful):
    """State for the keyboard shortcut help panel."""

    visible: bool = False


@component
def WidgetShowcase() -> None:
    """Main application component with routed navigation."""
    path = router().path
    active_tab = _active_tab_from_path(path)
    tabs = resolve_tabs()
    help_state = HelpPanelState()

    # Build tab IDs list for next/prev navigation
    tab_ids = [tab_id for tab_id, *_ in tabs]
    r = router()

    # --- Navigation hotkeys ---

    async def go_next() -> bool:
        idx = tab_ids.index(active_tab) if active_tab in tab_ids else 0
        next_id = tab_ids[(idx + 1) % len(tab_ids)]
        await r.navigate(_tab_path(next_id))
        return True

    async def go_prev() -> bool:
        idx = tab_ids.index(active_tab) if active_tab in tab_ids else 0
        prev_id = tab_ids[(idx - 1) % len(tab_ids)]
        await r.navigate(_tab_path(prev_id))
        return True

    HotKey(filter=sequence("Mod+K", "]"), handler=go_next)
    HotKey(filter=sequence("Mod+K", "["), handler=go_prev)

    # Desktop-only: platform-native back/forward keys for router history
    if _resolve_platform() == PlatformType.DESKTOP:
        _HistoryHotKeys()

    # Section jump: Mod+K → <letter>
    for letter, section_id in _SECTION_KEYS.items():
        if section_id in tab_ids:
            _SectionHotKey(letter=letter, section_id=section_id)

    # Help panel toggle
    def toggle_help() -> bool:
        help_state.visible = not help_state.visible
        return True

    HotKey(filter="Shift+?", handler=toggle_help)

    with w.Column(gap=0, style=h.Style(height=h.vh(100))):
        # Header
        with w.Row(
            align="center",
            gap=12,
            padding=h.padding(16, 24),
            style=h.Style(
                border_bottom=f"1px solid {theme.border_default}",
                background_color=theme.bg_surface,
                flex_shrink=h.raw("0"),
            ),
        ):
            w.Icon(name=IconName.LAYOUT_DASHBOARD, size=24, color=theme.accent_primary)
            w.Heading(text="Trellis Widget Showcase", level=2, flex=1)
            w.Button(
                text="?",
                variant="ghost",
                size="sm",
                on_click=toggle_help,
                style={
                    "fontFamily": "ui-monospace, SFMono-Regular, Menlo, monospace",
                    "fontSize": "14px",
                    "width": "32px",
                },
            )
            ThemeSwitcher()

        # Main content with sidebar tabs
        with w.Row(gap=0, flex=1, style=h.Style(min_height=0, align_items="stretch")):
            # Sidebar
            with w.Column(
                gap=2,
                width=200,
                padding=12,
                style=h.Style(
                    border_right=f"1px solid {theme.border_default}",
                    background_color=theme.bg_page,
                    overflow="auto",
                    flex_shrink=h.raw("0"),
                ),
            ):
                for tab_id, label, _icon, _ in tabs:
                    is_active = active_tab == tab_id
                    w.Button(
                        text=label,
                        variant="primary" if is_active else "ghost",
                        size="sm",
                        href=_tab_path(tab_id),
                        full_width=True,
                        style=h.Style(justify_content="flex-start"),
                    )

            # Content area
            with w.Column(
                flex=1,
                padding=24,
                style=h.Style(overflow="auto"),
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
                    for tab_id, label, icon, SectionComponent in tabs:
                        if tab_id != "layout":
                            with Route(pattern=f"/{tab_id}"):
                                SectionContent(
                                    label=label,
                                    icon=icon,
                                    section=SectionComponent,
                                )

            # Help panel (slides in from right)
            if help_state.visible:
                HelpPanel(tabs=tabs, on_close=toggle_help)


@component
def _SectionHotKey(*, letter: Hotkey, section_id: str) -> None:
    """Register a Mod+K → <letter> hotkey for a section."""
    r = router()

    async def handler() -> bool:
        await r.navigate(_tab_path(section_id))
        return True

    HotKey(filter=sequence("Mod+K", letter), handler=handler)


@component
def _HistoryHotKeys() -> None:
    """Register platform-native back/forward hotkeys for desktop."""
    r = router()

    async def go_back() -> bool:
        await r.go_back()
        return True

    async def go_forward() -> bool:
        await r.go_forward()
        return True

    if sys.platform == "darwin":
        HotKey(filter="Meta+ArrowLeft", handler=go_back)
        HotKey(filter="Meta+ArrowRight", handler=go_forward)
        HotKey(filter="Meta+[", handler=go_back)
        HotKey(filter="Meta+]", handler=go_forward)
    else:
        HotKey(filter="Alt+ArrowLeft", handler=go_back)
        HotKey(filter="Alt+ArrowRight", handler=go_forward)


@component
def HelpPanel(*, tabs: list[ShowcaseTab], on_close: object) -> None:
    """Keyboard shortcut reference panel that slides in from the right."""
    with h.Div(
        style={
            "width": "300px",
            "flexShrink": "0",
            "borderLeft": f"1px solid {theme.border_default}",
            "backgroundColor": theme.bg_surface,
            "overflow": "auto",
            "padding": "20px",
        },
    ):
        with w.Column(gap=16):
            # Header
            with w.Row(justify="between", align="center"):
                w.Label(
                    text="Keyboard Shortcuts",
                    font_size=13,
                    bold=True,
                    color=theme.text_primary,
                )
                w.Button(
                    text="\u00d7",
                    variant="ghost",
                    size="sm",
                    on_click=on_close,
                    style={"fontSize": "18px", "width": "28px", "padding": "0"},
                )

            # Navigation section
            nav_shortcuts: list[tuple[str, str]] = [
                ("Mod+K  ]", "Next section"),
                ("Mod+K  [", "Previous section"),
            ]
            if _resolve_platform() == PlatformType.DESKTOP:
                if sys.platform == "darwin":
                    nav_shortcuts.append(("Cmd+Left", "Back"))
                    nav_shortcuts.append(("Cmd+Right", "Forward"))
                else:
                    nav_shortcuts.append(("Alt+Left", "Back"))
                    nav_shortcuts.append(("Alt+Right", "Forward"))
            _HelpSection(title="Navigation", shortcuts=nav_shortcuts)

            # Section jump
            section_shortcuts = []
            for letter, section_id in sorted(_SECTION_KEYS.items(), key=lambda kv: kv[1]):
                label = next((name for tid, name, *_ in tabs if tid == section_id), None)
                if label:
                    section_shortcuts.append((f"Mod+K  {letter}", label))

            _HelpSection(title="Jump to Section", shortcuts=section_shortcuts)

            # Other
            _HelpSection(
                title="Other",
                shortcuts=[
                    ("Shift+?", "Toggle this panel"),
                ],
            )


@component
def _HelpSection(*, title: str, shortcuts: list[tuple[str, str]]) -> None:
    """A group of shortcuts in the help panel."""
    with w.Column(gap=8):
        w.Label(
            text=title,
            font_size=11,
            bold=True,
            color=theme.text_muted,
            style={"textTransform": "uppercase", "letterSpacing": "0.05em"},
        )
        for keys, label in shortcuts:
            with w.Row(justify="between", align="center"):
                w.Label(text=label, font_size=13, color=theme.text_secondary)
                _ShortcutKeys(keys=keys)


@component
def _ShortcutKeys(*, keys: str) -> None:
    """Render a shortcut like 'Mod+K  J' as key caps with spacing for sequences."""
    parts = keys.split("  ")
    with h.Div(
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "gap": "6px",
        },
    ):
        for i, part in enumerate(parts):
            if i > 0:
                w.Label(text="\u2192", font_size=10, color=theme.text_muted)
            Kbd(keys=part)


@component
def SectionContent(
    label: str,
    icon: IconName,
    section: type,
) -> None:
    """Render a section with header and content card."""
    # Section header
    with w.Row(align="center", gap=8, style=h.Style(margin_bottom=16)):
        w.Icon(name=icon, size=20, color=theme.accent_primary)
        w.Heading(text=label, level=3)

    # Section content in a card
    with w.Card(padding=20):
        section()


app = App(WidgetShowcase)
