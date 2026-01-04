"""Tests for Breadcrumb with native Trellis anchor elements and router integration."""

from trellis.core.components.composition import component
from trellis.widgets import Breadcrumb


class TestBreadcrumbNativeAnchors:
    """Tests for Breadcrumb generating native Trellis elements."""

    def test_breadcrumb_generates_anchor_children(self, rendered) -> None:
        """Breadcrumb items with href generate native html.A elements."""

        @component
        def App() -> None:
            Breadcrumb(
                items=[
                    {"label": "Home", "href": "/"},
                    {"label": "Products", "href": "/products"},
                    {"label": "Details"},  # Current page, no href
                ],
            )

        result = rendered(App)

        # Breadcrumb should be a composition component
        breadcrumb = result.session.elements.get(result.root_element.child_ids[0])
        assert breadcrumb.component.name == "Breadcrumb"

        # Should have a container child
        container = result.session.elements.get(breadcrumb.child_ids[0])
        assert container.component.name == "_BreadcrumbContainer"

        # Container should have 3 children (the breadcrumb items)
        assert len(container.child_ids) == 3

        # First two items should be anchor elements (A)
        item1 = result.session.elements.get(container.child_ids[0])
        assert item1.component.name == "A"
        assert item1.properties.get("href") == "/"

        item2 = result.session.elements.get(container.child_ids[1])
        assert item2.component.name == "A"
        assert item2.properties.get("href") == "/products"

        # Last item (current page) should be a Label, not a link
        item3 = result.session.elements.get(container.child_ids[2])
        assert item3.component.name == "Label"
        assert item3.properties.get("text") == "Details"

    def test_breadcrumb_anchor_has_label_text(self, rendered) -> None:
        """Breadcrumb anchor elements contain the label text."""

        @component
        def App() -> None:
            Breadcrumb(
                items=[
                    {"label": "Home", "href": "/"},
                    {"label": "Current"},
                ],
            )

        result = rendered(App)

        breadcrumb = result.session.elements.get(result.root_element.child_ids[0])
        container = result.session.elements.get(breadcrumb.child_ids[0])

        # First item is an anchor with text
        anchor = result.session.elements.get(container.child_ids[0])
        assert anchor.component.name == "A"
        assert anchor.properties.get("_text") == "Home"

    def test_breadcrumb_separator_prop_passed_to_container(self, rendered) -> None:
        """Breadcrumb passes separator prop to container."""

        @component
        def App() -> None:
            Breadcrumb(
                items=[{"label": "A", "href": "/"}, {"label": "B"}],
                separator=">",
            )

        result = rendered(App)

        breadcrumb = result.session.elements.get(result.root_element.child_ids[0])
        container = result.session.elements.get(breadcrumb.child_ids[0])
        assert container.properties.get("separator") == ">"

    def test_breadcrumb_empty_items_renders_empty_container(self, rendered) -> None:
        """Breadcrumb with empty items renders container with no children."""

        @component
        def App() -> None:
            Breadcrumb(items=[])

        result = rendered(App)

        breadcrumb = result.session.elements.get(result.root_element.child_ids[0])
        container = result.session.elements.get(breadcrumb.child_ids[0])
        assert len(container.child_ids) == 0

    def test_breadcrumb_single_item_is_label(self, rendered) -> None:
        """Single breadcrumb item (current page) renders as Label."""

        @component
        def App() -> None:
            Breadcrumb(items=[{"label": "Home"}])

        result = rendered(App)

        breadcrumb = result.session.elements.get(result.root_element.child_ids[0])
        container = result.session.elements.get(breadcrumb.child_ids[0])

        # Single item should be a Label (current page)
        item = result.session.elements.get(container.child_ids[0])
        assert item.component.name == "Label"
        assert item.properties.get("text") == "Home"
