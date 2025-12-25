"""Actions section of the widget showcase."""

from trellis import component
from trellis import widgets as w
from trellis.widgets import IconName
from trellis.widgets import theme

from ..components import ExampleCard
from ..example import example


@example("Toolbar")
def ToolbarExample() -> None:
    """Grouped action buttons."""
    with w.Toolbar():
        w.Button(text="New", variant="primary", size="sm")
        w.Button(text="Edit", variant="secondary", size="sm")
        w.Button(text="Delete", variant="danger", size="sm")


@example("Menu")
def MenuExample() -> None:
    """Vertical list of actions."""
    with w.Menu(style={"maxWidth": "200px"}):
        w.MenuItem(text="New File", icon=IconName.FILE, shortcut="⌘N")
        w.MenuItem(text="Open...", icon=IconName.FOLDER_OPEN, shortcut="⌘O")
        w.MenuItem(text="Save", icon=IconName.SAVE, shortcut="⌘S")
        w.MenuDivider()
        w.MenuItem(text="Settings", icon=IconName.SETTINGS)
        w.MenuDivider()
        w.MenuItem(text="Delete", icon=IconName.TRASH, disabled=True)


@component
def ActionsSection() -> None:
    """Showcase action widgets."""
    with w.Column(gap=16):
        ExampleCard(example=ToolbarExample)
        ExampleCard(example=MenuExample)
