"""Tests for Breadcrumb with native HTML elements and router integration."""

from trellis.core.components.composition import component
from trellis.widgets import Breadcrumb


def _get_breadcrumb_items(result, breadcrumb_el):
    """Helper to traverse breadcrumb structure and return list items."""
    # Structure: breadcrumb -> nav -> ol -> [li, li, ...]
    nav = result.session.elements.get(breadcrumb_el.child_ids[0])
    ol = result.session.elements.get(nav.child_ids[0])
    return [result.session.elements.get(li_id) for li_id in ol.child_ids]


def _get_li_content(result, li_el):
    """Get the content element from a li (skipping separator span if present)."""
    # Each li contains: [separator_span (if not first), content_span_or_a]
    # Return the last child which is the content
    if not li_el.child_ids:
        return None
    content_id = li_el.child_ids[-1]
    return result.session.elements.get(content_id)


class TestBreadcrumbNativeElements:
    """Tests for Breadcrumb generating native HTML elements."""

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

        # Get li items
        li_items = _get_breadcrumb_items(result, breadcrumb)
        assert len(li_items) == 3

        # First two items should have anchor elements (A)
        content1 = _get_li_content(result, li_items[0])
        assert content1.component.name == "A"
        assert content1.properties.get("href") == "/"

        content2 = _get_li_content(result, li_items[1])
        assert content2.component.name == "A"
        assert content2.properties.get("href") == "/products"

        # Last item (current page) should be a Span, not a link
        content3 = _get_li_content(result, li_items[2])
        assert content3.component.name == "Span"
        assert content3.properties.get("_text") == "Details"

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
        li_items = _get_breadcrumb_items(result, breadcrumb)

        # First item is an anchor with text
        anchor = _get_li_content(result, li_items[0])
        assert anchor.component.name == "A"
        assert anchor.properties.get("_text") == "Home"

    def test_breadcrumb_separator_rendered_between_items(self, rendered) -> None:
        """Breadcrumb renders separators between items."""

        @component
        def App() -> None:
            Breadcrumb(
                items=[{"label": "A", "href": "/"}, {"label": "B"}],
                separator=">",
            )

        result = rendered(App)

        breadcrumb = result.session.elements.get(result.root_element.child_ids[0])
        li_items = _get_breadcrumb_items(result, breadcrumb)

        # First li has no separator (only content)
        assert len(li_items[0].child_ids) == 1

        # Second li has separator + content
        assert len(li_items[1].child_ids) == 2
        separator = result.session.elements.get(li_items[1].child_ids[0])
        assert separator.component.name == "Span"
        assert separator.properties.get("_text") == ">"

    def test_breadcrumb_empty_items_renders_empty_ol(self, rendered) -> None:
        """Breadcrumb with empty items renders ol with no children."""

        @component
        def App() -> None:
            Breadcrumb(items=[])

        result = rendered(App)

        breadcrumb = result.session.elements.get(result.root_element.child_ids[0])
        nav = result.session.elements.get(breadcrumb.child_ids[0])
        ol = result.session.elements.get(nav.child_ids[0])
        assert len(ol.child_ids) == 0

    def test_breadcrumb_single_item_is_span(self, rendered) -> None:
        """Single breadcrumb item (current page) renders as span."""

        @component
        def App() -> None:
            Breadcrumb(items=[{"label": "Home"}])

        result = rendered(App)

        breadcrumb = result.session.elements.get(result.root_element.child_ids[0])
        li_items = _get_breadcrumb_items(result, breadcrumb)

        # Single item should be a Span (current page)
        content = _get_li_content(result, li_items[0])
        assert content.component.name == "Span"
        assert content.properties.get("_text") == "Home"
