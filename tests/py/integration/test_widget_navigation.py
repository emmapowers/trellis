"""Tests for navigation widgets: Icon, Tabs, Tree, Breadcrumb."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.widgets import Breadcrumb, Icon, Label, Tab, Tabs, Tree


class TestIconWidget:
    """Tests for Icon widget."""

    def test_icon_with_name(self) -> None:
        """Icon stores name prop."""

        @component
        def App() -> None:
            """
            Component that renders a single Icon with the name "check".
            """
            Icon(name="check")

        ctx = RenderSession(App)
        render(ctx)

        icon = ctx.elements.get(ctx.root_element.child_ids[0])
        assert icon.component.name == "Icon"
        assert icon.properties["name"] == "check"

    def test_icon_with_size_and_color(self) -> None:
        """Icon accepts size and color props."""

        @component
        def App() -> None:
            """
            Component that renders a single Icon configured as an alert triangle.
            
            Renders an Icon with name "alert-triangle", size 24, and color "#d97706".
            """
            Icon(name="alert-triangle", size=24, color="#d97706")

        ctx = RenderSession(App)
        render(ctx)

        icon = ctx.elements.get(ctx.root_element.child_ids[0])
        assert icon.properties["size"] == 24
        assert icon.properties["color"] == "#d97706"

    def test_icon_with_stroke_width(self) -> None:
        """Icon accepts stroke_width prop."""

        @component
        def App() -> None:
            Icon(name="circle", stroke_width=3)

        ctx = RenderSession(App)
        render(ctx)

        icon = ctx.elements.get(ctx.root_element.child_ids[0])
        assert icon.properties["stroke_width"] == 3


class TestNavigationWidgets:
    """Tests for navigation widgets."""

    def test_tabs_with_children(self) -> None:
        """Tabs renders children and stores props."""

        @component
        def App() -> None:
            """
            Defines an App component that renders an enclosed Tabs widget with two Tab children.
            
            Renders a Tabs container with selected tab "tab1" and variant "enclosed". The first Tab has id "tab1" and label "First" containing a Label with text "Content 1"; the second Tab has id "tab2" and label "Second" containing a Label with text "Content 2".
            """
            with Tabs(selected="tab1", variant="enclosed"):
                with Tab(id="tab1", label="First"):
                    Label(text="Content 1")
                with Tab(id="tab2", label="Second"):
                    Label(text="Content 2")

        ctx = RenderSession(App)
        render(ctx)

        tabs = ctx.elements.get(ctx.root_element.child_ids[0])
        assert tabs.component.name == "Tabs"
        assert tabs.properties["selected"] == "tab1"
        assert tabs.properties["variant"] == "enclosed"
        assert len(tabs.child_ids) == 2

    def test_tabs_with_callback(self) -> None:
        """Tabs captures on_change callback."""
        selections: list[str] = []

        @component
        def App() -> None:
            """
            Render a Tabs widget containing a single Tab labeled "Tab 1" with a Label as its content.
            
            The Tabs' on_change handler appends the selected tab id to the enclosing `selections` list.
            """
            with Tabs(on_change=lambda v: selections.append(v)):
                with Tab(id="t1", label="Tab 1"):
                    Label(text="Content")

        ctx = RenderSession(App)
        render(ctx)

        tabs = ctx.elements.get(ctx.root_element.child_ids[0])
        assert callable(tabs.properties["on_change"])

        tabs.properties["on_change"]("t2")
        assert selections == ["t2"]

    def test_tab_with_props(self) -> None:
        """Tab stores id, label, and other props."""

        @component
        def App() -> None:
            """
            Create an application component that renders a Tabs widget containing a single disabled Tab.
            
            The Tab has id "disabled-tab", label "Disabled", disabled set to True, icon "lock", and contains a Label with text "Content".
            """
            with Tabs():
                with Tab(id="disabled-tab", label="Disabled", disabled=True, icon="lock"):
                    Label(text="Content")

        ctx = RenderSession(App)
        render(ctx)

        tabs = ctx.elements.get(ctx.root_element.child_ids[0])
        tab = ctx.elements.get(tabs.child_ids[0])
        assert tab.component.name == "Tab"
        assert tab.properties["id"] == "disabled-tab"
        assert tab.properties["label"] == "Disabled"
        assert tab.properties["disabled"] is True
        assert tab.properties["icon"] == "lock"

    def test_tree_with_data(self) -> None:
        """Tree stores data and selection props."""

        @component
        def App() -> None:
            """
            Render a Tree component with a root node and a single child, preselecting and expanding the root.
            
            The tree's data contains a root node (id "1", label "Root") with one child (id "1.1", label "Child"). The root node is set as the selected node and included in the expanded nodes.
            """
            Tree(
                data=[{"id": "1", "label": "Root", "children": [{"id": "1.1", "label": "Child"}]}],
                selected="1",
                expanded=["1"],
            )

        ctx = RenderSession(App)
        render(ctx)

        tree = ctx.elements.get(ctx.root_element.child_ids[0])
        assert tree.component.name == "Tree"
        assert tree.properties["selected"] == "1"
        assert tree.properties["expanded"] == ["1"]

    def test_tree_with_callbacks(self) -> None:
        """Tree captures on_select and on_expand callbacks."""
        selections: list[str] = []
        expansions: list[tuple[str, bool]] = []

        @component
        def App() -> None:
            """
            Renders a Tree component with a single root node and attaches callbacks that record selection and expansion events.
            
            The Tree is created with one node (id "1", label "Root"). The `on_select` callback appends the selected node id to the external `selections` list; the `on_expand` callback appends a tuple (node id, expanded) to the external `expansions` list.
            """
            Tree(
                data=[{"id": "1", "label": "Root"}],
                on_select=lambda v: selections.append(v),
                on_expand=lambda id, exp: expansions.append((id, exp)),
            )

        ctx = RenderSession(App)
        render(ctx)

        tree = ctx.elements.get(ctx.root_element.child_ids[0])
        tree.properties["on_select"]("1")
        tree.properties["on_expand"]("1", True)

        assert selections == ["1"]
        assert expansions == [("1", True)]

    def test_breadcrumb_with_items(self) -> None:
        """Breadcrumb stores items and separator props."""

        @component
        def App() -> None:
            """
            Render a Breadcrumb component with three items and a ">" separator.
            
            Used by tests to instantiate a Breadcrumb with items labeled "Home", "Products", and "Details" and a separator of ">".
            """
            Breadcrumb(
                items=[{"label": "Home"}, {"label": "Products"}, {"label": "Details"}],
                separator=">",
            )

        ctx = RenderSession(App)
        render(ctx)

        breadcrumb = ctx.elements.get(ctx.root_element.child_ids[0])
        assert breadcrumb.component.name == "Breadcrumb"
        assert len(breadcrumb.properties["items"]) == 3
        assert breadcrumb.properties["separator"] == ">"

    def test_breadcrumb_with_callback(self) -> None:
        """Breadcrumb captures on_click callback."""
        clicks: list[int] = []

        @component
        def App() -> None:
            """
            Create a Breadcrumb component with two items and an index click handler.
            
            Renders a Breadcrumb containing "Home" and "Page" items and supplies an on_click callback that appends the clicked item's index to the enclosing `clicks` list.
            """
            Breadcrumb(
                items=[{"label": "Home"}, {"label": "Page"}],
                on_click=lambda idx: clicks.append(idx),
            )

        ctx = RenderSession(App)
        render(ctx)

        breadcrumb = ctx.elements.get(ctx.root_element.child_ids[0])
        breadcrumb.properties["on_click"](0)
        assert clicks == [0]