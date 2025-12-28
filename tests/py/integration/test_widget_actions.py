"""Tests for action widgets: Callout, Collapsible, Menu, Toolbar."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
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

    def test_callout_with_title_and_intent(self) -> None:
        """Callout stores title and intent props."""

        @component
        def App() -> None:
            """
            Create a small test application containing a warning Callout with a label.
            
            Defines a Callout titled "Warning" with intent "warning" that contains a Label with the text "Be careful!".
            """
            with Callout(title="Warning", intent="warning"):
                Label(text="Be careful!")

        ctx = RenderSession(App)
        render(ctx)

        callout = ctx.elements.get(ctx.root_element.child_ids[0])
        assert callout.component.name == "Callout"
        assert callout.properties["title"] == "Warning"
        assert callout.properties["intent"] == "warning"
        assert len(callout.child_ids) == 1

    def test_callout_dismissible_with_callback(self) -> None:
        """Callout captures on_dismiss callback when dismissible."""
        dismissed = []

        @component
        def App() -> None:
            with Callout(dismissible=True, on_dismiss=lambda: dismissed.append(True)):
                Label(text="Dismissable")

        ctx = RenderSession(App)
        render(ctx)

        callout = ctx.elements.get(ctx.root_element.child_ids[0])
        assert callout.properties["dismissible"] is True
        callout.properties["on_dismiss"]()
        assert dismissed == [True]

    def test_collapsible_with_title(self) -> None:
        """Collapsible stores title and expanded props."""

        @component
        def App() -> None:
            """
            Define a component tree with a collapsed Collapsible titled "Details" containing a Label.
            
            The Collapsible is created with expanded set to False and contains a single Label with text "Hidden content".
            """
            with Collapsible(title="Details", expanded=False):
                Label(text="Hidden content")

        ctx = RenderSession(App)
        render(ctx)

        collapsible = ctx.elements.get(ctx.root_element.child_ids[0])
        assert collapsible.component.name == "Collapsible"
        assert collapsible.properties["title"] == "Details"
        assert collapsible.properties["expanded"] is False

    def test_collapsible_with_callback(self) -> None:
        """Collapsible captures on_toggle callback."""
        toggles: list[bool] = []

        @component
        def App() -> None:
            """
            Create an App component that renders a Collapsible titled "Toggle" containing a Label.
            
            The Collapsible's on_toggle callback appends the new expanded state to the outer-scope list `toggles`.
            """
            with Collapsible(title="Toggle", on_toggle=lambda v: toggles.append(v)):
                Label(text="Content")

        ctx = RenderSession(App)
        render(ctx)

        collapsible = ctx.elements.get(ctx.root_element.child_ids[0])
        collapsible.properties["on_toggle"](True)
        assert toggles == [True]


class TestActionWidgets:
    """Tests for action widgets."""

    def test_menu_with_items(self) -> None:
        """Menu renders children."""

        @component
        def App() -> None:
            """
            Create an application menu containing common file actions.
            
            The menu contains four entries in order: "Open", "Save", a divider, and "Exit".
            """
            with Menu():
                MenuItem(text="Open")
                MenuItem(text="Save")
                MenuDivider()
                MenuItem(text="Exit")

        ctx = RenderSession(App)
        render(ctx)

        menu = ctx.elements.get(ctx.root_element.child_ids[0])
        assert menu.component.name == "Menu"
        assert len(menu.child_ids) == 4

    def test_menu_item_with_props(self) -> None:
        """
        Verifies that a MenuItem preserves the provided properties `text`, `icon`, `disabled`, and `shortcut`.
        """

        @component
        def App() -> None:
            """
            Defines a test application that renders a Menu containing a single disabled "Delete" MenuItem.
            
            The MenuItem is labeled "Delete", uses the "trash" icon, is disabled, and has the shortcut "Ctrl+D".
            """
            with Menu():
                MenuItem(text="Delete", icon="trash", disabled=True, shortcut="Ctrl+D")

        ctx = RenderSession(App)
        render(ctx)

        menu = ctx.elements.get(ctx.root_element.child_ids[0])
        item = ctx.elements.get(menu.child_ids[0])
        assert item.component.name == "MenuItem"
        assert item.properties["text"] == "Delete"
        assert item.properties["icon"] == "trash"
        assert item.properties["disabled"] is True
        assert item.properties["shortcut"] == "Ctrl+D"

    def test_menu_item_with_callback(self) -> None:
        """
        Verifies that a MenuItem calls its `on_click` callback when invoked.
        
        Sets up a MenuItem with an `on_click` handler that records a value and asserts the handler was executed.
        """
        clicks = []

        @component
        def App() -> None:
            """
            Test App component that renders a Menu containing a single MenuItem wired to record clicks.
            
            Defines a Menu with one MenuItem whose `on_click` callback appends `True` to the outer `clicks` list.
            """
            with Menu():
                MenuItem(text="Click me", on_click=lambda: clicks.append(True))

        ctx = RenderSession(App)
        render(ctx)

        menu = ctx.elements.get(ctx.root_element.child_ids[0])
        item = ctx.elements.get(menu.child_ids[0])
        item.properties["on_click"]()
        assert clicks == [True]

    def test_menu_divider_renders(self) -> None:
        """MenuDivider component renders."""

        @component
        def App() -> None:
            """
            Defines an App component that renders a Menu with a single MenuDivider child.
            
            This component is intended for tests that verify a Menu containing a divider renders correctly.
            """
            with Menu():
                MenuDivider()

        ctx = RenderSession(App)
        render(ctx)

        menu = ctx.elements.get(ctx.root_element.child_ids[0])
        divider = ctx.elements.get(menu.child_ids[0])
        assert divider.component.name == "MenuDivider"

    def test_toolbar_with_children(self) -> None:
        """Toolbar renders children and stores props."""

        @component
        def App() -> None:
            """
            Create a Toolbar with variant "minimal" and vertical orientation containing two Buttons labeled "Bold" and "Italic".
            
            This component is used in tests to verify Toolbar rendering, its `variant` and `orientation` properties, and that it contains two child Button elements.
            """
            with Toolbar(variant="minimal", orientation="vertical"):
                Button(text="Bold")
                Button(text="Italic")

        ctx = RenderSession(App)
        render(ctx)

        toolbar = ctx.elements.get(ctx.root_element.child_ids[0])
        assert toolbar.component.name == "Toolbar"
        assert toolbar.properties["variant"] == "minimal"
        assert toolbar.properties["orientation"] == "vertical"
        assert len(toolbar.child_ids) == 2