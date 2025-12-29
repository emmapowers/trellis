"""Tests for action widgets: Callout, Collapsible, Menu, Toolbar."""

from trellis.core.components.composition import component
from trellis.widgets import (
    Button,
    Callout,
    Collapsible,
    Label,
    Menu,
    MenuDivider,
    MenuItem,
    Toolbar,
)


class TestFeedbackWidgets:
    """Tests for feedback widgets."""

    def test_callout_with_title_and_intent(self, rendered) -> None:
        """Callout stores title and intent props."""

        @component
        def App() -> None:
            with Callout(title="Warning", intent="warning"):
                Label(text="Be careful!")

        result = rendered(App)

        callout = result.session.elements.get(result.root_element.child_ids[0])
        assert callout.component.name == "Callout"
        assert callout.properties["title"] == "Warning"
        assert callout.properties["intent"] == "warning"
        assert len(callout.child_ids) == 1

    def test_callout_dismissible_with_callback(self, rendered) -> None:
        """Callout captures on_dismiss callback when dismissible."""
        dismissed = []

        @component
        def App() -> None:
            with Callout(dismissible=True, on_dismiss=lambda: dismissed.append(True)):
                Label(text="Dismissable")

        result = rendered(App)

        callout = result.session.elements.get(result.root_element.child_ids[0])
        assert callout.properties["dismissible"] is True
        callout.properties["on_dismiss"]()
        assert dismissed == [True]

    def test_collapsible_with_title(self, rendered) -> None:
        """Collapsible stores title and expanded props."""

        @component
        def App() -> None:
            with Collapsible(title="Details", expanded=False):
                Label(text="Hidden content")

        result = rendered(App)

        collapsible = result.session.elements.get(result.root_element.child_ids[0])
        assert collapsible.component.name == "Collapsible"
        assert collapsible.properties["title"] == "Details"
        assert collapsible.properties["expanded"] is False

    def test_collapsible_with_callback(self, rendered) -> None:
        """Collapsible captures on_toggle callback."""
        toggles: list[bool] = []

        @component
        def App() -> None:
            with Collapsible(title="Toggle", on_toggle=lambda v: toggles.append(v)):
                Label(text="Content")

        result = rendered(App)

        collapsible = result.session.elements.get(result.root_element.child_ids[0])
        collapsible.properties["on_toggle"](True)
        assert toggles == [True]


class TestActionWidgets:
    """Tests for action widgets."""

    def test_menu_with_items(self, rendered) -> None:
        """Menu renders children."""

        @component
        def App() -> None:
            with Menu():
                MenuItem(text="Open")
                MenuItem(text="Save")
                MenuDivider()
                MenuItem(text="Exit")

        result = rendered(App)

        menu = result.session.elements.get(result.root_element.child_ids[0])
        assert menu.component.name == "Menu"
        assert len(menu.child_ids) == 4

    def test_menu_item_with_props(self, rendered) -> None:
        """MenuItem stores text, icon, and other props."""

        @component
        def App() -> None:
            with Menu():
                MenuItem(text="Delete", icon="trash", disabled=True, shortcut="Ctrl+D")

        result = rendered(App)

        menu = result.session.elements.get(result.root_element.child_ids[0])
        item = result.session.elements.get(menu.child_ids[0])
        assert item.component.name == "MenuItem"
        assert item.properties["text"] == "Delete"
        assert item.properties["icon"] == "trash"
        assert item.properties["disabled"] is True
        assert item.properties["shortcut"] == "Ctrl+D"

    def test_menu_item_with_callback(self, rendered) -> None:
        """MenuItem captures on_click callback."""
        clicks = []

        @component
        def App() -> None:
            with Menu():
                MenuItem(text="Click me", on_click=lambda: clicks.append(True))

        result = rendered(App)

        menu = result.session.elements.get(result.root_element.child_ids[0])
        item = result.session.elements.get(menu.child_ids[0])
        item.properties["on_click"]()
        assert clicks == [True]

    def test_menu_divider_renders(self, rendered) -> None:
        """MenuDivider component renders."""

        @component
        def App() -> None:
            with Menu():
                MenuDivider()

        result = rendered(App)

        menu = result.session.elements.get(result.root_element.child_ids[0])
        divider = result.session.elements.get(menu.child_ids[0])
        assert divider.component.name == "MenuDivider"

    def test_toolbar_with_children(self, rendered) -> None:
        """Toolbar renders children and stores props."""

        @component
        def App() -> None:
            with Toolbar(variant="minimal", orientation="vertical"):
                Button(text="Bold")
                Button(text="Italic")

        result = rendered(App)

        toolbar = result.session.elements.get(result.root_element.child_ids[0])
        assert toolbar.component.name == "Toolbar"
        assert toolbar.properties["variant"] == "minimal"
        assert toolbar.properties["orientation"] == "vertical"
        assert len(toolbar.child_ids) == 2
