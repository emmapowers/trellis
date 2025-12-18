"""Actions section of the widget showcase."""

from trellis import component
from trellis import widgets as w
from trellis.icons import IconName


@component
def ActionsSection() -> None:
    """Showcase action widgets."""
    with w.Column(gap=16):
        # Toolbar
        w.Label(text="Toolbar", font_size=12, color="#64748b", bold=True)
        with w.Toolbar(style={"marginTop": "8px"}):
            w.Button(text="New", variant="primary", size="sm")
            w.Button(text="Edit", variant="secondary", size="sm")
            w.Button(text="Delete", variant="danger", size="sm")

        # Menu
        w.Label(text="Menu", font_size=12, color="#64748b", bold=True)
        with w.Menu(style={"marginTop": "8px", "maxWidth": "200px"}):
            w.MenuItem(text="New File", icon=IconName.FILE, shortcut="⌘N")
            w.MenuItem(text="Open...", icon=IconName.FOLDER_OPEN, shortcut="⌘O")
            w.MenuItem(text="Save", icon=IconName.SAVE, shortcut="⌘S")
            w.MenuDivider()
            w.MenuItem(text="Settings", icon=IconName.SETTINGS)
            w.MenuDivider()
            w.MenuItem(text="Delete", icon=IconName.TRASH, disabled=True)
