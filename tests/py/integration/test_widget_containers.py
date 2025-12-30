"""Tests for container widgets: Card, Divider, Heading."""

from trellis.core.components.composition import component
from trellis.widgets import Card, Column, Divider, Heading, Label


class TestCardAndDivider:
    """Tests for Card and Divider widgets."""

    def test_card_renders_children(self, rendered) -> None:
        """Card component renders its children."""

        @component
        def App() -> None:
            with Card():
                Label(text="Inside card")

        result = rendered(App)

        card = result.session.elements.get(result.root_element.child_ids[0])
        assert card.component.name == "Card"
        assert len(card.child_ids) == 1
        assert result.session.elements.get(card.child_ids[0]).component.name == "Label"

    def test_card_with_padding(self, rendered) -> None:
        """Card accepts padding prop."""

        @component
        def App() -> None:
            with Card(padding=32):
                Label(text="Content")

        result = rendered(App)

        card = result.session.elements.get(result.root_element.child_ids[0])
        assert card.properties["padding"] == 32

    def test_card_nested_in_layout(self, rendered) -> None:
        """Card can be nested inside layout widgets."""

        @component
        def App() -> None:
            with Column():
                with Card():
                    Label(text="Card 1")
                with Card():
                    Label(text="Card 2")

        result = rendered(App)

        column = result.session.elements.get(result.root_element.child_ids[0])
        assert len(column.child_ids) == 2
        assert result.session.elements.get(column.child_ids[0]).component.name == "Card"
        assert result.session.elements.get(column.child_ids[1]).component.name == "Card"

    def test_divider_renders(self, rendered) -> None:
        """Divider component renders."""

        @component
        def App() -> None:
            Divider()

        result = rendered(App)

        divider = result.session.elements.get(result.root_element.child_ids[0])
        assert divider.component.name == "Divider"

    def test_divider_with_props(self, rendered) -> None:
        """Divider accepts margin and color props."""

        @component
        def App() -> None:
            Divider(margin=24, color="#6366f1")

        result = rendered(App)

        divider = result.session.elements.get(result.root_element.child_ids[0])
        assert divider.properties["margin"] == 24
        assert divider.properties["color"] == "#6366f1"

    def test_divider_vertical_orientation(self, rendered) -> None:
        """Divider accepts orientation prop."""

        @component
        def App() -> None:
            Divider(orientation="vertical")

        result = rendered(App)

        divider = result.session.elements.get(result.root_element.child_ids[0])
        assert divider.properties["orientation"] == "vertical"

    def test_divider_in_layout(self, rendered) -> None:
        """Divider can separate content in a layout."""

        @component
        def App() -> None:
            with Column():
                Label(text="Above")
                Divider()
                Label(text="Below")

        result = rendered(App)

        column = result.session.elements.get(result.root_element.child_ids[0])
        assert len(column.child_ids) == 3
        assert result.session.elements.get(column.child_ids[0]).component.name == "Label"
        assert result.session.elements.get(column.child_ids[1]).component.name == "Divider"
        assert result.session.elements.get(column.child_ids[2]).component.name == "Label"


class TestHeadingWidget:
    """Tests for Heading widget."""

    def test_heading_with_text(self, rendered) -> None:
        """Heading stores text prop."""

        @component
        def App() -> None:
            Heading(text="Welcome")

        result = rendered(App)

        heading = result.session.elements.get(result.root_element.child_ids[0])
        assert heading.component.name == "Heading"
        assert heading.properties["text"] == "Welcome"

    def test_heading_with_level(self, rendered) -> None:
        """Heading accepts level prop for h1-h6."""

        @component
        def App() -> None:
            Heading(text="Section", level=2)

        result = rendered(App)

        heading = result.session.elements.get(result.root_element.child_ids[0])
        assert heading.properties["level"] == 2

    def test_heading_with_color(self, rendered) -> None:
        """Heading accepts color prop."""

        @component
        def App() -> None:
            Heading(text="Colored", color="#333")

        result = rendered(App)

        heading = result.session.elements.get(result.root_element.child_ids[0])
        assert heading.properties["color"] == "#333"

    def test_heading_with_style(self, rendered) -> None:
        """Heading accepts style dict."""

        @component
        def App() -> None:
            Heading(text="Styled", style={"marginBottom": "16px"})

        result = rendered(App)

        heading = result.session.elements.get(result.root_element.child_ids[0])
        assert heading.properties["style"] == {"marginBottom": "16px"}

    def test_heading_default_level(self, rendered) -> None:
        """Heading without explicit level has no level in properties."""

        @component
        def App() -> None:
            Heading(text="Default")

        result = rendered(App)

        heading = result.session.elements.get(result.root_element.child_ids[0])
        # Default values are applied by React client, not stored in properties
        assert "level" not in heading.properties
