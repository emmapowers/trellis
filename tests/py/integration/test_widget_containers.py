"""Tests for container widgets: Card, Divider, Heading."""

from trellis.core.components.composition import component
from trellis.core.rendering.render import render
from trellis.core.rendering.session import RenderSession
from trellis.widgets import Card, Column, Divider, Heading, Label


class TestCardAndDivider:
    """Tests for Card and Divider widgets."""

    def test_card_renders_children(self) -> None:
        """Card component renders its children."""

        @component
        def App() -> None:
            """
            Root test component that renders a Card containing a single Label with text "Inside card".
            
            Used by tests to produce an element tree where the Card component contains one Label child.
            """
            with Card():
                Label(text="Inside card")

        ctx = RenderSession(App)
        render(ctx)

        card = ctx.elements.get(ctx.root_element.child_ids[0])
        assert card.component.name == "Card"
        assert len(card.child_ids) == 1
        assert ctx.elements.get(card.child_ids[0]).component.name == "Label"

    def test_card_with_padding(self) -> None:
        """
        Verify that a Card element stores the provided `padding` property.
        """

        @component
        def App() -> None:
            """
            Render an App component containing a Card with padding set to 32 that wraps a Label with text "Content".
            """
            with Card(padding=32):
                Label(text="Content")

        ctx = RenderSession(App)
        render(ctx)

        card = ctx.elements.get(ctx.root_element.child_ids[0])
        assert card.properties["padding"] == 32

    def test_card_nested_in_layout(self) -> None:
        """Card can be nested inside layout widgets."""

        @component
        def App() -> None:
            """
            Declare a component that renders a Column containing two Card widgets, each with a Label.
            
            The first Card contains a Label with text "Card 1" and the second Card contains a Label with text "Card 2".
            """
            with Column():
                with Card():
                    Label(text="Card 1")
                with Card():
                    Label(text="Card 2")

        ctx = RenderSession(App)
        render(ctx)

        column = ctx.elements.get(ctx.root_element.child_ids[0])
        assert len(column.child_ids) == 2
        assert ctx.elements.get(column.child_ids[0]).component.name == "Card"
        assert ctx.elements.get(column.child_ids[1]).component.name == "Card"

    def test_divider_renders(self) -> None:
        """Divider component renders."""

        @component
        def App() -> None:
            """
            A test component that renders a Divider widget.
            
            Used in integration tests to produce a root element containing a single Divider for rendering assertions.
            """
            Divider()

        ctx = RenderSession(App)
        render(ctx)

        divider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert divider.component.name == "Divider"

    def test_divider_with_props(self) -> None:
        """Divider accepts margin and color props."""

        @component
        def App() -> None:
            """
            Render a Divider configured with margin 24 and color "#6366f1".
            """
            Divider(margin=24, color="#6366f1")

        ctx = RenderSession(App)
        render(ctx)

        divider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert divider.properties["margin"] == 24
        assert divider.properties["color"] == "#6366f1"

    def test_divider_vertical_orientation(self) -> None:
        """Divider accepts orientation prop."""

        @component
        def App() -> None:
            """
            Renders a vertical Divider component.
            
            This test component creates a Divider with orientation set to "vertical".
            """
            Divider(orientation="vertical")

        ctx = RenderSession(App)
        render(ctx)

        divider = ctx.elements.get(ctx.root_element.child_ids[0])
        assert divider.properties["orientation"] == "vertical"

    def test_divider_in_layout(self) -> None:
        """Divider can separate content in a layout."""

        @component
        def App() -> None:
            """
            Renders a Column containing a top label, a Divider, and a bottom label.
            
            The component creates a vertical layout with a Label displaying "Above", a Divider between items, and a Label displaying "Below".
            """
            with Column():
                Label(text="Above")
                Divider()
                Label(text="Below")

        ctx = RenderSession(App)
        render(ctx)

        column = ctx.elements.get(ctx.root_element.child_ids[0])
        assert len(column.child_ids) == 3
        assert ctx.elements.get(column.child_ids[0]).component.name == "Label"
        assert ctx.elements.get(column.child_ids[1]).component.name == "Divider"
        assert ctx.elements.get(column.child_ids[2]).component.name == "Label"


class TestHeadingWidget:
    """Tests for Heading widget."""

    def test_heading_with_text(self) -> None:
        """Heading stores text prop."""

        @component
        def App() -> None:
            """
            Simple app component that renders a Heading with text "Welcome".
            
            Used by tests to verify Heading rendering and propagation of the `text` property.
            """
            Heading(text="Welcome")

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.elements.get(ctx.root_element.child_ids[0])
        assert heading.component.name == "Heading"
        assert heading.properties["text"] == "Welcome"

    def test_heading_with_level(self) -> None:
        """
        Verify that Heading stores the provided heading level (1–6) in its properties.
        """

        @component
        def App() -> None:
            """
            Renders a Heading component with text "Section" at heading level 2.
            """
            Heading(text="Section", level=2)

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.elements.get(ctx.root_element.child_ids[0])
        assert heading.properties["level"] == 2

    def test_heading_with_color(self) -> None:
        """Heading accepts color prop."""

        @component
        def App() -> None:
            """
            Defines an app component that renders a Heading with text "Colored" and color "#333".
            """
            Heading(text="Colored", color="#333")

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.elements.get(ctx.root_element.child_ids[0])
        assert heading.properties["color"] == "#333"

    def test_heading_with_style(self) -> None:
        """Heading accepts style dict."""

        @component
        def App() -> None:
            """
            Render a Heading component with text "Styled" and a custom style.
            
            This component creates a Heading whose `text` is "Styled" and whose `style` property is {"marginBottom": "16px"}.
            """
            Heading(text="Styled", style={"marginBottom": "16px"})

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.elements.get(ctx.root_element.child_ids[0])
        assert heading.properties["style"] == {"marginBottom": "16px"}

    def test_heading_default_level(self) -> None:
        """Heading without explicit level has no level in properties."""

        @component
        def App() -> None:
            """
            Render an application component containing a Heading with the text "Default".
            """
            Heading(text="Default")

        ctx = RenderSession(App)
        render(ctx)

        heading = ctx.elements.get(ctx.root_element.child_ids[0])
        # Default values are applied by React client, not stored in properties
        assert "level" not in heading.properties